"""Comprehensive Milestone 3 End-to-End Verification Script.

Tests all analyst workflow requirements against live backend APIs and PostgreSQL:
1. Credential enforcement (401 invalid, 403 service-role rejection, 200 analyst access)
2. Case Queue listing, pagination, and backend filters
3. Case Detail inspection (uncalibrated score, TreeSHAP factors, policy reasons, features)
4. Release action with reason and expected_version
5. Terminal state controls (rejecting subsequent actions on resolved case)
6. Reject action with reason and expected_version
7. Stale-version conflict detection (HTTP 409)
8. Audit timeline verification (actor, reason, Asia/Dhaka timestamp conversion)
9. Data persistence across independent sessions
"""
import json
import os
import sys
from datetime import datetime, timezone
import zoneinfo
import httpx

API_URL = os.environ.get("FRAUDSHIELD_URL", "http://127.0.0.1:8000")
SERVICE_KEY = os.environ.get("FRAUDSHIELD_SERVICE_KEY", "service-secret-token-key-32chars-checkout")
ANALYST_KEY = os.environ.get("FRAUDSHIELD_ANALYST_KEY", "analyst-secret-token-key-32chars-jane")
INVALID_KEY = "invalid-token-that-is-not-registered-anywhere"

def run_verification():
    client = httpx.Client(base_url=API_URL, timeout=15, trust_env=False)
    print("=" * 70)
    print("       FRAUDSHIELD MILESTONE 3: ANALYST WORKFLOW E2E VERIFICATION     ")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. System Health
    # -------------------------------------------------------------
    print("\n[Step 1] System Health & Readiness")
    res = client.get("/health/ready")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    health = res.json()
    print(f"  Health status: {health.get('status')} | Database: {health.get('database')}")
    assert health.get("status") == "ready"
    assert health.get("database") == "connected"

    # -------------------------------------------------------------
    # 2. Credential Enforcement & Role Separation
    # -------------------------------------------------------------
    print("\n[Step 2] Credential Enforcement & Role Separation")
    
    # 2a. Unauthenticated / Invalid credentials
    res_no_auth = client.get("/v1/auth/me")
    print(f"  No auth GET /v1/auth/me -> HTTP {res_no_auth.status_code} (Expected 401)")
    assert res_no_auth.status_code == 401

    res_bad = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {INVALID_KEY}"})
    print(f"  Invalid bearer token GET /v1/auth/me -> HTTP {res_bad.status_code} (Expected 401)")
    assert res_bad.status_code == 401

    # 2b. Service token on analyst endpoints
    res_service_me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {SERVICE_KEY}"})
    print(f"  Service token GET /v1/auth/me -> HTTP {res_service_me.status_code} | Role: {res_service_me.json().get('role')}")
    assert res_service_me.status_code == 200
    assert res_service_me.json().get("role") == "service"

    res_service_cases = client.get("/v1/cases", headers={"Authorization": f"Bearer {SERVICE_KEY}"})
    print(f"  Service token GET /v1/cases -> HTTP {res_service_cases.status_code} (Expected 403 Forbidden)")
    assert res_service_cases.status_code == 403

    # 2c. Analyst token
    res_analyst_me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {ANALYST_KEY}"})
    print(f"  Analyst token GET /v1/auth/me -> HTTP {res_analyst_me.status_code} | Identity: {res_analyst_me.json().get('identity')}, Role: {res_analyst_me.json().get('role')}")
    assert res_analyst_me.status_code == 200
    assert res_analyst_me.json().get("role") == "analyst"
    assert res_analyst_me.json().get("identity") == "analyst_jane"

    # -------------------------------------------------------------
    # 3. Case Queue & Filtering
    # -------------------------------------------------------------
    print("\n[Step 3] Case Queue Listing, Pagination & Filters")
    analyst_headers = {"Authorization": f"Bearer {ANALYST_KEY}"}

    res_queue = client.get("/v1/cases?limit=10&offset=0", headers=analyst_headers)
    assert res_queue.status_code == 200
    queue_data = res_queue.json()
    items = queue_data.get("items", [])
    total = queue_data.get("total", 0)
    print(f"  Total review cases in database: {total} (showing {len(items)} items)")
    assert len(items) > 0, "Expected at least one case in database"

    # Verify queue columns
    sample_case = items[0]
    tx = sample_case.get("transaction") or {}
    print(f"  Queue row sample:")
    print(f"    - Case ID: {sample_case['id']}")
    print(f"    - Client Reference: {tx.get('client_transaction_id')}")
    print(f"    - Model Score (uncalibrated): {tx.get('model_score')}")
    print(f"    - Recommended Action: {tx.get('recommended_action')}")
    print(f"    - Transaction Status: {tx.get('status')}")
    print(f"    - Case Status: {sample_case.get('status')}")
    print(f"    - Created: {sample_case.get('created_at')}")

    # Test status filters
    res_open = client.get("/v1/cases?status=open", headers=analyst_headers)
    assert res_open.status_code == 200
    open_cases = res_open.json().get("items", [])
    print(f"  Filter status=open -> {len(open_cases)} cases found")
    for c in open_cases:
        assert c["status"] == "open"

    res_resolved = client.get("/v1/cases?status=resolved", headers=analyst_headers)
    assert res_resolved.status_code == 200
    resolved_cases = res_resolved.json().get("items", [])
    print(f"  Filter status=resolved -> {len(resolved_cases)} cases found")
    for c in resolved_cases:
        assert c["status"] == "resolved"

    # Find open cases for release and reject tests
    held_cases = [c for c in open_cases if (c.get("transaction") or {}).get("status") in ["held_for_review", "pending_verification"]]
    assert len(held_cases) >= 2, f"Expected at least 2 held open cases, found {len(held_cases)}"

    case_to_release = held_cases[0]
    case_to_reject = held_cases[1]

    # -------------------------------------------------------------
    # 4. Case Detail Inspection
    # -------------------------------------------------------------
    print("\n[Step 4] Case Detail Inspection")
    res_detail = client.get(f"/v1/cases/{case_to_release['id']}", headers=analyst_headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    detail_tx = detail["transaction"]

    print(f"  Case ID: {detail['id']}")
    print(f"  Uncalibrated Model Score: {detail_tx['model_score']} (Notice: strictly labeled uncalibrated)")
    print(f"  Policy Reasons: {detail_tx['policy_reasons']}")
    print(f"  Model Version: {detail_tx['model_version']} | Policy: {detail_tx['policy_version']} | Schema: {detail_tx['schema_version']}")
    
    raw_factors = detail_tx.get("model_factors", [])
    if isinstance(raw_factors, dict):
        factors = raw_factors.get("top_factors", [])
    elif isinstance(raw_factors, list):
        factors = raw_factors
    else:
        factors = []
    print(f"  TreeSHAP Top Factors: {len(factors)} features contributing to score")
    for f in factors[:3]:
        print(f"    * {f.get('feature')}: contribution={f.get('contribution_log_odds'):+.4f}, dir={f.get('direction')}")
    
    features = detail_tx.get("features", {})
    print(f"  Saved Feature Snapshot: {len(features)} attributes saved (e.g. TransactionAmt={features.get('TransactionAmt')}, ProductCD={features.get('ProductCD')})")
    assert "TransactionAmt" in features
    assert "ProductCD" in features

    # -------------------------------------------------------------
    # 5. Release Action with Reason & Expected Version
    # -------------------------------------------------------------
    print("\n[Step 5] Release Action Execution")
    expected_v = detail_tx["version"]
    release_payload = {
        "action": "release",
        "reason": "Simulated analyst release: customer identity review and verification are simulated.",
        "expected_version": expected_v
    }
    print(f"  Submitting POST /v1/cases/{case_to_release['id']}/actions with expected_version={expected_v}")
    res_action = client.post(
        f"/v1/cases/{case_to_release['id']}/actions",
        headers=analyst_headers,
        json=release_payload
    )
    assert res_action.status_code == 200, f"Expected 200, got {res_action.status_code}: {res_action.text}"
    action_result = res_action.json()
    print(f"  -> Release successful! Resulting case status: {action_result['case']['status']}, resolution: {action_result['case']['resolution']}, tx status: {action_result['transaction']['status']}")
    assert action_result["case"]["status"] == "resolved"
    assert action_result["case"]["resolution"] == "released"
    assert action_result["transaction"]["status"] == "completed"

    # -------------------------------------------------------------
    # 6. Terminal State Enforcement (Cannot re-act on resolved case)
    # -------------------------------------------------------------
    print("\n[Step 6] Terminal State Enforcement")
    res_re_release = client.post(
        f"/v1/cases/{case_to_release['id']}/actions",
        headers=analyst_headers,
        json={
            "action": "release",
            "reason": "Attempting second release on terminal case.",
            "expected_version": action_result["transaction"]["version"]
        }
    )
    print(f"  Duplicate action on resolved case -> HTTP {res_re_release.status_code} (Expected 409 Conflict)")
    assert res_re_release.status_code == 409

    # -------------------------------------------------------------
    # 7. Reject Action Execution
    # -------------------------------------------------------------
    print("\n[Step 7] Reject Action Execution")
    res_reject_detail = client.get(f"/v1/cases/{case_to_reject['id']}", headers=analyst_headers)
    reject_tx = res_reject_detail.json()["transaction"]
    reject_payload = {
        "action": "reject",
        "reason": "Simulated analyst rejection based on displayed historical replay risk factors.",
        "expected_version": reject_tx["version"]
    }
    print(f"  Submitting POST /v1/cases/{case_to_reject['id']}/actions (reject) with expected_version={reject_tx['version']}")
    res_reject = client.post(
        f"/v1/cases/{case_to_reject['id']}/actions",
        headers=analyst_headers,
        json=reject_payload
    )
    assert res_reject.status_code == 200
    reject_result = res_reject.json()
    print(f"  -> Reject successful! Case status: {reject_result['case']['status']}, resolution: {reject_result['case']['resolution']}, tx status: {reject_result['transaction']['status']}")
    assert reject_result["case"]["status"] == "resolved"
    assert reject_result["case"]["resolution"] == "rejected"
    assert reject_result["transaction"]["status"] == "rejected"

    # -------------------------------------------------------------
    # 8. Stale-Version Conflict Handling (HTTP 409)
    # -------------------------------------------------------------
    print("\n[Step 8] Stale-Version Optimistic Locking Conflict")
    # Submitting expected_version = 1 on reject_result where version is now 2
    res_stale = client.post(
        f"/v1/cases/{case_to_reject['id']}/actions",
        headers=analyst_headers,
        json={
            "action": "reject",
            "reason": "Stale version test",
            "expected_version": 1  # Intentionally stale
        }
    )
    print(f"  Submitting action with stale expected_version=1 -> HTTP {res_stale.status_code} (Expected 409 Conflict)")
    assert res_stale.status_code == 409
    print(f"  Conflict detail: {res_stale.json().get('detail')}")

    # -------------------------------------------------------------
    # 9. Audit Timeline Verification (Asia/Dhaka timezone)
    # -------------------------------------------------------------
    print("\n[Step 9] Audit Timeline Verification")
    res_audit = client.get(
        f"/v1/transactions/{action_result['transaction']['id']}/audit",
        headers=analyst_headers
    )
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    events = audit_data.get("audit_events", [])
    print(f"  Retrieved {len(events)} audit events for released transaction {action_result['transaction']['id']}")
    assert len(events) >= 2, "Expected initial submission event and analyst decision event"

    dhaka_tz = zoneinfo.ZoneInfo("Asia/Dhaka")
    for ev in events:
        utc_dt = datetime.fromisoformat(ev["created_at"])
        dhaka_dt = utc_dt.astimezone(dhaka_tz)
        dhaka_str = dhaka_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        print(f"    - Event: {ev['event_type']} | Action: {ev['action']} | Actor: {ev['actor']} ({ev['actor_role']})")
        print(f"      Transition: {ev.get('previous_status')} -> {ev.get('resulting_status')}")
        print(f"      Reason: {ev.get('reason')}")
        print(f"      UTC: {ev['created_at']} -> Asia/Dhaka: {dhaka_str}")

    # Check analyst release event specifically
    analyst_events = [e for e in events if e["actor"] == "analyst_jane"]
    assert len(analyst_events) > 0
    assert "release" in analyst_events[0]["action"]
    assert analyst_events[0]["resulting_status"] == "completed"
    assert analyst_events[0]["previous_status"] == "held_for_review"

    # -------------------------------------------------------------
    # 10. Persistence Verification
    # -------------------------------------------------------------
    print("\n[Step 10] Data Persistence Across Independent Session")
    new_client = httpx.Client(base_url=API_URL, timeout=15, trust_env=False)
    res_verify = new_client.get(f"/v1/cases/{case_to_release['id']}", headers=analyst_headers)
    assert res_verify.status_code == 200
    persisted_case = res_verify.json()
    assert persisted_case["status"] == "resolved"
    assert persisted_case["resolution"] == "released"
    print(f"  Verified Case {case_to_release['id']} is persisted as resolved/released in PostgreSQL.")

    print("\n" + "=" * 70)
    print("      ALL MILESTONE 3 E2E VERIFICATION CHECKS PASSED (10/10)     ")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
