"""SQLAlchemy models for persistent transactions, review cases, and audit events."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def gen_uuid() -> str:
    return str(uuid.uuid4())

class TransactionRecord(Base):
    __tablename__ = 'transactions'

    id = Column(String(36), primary_key=True, default=gen_uuid)
    client_transaction_id = Column(String(100), nullable=False, index=True)
    service_actor = Column(String(100), nullable=False, index=True)
    idempotency_key = Column(String(255), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False) # SHA-256 canonical hex
    features = Column(JSON, nullable=False)
    model_score = Column(Float, nullable=False)
    model_factors = Column(JSON, nullable=False)
    policy_reasons = Column(JSON, nullable=False)
    recommended_action = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, index=True)
    model_version = Column(String(64), nullable=False)
    policy_version = Column(String(64), nullable=False)
    schema_version = Column(String(64), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint('service_actor', 'idempotency_key', name='uq_service_actor_idempotency_key'),
        Index('ix_transactions_created_at', 'created_at'),
    )

    review_case = relationship('ReviewCaseRecord', back_populates='transaction', uselist=False, cascade='all, delete-orphan')
    audit_events = relationship('AuditEventRecord', back_populates='transaction', cascade='all, delete-orphan', order_by='AuditEventRecord.created_at')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'client_transaction_id': self.client_transaction_id,
            'service_actor': self.service_actor,
            'idempotency_key': self.idempotency_key,
            'request_hash': self.request_hash,
            'model_score': self.model_score,
            'model_factors': self.model_factors,
            'policy_reasons': self.policy_reasons,
            'recommended_action': self.recommended_action,
            'status': self.status,
            'model_version': self.model_version,
            'policy_version': self.policy_version,
            'schema_version': self.schema_version,
            'version': self.version,
            'case_id': self.review_case.id if self.review_case else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class ReviewCaseRecord(Base):
    __tablename__ = 'review_cases'

    id = Column(String(36), primary_key=True, default=gen_uuid)
    transaction_id = Column(String(36), ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    status = Column(String(32), nullable=False, default='open', index=True) # 'open', 'resolved'
    resolution = Column(String(32), nullable=True) # 'released', 'rejected'
    resolution_reason = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    transaction = relationship('TransactionRecord', back_populates='review_case')
    actions = relationship('AnalystActionRecord', back_populates='review_case', cascade='all, delete-orphan', order_by='AnalystActionRecord.created_at')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'resolution': self.resolution,
            'resolution_reason': self.resolution_reason,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'transaction': self.transaction.to_dict() if self.transaction else None,
        }

class AnalystActionRecord(Base):
    __tablename__ = 'analyst_actions'

    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_id = Column(String(36), ForeignKey('review_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(32), nullable=False) # 'release', 'reject'
    reason = Column(Text, nullable=False)
    previous_status = Column(String(32), nullable=False)
    resulting_status = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    review_case = relationship('ReviewCaseRecord', back_populates='actions')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'case_id': self.case_id,
            'transaction_id': self.transaction_id,
            'actor': self.actor,
            'action': self.action,
            'reason': self.reason,
            'previous_status': self.previous_status,
            'resulting_status': self.resulting_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class AuditEventRecord(Base):
    __tablename__ = 'audit_events'

    id = Column(String(36), primary_key=True, default=gen_uuid)
    transaction_id = Column(String(36), ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey('review_cases.id', ondelete='SET NULL'), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    actor_role = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)
    reason = Column(Text, nullable=True)
    previous_status = Column(String(32), nullable=True)
    resulting_status = Column(String(32), nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    transaction = relationship('TransactionRecord', back_populates='audit_events')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'case_id': self.case_id,
            'event_type': self.event_type,
            'actor': self.actor,
            'actor_role': self.actor_role,
            'action': self.action,
            'reason': self.reason,
            'previous_status': self.previous_status,
            'resulting_status': self.resulting_status,
            'payload': self.payload,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
