# FraudShield 2.0 — Temporal Graph Intelligence & AI Investigation Platform for Financial Fraud

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost%20%2B%20SHAP-orange.svg)](https://xgboost.readthedocs.io/)
[![Neo4j](https://img.shields.io/badge/Graph-Neo4j%205.18-45818e.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**FraudShield 2.0** is an evidence-driven financial fraud intelligence and investigation platform designed to move beyond traditional point-in-time classifiers. By fusing **Supervised ML**, **Anomaly Detection**, **User Behavioral Profiles**, **Deterministic Business Rules**, **Entity Graph Topology**, **Temporal Risk Timelines**, **RAG Knowledge Retrieval**, and an **AI Investigation Copilot**, FraudShield empowers human analysts to understand _why_ a transaction is suspicious and _how_ risk evolved across connected networks.

---

## 🚀 Key Features

- **Calibrated Multi-Signal Risk Fusion**: Fuses ML probability, anomaly scores, behavioral deviation, rule triggers, graph topology, and sequence timeline into a calibrated risk score (0–100%).
- **SHAP Feature Importance & Explainability**: Mathematical attribution breaking down exact risk drivers for every transaction.
- **Temporal Risk Timeline Engine**: Visualizes event-by-event risk evolution sequence from ingestion to final triage.
- **Neo4j Entity Graph & Fraud-Ring Detection**: Multi-hop link analysis uncovering shared device fingerprints, proxy IPs, and coordinated money mule clusters.
- **RAG Policy & Historical Case Retrieval**: Grounded policy citations (pgvector retrieval) explaining applicable compliance guidelines.
- **Tool-Enabled AI Investigation Agent**: AI copilot synthesizing auditable investigation summaries with explicit evidence citations and recommended next steps.
- **Human-in-the-Loop Feedback & Governance**: Decision recording (`CONFIRMED_FRAUD`, `FALSE_POSITIVE`, `INCONCLUSIVE`) with model registry versioning and drift monitoring.

---

## 🏗️ System Architecture

```text
                               ┌───────────────────────┐
                               │       FRONTEND        │
                               │ Next.js 14 (App Dir)  │
                               │ Tailwind + Lucide UI  │
                               │ Recharts + ReactFlow  │
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
```

---

## 🛠️ Technology Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Recharts, @xyflow/react.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0.
- **Databases**: PostgreSQL (with pgvector), Neo4j Graph DB (Community Edition), Redis.
- **Machine Learning**: XGBoost, Scikit-Learn, Pandas, NumPy, SHAP.
- **AI & RAG**: Tool-Calling Investigation Agent, Vector RAG Retrieval Engine.
- **Containerization**: Docker, Docker Compose.

---

## 💻 Quick Start & Running Locally

### 1. Environment Setup

Clone the repository and create your configuration file:

```bash
cp .env.example .env
```

### 2. Python Virtual Environment & Dependencies

```bash
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Install backend requirements:
pip install -r backend/requirements.txt
```

### 3. Generate Synthetic Dataset & Train Models

```bash
$env:PYTHONPATH="."
python ml/training/train_models.py
```

### 4. Run Demonstration Scenarios (Scenarios A through E)

```bash
$env:PYTHONPATH="."
python scripts/run_demo_scenarios.py
```

### 5. Run Unit & Integration Tests

```bash
$env:PYTHONPATH="."
python -m unittest discover -s backend/tests -p "test_*.py"
```

### 6. Launch Backend Server

```bash
$env:PYTHONPATH="."
uvicorn backend.app.main:app --reload --port 8000
```

Open API docs at [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs).

### 7. Launch Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open Dashboard in browser at [http://localhost:3000](http://localhost:3000).

---

## 🐳 Docker Deployment

To launch all infrastructure services (PostgreSQL + pgvector, Neo4j, Redis, Backend, Frontend) via Docker Compose:

```bash
docker-compose up --build -d
```

---

## 🎭 Competition Demo Scenarios

Run `python scripts/run_demo_scenarios.py` to evaluate the 5 pre-configured competition scenarios:

1. **Scenario A — Normal Transaction**: Low risk baseline purchase.
2. **Scenario B — Behavioral Anomaly**: High deviation in amount & new device.
3. **Scenario C — Account Takeover (ATO)**: New device + proxy IP location + rapid WIRE transfer.
4. **Scenario D — Fraud Ring**: Multi-account cluster sharing device node `DEV_RING_999`.
5. **Scenario E — False Positive**: Legitimate high-amount purchase verified clean by analyst.

---

## ⚖️ Responsible AI

FraudShield 2.0 operates under the principle that **Risk ≠ Guilt**. High-risk transactions trigger structured evidence packages for human analyst review. No criminal behavior or autonomous account freezes occur without human verification.

---

## 📄 Documentation

Detailed architecture specifications are located in `docs/`:

- [`docs/implementation-plan.md`](docs/implementation-plan.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/responsible-ai.md`](docs/responsible-ai.md)

---

## 📜 License

[MIT License](LICENSE)
