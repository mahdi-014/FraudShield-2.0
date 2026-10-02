# Paste this into Antigravity

Use the supplied FraudShield Milestone 3.1 package as the implementation for hardening the existing project. Read START_M31.md first and inspect the existing working tree before changing it. Preserve uncommitted work; use a new branch or separate folder. Do not discard files or reset the repository.

Preserve the existing .env, application database, Milestone 2 dependencies and every model artifact. Do not retrain, calibrate scores or change thresholds. Do not add numerical-function stubs or disable security controls. The package model artifacts must match the existing uploaded baseline hashes.

Apply the code changes and new files, including the test fixtures, safe test database validator, repository locks, API handlers, schema-aware Alembic setup, frontend request guards and Playwright tests. Preserve the requirements pins. Keep audit history described as application-level append behavior; do not claim database-enforced immutability.

Create .venv-m31 with Python 3.12 and install the original requirements there. Inspect .env locally without printing credentials. Verify TEST_DATABASE_URL names an existing PostgreSQL test database distinct from the application DB, using an appropriate test role. Never fall back to DATABASE_URL and never drop application tables. If anything blocks dependency loading, show the exact error; do not mask it.

Follow START_M31.md: install frontend dependencies/browser and run scripts/verify_m31.py --browser. This must exercise all 65 backend tests without skips, all eight fixture browser tests, the live browser workflow, both scoring samples, reconciliation, actual isolated migrations, both demos and actual API process restart persistence. If a check fails, fix the underlying implementation/configuration and rerun the affected checks. Do not weaken assertions, skip tests or alter sample scores to get a pass.

Return a concise report with passed/failed/skipped counts, both sample scores, explanation reconciliation, frontend build/lint results, live PostgreSQL/browser results and any unresolved exact dependency errors. Keep fixtures and simulated verification explicitly labeled. Mark M3.1 complete only when the live gate passes. Do not start graph/RAG or M4 features in this hardening task.
