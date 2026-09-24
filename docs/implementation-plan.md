# FraudShield 2.0 — Implementation Plan

## 1. Current State
* **Repository**: Freshly initialized workspace at `d:/FraudShield`.
* **Environment**: Windows OS environment with Python 3, Node.js/npm, Docker capability.
* **Goal**: Build a competition-grade, production-oriented prototype for **FraudShield 2.0 — Temporal Graph Intelligence & AI Investigation Platform for Financial Fraud**.

---

## 2. Target Architecture

```text
                               ┌───────────────────────┐
                               │       FRONTEND        │
                               │ Next.js 14+ (App Dir) │
                               │ Tailwind + Lucide UI  │
                               │ Recharts + Graph Viz  │
                               └───────────┬───────────┘
                                           │ (REST API / JSON)
                                           ▼
                               ┌───────────────────────┐
                               │       FASTAPI         │
                               │   API Gateway & Core  │
                               └───────────┬───────────┘
                                           │
             ┌─────────────────────────────┼─────────────────────────────┐
             │                             │                             │
             ▼                             ▼                             ▼
  ┌───────────────────┐          ┌───────────────────┐         ┌───────────────────┐
  │    PostgreSQL     │          │    ML & Risk      │         │   Neo4j Graph DB  │
  │ Transactions,     │          │ Supervised XGBoost│         │ Customer, Account,│
  │ Cases, Users,     │          │ Anomaly IsoForest │         │ Device, IP,      │
  │ pgvector Knowledge│          │ SHAP Explainer    │         │ Beneficiary Nodes │
  └───────────────────┘          └───────────────────┘         └───────────────────┘
                                           │
                                           ▼
                                 ┌───────────────────┐
                                 │ Temporal & Fusion │
                                 │ Risk Evolution    │
                                 │ Calibrated Fusion │
                                 └─────────┬─────────┘
                                           │
                                           ▼
                                 ┌───────────────────┐
                                 │ AI Agent & RAG    │
                                 │ Policy Retrieval  │
                                 │ Tool-Based Agent  │
                                 └─────────┬─────────┘
                                           │
                                           ▼
                                 ┌───────────────────┐
                                 │ Case & Governance │
                                 │ Human Feedback    │
                                 │ Audit & Registry  │
                                 └─────────┬─────────┘
```

---

## 3. Missing Components (To Be Built)

1. **Project Infrastructure & Tooling** (Directory structure, Docker Compose setup, `.env.example`, Python dependencies, Next.js app initialization).
2. **Database & Persistence** (PostgreSQL schema with SQLAlchemy models, Alembic/schema initializer, Pydantic schemas, repositories).
3. **Synthetic Generator & ML Pipeline** (Scenario-driven financial transaction generator, feature extraction, train/val/test split without leakage, XGBoost, Isolation Forest, model serialization).
4. **Behavior Engine** (User profiling, velocity tracking, baseline comparison, deviation scores).
5. **Calibrated Risk Fusion** (Combining ML, anomaly, behavior, rule, temporal, and graph scores into a unified calibrated risk rating).
6. **FastAPI Backend Endpoints** (Auth, transactions, alerts, cases, risk timeline, graph query, AI investigation, governance endpoints).
7. **Next.js Frontend Dashboard** (Dark/light theme financial security UI, real-time metrics, interactive risk timeline, SHAP visualizations, graph canvas, AI assistant drawer, case management UI).
8. **Neo4j Entity Graph Service** (Graph modeling, Cypher queries, multi-hop link analysis, shared infrastructure detection).
9. **Temporal Risk Timeline** (Event sequence risk evolution engine).
10. **Fraud-Ring Detection** (Heuristic graph network analysis for shared device/IP/beneficiary clusters).
11. **Explainability Module** (SHAP value computation, visual breakdown, evidence mapping).
12. **RAG Knowledge Base** (Fraud typologies, policies, historical cases, pgvector embeddings, semantic search).
13. **AI Investigation Agent** (Controlled tool calling, structured investigation output, prompt injection defense, grounding checks).
14. **Case Management & Analyst Feedback** (Lifecycle tracking, audit logs, decision recording, retraining candidate dataset validation).
15. **Model Governance & Monitoring** (Registry tracking model versions, metrics, drift detection).
16. **Security & RBAC** (JWT authentication, role enforcement, hashed sensitive PII).
17. **Test Suite & Verification** (Unit tests, integration tests, synthetic end-to-end scenario verifications).

---

## 4. Implementation Phases (20 Stages)

