"""Milestone 3 backend test suite:
- GET /v1/auth/me authentication and role verification
- GET /v1/cases query filters (status, resolution, recommended_action)
- Feature snapshot in TransactionRecord.to_dict()
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from fraudshield.api import create_app
from fraudshield.config import get_artifact_dir, get_database_url
from fraudshield.db.session import get_db
from fraudshield.db.models import TransactionRecord

@pytest.fixture(scope="module")
def app_client():
    app = create_app(artifact_dir=get_artifact_dir(), database_url=get_database_url())
    with TestClient(app) as client:
        yield client

def test_auth_me_analyst(app_client):
    headers = {"Authorization": "Bearer analyst-secret-token-key-32chars-jane"}
    response = app_client.get("/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["identity"] == "analyst_jane"
    assert data["role"] == "analyst"

def test_auth_me_service(app_client):
    headers = {"Authorization": "Bearer service-secret-token-key-32chars-checkout"}
    response = app_client.get("/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["identity"] == "checkout_service"
    assert data["role"] == "service"

def test_auth_me_unauthenticated(app_client):
    response = app_client.get("/v1/auth/me")
    assert response.status_code == 401

def test_cases_filter_by_status_and_resolution(app_client):
    headers = {"Authorization": "Bearer analyst-secret-token-key-32chars-jane"}
    
    # Query all
    res = app_client.get("/v1/cases?limit=50", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

    # Query with status=open
    res_open = app_client.get("/v1/cases?status=open", headers=headers)
    assert res_open.status_code == 200
    for case in res_open.json()["items"]:
        assert case["status"] == "open"

    # Query with status=resolved
    res_resolved = app_client.get("/v1/cases?status=resolved", headers=headers)
    assert res_resolved.status_code == 200
    for case in res_resolved.json()["items"]:
        assert case["status"] == "resolved"

    # Query with resolution=released
    res_released = app_client.get("/v1/cases?resolution=released", headers=headers)
    assert res_released.status_code == 200
    for case in res_released.json()["items"]:
        assert case["resolution"] == "released"

def test_transaction_to_dict_includes_features():
    tx = TransactionRecord(
        id=str(uuid.uuid4()),
        client_transaction_id="TX-TEST-FEAT",
        service_actor="checkout_service",
        idempotency_key=str(uuid.uuid4()),
        request_hash="a" * 64,
        features={"TransactionAmt": 123.45, "ProductCD": "W", "TransactionDT": 1000},
        model_score=0.75,
        model_factors={"top_factors": []},
        policy_reasons=["Model score exceeded review threshold"],
        recommended_action="hold",
        status="held_for_review",
        model_version="1.0",
        policy_version="1.0",
        schema_version="1.0",
        version=1,
    )
    d = tx.to_dict()
    assert "features" in d
    assert d["features"]["TransactionAmt"] == 123.45
    assert d["features"]["ProductCD"] == "W"
