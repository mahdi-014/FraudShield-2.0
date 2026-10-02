"""Milestone 3 backend test suite:
- GET /v1/auth/me authentication and role verification
- GET /v1/cases query filters (status, resolution, recommended_action)
- Feature snapshot in TransactionRecord.to_dict()
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from fraudshield.api import create_app
from fraudshield.config import get_artifact_dir
from conftest import safe_test_url
from fraudshield.db.session import get_db
from fraudshield.db.models import TransactionRecord

@pytest.fixture
def app_client():
    app = create_app(artifact_dir=get_artifact_dir(), database_url=safe_test_url() or "postgresql+pg8000://test:test@127.0.0.1:1/unavailable_test_db")
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

def test_cases_filter_by_status_and_resolution(app_client, pg_engine):
    from fraudshield.db.repository import submit_transaction, execute_analyst_action
    from fraudshield.scoring import Scorer
    from sqlalchemy.orm import Session
    import json
    from pathlib import Path
    scorer = Scorer(Path(__file__).resolve().parents[1] / 'artifacts')
    sample = json.loads((Path(__file__).resolve().parents[1] / 'artifacts/sample_fraud.json').read_text())
    with Session(pg_engine) as session:
        tx1, _ = submit_transaction(session, 'checkout_service', uuid.uuid4().hex,
            uuid.uuid4().hex, sample['features'], scorer)
        tx2, _ = submit_transaction(session, 'checkout_service', uuid.uuid4().hex,
            uuid.uuid4().hex, sample['features'], scorer)
        open_id, resolved_id = tx1.review_case.id, tx2.review_case.id
        execute_analyst_action(session, resolved_id, 'analyst_jane', 'release',
            'Simulated analyst review', 1)
    headers = {"Authorization": "Bearer analyst-secret-token-key-32chars-jane"}
    for query, expected, field, value in [
        ('status=open', open_id, 'status', 'open'),
        ('status=resolved', resolved_id, 'status', 'resolved'),
        ('resolution=released', resolved_id, 'resolution', 'released'),
    ]:
        response = app_client.get('/v1/cases?limit=100&' + query, headers=headers)
        assert response.status_code == 200
        items = response.json()['items']
        assert expected in {case['id'] for case in items}
        assert all(case[field] == value for case in items)
    held = app_client.get('/v1/cases?limit=100&recommended_action=hold', headers=headers).json()
    assert open_id in {case['id'] for case in held['items']}
    assert all(case['transaction']['recommended_action'] == 'hold' for case in held['items'])
    first = app_client.get('/v1/cases?limit=1&offset=0', headers=headers).json()
    second = app_client.get('/v1/cases?limit=1&offset=1', headers=headers).json()
    assert len(first['items']) == len(second['items']) == 1
    assert first['items'][0]['id'] != second['items'][0]['id']
    assert first['total'] == second['total'] >= 2


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