* **Stage 1 — Project Foundation**: Repository structure (`backend/`, `frontend/`, `ml/`, `knowledge/`, `docs/`, `docker/`, `scripts/`), `docker-compose.yml`, Python virtual environment & requirements, Next.js scaffolding.
* **Stage 2 — Database**: SQLAlchemy models for all 15 core entities, PostgreSQL database initialization scripts, Alembic migrations.
* **Stage 3 — Dataset + ML**: Synthetic transaction data generator (Scenarios A-E), XGBoost/RandomForest/Logistic Regression training pipeline, class imbalance handling, evaluation, SHAP explainer setup.
* **Stage 4 — Behavior Engine**: Stateful user/account behavioral profiling, velocity calculation, deviation scoring.
* **Stage 5 — Risk Fusion**: Configurable calibrated multi-signal risk fusion engine.
* **Stage 6 — Backend API**: Core FastAPI application, routers, dependency injection, CORS, error handling middleware.
* **Stage 7 — Frontend Dashboard**: Next.js App Router, Tailwind CSS design system, Executive Dashboard, Transaction Detail, Alert Feed.
* **Stage 8 — Neo4j Entity Graph**: Graph database connection, Cypher query layer, interactive React Flow/Cytoscape graph visualization in UI.
* **Stage 9 — Temporal Risk**: Sequence risk engine, timeline step visualization on frontend.
* **Stage 10 — Fraud-Ring Detection**: Graph heuristic algorithms for shared infrastructure detection, potential network UI cards.
* **Stage 11 — Explainability**: SHAP visual breakdown component, evidence rationale mapping.
* **Stage 12 — RAG**: Fraud policy documents, chunking, pgvector indexing, semantic retriever.
* **Stage 13 — AI Investigation Agent**: Tool-enabled agent calling graph, transaction, temporal, and RAG tools to synthesize structured evidence reports.
* **Stage 14 — Case Management**: Case creation, assignment, evidence attachment, audit trail logging.
* **Stage 15 — Human Feedback**: Analyst feedback submission API, model training candidate dataset staging.
* **Stage 16 — Governance**: Model registry dashboard, performance tracking, drift metrics.
* **Stage 17 — Security**: JWT auth, password hashing, RBAC middleware, input sanitization.
* **Stage 18 — Testing**: Comprehensive pytest suite & synthetic pipeline execution test.
* **Stage 19 — Deployment**: Fully containerized Docker Compose environment verified with health checks.
* **Stage 20 — Competition Demo**: End-to-end scenario runner demonstrating Scenarios A-E with full evidence flow.

---

## 5. Dependencies

### Backend & ML (Python)
* `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
* `sqlalchemy`, `psycopg2-binary`, `pgvector`, `alembic`
* `xgboost`, `scikit-learn`, `pandas`, `numpy`, `shap`, `joblib`
* `neo4j`
* `python-jose`, `passlib`, `bcrypt`
* `pytest`, `httpx`
* `openai` (or configurable OpenAI-compatible LLM client)

### Frontend (Node.js/React/Next.js)
* `next`, `react`, `react-dom`
* `typescript`, `@types/node`, `@types/react`
* `tailwindcss`, `postcss`, `autoprefixer`, `lucide-react`, `clsx`, `tailwind-merge`
* `recharts`
* `@xyflow/react` (or `reactflow`) for graph visualization

---

## 6. Risks & Mitigation Strategies

1. **Neo4j / PostgreSQL Service Availability**:
   * *Mitigation*: Build explicit fallback/mock query interfaces in the backend so the system operates seamlessly if Neo4j or vector services are running in lightweight local mode.
2. **LLM Provider Dependency / Rate Limits**:
   * *Mitigation*: Abstract LLM interaction behind a tool-calling fallback engine; support mock provider mode with structured rule-based fallback responses when `LLM_API_KEY` is absent or unconfigured.
3. **Data Leakage in Feature Engineering**:
   * *Mitigation*: Enforce temporal split for dataset train/val/test splits and fit scalers/oversamplers strictly on training folds.
4. **SHAP Latency on High-Dimensional Trees**:
   * *Mitigation*: Cache tree explainer objects and background SHAP computation for live inference endpoints using tree path approximations (`TreeExplainer`).

---

## 7. Testing Strategy
* **Unit Tests**: Test behavioral profile calculators, rule engine triggers, risk fusion math, feature extraction routines, and database models.
* **Integration Tests**: Test FastAPI endpoints using `TestClient` with test SQLite/Postgres instances.
* **Agent & Tool Tests**: Verify tool schemas, parameter validation, and prompt injection defense.
* **End-to-End Scenarios**: Executable script `scripts/run_demo_scenarios.py` validating Scenarios A through E end-to-end.

---

## 8. Deployment Strategy
* Multi-container Docker setup via `docker-compose.yml`:
  - `postgres` (with `pgvector` extension)
  - `neo4j` (Community Edition with APOC plugin)
  - `redis` (Cache & event pub-sub baseline)
  - `backend` (FastAPI + Uvicorn)
  - `frontend` (Next.js Node server)
* Configured using clean `.env` variables with robust defaults for local development.
