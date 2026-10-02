"""Fail-closed validation for integration-test targets; never falls back to app data."""
import re
from sqlalchemy.engine import make_url


def validate_test_database_url(test_url, application_url=None):
    if not test_url:
        return None
    target = make_url(test_url)
    override_keys = {'dbname', 'database', 'service', 'servicefile'}
    if override_keys.intersection(target.query):
        raise ValueError('Test database target overrides in URL query are not allowed')
    if application_url and override_keys.intersection(make_url(application_url).query):
        raise ValueError('Application database target overrides must be removed before testing')
    if target.get_backend_name() != 'postgresql':
        raise ValueError('TEST_DATABASE_URL must point to PostgreSQL')
    if not target.database or not re.search(r'(?:^|_)test(?:_|$)', target.database):
        raise ValueError('Test database name must contain a separate _test component')
    # Conservative: require different database names even across hosts/drivers/users.
    # This also rejects aliases and credentials that refer to the same database.
    if application_url and target.database == make_url(application_url).database:
        raise ValueError('Test and application database names must be different')
    return test_url
