"""Prepare demonstration review cases for Milestone 3 Analyst Dashboard.
Submits realistic replay fraud samples through the authorized service endpoint.
"""
import json
import uuid
from pathlib import Path
import httpx

API_URL = "http://127.0.0.1:8000"
SERVICE_KEY = "service-secret-token-key-32chars-checkout"

def prepare_cases():
    client = httpx.Client(base_url=API_URL, timeout=15, trust_env=False)
    
    # Verify health
    res = client.get("/health/ready")
    res.raise_for_status()
    print("API is ready:", res.json())

    sample_path = Path("artifacts/sample_fraud.json")
    sample_data = json.loads(sample_path.read_text())
    base_features = sample_data["features"]

    cases_created = []

    # Case 1: Held case for release test
    idemp_1 = f"m3-demo-release-{uuid.uuid4().hex[:8]}"
    client_tx_1 = f"TX-M3-REL-{uuid.uuid4().hex[:6].upper()}"
    feat_1 = dict(base_features)
    # Vary TransactionAmt slightly for realistic differentiation
    feat_1["TransactionAmt"] = 150.00
    res_1 = client.post(
        "/v1/transactions",
        headers={
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Idempotency-Key": idemp_1
        },
        json={
            "client_transaction_id": client_tx_1,
            "features": feat_1
        }
    )
    res_1.raise_for_status()
    data_1 = res_1.json()
    print(f"Created Case 1: tx_id={data_1['id']}, client_id={client_tx_1}, status={data_1['status']}, case_id={data_1.get('case_id')}")
    cases_created.append(data_1)

    # Case 2: Held case for reject test
    idemp_2 = f"m3-demo-reject-{uuid.uuid4().hex[:8]}"
    client_tx_2 = f"TX-M3-REJ-{uuid.uuid4().hex[:6].upper()}"
    feat_2 = dict(base_features)
    feat_2["TransactionAmt"] = 350.50
    res_2 = client.post(
        "/v1/transactions",
        headers={
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Idempotency-Key": idemp_2
        },
        json={
            "client_transaction_id": client_tx_2,
            "features": feat_2
        }
    )
    res_2.raise_for_status()
    data_2 = res_2.json()
    print(f"Created Case 2: tx_id={data_2['id']}, client_id={client_tx_2}, status={data_2['status']}, case_id={data_2.get('case_id')}")
    cases_created.append(data_2)

    # Case 3: Additional open case for queue exploration
    idemp_3 = f"m3-demo-queue-{uuid.uuid4().hex[:8]}"
    client_tx_3 = f"TX-M3-QUE-{uuid.uuid4().hex[:6].upper()}"
    feat_3 = dict(base_features)
    feat_3["TransactionAmt"] = 720.00
    res_3 = client.post(
        "/v1/transactions",
        headers={
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Idempotency-Key": idemp_3
        },
        json={
            "client_transaction_id": client_tx_3,
            "features": feat_3
        }
    )
    res_3.raise_for_status()
    data_3 = res_3.json()
    print(f"Created Case 3: tx_id={data_3['id']}, client_id={client_tx_3}, status={data_3['status']}, case_id={data_3.get('case_id')}")
    cases_created.append(data_3)

    return cases_created

if __name__ == "__main__":
    prepare_cases()
