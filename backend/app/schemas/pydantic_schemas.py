from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


# Transaction Schemas
class TransactionCreate(BaseModel):
    transaction_id: Optional[str] = None
    user_id: str
    account_id: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    transaction_type: str = "CARD" # CARD, ACH, WIRE, P2P, ATM
    merchant_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address_hash: Optional[str] = None
    location: Optional[str] = None
    timestamp: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    transaction_id: str
    user_id: str
    account_id: str
    amount: float
    currency: str
    transaction_type: str
    merchant_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address_hash: Optional[str] = None
    location: Optional[str] = None
    timestamp: datetime
    status: str
    ml_fraud_probability: float = 0.0
    anomaly_score: float = 0.0
    behavior_score: float = 0.0
    rule_score: float = 0.0
    graph_score: float = 0.0
    fused_risk_score: float = 0.0
    risk_level: str = "LOW"
    shap_explanation: Optional[Dict[str, Any]] = None
    rule_matches: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


# Analysis Schema
class FraudAnalysisRequest(BaseModel):
    transaction: TransactionCreate
    user_history: Optional[List[Dict[str, Any]]] = []


# Case Schemas
class CaseCreate(BaseModel):
    alert_id: Optional[str] = None
    title: str
    priority: str = "HIGH"
    summary: Optional[str] = None


class CaseUpdate(BaseModel):
    status: Optional[str] = None # NEW, UNDER_INVESTIGATION, CONFIRMED_FRAUD, FALSE_POSITIVE, INCONCLUSIVE, CLOSED
    assigned_analyst_id: Optional[str] = None
    priority: Optional[str] = None
    summary: Optional[str] = None


class AnalystFeedbackCreate(BaseModel):
    case_id: str
    transaction_id: str
    decision: str # CONFIRMED_FRAUD, FALSE_POSITIVE, INCONCLUSIVE
    justification_reason: Optional[str] = None


# Dashboard Stats
class DashboardStatsResponse(BaseModel):
    transactions_analyzed: int
    high_risk_transactions: int
    open_cases: int
    potential_fraud_rings: int
    confirmed_fraud: int
    false_positive_rate: float
    avg_detection_latency_ms: float
    risk_level_distribution: Dict[str, int]
    daily_trend: List[Dict[str, Any]]
