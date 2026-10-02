"""Regressions for isolation, sensitive error disclosure and concurrency contracts."""
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from fraudshield.api import create_app, CreateTransactionRequest, AnalystActionRequest
from fraudshield.db.test_safety import validate_test_database_url
from fraudshield.db.repository import submit_transaction, execute_analyst_action
from fraudshield.db.models import TransactionRecord, AuditEventRecord
from fraudshield.scoring import Scorer

ARTIFACTS = Path(__file__).resolve().parents[1] / 'artifacts'
AUTH = {'Authorization': 'Bearer service-secret-token-key-32chars-checkout'}
FEATURES = {'TransactionAmt': 10, 'TransactionDT': 100, 'ProductCD': 'W'}


def test_missing_test_url_never_uses_application_database():
    assert validate_test_database_url(None, 'postgresql://a:b@localhost/live_db') is None


@pytest.mark.parametrize('url', [
    'postgresql://a:b@localhost/live_db',
    'sqlite:///fraudshield_test_db',
])
def test_non_test_database_targets_refused(url):
    with pytest.raises(ValueError):
        validate_test_database_url(url)


def test_driver_host_and_user_aliases_cannot_bypass_same_database_refusal():
    with pytest.raises(ValueError, match='different'):
        validate_test_database_url(
            'postgresql+pg8000://test:other@127.0.0.1:5432/fraudshield_test_db',
            'postgresql+psycopg2://app:secret@localhost/fraudshield_test_db')


@pytest.mark.parametrize('fields', [
    {'transaction_id': '   '},
    {'transaction_id': 'one', 'client_transaction_id': 'two'},
    {},
])
def test_invalid_transaction_references(fields):
    with pytest.raises(ValidationError):
        CreateTransactionRequest(features=FEATURES, **fields)


def test_whitespace_reason_is_refused_and_valid_reason_trimmed():
    with pytest.raises(ValidationError):
        AnalystActionRequest(action='release', reason='    ', expected_version=1)
    assert AnalystActionRequest(action='release', reason='  Simulated review  ',
                                expected_version=1).reason == 'Simulated review'


@pytest.mark.parametrize('database_error,expected', [(True, 503), (False, 500)])
def test_failure_responses_and_logs_do_not_disclose_sensitive_exception(monkeypatch, caplog, database_error, expected):
    secret = 'PRIVATE_CUSTOMER_FEATURE_AND_DB_PASSWORD'
    @contextmanager
    def fail(_):
        if database_error:
            raise OperationalError('SELECT private', {'customer': secret}, RuntimeError(secret))
        raise RuntimeError(secret)
        yield
    monkeypatch.setattr('fraudshield.api.get_db', fail)
    caplog.set_level(logging.ERROR)
    with TestClient(create_app(ARTIFACTS, 'postgresql://unavailable/test'),
                    raise_server_exceptions=False) as client:
        response = client.get('/v1/transactions/example', headers=AUTH)
    assert response.status_code == expected
    assert secret not in response.text and secret not in caplog.text
    assert 'SELECT private' not in response.text
    assert response.headers['x-request-id'] == response.json()['request_id']


def test_full_readiness_fails_but_scorer_readiness_stays_available(monkeypatch):
    monkeypatch.setattr('fraudshield.api.check_database_connection', lambda _: False)
    with TestClient(create_app(ARTIFACTS)) as client:
        response = client.get('/health/ready')
        assert response.status_code == 503
        assert response.json()['status'] == 'not_ready'
        assert client.get('/health/scorer').status_code == 200


def test_unapproved_cors_origin_not_allowed(monkeypatch):
    monkeypatch.setenv('FRAUDSHIELD_CORS_ORIGINS', 'https://approved.example')
    with TestClient(create_app(ARTIFACTS)) as client:
        response = client.options('/v1/cases', headers={
            'Origin': 'https://unapproved.example',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Authorization',
        })
        assert response.status_code == 400
        assert 'access-control-allow-origin' not in response.headers


def test_row_lock_failure_does_not_use_unlocked_query():
    session = MagicMock()
    case_query, tx_query = MagicMock(), MagicMock()
    session.query.side_effect = [case_query, tx_query]
    case_query.filter.return_value.first.return_value.transaction_id = 'tx'
    filtered = tx_query.filter.return_value
    filtered.with_for_update.side_effect = RuntimeError('lock unavailable')
    with pytest.raises(RuntimeError, match='lock unavailable'):
        execute_analyst_action(session, 'case', 'analyst', 'release', 'Simulated review', 1)
    filtered.first.assert_not_called()
    session.commit.assert_not_called()


def test_pg_concurrent_retry_scores_once_and_saves_reconciliation(pg_engine):
    import threading
    from conftest import safe_test_url
    sample = json.loads((ARTIFACTS / 'sample_fraud.json').read_text())
    scorer = Scorer(ARTIFACTS)
    counter = {'calls': 0}
    guard = threading.Lock()
    barrier = threading.Barrier(5)
    class CountedScorer:
        def score(self, reference, features):
            with guard:
                counter['calls'] += 1
            return scorer.score(reference, features)
    key = uuid.uuid4().hex
    def submit():
        barrier.wait(timeout=20)
        with Session(pg_engine) as session:
            tx, created = submit_transaction(session, 'checkout_service', key, key,
                                             sample['features'], CountedScorer())
            return tx.id, created
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: submit(), range(5)))
    assert len({tx_id for tx_id, _ in results}) == 1
    assert sum(created for _, created in results) == 1
    assert counter['calls'] == 1
    with Session(pg_engine) as session:
        events = session.query(AuditEventRecord).filter_by(transaction_id=results[0][0]).all()
        assert len(events) == 1
        explanation = events[0].payload['explanation']
        assert explanation['base_margin'] + explanation['all_feature_contributions_sum'] == pytest.approx(
            explanation['model_margin'], abs=1e-4)


def test_pg_failed_audit_insert_leaves_no_transaction(monkeypatch, pg_engine):
    """Real rollback assertion, not only a mock rollback-call check."""
    from sqlalchemy import event
    sample = json.loads((ARTIFACTS / 'sample_fraud.json').read_text())
    key = uuid.uuid4().hex
    def reject_audit(mapper, connection, target):
        raise RuntimeError('simulated audit insert failure')
    event.listen(AuditEventRecord, 'before_insert', reject_audit)
    try:
        with Session(pg_engine) as session:
            with pytest.raises(RuntimeError, match='audit insert'):
                submit_transaction(session, 'checkout_service', key, key,
                                   sample['features'], Scorer(ARTIFACTS))
    finally:
        event.remove(AuditEventRecord, 'before_insert', reject_audit)
    with Session(pg_engine) as session:
        assert session.query(TransactionRecord).filter_by(idempotency_key=key).count() == 0


def test_test_database_query_cannot_override_the_validated_target():
    with pytest.raises(ValueError, match='overrides'):
        validate_test_database_url('postgresql://a:b@localhost/fraudshield_test_db?dbname=live_db')
