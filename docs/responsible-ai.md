# Responsible AI Principles & Human-in-the-Loop Governance

## Core Principle: Risk ≠ Guilt

FraudShield 2.0 adheres strictly to the fundamental rule: **Risk Score ≠ Guilt**. 

A high composite risk score or ML probability triggers an investigative review process; it does NOT autonomously establish criminal intent or inflict automatic financial penalties without human oversight.

---

## 1. Human-in-the-Loop (HITL) Safeguards
- **No Autonomous Prosecution**: The AI system provides structured intelligence, SHAP feature attributions, and policy citations to human analysts. Final classification (`CONFIRMED_FRAUD`, `FALSE_POSITIVE`, `INCONCLUSIVE`) requires human verification.
- **Auditable Decision Trail**: All human decisions are logged in `analyst_feedback` tables alongside justification notes and timestamps.

---

## 2. Evidence Grounding & Hallucination Defense
- **Explicit Tool Calling**: The AI Investigation Agent queries validated database endpoints rather than guessing financial attributes.
- **Explicit Missing Evidence Reporting**: If IP geolocation, device history, or historical baseline is insufficient, the system explicitly reports `"Missing Evidence"` rather than hallucinating facts.

---

## 3. Privacy & Data Minimization
- **PII Hashing**: Real IP addresses, bank account numbers, and device serial numbers are hashed using SHA-256 before storage.
- **Synthetic Datasets**: All demonstration data is strictly synthetic; no real customer financial records are used.

---

## 4. Bias & Model Governance
- **Fairness Monitoring**: Model performance metrics (Precision, Recall, FPR) are monitored across transaction types and geographic buckets.
- **Model Registry**: Every model candidate is versioned and validated offline before promotion to active status.
