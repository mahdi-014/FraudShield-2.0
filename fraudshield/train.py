"""Run from project root: python -m fraudshield.train --data-zip PATH."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import zipfile
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, roc_auc_score,
    precision_recall_curve, confusion_matrix, precision_score, recall_score, f1_score)
from xgboost import XGBClassifier
from .features import RAW_FEATURES, SCHEMA_VERSION, make_features, make_preprocessor

def split_time(data):
    # Boundary ties stay together. Nothing at a cutoff is split across partitions.
    cut1, cut2 = data.TransactionDT.quantile([.70, .85]).to_numpy()
    parts = [data[data.TransactionDT <= cut1],
             data[(data.TransactionDT > cut1) & (data.TransactionDT <= cut2)],
             data[data.TransactionDT > cut2]]
    if any(len(p) == 0 or p.isFraud.nunique() != 2 for p in parts):
        raise ValueError('Each chronological partition must contain both classes')
    return parts, [float(cut1), float(cut2)]

def choose_threshold(y, scores, review_budget=.10):
    precision, recall, thresholds = precision_recall_curve(y, scores)
    precision, recall = precision[:-1], recall[:-1]
    f2 = 5 * precision * recall / np.maximum(4 * precision + recall, 1e-12)
    ordered = np.sort(scores)
    rates = (len(scores) - np.searchsorted(ordered, thresholds, side='left')) / len(scores)
    eligible = np.flatnonzero(rates <= review_budget)
    if not len(eligible):
        raise ValueError('No threshold satisfies review budget')
    best = eligible[np.argmax(f2[eligible])]
    return float(thresholds[best]), {'objective': 'maximize validation F2 under hold-rate budget',
        'hold_rate_budget': review_budget, 'validation_hold_rate': float(rates[best]),
        'validation_precision': float(precision[best]), 'validation_recall': float(recall[best])}

def metrics(y, scores, threshold):
    pred = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'average_precision': float(average_precision_score(y, scores)),
        'roc_auc': float(roc_auc_score(y, scores)),
        'precision': float(precision_score(y, pred, zero_division=0)),
        'recall': float(recall_score(y, pred, zero_division=0)),
        'f1': float(f1_score(y, pred, zero_division=0)),
        'false_positive_rate': float(fp / (fp + tn)),
        'hold_rate': float(pred.mean()), 'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)},
        'threshold': threshold}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-zip', required=True, type=Path)
    parser.add_argument('--output', default='artifacts', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print('Loading selected IEEE-CIS columns', flush=True)
    with zipfile.ZipFile(args.data_zip) as archive:
        with archive.open('train_transaction.csv') as stream:
            transaction = pd.read_csv(stream, usecols=lambda c: c in RAW_FEATURES + ['TransactionID', 'isFraud'])
        with archive.open('train_identity.csv') as stream:
            identity = pd.read_csv(stream, usecols=['TransactionID', 'DeviceType', 'DeviceInfo'])
    if transaction.TransactionID.duplicated().any() or identity.TransactionID.duplicated().any():
        raise ValueError('Duplicate transaction keys')
    data = transaction.merge(identity, how='left', on='TransactionID', validate='one_to_one')
    parts, cutoffs = split_time(data)
    train, validation, test = parts
    print('Chronological rows:', [len(p) for p in parts], flush=True)
    prep = make_preprocessor()
    x_train = prep.fit_transform(make_features(train))
    x_val = prep.transform(make_features(validation))
    x_test = prep.transform(make_features(test))
    y_train, y_val, y_test = [p.isFraud.to_numpy() for p in parts]
    print('Training logistic baseline', flush=True)
    baseline = LogisticRegression(solver='saga', max_iter=500, tol=.001,
                                  class_weight='balanced', random_state=42)
    baseline.fit(x_train, y_train)
    base_val = baseline.predict_proba(x_val)[:, 1]
    base_threshold, base_policy = choose_threshold(y_val, base_val)
    print('Training XGBoost', flush=True)
    model = XGBClassifier(n_estimators=220, max_depth=6, learning_rate=.08,
        tree_method='hist', n_jobs=4, subsample=.85, colsample_bytree=.85,
        min_child_weight=5, reg_lambda=3, random_state=42, eval_metric='aucpr',
        scale_pos_weight=float((y_train == 0).sum() / (y_train == 1).sum()))
    model.fit(x_train, y_train)
    val_scores = model.predict_proba(x_val)[:, 1]
    threshold, policy_selection = choose_threshold(y_val, val_scores)
    # Candidate and thresholds fixed before held-out test metrics are computed.
    print('Evaluating locked candidates on held-out test', flush=True)
    test_scores = model.predict_proba(x_test)[:, 1]
    baseline_test = baseline.predict_proba(x_test)[:, 1]
    model_version = 'ieee-xgb-v0.1.0'
    policy = {'version': 'research-policy-v0.1.0', 'warn': threshold*.25,
              'pause': threshold*.60, 'hold': threshold,
              'note': 'Only hold threshold tuned; warn and pause bands are illustrative research policy.'}
    report = {'model_version': model_version, 'schema_version': SCHEMA_VERSION,
        'dataset_sha256': hashlib.file_digest(args.data_zip.open('rb'), 'sha256').hexdigest(),
        'raw_feature_contract': RAW_FEATURES, 'encoded_feature_count': x_train.shape[1],
        'split': {'method': 'chronological 70/15/15 with boundary ties grouped', 'cutoffs': cutoffs,
            'parts': [{ 'name': name, 'rows': len(p), 'frauds': int(p.isFraud.sum()),
                'time_min': float(p.TransactionDT.min()), 'time_max': float(p.TransactionDT.max())}
                for name, p in zip(['train', 'validation', 'test'], parts)]},
        'data_summary': {'rows': len(data), 'frauds': int(data.isFraud.sum()),
            'identity_coverage': len(identity)/len(data),
            'missing_fraction': data[RAW_FEATURES].isna().mean().to_dict()},
        'baseline': {'validation': metrics(y_val, base_val, base_threshold),
                     'test': metrics(y_test, baseline_test, base_threshold), 'threshold_selection': base_policy},
        'xgboost': {'validation': metrics(y_val, val_scores, threshold),
                    'test': metrics(y_test, test_scores, threshold), 'threshold_selection': policy_selection},
        'policy': policy,
        'runtime_versions': {p: importlib.metadata.version(p) for p in ['pandas','numpy','scipy','scikit-learn','xgboost','joblib']},
        'limitations': ['Historical IEEE-CIS replay only; not validated on Bangladesh MFS or bank transfers.',
            'Scores are uncalibrated; class weighting changes their interpretation.',
            'Feature availability at payment authorization must be verified with a real provider.',
            'No customer IDs or unique device IDs; no claimed account/network fraud evidence.',
            'Identity coverage is partial; DeviceInfo is a description, not a unique identifier.',
            'XGBoost is an integration candidate; compare baseline before promoting.',
            'No hyperparameter search; first fixed baseline experiment.'],
        'training_seconds': time.perf_counter()-started}
    model.save_model(args.output/'model.ubj')
    joblib.dump(prep, args.output/'preprocessor.joblib')
    joblib.dump(baseline, args.output/'baseline.joblib')
    (args.output/'metadata.json').write_text(json.dumps(report, indent=2))
    # Fixed demo sample: first held-out fraud and legitimate transaction, not selected by score.
    for label, name in [(0,'legitimate'), (1,'fraud')]:
        row = test[test.isFraud == label].iloc[0]
        feature_dict = json.loads(row[RAW_FEATURES].to_json())
        sample = {'transaction_id': str(int(row.TransactionID)), 'features': feature_dict}
        (args.output/f'sample_{name}.json').write_text(json.dumps(sample, indent=2))
    lines = ['# FraudShield first model evaluation', '',
        'Historical IEEE-CIS dataset replay. No production or Bangladesh MFS validation.', '',
        '| Model | Test AP | Precision | Recall | FPR | Hold rate |',
        '|---|---:|---:|---:|---:|---:|']
    for name in ['baseline','xgboost']:
        r=report[name]['test']
        lines.append(f"| {name} | {r['average_precision']:.4f} | {r['precision']:.2%} | {r['recall']:.2%} | {r['false_positive_rate']:.2%} | {r['hold_rate']:.2%} |")
    lines += ['', 'AP means average precision, a discrete precision-recall summary; not trapezoidal PR-AUC.', '',
        'Hold thresholds maximize validation F2 with a validation hold-rate cap of 10%. The cap is not guaranteed on future data.', '',
        '## Split', *[f"- {p['name']}: {p['rows']:,} rows, {p['frauds']:,} fraud labels" for p in report['split']['parts']],
        '', '## Limitations', *['- '+s for s in report['limitations']], '',
        'See metadata.json for full metrics, confusion matrices, policy, provenance and runtime versions.']
    (args.output/'evaluation.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'test': report['xgboost']['test'], 'seconds': report['training_seconds']}), flush=True)

if __name__ == '__main__':
    main()
