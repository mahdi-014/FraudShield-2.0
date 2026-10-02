import json
from pathlib import Path
import time
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from .features import RAW_FEATURES, NUMERIC, CATEGORICAL, make_features

def apply_policy(score, policy):
    for action in ['hold', 'pause', 'warn']:
        if score >= policy[action]:
            return action, [f"Model score meets {action} threshold ({policy[action]:.6f})"]
    return 'allow', ['Model score is below the warning threshold']

class Scorer:
    def __init__(self, directory):
        directory = Path(directory)
        self.metadata = json.loads((directory/'metadata.json').read_text())
        self.preprocessor = joblib.load(directory/'preprocessor.joblib')
        self.model = xgb.XGBClassifier(n_jobs=1)
        self.model.load_model(directory/'model.ubj')
        self.model.set_params(n_jobs=1)
        self.booster = self.model.get_booster()
        self.booster.set_param({'nthread': 1})
        names = self.preprocessor.get_feature_names_out()
        self.group_names = []
        for encoded in names:
            if encoded.startswith('num__'):
                self.group_names.append(encoded[5:])
            else:
                matched = [c for c in CATEGORICAL if encoded[5:].startswith(c+'_')]
                if not matched:
                    raise ValueError('Cannot map encoded feature '+encoded)
                self.group_names.append(max(matched, key=len))

    def score(self, transaction_id, features):
        start = time.perf_counter()
        unknown = set(features)-set(RAW_FEATURES)
        if unknown:
            raise ValueError('Unknown or forbidden input features: '+', '.join(sorted(unknown)))
        raw = pd.DataFrame([features])
        engineered = make_features(raw)
        encoded = self.preprocessor.transform(engineered)
        matrix = xgb.DMatrix(encoded, nthread=1)
        score = float(self.booster.predict(matrix)[0])
        contributions = self.booster.predict(matrix, pred_contribs=True)[0]
        groups = {}
        for name, value in zip(self.group_names, contributions[:-1]):
            groups[name] = groups.get(name, 0.0)+float(value)
        margin = float(self.booster.predict(matrix, output_margin=True)[0])
        base = float(contributions[-1])
        if not np.isclose(base+sum(groups.values()), margin, atol=1e-4):
            raise RuntimeError('Explanation does not reconcile with prediction')
        action, reasons = apply_policy(score, self.metadata['policy'])
        top = sorted(groups.items(), key=lambda pair: abs(pair[1]), reverse=True)[:5]
        return {'transaction_id': transaction_id, 'model_score': score,
            'score_interpretation': 'uncalibrated model score, not validated fraud probability',
            'action': action, 'policy_reasons': reasons,
            'model_factors': [{'feature': name, 'contribution_log_odds': value,
                'direction': 'increases_score' if value>0 else 'decreases_score',
                'value': engineered.iloc[0][name] if name in CATEGORICAL else
                    (float(engineered.iloc[0][name]) if pd.notna(engineered.iloc[0][name]) else None)}
                for name, value in top],
            'explanation': {'method': 'XGBoost TreeSHAP', 'units': 'log odds',
                'base_margin': base, 'all_feature_contributions_sum': sum(groups.values()),
                'model_margin': margin, 'note': 'Top factors are associations, not causal proof or full explanation sum.'},
            'missing_features': [f for f in RAW_FEATURES if features.get(f) is None],
            'model_version': self.metadata['model_version'],
            'policy_version': self.metadata['policy']['version'],
            'schema_version': self.metadata['schema_version'],
            'mode': 'historical_dataset_replay',
            'processing_ms': (time.perf_counter()-start)*1000}
