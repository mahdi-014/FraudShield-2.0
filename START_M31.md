# FraudShield Milestone 3.1 — install and finish verification

This package implements the hardening changes from the developer review. It extends the existing project; it does not train a model or change policy thresholds. Customer verification, graph intelligence and RAG remain future milestones.

## Verified in the development environment

- New, separate Python 3.12.14 virtual environment; original requirements installed successfully; `pip check` passed.
- Backend: **56 passed, 0 failed, 9 skipped** out of 65 tests. The nine skips require PostgreSQL, which was unavailable here.
- Real Chromium UI regression tests with explicitly mocked API responses: **8 passed**. These test rendered workflows, timezone, expired authentication, role rejection, stale queue/audit responses, conflict and logout.
- Frontend production build passed. Lint has three state-in-effect warnings and no errors.
- Real scipy/sklearn imports and saved preprocessor loaded normally.
- Fraud score **0.8056925535 -> hold**; legitimate score **0.0410388671 -> allow**. TreeSHAP sums reconcile.
- All uploaded artifact files remain byte-for-byte identical, including model, preprocessor, metadata and thresholds.
- Offline Alembic SQL generation passed; live migration execution remains unverified.

**The complete M3.1 gate is pending a live PostgreSQL run on your machine.** Live API/database demos and the live browser test were added to the strict verification command but were not executed against PostgreSQL here. The normal browser download endpoint was unavailable in this environment; the eight UI tests were run with a separately supplied Chromium executable. That testing executable is not part of this source package.

## Changes included

1. Removed test database fallback to application DATABASE_URL. Tests reject unsafe targets, driver/host aliases with the same database name and URL query overrides that alter the validated database target.
2. Tests create a fresh random schema inside the dedicated test DB and drop only that schema. They never call `drop_all()` on the application database.
3. Synthetic test credentials and seeded M3 filters/pagination assertions; no dependence on real analyst tokens.
4. Generic 503 database and 500 internal responses with request IDs. No SQL, exception parameters or customer features in error responses/log messages.
5. Removed silent unlocked fallback. Concurrent idempotent submissions acquire a transaction-scoped PostgreSQL advisory lock before scoring. Uniqueness remains enforced by the database.
6. Full TreeSHAP reconciliation fields preserved in submission audit payloads; top factors remain unchanged.
7. Queue generation guards, audit cancellation, reset of selected detail state and centralized 401/403 session invalidation.
8. Full workflow readiness returns 503 when persistence is unavailable; `/health/scorer` reports scorer readiness separately.
9. Explicit CORS origins; default same-origin deployment works with the existing Vite proxy. Blank reasons/references and conflicting reference aliases rejected.
10. Honest audit-history and simulated-verification wording. Audit immutability is not database-enforced.
11. Configured database driver respected. No automatic driver substitution, dependency stubs or security-control changes.

## Safe Windows setup

Extract this ZIP into a **new folder**. Keep your existing project, `.venv`, `.env`, database and artifacts as a backup. Copy your existing `.env` into the extracted project without posting its contents to a chat or terminal log. The ZIP contains `.env.example`; it intentionally contains no real `.env`, database data, installed environments or node_modules.

Open PowerShell in the extracted `fraudshield` folder:

```powershell
py -3.12 -m venv .venv-m31
.\.venv-m31\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-m31\Scripts\python.exe -m pip check
.\.venv-m31\Scripts\python.exe -m pytest -v
```

These commands use the new interpreter directly; PowerShell activation policy does not need to be changed. Do not delete your original environment. If Windows blocks an import, retain and report its exact error. Do not add SciPy/sklearn stubs or change Windows security settings.

Ensure `TEST_DATABASE_URL` in `.env` points to an existing **separate PostgreSQL database** whose name contains an underscore-delimited `test` component, for example `fraudshield_test_db`. Its name must differ from the database in `DATABASE_URL`; different hosts/drivers/credentials do not bypass this check. Use a dedicated test role that can create/drop schemas in the test DB and cannot access application data. If your test database does not exist, create it with your PostgreSQL administrator before running the strict gate.

Keep the driver you actually verified. `postgresql+psycopg2://...` uses psycopg2. `postgresql+pg8000://...` explicitly selects the real Python pg8000 driver. Report a blocked psycopg2 import before deliberately selecting another driver; this package never silently substitutes it.

Frontend dependencies and browser preparation:

```powershell
Set-Location frontend
npm ci
npx playwright install chromium
npm run build
npm run lint
npm run test:e2e
Set-Location ..
```

Finish the entire verification gate:

```powershell
.\.venv-m31\Scripts\python.exe scripts\verify_m31.py --browser
```

The strict command:

- Checks Python/model dependency versions and both sample scores with reconciliation.
- Runs every backend test with `--require-postgres`, so unavailable DB tests fail instead of producing a misleading all-clear.
- Creates a separate random verification schema in TEST_DATABASE_URL and applies the actual Alembic migration there.
- Starts a temporary API on a random loopback port using only synthetic credentials.
- Runs the full M2 demo, seeds M3 cases and runs the M3 API workflow.
- Restarts the API process and compares persisted case data.
- Builds/lints the frontend and runs the eight fixture-based browser regressions plus the live browser release/reject workflow against the temporary API/database.
- Stops its temporary server and drops only its own verification schema in a `finally` cleanup.

It leaves your application DB, original `.env` and existing model artifacts alone. Port 4173 must be free for Playwright's temporary frontend server. Do not run multiple strict verification commands concurrently in the same folder.

## Completion criteria

For this package, expect **65 backend tests passed, zero failed and zero skipped**, eight fixture-based UI browser tests passed, and one live browser workflow passed (which exercises release and reject). M2 and M3 scripts, the actual API process restart, dependency alignment and sample checks must also pass. Build/lint status and any warnings should be retained in the report. Actual Windows dependency errors must be reported, not hidden.

Run the optional development servers only after verification:

```powershell
.\.venv-m31\Scripts\python.exe -m uvicorn fraudshield.api:app --host 127.0.0.1 --port 8000
```

In a second terminal, run `npm run dev` from `frontend`. Normal development uses your configured application DB, so the temporary verification data will not appear there. The changed readiness endpoint intentionally reports an unavailable DB as 503.

Read `ANTIGRAVITY_M31_PROMPT.md` to have your Antigravity agent apply/verify this package. Only move to M4 after the live gate passes. M4 will implement the remaining simulated acknowledgement/verification and analyst disposition flows.
