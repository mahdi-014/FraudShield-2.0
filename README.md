# FraudShield: Machine Learning Risk Assessment & Decision System

FraudShield scores transaction requests against a reproducible IEEE-CIS fraud detection model (XGBoost candidate with TreeSHAP explanations), enforces policy thresholds, and provides persistent PostgreSQL storage, a simulated payment state machine, analyst review queues, optimistic concurrency control, and append-only audit histories.

> **Note on Research Prototype Scope:**
> This is a simulated transaction risk system. It does not move actual funds, validate live Bangladesh MFS rails, or connect to production payment gateways. Labels indicate historical dataset outcomes. Customer acknowledgement (`awaiting_acknowledgement`) and multi-factor customer verification flows (`pending_verification`) are deferred to future milestones.

---

## Architecture & System Overview

- **ML Inference & Explainability:** Preprocessor and XGBoost booster generating calibrated risk scores and exact TreeSHAP log-odds feature contributions.
- **Persistence:** PostgreSQL database accessed via SQLAlchemy 2.0 and versioned with Alembic migrations.
- **Workflow State Machine:**
  - Initial scoring policy mapping:
    - `allow` &rarr; `completed` (terminal state)
    - `warn` &rarr; `awaiting_acknowledgement` (customer flow deferred)
    - `pause` &rarr; `pending_verification` (analyst reviewable)
    - `hold` &rarr; `held_for_review` (analyst reviewable)
  - Analyst interventions:
    - `release` &rarr; `completed` (terminal state)
    - `reject` &rarr; `rejected` (terminal state)
  - Terminal states (`completed`, `rejected`) are immutable; subsequent modification attempts return HTTP 409 Conflict.
- **Server-Side Authorization & RBAC:**
  - Service Credentials: Submit transactions and read only their own transaction records.
  - Analyst Credentials: View review cases, resolve cases with atomic optimistic concurrency, and inspect audit logs.
  - Legacy Scorer Credential: Maintained for backwards compatibility with `/v1/schema` and `/v1/score`.
  - Server binds identities strictly from credentials; request bodies cannot set or spoof actors.
  - Config rejects duplicate tokens configured across different roles.
- **Idempotency & Concurrency:**
  - `POST /v1/transactions` enforces the `Idempotency-Key` header with SHA-256 canonical payload hashing.
  - Identical submissions return the stored transaction without rescoring or duplicate audit logs.
  - Reusing a key with altered inputs returns HTTP 409 Conflict.
  - Optimistic locking (`expected_version`) on analyst decisions guards against race conditions.
- **Audit Trail:** Append-only log capturing authenticated actor, role, timestamp, previous status, resulting status, and action reasons.

---

## Quick Start (Windows PowerShell)

### 1. Environment & Dependencies

Use Python 3.12+ in an isolated virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` or set required variables:

```powershell
Copy-Item .env.example .env
```

Key environment configuration variables:
```ini
DATABASE_URL=postgresql+psycopg2://fraudshield:fraudshield_password@localhost:5432/fraudshield_db
TEST_DATABASE_URL=postgresql+psycopg2://fraudshield:fraudshield_password@localhost:5432/fraudshield_test_db
FRAUDSHIELD_API_KEY=fraudshield-dev-secret-key-32characters-secure
FRAUDSHIELD_SERVICE_KEYS=service-secret-token-key-32chars-checkout:checkout_service,service-secret-token-key-32chars-payments:payments_service
FRAUDSHIELD_ANALYST_KEYS=analyst-secret-token-key-32chars-jane:analyst_jane,analyst-secret-token-key-32chars-bob:analyst_bob
FRAUDSHIELD_ARTIFACT_DIR=artifacts
```

### 3. PostgreSQL Database Setup

#### Option A: Docker Compose (Recommended)
If Docker Desktop is installed:
```powershell
docker compose up -d
```
This runs PostgreSQL 16 on port 5432 with persistent storage in volume `postgres_data`.

#### Option B: Native PostgreSQL (When Docker is Unavailable)
1. Install PostgreSQL via installer or package manager:
   ```powershell
   winget install PostgreSQL.PostgreSQL.16
   ```
2. Start the Windows PostgreSQL service:
   ```powershell
   Start-Service postgresql*
   ```
3. Initialize the development and test databases using `psql`:
   ```sql
   CREATE USER fraudshield WITH PASSWORD 'fraudshield_password';
   CREATE DATABASE fraudshield_db OWNER fraudshield;
   CREATE DATABASE fraudshield_test_db OWNER fraudshield;
   ```

### 4. Run Alembic Database Migrations

Apply database schema migrations:

```powershell
python -m alembic upgrade head
```

To preview SQL without connecting to a live database (offline mode):
```powershell
python -m alembic upgrade head --sql
```

### 5. Start the API Server

```powershell
python -m uvicorn fraudshield.api:app --host 127.0.0.1 --port 8000
```

- Interactive OpenAPI Swagger documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: `GET http://127.0.0.1:8000/health/ready`

