

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Integer, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="ANALYST") # ADMIN, ANALYST, INVESTIGATOR, AUDITOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    accounts = relationship("Account", back_populates="user")
    cases = relationship("Case", back_populates="assigned_analyst")
    audit_logs = relationship("AuditLog", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    account_number = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    account_type = Column(String(50), default="SAVINGS")
    balance = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="ACTIVE")
    risk_profile_level = Column(String(50), default="LOW")
    avg_transaction_amount = Column(Float, default=0.0)
    std_transaction_amount = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_fingerprint = Column(String(255), unique=True, nullable=False, index=True)
    device_type = Column(String(50), default="MOBILE") # MOBILE, DESKTOP, TABLET
    operating_system = Column(String(100), nullable=True)
    ip_hash = Column(String(255), nullable=True, index=True)
    is_suspicious = Column(Boolean, default=False)
    first_seen = Column(DateTime(timezone=True), default=utc_now)
    last_seen = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    transactions = relationship("Transaction", back_populates="device")


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    merchant_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    transactions = relationship("Transaction", back_populates="merchant")


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    account_number_hash = Column(String(255), nullable=False, index=True)
    bank_code = Column(String(50), nullable=True)
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    transactions = relationship("Transaction", back_populates="beneficiary")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True)
    beneficiary_id = Column(String(36), ForeignKey("beneficiaries.id"), nullable=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    transaction_type = Column(String(50), nullable=False) # WIRE, ACH, CARD, ATM, P2P
    location = Column(String(100), nullable=True)
    ip_address_hash = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    status = Column(String(50), default="COMPLETED") # PENDING, COMPLETED, BLOCKED, REJECTED

    # ML & Risk Fusion Output Scores
    ml_fraud_probability = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    behavior_score = Column(Float, default=0.0)
    rule_score = Column(Float, default=0.0)
    graph_score = Column(Float, default=0.0)
    fused_risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    shap_explanation = Column(JSON, nullable=True)
    rule_matches = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)

    account = relationship("Account", back_populates="transactions")
    device = relationship("Device", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    beneficiary = relationship("Beneficiary", back_populates="transactions")
    alerts = relationship("Alert", back_populates="transaction")
    risk_events = relationship("RiskEvent", back_populates="transaction")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(100), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), default=utc_now)
    event_name = Column(String(100), nullable=False)
    risk_delta = Column(Float, default=0.0)
    resulting_risk_score = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    transaction = relationship("Transaction", back_populates="risk_events")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    alert_id = Column(String(100), unique=True, nullable=False, index=True)
    transaction_id = Column(String(100), ForeignKey("transactions.transaction_id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    status = Column(String(50), default="NEW") # NEW, IN_REVIEW, CASE_CREATED, DISMISSED
    trigger_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    transaction = relationship("Transaction", back_populates="alerts")
    cases = relationship("Case", back_populates="alert")


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(100), unique=True, nullable=False, index=True)
    alert_id = Column(String(100), ForeignKey("alerts.alert_id"), nullable=True)
    assigned_analyst_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="NEW") # NEW, UNDER_INVESTIGATION, CONFIRMED_FRAUD, FALSE_POSITIVE, INCONCLUSIVE, CLOSED
    priority = Column(String(20), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    summary = Column(Text, nullable=True)
    ai_investigation_report = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    assigned_analyst = relationship("User", back_populates="cases")
    alert = relationship("Alert", back_populates="cases")
    evidence = relationship("CaseEvidence", back_populates="case")
    feedback = relationship("AnalystFeedback", back_populates="case")


class CaseEvidence(Base):
    __tablename__ = "case_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(100), ForeignKey("cases.case_id"), nullable=False)
    evidence_type = Column(String(50), nullable=False) # BEHAVIOR, GRAPH, SHAP, POLICY, HISTORICAL_CASE
    description = Column(Text, nullable=False)
    evidence_data = Column(JSON, nullable=True)
    source_citation = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    case = relationship("Case", back_populates="evidence")


class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(100), ForeignKey("cases.case_id"), nullable=False)
    transaction_id = Column(String(100), nullable=False)
    analyst_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    decision = Column(String(50), nullable=False) # CONFIRMED_FRAUD, FALSE_POSITIVE, INCONCLUSIVE
    justification_reason = Column(Text, nullable=True)
    is_validated_for_retraining = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    case = relationship("Case", back_populates="feedback")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, unique=True)
    algorithm = Column(String(100), nullable=False) # XGBoost, Random Forest, Isolation Forest
    training_dataset = Column(String(255), nullable=False)
    training_date = Column(DateTime(timezone=True), default=utc_now)
    features_used = Column(JSON, nullable=False)
    threshold = Column(Float, default=0.5)
    status = Column(String(50), default="ACTIVE") # EXPERIMENTAL, VALIDATED, ACTIVE, RETIRED
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    metrics = relationship("ModelMetric", back_populates="model_version")


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False)
    metric_name = Column(String(50), nullable=False) # PRECISION, RECALL, F1, PR_AUC, FPR, FNR, LATENCY_MS
    metric_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now)

    model_version = relationship("ModelVersion", back_populates="metrics")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False) # LOGIN, TRANSACTION_VIEW, CASE_CREATED, ANALYST_DECISION, MODEL_CHANGED
    resource = Column(String(255), nullable=False)
    ip_address = Column(String(100), nullable=True)
    log_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

    user = relationship("User", back_populates="audit_logs")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False) # POLICY, FRAUD_TYPOLOGY, HISTORICAL_CASE
    source = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True) # Vector stored as JSON array for cross-DB compatibility
    created_at = Column(DateTime(timezone=True), default=utc_now)
