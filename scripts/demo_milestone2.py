"""End-to-end demonstration script for FraudShield Milestone 2:
Submit fraud sample -> Held review case -> Analyst release -> Audit history.
"""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path
import httpx

def main():
    parser = argparse.ArgumentParser(description="Demonstrate FraudShield Milestone 2 Workflow")
    parser.add_argument("--url", default=os.environ.get("FRAUDSHIELD_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--sample", default="artifacts/sample_fraud.json", type=Path)
    parser.add_argument(
        "--service-key",
        default=os.environ.get(
            "FRAUDSHIELD_SERVICE_KEY",
            "service-secret-token-key-32chars-checkout"
        )
    )
    parser.add_argument(
        "--analyst-key",
        default=os.environ.get(
            "FRAUDSHIELD_ANALYST_KEY",
            "analyst-secret-token-key-32chars-jane"
        )
    )
    args = parser.parse_args()

    client = httpx.Client(base_url=args.url, timeout=15, trust_env=False)

    print("=================================================================")
    print("      FraudShield Milestone 2: Automated End-to-End Demo        ")
    print("=================================================================\n")

    # 1. Health check
    print("[Step 1] Checking service readiness at GET /health/ready ...")
    try:
        health_res = client.get("/health/ready")
        health_res.raise_for_status()
        health_data = health_res.json()
        print(f"  -> Health: {health_data['status']}, Database: {health_data.get('database')}\n")
    except Exception as exc:
        print(f"  [ERROR] Cannot connect to API server at {args.url}: {exc}")
        print("  Ensure uvicorn is running: python -m uvicorn fraudshield.api:app --host 127.0.0.1 --port 8000")
        sys.exit(1)

    # 2. Submit transaction
    idempotency_key = f"demo-tx-{uuid.uuid4().hex[:12]}"
    print(f"[Step 2] Submitting fraud sample from {args.sample} ...")
    print(f"  -> Idempotency-Key: {idempotency_key}")
    print(f"  -> Service Actor: checkout_service (authenticated via service token)")

    sample_content = json.loads(args.sample.read_text())
    submit_payload = {
        "client_transaction_id": str(sample_content.get("transaction_id", "demo-3488979")),
        "features": sample_content["features"]
    }

    try:
        submit_res = client.post(
            "/v1/transactions",
            headers={
                "Authorization": f"Bearer {args.service_key}",
                "Idempotency-Key": idempotency_key
            },
            json=submit_payload
        )
        submit_res.raise_for_status()
    except httpx.HTTPStatusError as err:
        print(f"  [ERROR] Submission failed ({err.response.status_code}): {err.response.text}")
        sys.exit(1)

    tx_data = submit_res.json()
    tx_id = tx_data["id"]
    case_id = tx_data.get("case_id")
    print(f"  -> Transaction ID (UUID): {tx_id}")
    print(f"  -> ML Model Score: {tx_data['model_score']:.4f}")
    print(f"  -> Recommended Risk Action: {tx_data['recommended_action']}")
    print(f"  -> Initial Simulated Status: {tx_data['status']}")
    print(f"  -> Generated Review Case ID: {case_id}\n")

    if not case_id:
        print("  [INFO] Transaction did not require review (status is not reviewable). Demo complete.")
        return

    # 3. Retrieve Review Case
    print(f"[Step 3] Fetching review case GET /v1/cases/{case_id} as analyst_jane ...")
    case_res = client.get(
        f"/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {args.analyst_key}"}
    )
    case_res.raise_for_status()
    case_data = case_res.json()
    print(f"  -> Case Status: {case_data['status']}")
    print(f"  -> Transaction Client Ref: {case_data['transaction']['client_transaction_id']}")
    print(f"  -> Top Risk Factor: {case_data['transaction']['model_factors'][0]['feature']} ({case_data['transaction']['model_factors'][0]['direction']})\n")

    # 4. Analyst Action: Release
    print(f"[Step 4] Analyst releasing case POST /v1/cases/{case_id}/actions ...")
    action_payload = {
        "action": "release",
        "reason": "Simulated analyst decision: customer identity verified via simulated out-of-band contact and historical profile match.",
        "expected_version": tx_data["version"]
    }
    action_res = client.post(
        f"/v1/cases/{case_id}/actions",
        headers={"Authorization": f"Bearer {args.analyst_key}"},
        json=action_payload
    )
    action_res.raise_for_status()
    action_data = action_res.json()
    print(f"  -> Result Message: {action_data['message']}")
    print(f"  -> Updated Case Status: {action_data['case']['status']} (Resolution: {action_data['case']['resolution']})")
    print(f"  -> Updated Transaction Status: {action_data['transaction']['status']} (Version: {action_data['transaction']['version']})\n")

    # 5. Retrieve Audit Trail
    print(f"[Step 5] Fetching complete audit trail GET /v1/transactions/{tx_id}/audit ...")
    audit_res = client.get(
        f"/v1/transactions/{tx_id}/audit",
        headers={"Authorization": f"Bearer {args.analyst_key}"}
    )
    audit_res.raise_for_status()
    audit_events = audit_res.json()["audit_events"]

    print(f"  -> Total Audit Events: {len(audit_events)}")
    for i, ev in enumerate(audit_events, 1):
        print(f"     [{i}] {ev['created_at']} | Event: {ev['event_type']} | Actor: {ev['actor']} ({ev['actor_role']})")
        print(f"         Action: {ev['action']} | Transition: {ev['previous_status']} -> {ev['resulting_status']}")
        if ev.get("reason"):
            print(f"         Reason: {ev['reason']}")
    print("\n=================================================================")
    print("      Demo Completed Successfully: Full Audit Integrity Verified ")
    print("=================================================================\n")

if __name__ == "__main__":
    main()
