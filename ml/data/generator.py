import os
import uuid
import random
import hashlib
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np


class SyntheticFraudDataGenerator:
    """
    Generates competition-grade synthetic financial transaction dataset with realistic scenarios:
    - Scenario A: Normal transactions (low risk)
    - Scenario B: Behavioral Anomaly (unusual amount/time/device)
    - Scenario C: Account Takeover Pattern (new device + unusual location + rapid high amount)
    - Scenario D: Fraud Ring (multiple accounts sharing device/IP/beneficiary network)
    - Scenario E: False Positive (high amount / new device, but legitimate user activity)
    """

    def __init__(self, num_users=500, num_transactions=5000, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        self.num_users = num_users
        self.num_transactions = num_transactions

        self.user_ids = [f"USR_{1000 + i}" for i in range(num_users)]
        self.account_ids = {u_id: f"ACC_{2000 + i}" for i, u_id in enumerate(self.user_ids)}
        
        # User baselines
        self.user_baselines = {}
        for u_id in self.user_ids:
            self.user_baselines[u_id] = {
                "mean_amount": round(float(np.random.gamma(shape=3.0, scale=30.0)), 2),
                "std_amount": round(float(np.random.uniform(10.0, 50.0)), 2),
                "usual_devices": [f"DEV_{random.randint(100, 999)}" for _ in range(random.randint(1, 2))],
                "usual_ips": [self._hash_ip(f"192.168.{random.randint(1,254)}.{random.randint(1,254)}") for _ in range(2)],
                "usual_locations": random.choice(["New York, US", "London, UK", "Tokyo, JP", "Sydney, AU", "Toronto, CA"]),
                "usual_beneficiaries": [f"BEN_{random.randint(500, 999)}" for _ in range(random.randint(2, 5))],
                "usual_merchants": [f"MER_{random.randint(100, 400)}" for _ in range(5)],
            }

        # Shared infrastructure for Fraud Ring (Scenario D)
        self.ring_shared_device = "DEV_RING_999"
        self.ring_shared_ip = self._hash_ip("10.0.99.99")
        self.ring_shared_beneficiary = "BEN_RING_777"
        self.ring_user_ids = self.user_ids[:15] # First 15 users involved in ring

    def _hash_ip(self, ip_str: str) -> str:
        return hashlib.sha256(ip_str.encode()).hexdigest()[:16]

    def generate(self) -> pd.DataFrame:
        start_time = datetime.now(timezone.utc) - timedelta(days=30)
        transactions = []

        # Track temporal user state
        user_last_txn_time = {u: start_time for u in self.user_ids}
        user_txn_counts = {u: 0 for u in self.user_ids}

        for i in range(self.num_transactions):
            txn_id = f"TX{10000 + i}"
            
            # Determine transaction scenario probability
            # 88% Normal (A), 4% Behavioral Anomaly (B), 3% ATO (C), 3% Fraud Ring (D), 2% False Positive (E)
            rand_val = random.random()
            if rand_val < 0.88:
                scenario = "A" # Normal
            elif rand_val < 0.92:
                scenario = "B" # Behavioral Anomaly
            elif rand_val < 0.95:
                scenario = "C" # Account Takeover
            elif rand_val < 0.98:
                scenario = "D" # Fraud Ring
            else:
                scenario = "E" # False Positive

            if scenario == "D":
                user_id = random.choice(self.ring_user_ids)
            else:
                user_id = random.choice(self.user_ids)

            account_id = self.account_ids[user_id]
            baseline = self.user_baselines[user_id]

            # Advance time monotonically with bursts
            last_t = user_last_txn_time[user_id]
            time_gap = timedelta(minutes=random.randint(5, 1440) if scenario != "C" else random.randint(1, 15))
            txn_time = last_t + time_gap
            user_last_txn_time[user_id] = txn_time
            user_txn_counts[user_id] += 1

            # Default transaction properties
            amount = max(5.0, round(float(np.random.normal(baseline["mean_amount"], baseline["std_amount"])), 2))
            txn_type = random.choice(["CARD", "ACH", "WIRE", "P2P"])
            merchant_id = random.choice(baseline["usual_merchants"])
            beneficiary_id = random.choice(baseline["usual_beneficiaries"])
            device_id = random.choice(baseline["usual_devices"])
            ip_hash = random.choice(baseline["usual_ips"])
            location = baseline["usual_locations"]
            is_fraud = 0

            # Scenario modifications
            if scenario == "B":
                # Behavioral anomaly (suspicious but medium risk)
                amount = round(baseline["mean_amount"] * random.uniform(4.0, 8.0), 2)
                device_id = f"DEV_NEW_{random.randint(1000, 9999)}"
                is_fraud = 1 if random.random() > 0.3 else 0

            elif scenario == "C":
                # Account Takeover (high risk fraud)
                amount = round(baseline["mean_amount"] * random.uniform(10.0, 25.0), 2)
                device_id = f"DEV_ATO_{random.randint(5000, 9999)}"
                ip_hash = self._hash_ip(f"185.{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}")
                location = "Unknown / Proxy IP"
                beneficiary_id = f"BEN_NEW_{random.randint(8000, 9999)}"
                txn_type = "WIRE"
                is_fraud = 1

            elif scenario == "D":
                # Fraud Ring (coordinated network fraud)
                amount = round(random.uniform(2000.0, 9500.0), 2)
                device_id = self.ring_shared_device
                ip_hash = self.ring_shared_ip
                beneficiary_id = self.ring_shared_beneficiary
                txn_type = "P2P"
                is_fraud = 1

            elif scenario == "E":
                # False Positive (looks suspicious: high amount + new device, but LEGITIMATE)
                amount = round(baseline["mean_amount"] * random.uniform(5.0, 9.0), 2)
                device_id = f"DEV_UPGRADE_{random.randint(3000, 4000)}"
                beneficiary_id = f"BEN_CAR_DEALER_{random.randint(100, 200)}"
                is_fraud = 0

            transactions.append({
                "transaction_id": txn_id,
                "user_id": user_id,
                "account_id": account_id,
                "amount": amount,
                "currency": "USD",
                "transaction_type": txn_type,
                "merchant_id": merchant_id,
                "beneficiary_id": beneficiary_id,
                "device_id": device_id,
                "ip_address_hash": ip_hash,
                "location": location,
                "timestamp": txn_time.isoformat(),
                "is_fraud": is_fraud,
                "scenario": scenario,
            })

        df = pd.DataFrame(transactions)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df


if __name__ == "__main__":
    generator = SyntheticFraudDataGenerator(num_users=300, num_transactions=5000)
    df = generator.generate()
    os.makedirs("ml/data", exist_ok=True)
    df.to_csv("ml/data/transactions_dataset.csv", index=False)
    print(f"Successfully generated {len(df)} synthetic transactions. Fraud count: {df['is_fraud'].sum()} ({df['is_fraud'].mean():.2%})")
