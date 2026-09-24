# FraudShield 2.0 — High-Level System Architecture

## Architecture Overview

FraudShield 2.0 is built as an evidence-driven temporal graph intelligence and AI investigation platform for financial fraud detection. Rather than relying on static isolated predictions, FraudShield correlates transaction anomalies, behavioral profiles, multi-hop entity graphs, sequence risk timelines, and RAG policy documents into unified evidence packages for human analyst triage.

```text
                               ┌───────────────────────┐
                               │       FRONTEND        │
                               │ Next.js 14 Dashboard  │
                               │ Tailwind + Lucide UI  │
                               │ Recharts + Graph Canvas
                               └───────────┬───────────┘
                                           │ (REST API / JSON)
                                           ▼
                               ┌───────────────────────┐
                               │       FASTAPI         │
                               │      API Gateway      │
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
                                 └───────────────────┘
```

## Subsystem Details

### 1. Ingestion & Validation Gateway
- FastAPI REST gateway accepting transactions via `POST /api/v1/transactions` or stream simulation.
- Schema validation via Pydantic v2.

### 2. Behavioral Profile Engine
- Maintains stateful user profiles (mean transaction amount, standard deviation, usual devices, usual IP hashes, usual beneficiaries, transaction velocity over 1h and 24h).
- Computes normalized deviation metrics ($Z$-scores, ratio multipliers).

### 3. ML Supervised & Anomaly Engine
- Supervised XGBoost classifier predicting fraud probability ($P(Fraud)$).
- Unsupervised Isolation Forest model detecting statistical outlier patterns.
- SHAP TreeExplainer computing exact mathematical feature attributions.

### 4. Entity Graph & Fraud Ring Detection
- Neo4j database storing `Customer`, `Account`, `Device`, `IP`, `Beneficiary`, `Merchant`, and `Transaction` nodes.
- Graph heuristics for multi-account infrastructure sharing (detecting shared devices and IP subnet clusters).

### 5. Calibrated Risk Fusion
- Combines Supervised ML, Anomaly, Behavior, Rule, Graph, and Temporal signals using a calibrated weighted linear combination with non-linear multi-signal co-occurrence amplification.

### 6. RAG Knowledge & AI Investigation Agent
- Vector retrieval over financial compliance policies, fraud typologies, and historical precedent cases.
- Tool-calling AI Agent synthesizing auditable investigation summaries.

### 7. Analyst Human-in-the-Loop & Governance
- Analyst decision recording (`CONFIRMED_FRAUD`, `FALSE_POSITIVE`, `INCONCLUSIVE`).
- Model versioning registry & performance monitoring (Precision, Recall, F1, PR-AUC, Latency).
