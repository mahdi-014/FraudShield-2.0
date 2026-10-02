"""Synthetic credentials and disposable-schema PostgreSQL fixtures."""
import os
import uuid
from pathlib import Path
import pytest
from sqlalchemy import text
from fraudshield.config import get_database_url, get_test_database_url
from fraudshield.db.session import get_engine, check_database_connection
from fraudshield.db.models import Base
from fraudshield.db.test_safety import validate_test_database_url

ARTIFACTS = Path(__file__).resolve().parents[1] / 'artifacts'

def safe_test_url():
    try:
        return validate_test_database_url(get_test_database_url(), get_database_url())
    except ValueError as exc:
        raise pytest.UsageError(str(exc)) from None

def pytest_addoption(parser):
    parser.addoption('--require-postgres', action='store_true',
                     help='Fail if PostgreSQL integration tests cannot run')

@pytest.fixture(autouse=True)
def synthetic_credentials(monkeypatch):
    monkeypatch.setenv('FRAUDSHIELD_API_KEY', 'test-only-credential-1234567890')
    monkeypatch.setenv('FRAUDSHIELD_SERVICE_KEYS',
        'service-secret-token-key-32chars-checkout:checkout_service,'
        'service-secret-token-key-32chars-payments:payments_service')
    monkeypatch.setenv('FRAUDSHIELD_ANALYST_KEYS',
        'analyst-secret-token-key-32chars-jane:analyst_jane')
    monkeypatch.delenv('FRAUDSHIELD_SERVICE_KEY', raising=False)
    monkeypatch.delenv('FRAUDSHIELD_ANALYST_KEY', raising=False)
    monkeypatch.setenv('FRAUDSHIELD_ARTIFACT_DIR', str(ARTIFACTS))

@pytest.fixture(scope='session')
def pg_engine(request):
    url = safe_test_url()
    if not url or not check_database_connection(url):
        if request.config.getoption('--require-postgres'):
            pytest.fail('Dedicated TEST_DATABASE_URL is missing or PostgreSQL is unavailable')
        pytest.skip('Dedicated PostgreSQL test database unavailable; integration unverified')
    schema = 'fs_test_' + uuid.uuid4().hex
    patch = pytest.MonkeyPatch()
    patch.setenv('FRAUDSHIELD_DB_SCHEMA', schema)
    engine = get_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        Base.metadata.create_all(engine)
        yield engine
    finally:
        # Only the schema created by this run is eligible for cleanup.
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()
        patch.undo()
