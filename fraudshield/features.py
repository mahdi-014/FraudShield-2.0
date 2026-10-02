"""One authoritative feature contract for training and inference."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ['TransactionAmt', 'dist1', 'dist2', 'relative_hour_sin', 'relative_hour_cos']
CATEGORICAL = ['ProductCD', 'card1', 'card2', 'card3', 'card4', 'card5', 'card6',
               'addr1', 'addr2', 'P_emaildomain', 'R_emaildomain', 'DeviceType', 'DeviceInfo']
RAW_NUMERIC = ['TransactionAmt', 'TransactionDT', 'dist1', 'dist2']
RAW_FEATURES = RAW_NUMERIC + CATEGORICAL
SCHEMA_VERSION = 'ieee-replay-v1'

def make_features(raw):
    frame = raw.reindex(columns=RAW_FEATURES).copy()
    for name in RAW_NUMERIC:
        frame[name] = pd.to_numeric(frame[name], errors='raise').astype(float)
    if np.isinf(frame[RAW_NUMERIC].to_numpy()).any():
        raise ValueError('Infinite numeric features are not supported')
    hour = (frame['TransactionDT'] % 86400) / 86400 * 2 * np.pi
    frame['relative_hour_sin'] = np.sin(hour)
    frame['relative_hour_cos'] = np.cos(hour)
    # Time is relative to an undisclosed origin, not verified local clock time.
    for name in CATEGORICAL:
        def normalize(value):
            if pd.isna(value):
                return '__MISSING__'
            if isinstance(value, (int, float, np.number)):
                return format(float(value), '.15g')
            return str(value)
        frame[name] = frame[name].map(normalize)
    return frame[NUMERIC + CATEGORICAL]

def make_preprocessor():
    numeric = Pipeline([
        ('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
        ('scale', StandardScaler()),
    ])
    return ColumnTransformer([
        ('num', numeric, NUMERIC),
        ('cat', OneHotEncoder(handle_unknown='infrequent_if_exist',
                              max_categories=128, min_frequency=50,
                              dtype=np.float32), CATEGORICAL),
    ], sparse_threshold=1.0)
