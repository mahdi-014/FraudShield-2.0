# FraudShield first model evaluation

Historical IEEE-CIS dataset replay. No production or Bangladesh MFS validation.

| Model | Test AP | Precision | Recall | FPR | Hold rate |
|---|---:|---:|---:|---:|---:|
| baseline | 0.1351 | 13.33% | 44.63% | 10.47% | 11.66% |
| xgboost | 0.2109 | 19.62% | 44.92% | 6.64% | 7.97% |

AP means average precision, a discrete precision-recall summary; not trapezoidal PR-AUC.

Hold thresholds maximize validation F2 with a validation hold-rate cap of 10%. The cap is not guaranteed on future data.

## Split
- train: 413,378 rows, 14,538 fraud labels
- validation: 88,581 rows, 3,042 fraud labels
- test: 88,581 rows, 3,083 fraud labels

## Limitations
- Historical IEEE-CIS replay only; not validated on Bangladesh MFS or bank transfers.
- Scores are uncalibrated; class weighting changes their interpretation.
- Feature availability at payment authorization must be verified with a real provider.
- No customer IDs or unique device IDs; no claimed account/network fraud evidence.
- Identity coverage is partial; DeviceInfo is a description, not a unique identifier.
- XGBoost is an integration candidate; compare baseline before promoting.
- No hyperparameter search; first fixed baseline experiment.

See metadata.json for full metrics, confusion matrices, policy, provenance and runtime versions.
