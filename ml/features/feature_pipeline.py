import numpy as np
import pandas as pd
from typing import Dict, List, Any


FEATURE_COLUMNS = [
    "amount",
    "amount_log",
    "transaction_hour",
    "transaction_day_of_week",
    "is_weekend",
    "amount_deviation",
    "transaction_velocity_1h",
    "transaction_velocity_24h",
    "time_since_last_txn_min",
    "device_novelty",
    "beneficiary_novelty",
    "shared_device_count",
    "shared_ip_count",
    "is_high_risk_type",
]


class FeaturePipeline:
    """
    Extracts transaction, behavioral, network, and temporal features from transactions dataframe or live dictionary.
    Enforces identical feature schema across training and online inference.
    """

    def __init__(self):
        self.feature_columns = FEATURE_COLUMNS

    def extract_dataframe_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Datetime processing
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        df["amount_log"] = np.log1p(df["amount"])
        df["transaction_hour"] = df["timestamp"].dt.hour
        df["transaction_day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_weekend"] = df["transaction_day_of_week"].apply(lambda x: 1 if x >= 5 else 0)

        # High risk transaction types
        df["is_high_risk_type"] = df["transaction_type"].apply(lambda x: 1 if x in ["WIRE", "P2P"] else 0)

        # Behavioral & Temporal Windowing
        df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

        # User historical rolling statistics
        user_means = df.groupby("user_id")["amount"].transform("mean")
        user_stds = df.groupby("user_id")["amount"].transform("std").fillna(10.0)
        df["amount_deviation"] = (df["amount"] - user_means) / (user_stds + 1e-5)
        df["amount_deviation"] = df["amount_deviation"].clip(lower=-3.0, upper=15.0)

        # Time since last transaction
        df["prev_timestamp"] = df.groupby("user_id")["timestamp"].shift(1)
        df["time_since_last_txn_min"] = (df["timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 60.0
        df["time_since_last_txn_min"] = df["time_since_last_txn_min"].fillna(1440.0).clip(upper=10080.0)

        # Device & Beneficiary Novelty (first time seen for this user)
        df["user_device_first"] = df.groupby(["user_id", "device_id"])["timestamp"].transform("min")
        df["device_novelty"] = (df["timestamp"] == df["user_device_first"]).astype(int)

        df["user_ben_first"] = df.groupby(["user_id", "beneficiary_id"])["timestamp"].transform("min")
        df["beneficiary_novelty"] = (df["timestamp"] == df["user_ben_first"]).astype(int)

        # Network Infrastructure Sharing
        device_users = df.groupby("device_id")["user_id"].transform("nunique")
        df["shared_device_count"] = device_users

        ip_users = df.groupby("ip_address_hash")["user_id"].transform("nunique")
        df["shared_ip_count"] = ip_users

        # Velocity (transactions in last 1h and 24h)
        # Using simplified expanding rolling count for batch pipeline
        df["transaction_velocity_1h"] = 1
        df["transaction_velocity_24h"] = 1

        for u_id, group in df.groupby("user_id"):
            times = group["timestamp"].values
            for idx, curr_t in enumerate(times):
                row_idx = group.index[idx]
                t_1h_ago = curr_t - np.timedelta64(1, 'h')
                t_24h_ago = curr_t - np.timedelta64(24, 'h')
                
                cnt_1h = np.sum((times[:idx+1] >= t_1h_ago) & (times[:idx+1] <= curr_t))
                cnt_24h = np.sum((times[:idx+1] >= t_24h_ago) & (times[:idx+1] <= curr_t))
                
                df.at[row_idx, "transaction_velocity_1h"] = cnt_1h
                df.at[row_idx, "transaction_velocity_24h"] = cnt_24h

        return df[self.feature_columns]

    def extract_single_transaction_features(
        self,
        transaction_data: Dict[str, Any],
        user_history: List[Dict[str, Any]],
        network_stats: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Extract feature vector for live single transaction inference against historical profile.
        """
        amount = float(transaction_data.get("amount", 0.0))
        amount_log = float(np.log1p(amount))

        ts_str = transaction_data.get("timestamp")
        if isinstance(ts_str, str):
            ts = pd.to_datetime(ts_str)
        else:
            ts = pd.Timestamp.now()

        hour = ts.hour
        dayofweek = ts.dayofweek
        is_weekend = 1 if dayofweek >= 5 else 0
        is_high_risk = 1 if transaction_data.get("transaction_type") in ["WIRE", "P2P"] else 0

        # Behavioral stats from history
        if user_history:
            amounts = [h.get("amount", amount) for h in user_history]
            mean_amt = float(np.mean(amounts))
            std_amt = float(np.std(amounts)) if len(amounts) > 1 else 10.0
            amt_dev = (amount - mean_amt) / (std_amt + 1e-5)
            amt_dev = float(np.clip(amt_dev, -3.0, 15.0))

            last_ts = pd.to_datetime(user_history[-1].get("timestamp"))
            time_since = (ts - last_ts).total_seconds() / 60.0
            time_since = float(np.clip(time_since, 0.0, 10080.0))

            seen_devices = {h.get("device_id") for h in user_history}
            device_novelty = 0 if transaction_data.get("device_id") in seen_devices else 1

            seen_bens = {h.get("beneficiary_id") for h in user_history}
            ben_novelty = 0 if transaction_data.get("beneficiary_id") in seen_bens else 1

            t_1h_ago = ts - pd.Timedelta(hours=1)
            t_24h_ago = ts - pd.Timedelta(hours=24)
            vel_1h = sum(1 for h in user_history if pd.to_datetime(h.get("timestamp")) >= t_1h_ago) + 1
            vel_24h = sum(1 for h in user_history if pd.to_datetime(h.get("timestamp")) >= t_24h_ago) + 1
        else:
            amt_dev = 0.0
            time_since = 1440.0
            device_novelty = 1
            ben_novelty = 1
            vel_1h = 1
            vel_24h = 1

        shared_device_count = network_stats.get("shared_device_count", 1)
        shared_ip_count = network_stats.get("shared_ip_count", 1)

        return {
            "amount": amount,
            "amount_log": amount_log,
            "transaction_hour": float(hour),
            "transaction_day_of_week": float(dayofweek),
            "is_weekend": float(is_weekend),
            "amount_deviation": amt_dev,
            "transaction_velocity_1h": float(vel_1h),
            "transaction_velocity_24h": float(vel_24h),
            "time_since_last_txn_min": float(time_since),
            "device_novelty": float(device_novelty),
            "beneficiary_novelty": float(ben_novelty),
            "shared_device_count": float(shared_device_count),
            "shared_ip_count": float(shared_ip_count),
            "is_high_risk_type": float(is_high_risk),
        }
