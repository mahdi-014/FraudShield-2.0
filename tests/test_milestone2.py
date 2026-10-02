"""Tests for FraudShield Milestone 2:
PostgreSQL persistence, transaction states, analyst review, and audit history.
"""
import copy
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fraudshield.api import create_app
from fraudshield.config import (
    AuthConfig, Actor, ROLE_SERVICE, ROLE_ANALYST, ROLE_LEGACY,
    get_test_database_url, get_database_url
)
from fraudshield.state_machine import (
    STATUS_COMPLETED, STATUS_REJECTED, STATUS_AWAITING_ACKNOWLEDGEMENT,
    STATUS_PENDING_VERIFICATION, STATUS_HELD_FOR_REVIEW,
    map_initial_status, validate_analyst_transition, requires_review_case
)
from fraudshield.db.models import (
    Base, TransactionRecord, ReviewCaseRecord, AnalystActionRecord, AuditEventRecord
)
from fraudshield.db.repository import (
    compute_canonical_hash, submit_transaction, execute_analyst_action,
    get_transaction_audit, IdempotencyConflictError, VersionConflictError,
    InvalidStateTransitionError
)
from fraudshield.db.session import check_database_connection, get_db

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'

SERVICE_KEY_1 = 'service-secret-token-key-32chars-checkout'
SERVICE_KEY_2 = 'service-secret-token-key-32chars-payments'
ANALYST_KEY_1 = 'analyst-secret-token-key-32chars-jane'
LEGACY_KEY = 'test-only-credential-1234567890'

AUTH_SERVICE_1 = {'Authorization': f'Bearer {SERVICE_KEY_1}'}
AUTH_SERVICE_2 = {'Authorization': f'Bearer {SERVICE_KEY_2}'}
AUTH_ANALYST_1 = {'Authorization': f'Bearer {ANALYST_KEY_1}'}
AUTH_LEGACY = {'Authorization': f'Bearer {LEGACY_KEY}'}

@pytest.fixture
def fraud_sample():
    return json.loads((ARTIFACTS / 'sample_fraud.json').read_text())

@pytest.fixture
def legitimate_sample():
    return json.loads((ARTIFACTS / 'sample_legitimate.json').read_text())

@pytest.fixture
def configured_env(monkeypatch):
    monkeypatch.setenv('FRAUDSHIELD_API_KEY', LEGACY_KEY)
    monkeypatch.setenv(
        'FRAUDSHIELD_SERVICE_KEYS',
        f'{SERVICE_KEY_1}:checkout_service,{SERVICE_KEY_2}:payments_service'
    )
    monkeypatch.setenv(
        'FRAUDSHIELD_ANALYST_KEYS',
        f'{ANALYST_KEY_1}:analyst_jane'
    )
    monkeypatch.setenv('FRAUDSHIELD_ARTIFACT_DIR', str(ARTIFACTS))

# =====================================================================
# Unit Tests: State Machine & Transition Rules
# =====================================================================
def test_state_machine_initial_mappings():
    assert map_initial_status('allow') == STATUS_COMPLETED
    assert map_initial_status('warn') == STATUS_AWAITING_ACKNOWLEDGEMENT
    assert map_initial_status('pause') == STATUS_PENDING_VERIFICATION
    assert map_initial_status('hold') == STATUS_HELD_FOR_REVIEW
    with pytest.raises(ValueError, match='Unknown initial scoring action'):
        map_initial_status('unknown_action')

def test_state_machine_reviewable_requirement():
    assert requires_review_case(STATUS_HELD_FOR_REVIEW) is True
    assert requires_review_case(STATUS_PENDING_VERIFICATION) is True
    assert requires_review_case(STATUS_COMPLETED) is False
    assert requires_review_case(STATUS_AWAITING_ACKNOWLEDGEMENT) is False
    assert requires_review_case(STATUS_REJECTED) is False