---

## End-to-End Workflow Demonstration

Run the automated demonstration script to observe the full lifecycle:
1. Submit held-out fraud sample with service credentials (`checkout_service`).
2. Observe model assessment (`hold`, score ~0.8057) and creation of a review case in `held_for_review`.
3. Analyst (`analyst_jane`) fetches the case and reviews TreeSHAP factors.
4. Analyst releases the case with verified justification and expected record version.
5. Review complete audit log demonstrating authenticated actors and timestamps.

```powershell
python scripts/demo_milestone2.py
```

---

## API Endpoints & Sample Requests

### 1. System Health
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/ready" | ConvertTo-Json
```

### 2. Submit Transaction (Service Role)
Requires `Idempotency-Key` header and service authorization:

```powershell
$headers = @{
    "Authorization" = "Bearer service-secret-token-key-32chars-checkout"
    "Idempotency-Key" = "tx-sample-001"
}
$body = Get-Content artifacts/sample_fraud.json -Raw
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/transactions" -Method Post -Headers $headers -Body $body -ContentType "application/json" | ConvertTo-Json
```

### 3. List Review Cases (Analyst Role)
```powershell
$headers = @{ "Authorization" = "Bearer analyst-secret-token-key-32chars-jane" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cases?status=open" -Headers $headers | ConvertTo-Json
```

### 4. Execute Analyst Action (Release / Reject)
Atomic transition with optimistic concurrency check (`expected_version`):

```powershell
$headers = @{
    "Authorization" = "Bearer analyst-secret-token-key-32chars-jane"
    "Content-Type" = "application/json"
}
$body = @{
    action = "release"
    reason = "Customer telephone confirmation and valid identity matched."
    expected_version = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/cases/<CASE_ID>/actions" -Method Post -Headers $headers -Body $body | ConvertTo-Json
```

### 5. Fetch Audit Trail
```powershell
$headers = @{ "Authorization" = "Bearer analyst-secret-token-key-32chars-jane" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/transactions/<TRANSACTION_ID>/audit" -Headers $headers | ConvertTo-Json
```

---

## Testing & Verification

Run the entire test suite (pipeline validation, feature normalization, TreeSHAP explanation reconciliation, authentication, state transitions, idempotency, and concurrency):

```powershell
python -m pytest -v
```

If PostgreSQL is running at `DATABASE_URL` or `TEST_DATABASE_URL`, all live PostgreSQL integration tests run automatically. If PostgreSQL is offline, those integration tests are cleanly marked as unverified (skipped) without failing the suite.

---

## File Structure

- `fraudshield/features.py`: Feature normalization and contract definition.
- `fraudshield/scoring.py`: Model loader, policy evaluator, and TreeSHAP log-odds explanation reconciliation.
- `fraudshield/state_machine.py`: Transaction status lifecycle, initial risk mapping, and analyst transition rules.
- `fraudshield/config.py`: Environment configuration, role definitions, and credential validator.
- `fraudshield/db/models.py`: SQLAlchemy database models (`TransactionRecord`, `ReviewCaseRecord`, `AnalystActionRecord`, `AuditEventRecord`).
- `fraudshield/db/session.py`: Database engine and connection lifecycle management.
- `fraudshield/db/repository.py`: Atomic transaction submission, idempotency verification, optimistic concurrency, and audit logging.
- `fraudshield/api.py`: FastAPI implementation with role-based dependencies and error handling.
- `alembic/`: Alembic migrations configuration and revision scripts.
- `docker-compose.yml`: Local PostgreSQL container setup with persistent volume.
- `scripts/replay.py`: Legacy scoring replay client.
- `scripts/demo_milestone2.py`: End-to-end Milestone 2 workflow demonstration.
- `tests/test_pipeline.py`: Baseline tests for data splits, feature constraints, and model reconciliation.
- `tests/test_milestone2.py`: Milestone 2 state machine, auth, idempotency, and PostgreSQL integration tests.

---

## Remaining Scope & Next Milestones

- **Milestone 3:** Analyst Dashboard Web UI with real-time queues, metrics visualization, and case review filters.
- **Customer Verification Rails:** Implement customer SMS/OTP verification for `pending_verification` and customer acknowledgement for `awaiting_acknowledgement`.
- **Graph & Entity Resolution:** Identity network graphs, device sharing, and RAG entity context.
