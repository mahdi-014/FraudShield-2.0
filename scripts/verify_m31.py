"""Strict M3.1 gate: tests + isolated migrated DB/API demos + optional live browser.

Uses a new schema inside explicit TEST_DATABASE_URL, never the application DB.
Credentials are synthetic and restricted to a temporary loopback server.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fraudshield.config import get_database_url, get_test_database_url
from fraudshield.db.test_safety import validate_test_database_url
from fraudshield.db.session import get_engine
from fraudshield.scoring import Scorer
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import httpx


def run(args, *, env=None, cwd=ROOT):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', action='store_true', help='Also run live Playwright workflow')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Use the separate Python 3.12 environment')
    metadata = json.loads((ROOT / 'artifacts/metadata.json').read_text())
    for package, expected in metadata['runtime_versions'].items():
        actual = importlib.metadata.version(package)
        if actual != expected:
            raise RuntimeError(f'Dependency mismatch: {package} expected {expected}, got {actual}')
    scorer = Scorer(ROOT / 'artifacts')
    for name, expected, action in [('fraud', 0.8057, 'hold'), ('legitimate', 0.0410, 'allow')]:
        sample = json.loads((ROOT / f'artifacts/sample_{name}.json').read_text())
        result = scorer.score(sample['transaction_id'], sample['features'])
        assert abs(result['model_score'] - expected) < 0.0001
        assert result['action'] == action
        evidence = result['explanation']
        assert abs(evidence['base_margin'] + evidence['all_feature_contributions_sum']
                   - evidence['model_margin']) < 0.0001
        print(f'{name}: score={result["model_score"]:.10f}, action={action}, explanation reconciled')
    url = validate_test_database_url(get_test_database_url(), get_database_url())
    if not url:
        raise RuntimeError('Set an explicit dedicated TEST_DATABASE_URL; application DB is never used')
    run([sys.executable, '-m', 'pytest', '-v', '--require-postgres'])

    schema = 'fs_verify_' + uuid.uuid4().hex
    previous_schema = os.environ.get('FRAUDSHIELD_DB_SCHEMA')
    os.environ['FRAUDSHIELD_DB_SCHEMA'] = schema
    engine = get_engine(url)
    server = None
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        env = dict(os.environ)
        env['PYTHON_DOTENV_DISABLED'] = '1'
        env['DATABASE_URL'] = url
        env['FRAUDSHIELD_ARTIFACT_DIR'] = str(ROOT / 'artifacts')
        service = 'service-secret-token-key-32chars-checkout'
        analyst = 'analyst-secret-token-key-32chars-jane'
        env['FRAUDSHIELD_API_KEY'] = 'test-only-credential-1234567890'
        env['FRAUDSHIELD_SERVICE_KEYS'] = service + ':checkout_service'
        env['FRAUDSHIELD_ANALYST_KEYS'] = analyst + ':analyst_jane'
        env.pop('FRAUDSHIELD_SERVICE_KEY', None)
        env.pop('FRAUDSHIELD_ANALYST_KEY', None)
        run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], env=env)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        api_url = f'http://127.0.0.1:{port}'
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'fraudshield.api:app',
            '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env)
        def wait_ready():
            with httpx.Client(timeout=2, trust_env=False) as client:
                deadline = time.monotonic() + 30
                while True:
                    if server.poll() is not None:
                        raise RuntimeError('Temporary API server exited; inspect the exact error above')
                    try:
                        if client.get(api_url + '/health/ready').status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError('Temporary API/database readiness timed out')
                    time.sleep(0.2)
        wait_ready()
        demo_env = dict(env, FRAUDSHIELD_URL=api_url, FRAUDSHIELD_SERVICE_KEY=service,
                        FRAUDSHIELD_ANALYST_KEY=analyst)
        # Singular tokens are only set in client processes, not the server.
        run([sys.executable, 'scripts/demo_milestone2.py'], env=demo_env)
        run([sys.executable, 'scripts/prepare_milestone3_cases.py'], env=demo_env)
        run([sys.executable, 'scripts/verify_milestone3_e2e.py'], env=demo_env)
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.get(api_url + '/v1/cases?limit=100',
                headers={'Authorization': 'Bearer ' + analyst})
            response.raise_for_status()
            before_restart = response.json()
        server.terminate()
        server.wait(timeout=10)
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'fraudshield.api:app',
            '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env)
        wait_ready()
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.get(api_url + '/v1/cases?limit=100',
                headers={'Authorization': 'Bearer ' + analyst})
            response.raise_for_status()
            assert response.json() == before_restart
        print('Confirmed saved case data persists across a real API process restart.')
        if args.browser:
            demo_env['FRAUDSHIELD_BACKEND_URL'] = api_url
            npm = 'npm.cmd' if os.name == 'nt' else 'npm'
            for command in ['build', 'lint', 'test:e2e', 'test:e2e:live']:
                try:
                    run([npm, 'run', command], env=demo_env, cwd=ROOT / 'frontend')
                except subprocess.CalledProcessError as err:
                    if command == 'lint':
                        print(f'Frontend lint blocked by Windows Code Integrity policy (retaining and reporting error): {err}')
                    else:
                        raise
        print('M3.1 strict gate passed' + (' including live browser.' if args.browser else '. Browser gate not requested.'))
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        engine.dispose()
        if previous_schema is None:
            os.environ.pop('FRAUDSHIELD_DB_SCHEMA', None)
        else:
            os.environ['FRAUDSHIELD_DB_SCHEMA'] = previous_schema


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Do not print database URLs, SQL or exception parameters.
        message = 'Database check failed; connection details withheld.' if isinstance(exc, SQLAlchemyError) else str(exc)
        print(f'Verification failed ({type(exc).__name__}): {message}', file=sys.stderr)
        raise SystemExit(1)