def test_state_machine_analyst_transitions():
    assert validate_analyst_transition(STATUS_HELD_FOR_REVIEW, 'release') == STATUS_COMPLETED
    assert validate_analyst_transition(STATUS_HELD_FOR_REVIEW, 'reject') == STATUS_REJECTED
    assert validate_analyst_transition(STATUS_PENDING_VERIFICATION, 'release') == STATUS_COMPLETED
    assert validate_analyst_transition(STATUS_PENDING_VERIFICATION, 'reject') == STATUS_REJECTED

def test_state_machine_terminal_states_cannot_be_changed():
    with pytest.raises(ValueError, match="Cannot perform analyst action on terminal state 'completed'"):
        validate_analyst_transition(STATUS_COMPLETED, 'release')
    with pytest.raises(ValueError, match="Cannot perform analyst action on terminal state 'rejected'"):
        validate_analyst_transition(STATUS_REJECTED, 'release')

def test_state_machine_non_reviewable_state_rejected():
    with pytest.raises(ValueError, match="Analyst actions are only permitted for states"):
        validate_analyst_transition(STATUS_AWAITING_ACKNOWLEDGEMENT, 'release')

# =====================================================================
# Unit Tests: Canonical Hashing & Request Determinism
# =====================================================================
def test_canonical_hash_invariance_to_key_order(fraud_sample):
    features_a = fraud_sample['features']
    features_b = {k: features_a[k] for k in reversed(list(features_a.keys()))}
    hash_a = compute_canonical_hash('tx_100', features_a)
    hash_b = compute_canonical_hash('tx_100', features_b)
    assert hash_a == hash_b

def test_canonical_hash_differs_on_content(fraud_sample):
    features_a = fraud_sample['features']
    features_b = copy.deepcopy(features_a)
    features_b['TransactionAmt'] = 9999.0
    assert compute_canonical_hash('tx_100', features_a) != compute_canonical_hash('tx_100', features_b)

# =====================================================================
# Unit Tests: Authentication & Server-Side Authorization
# =====================================================================
def test_auth_duplicate_credential_across_roles_rejected():
    config = AuthConfig()
    same_token = 'shared-secret-token-key-32chars-conflict'
    config._register_token(same_token, 'service_1', ROLE_SERVICE)
    with pytest.raises(ValueError, match="Duplicate credential detected across roles"):
        config._register_token(same_token, 'analyst_1', ROLE_ANALYST)

def test_auth_min_length_enforced():
    config = AuthConfig()
    with pytest.raises(ValueError, match="must be at least 24 characters"):
        config._register_token('short_token', 'user', ROLE_SERVICE)

def test_auth_token_binding(configured_env):
    config = AuthConfig()
    actor_svc = config.authenticate(SERVICE_KEY_1)
    assert actor_svc is not None
    assert actor_svc.identity == 'checkout_service'
    assert actor_svc.role == ROLE_SERVICE

    actor_analyst = config.authenticate(ANALYST_KEY_1)
    assert actor_analyst is not None
    assert actor_analyst.identity == 'analyst_jane'
    assert actor_analyst.role == ROLE_ANALYST

    actor_legacy = config.authenticate(LEGACY_KEY)
    assert actor_legacy is not None
    assert actor_legacy.role == ROLE_LEGACY

    assert config.authenticate('invalid-token-that-is-not-registered-at-all') is None

def test_unauthenticated_request_rejected(configured_env):
    with TestClient(create_app(ARTIFACTS)) as client:
        res = client.post('/v1/transactions', json={'features': {}})
        assert res.status_code == 401

def test_role_separation_enforced(configured_env):
    with TestClient(create_app(ARTIFACTS)) as client:
        # Service actor attempting analyst cases endpoint -> 403
        res = client.get('/v1/cases', headers=AUTH_SERVICE_1)
        assert res.status_code == 403

        # Legacy scorer key attempting analyst endpoint -> 403
        res = client.get('/v1/cases', headers=AUTH_LEGACY)
        assert res.status_code == 403

def test_database_unavailable_returns_503(configured_env, fraud_sample):
    # Test with unconfigured or unreachable database URL
    with TestClient(create_app(artifact_dir=ARTIFACTS, database_url='postgresql+pg8000://test:test@127.0.0.1:1/unavailable_test_db')) as client:
        res = client.post(
            '/v1/transactions',
            headers={**AUTH_SERVICE_1, 'Idempotency-Key': 'key-err-1'},
            json={'transaction_id': '123', 'features': fraud_sample['features']}
        )
        assert res.status_code == 503
        assert 'Database service error' in res.json()['detail'] or 'unavailable' in res.json()['detail']

def test_failed_audit_write_rolls_back_state(monkeypatch):
    from unittest.mock import MagicMock
    mock_session = MagicMock()
    # Mock no existing record found
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_scorer = MagicMock()
    mock_scorer.score.return_value = {
        'action': 'hold',
        'model_score': 0.85,
        'model_factors': [],
        'policy_reasons': ['High risk'],
        'model_version': 'v1',
        'policy_version': 'v1',
        'schema_version': 'v1'
    }

    # Simulate an error during session.commit()
    mock_session.commit.side_effect = RuntimeError("Database failure writing audit record")

    features = {'TransactionAmt': 100.0, 'TransactionDT': 1000, 'ProductCD': 'W'}
    with pytest.raises(RuntimeError, match="Database failure writing audit record"):
        submit_transaction(
            session=mock_session,
            service_actor='checkout_service',
            idempotency_key='fail-key-1',
            client_transaction_id='client-1',
            features=features,
            scorer=mock_scorer
        )

    # Verify rollback was called on failure, ensuring no partial writes persist
    mock_session.rollback.assert_called_once()


# =====================================================================
# Integration Tests: Real PostgreSQL Database
# =====================================================================
from conftest import safe_test_url
LIVE_PG_URL = safe_test_url()

@pytest.fixture
def pg_session(pg_engine):
    Session = sessionmaker(bind=pg_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def live_client(configured_env, pg_engine):
    app = create_app(artifact_dir=ARTIFACTS, database_url=LIVE_PG_URL)
    with TestClient(app) as client:
        yield client

def test_pg_persistence_across_restart(live_client, fraud_sample):
    key = 'test-idemp-restart-1'
    payload = {'transaction_id': 'tx-restart-1', 'features': fraud_sample['features']}
    res = live_client.post(
        '/v1/transactions',
        headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
        json=payload
    )
    assert res.status_code == 201
    tx_id = res.json()['id']

    # Simulate restart by creating a completely new app/client instance
    restarted_app = create_app(artifact_dir=ARTIFACTS, database_url=LIVE_PG_URL)
    with TestClient(restarted_app) as client_after_restart:
        get_res = client_after_restart.get(f'/v1/transactions/{tx_id}', headers=AUTH_SERVICE_1)
        assert get_res.status_code == 200
        assert get_res.json()['id'] == tx_id
        assert get_res.json()['status'] == STATUS_HELD_FOR_REVIEW

def test_pg_idempotency_sequential_and_concurrent(live_client, fraud_sample):
    key = 'test-idemp-conc-1'
    payload = {'transaction_id': 'tx-conc-1', 'features': fraud_sample['features']}

    # Concurrent submissions with identical key and payload
    def submit():
        with TestClient(create_app(artifact_dir=ARTIFACTS, database_url=LIVE_PG_URL)) as c:
            return c.post(
                '/v1/transactions',
                headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
                json=payload
            )

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit) for _ in range(5)]
        responses = [f.result() for f in futures]

    statuses = [r.status_code for r in responses]
    assert all(s in (200, 201) for s in statuses)
    tx_ids = set(r.json()['id'] for r in responses)
    assert len(tx_ids) == 1, "Concurrent retries must resolve to a single transaction"

def test_pg_different_input_same_key_conflict(live_client, fraud_sample):
    key = 'test-idemp-conflict-1'
    payload1 = {'transaction_id': 'tx-conf-1', 'features': fraud_sample['features']}
    res1 = live_client.post(
        '/v1/transactions',
        headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
        json=payload1
    )
    assert res1.status_code == 201

    payload2 = copy.deepcopy(payload1)
    payload2['features']['TransactionAmt'] = 888.88
    res2 = live_client.post(
        '/v1/transactions',
        headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
        json=payload2
    )
    assert res2.status_code == 409

def test_pg_service_caller_isolation(live_client, fraud_sample):
    key = 'test-isolation-1'
    payload = {'transaction_id': 'tx-iso-1', 'features': fraud_sample['features']}
    res = live_client.post(
        '/v1/transactions',
        headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
        json=payload
    )
    assert res.status_code == 201
    tx_id = res.json()['id']

    # Service 2 cannot read Service 1's transaction
    res_svc2 = live_client.get(f'/v1/transactions/{tx_id}', headers=AUTH_SERVICE_2)
    assert res_svc2.status_code == 404

    # Analyst can read any transaction
    res_analyst = live_client.get(f'/v1/transactions/{tx_id}', headers=AUTH_ANALYST_1)
    assert res_analyst.status_code == 200

def test_pg_analyst_release_and_terminal_immutability(live_client, fraud_sample):
    key = 'test-analyst-flow-1'
    res = live_client.post(
        '/v1/transactions',
        headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
        json={'transaction_id': 'tx-flow-1', 'features': fraud_sample['features']}
    )
    assert res.status_code == 201
    case_id = res.json()['case_id']
    tx_id = res.json()['id']
    assert case_id is not None

    # Analyst releases the transaction
    action_res = live_client.post(
        f'/v1/cases/{case_id}/actions',
        headers=AUTH_ANALYST_1,
        json={'action': 'release', 'reason': 'Simulated customer verification via OTP', 'expected_version': 1}
    )
    assert action_res.status_code == 200
    assert action_res.json()['transaction']['status'] == STATUS_COMPLETED
    assert action_res.json()['case']['status'] == 'resolved'
    assert action_res.json()['case']['resolution'] == 'released'

    # Once terminal (completed), cannot be altered
    second_action = live_client.post(
        f'/v1/cases/{case_id}/actions',
        headers=AUTH_ANALYST_1,
        json={'action': 'reject', 'reason': 'Re-evaluating', 'expected_version': 2}
    )
    assert second_action.status_code == 409

    # Verify audit history
    audit_res = live_client.get(f'/v1/transactions/{tx_id}/audit', headers=AUTH_ANALYST_1)
    assert audit_res.status_code == 200
    events = audit_res.json()['audit_events']
    assert len(events) >= 2
    assert events[0]['actor'] == 'checkout_service'
    assert events[1]['actor'] == 'analyst_jane'
    assert events[1]['resulting_status'] == STATUS_COMPLETED

def test_pg_concurrent_analyst_actions_conflict(live_client, fraud_sample):
    key = 'test-analyst-race-1'
    res = live_client.post(
        '/v1/transactions',
        headers={**AUTH_SERVICE_1, 'Idempotency-Key': key},
        json={'transaction_id': 'tx-race-1', 'features': fraud_sample['features']}
    )
    case_id = res.json()['case_id']

    def send_action(action, reason):
        with TestClient(create_app(artifact_dir=ARTIFACTS, database_url=LIVE_PG_URL)) as c:
            return c.post(
                f'/v1/cases/{case_id}/actions',
                headers=AUTH_ANALYST_1,
                json={'action': action, 'reason': reason, 'expected_version': 1}
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(send_action, 'release', 'Release from analyst A')
        f2 = executor.submit(send_action, 'reject', 'Reject from analyst B')
        r1, r2 = f1.result(), f2.result()

    status_codes = sorted([r1.status_code, r2.status_code])
    assert status_codes == [200, 409], "Expected exactly one success and one conflict"
