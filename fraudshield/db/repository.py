"""Repository layer for atomic database operations, concurrency, and audit logs."""
import hashlib
import json
from typing import Optional, Tuple, List
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from .models import (
    TransactionRecord, ReviewCaseRecord, AnalystActionRecord, AuditEventRecord, utc_now
)
from ..state_machine import (
    map_initial_status, requires_review_case, validate_analyst_transition,
    TERMINAL_STATES, REVIEWABLE_STATES
)
from ..config import ROLE_SERVICE, ROLE_ANALYST

class IdempotencyConflictError(Exception):
    """Raised when an idempotency key is reused with differing request payloads."""
    pass

class VersionConflictError(Exception):
    """Raised when an optimistic concurrency check fails due to mismatched versions."""
    pass

class InvalidStateTransitionError(Exception):
    """Raised when an action is attempted on an invalid or terminal state."""
    pass

def compute_canonical_hash(client_transaction_id: str, features: dict) -> str:
    """Compute deterministic SHA-256 hash of canonicalized transaction submission."""
    canonical = {
        "client_transaction_id": str(client_transaction_id).strip(),
        "features": features,
    }
    dumped = json.dumps(canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(dumped.encode('utf-8')).hexdigest()

def submit_transaction(
    session: Session,
    service_actor: str,
    idempotency_key: str,
    client_transaction_id: str,
    features: dict,
    scorer
) -> Tuple[TransactionRecord, bool]:
    """Submit a transaction with atomic persistence, idempotency, and audit logging.

    Returns:
        Tuple[TransactionRecord, bool]: The transaction record and a boolean indicating
        whether a new record was created (True) or an existing record returned (False).
    """
    canonical_hash = compute_canonical_hash(client_transaction_id, features)

    # Serialize this actor/key across processes BEFORE checking or scoring.
    # Transaction-scoped PostgreSQL locks release on commit/rollback/session close.
    # Hash collisions only serialize unrelated requests; they cannot mix records.
    lock_bytes = hashlib.sha256(json.dumps([service_actor, idempotency_key]).encode()).digest()[:8]
    lock_key = int.from_bytes(lock_bytes, 'big', signed=True)
    session.execute(text('SELECT pg_advisory_xact_lock(:lock_key)'), {'lock_key': lock_key})

    # Check for existing idempotency key for this service actor
    existing = session.query(TransactionRecord).filter(
        TransactionRecord.service_actor == service_actor,
        TransactionRecord.idempotency_key == idempotency_key
    ).first()

    if existing:
        if existing.request_hash == canonical_hash:
            return existing, False
        raise IdempotencyConflictError(
            f"Idempotency-Key '{idempotency_key}' was previously used with a different request payload."
        )

    # Perform ML scoring and feature extraction
    assessment = scorer.score(client_transaction_id, features)
    status = map_initial_status(assessment['action'])

    tx = TransactionRecord(
        client_transaction_id=str(client_transaction_id).strip(),
        service_actor=service_actor,
        idempotency_key=idempotency_key,
        request_hash=canonical_hash,
        features=features,
        model_score=assessment['model_score'],
        model_factors=assessment['model_factors'],
        policy_reasons=assessment['policy_reasons'],
        recommended_action=assessment['action'],
        status=status,
        model_version=assessment['model_version'],
        policy_version=assessment['policy_version'],
        schema_version=assessment['schema_version'],
        version=1,
    )
    try:
        session.add(tx)
        session.flush() # Populate tx.id

        case_id = None
        if requires_review_case(status):
            case = ReviewCaseRecord(
                transaction_id=tx.id,
                status='open'
            )
            session.add(case)
            session.flush()
            case_id = case.id

        audit = AuditEventRecord(
            transaction_id=tx.id,
            case_id=case_id,
            event_type='TRANSACTION_SUBMITTED',
            actor=service_actor,
            actor_role=ROLE_SERVICE,
            action='submit_transaction',
            reason=f"Initial risk assessment action: {assessment['action']}",
            previous_status=None,
            resulting_status=status,
            payload={
                'model_score': tx.model_score,
                'recommended_action': tx.recommended_action,
                'policy_reasons': tx.policy_reasons,
                'explanation': assessment.get('explanation'),
                'score_interpretation': assessment.get('score_interpretation'),
            }
        )
        session.add(audit)
        session.commit()
    except IntegrityError:
        session.rollback()
        # Handle concurrent submission race condition
        existing = session.query(TransactionRecord).filter(
            TransactionRecord.service_actor == service_actor,
            TransactionRecord.idempotency_key == idempotency_key
        ).first()
        if existing:
            if existing.request_hash == canonical_hash:
                return existing, False
            raise IdempotencyConflictError(
                f"Idempotency-Key '{idempotency_key}' was previously used with a different request payload."
            )
        raise
    except Exception:
        session.rollback()
        raise

    session.refresh(tx)
    return tx, True

def get_transaction_by_id(session: Session, transaction_id: str) -> Optional[TransactionRecord]:
    return session.query(TransactionRecord).filter(TransactionRecord.id == transaction_id).first()

def list_cases(
    session: Session,
    status: Optional[str] = None,
    resolution: Optional[str] = None,
    recommended_action: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[ReviewCaseRecord], int]:
    query = session.query(ReviewCaseRecord)
    if status:
        query = query.filter(ReviewCaseRecord.status == status)
    if resolution:
        query = query.filter(ReviewCaseRecord.resolution == resolution)
    if recommended_action:
        query = query.join(TransactionRecord).filter(TransactionRecord.recommended_action == recommended_action)
    total = query.count()
    items = query.options(joinedload(ReviewCaseRecord.transaction).joinedload(TransactionRecord.review_case)).order_by(
        ReviewCaseRecord.created_at.desc(), ReviewCaseRecord.id.desc()
    ).offset(offset).limit(limit).all()
    return items, total

def get_case_by_id(session: Session, case_id: str) -> Optional[ReviewCaseRecord]:
    return session.query(ReviewCaseRecord).filter(ReviewCaseRecord.id == case_id).first()

def execute_analyst_action(
    session: Session,
    case_id: str,
    analyst_actor: str,
    action: str,
    reason: str,
    expected_version: int
) -> Tuple[ReviewCaseRecord, TransactionRecord]:
    """Execute an analyst decision atomically with concurrency locking and audit persistence."""
    case = session.query(ReviewCaseRecord).filter(ReviewCaseRecord.id == case_id).first()
    if not case:
        raise ValueError(f"Review case '{case_id}' not found.")

    # Apply row-level locking on transaction
    tx_query = session.query(TransactionRecord).filter(TransactionRecord.id == case.transaction_id)
    tx = tx_query.with_for_update().populate_existing().first()

    if not tx:
        raise ValueError(f"Transaction '{case.transaction_id}' linked to case '{case_id}' not found.")

    # Concurrency and version check
    if tx.version != expected_version:
        raise VersionConflictError(
            f"Version conflict: expected version {expected_version}, but current version is {tx.version}."
        )

    # State machine transition check
    try:
        resulting_status = validate_analyst_transition(tx.status, action)
    except ValueError as err:
        raise InvalidStateTransitionError(str(err))

    prev_status = tx.status
    now = utc_now()

    # Update transaction
    tx.status = resulting_status
    tx.version = tx.version + 1
    tx.updated_at = now

    # Update review case
    case.status = 'resolved'
    case.resolution = 'released' if action == 'release' else 'rejected'
    case.resolution_reason = reason
    case.resolved_by = analyst_actor
    case.resolved_at = now
    case.updated_at = now

    # Record analyst action
    analyst_action_rec = AnalystActionRecord(
        case_id=case.id,
        transaction_id=tx.id,
        actor=analyst_actor,
        action=action,
        reason=reason,
        previous_status=prev_status,
        resulting_status=resulting_status,
        created_at=now
    )
    session.add(analyst_action_rec)

    # Append audit event
    audit_rec = AuditEventRecord(
        transaction_id=tx.id,
        case_id=case.id,
        event_type='ANALYST_ACTION',
        actor=analyst_actor,
        actor_role=ROLE_ANALYST,
        action=f"analyst_{action}",
        reason=reason,
        previous_status=prev_status,
        resulting_status=resulting_status,
        payload={
            'expected_version': expected_version,
            'resulting_version': tx.version
        },
        created_at=now
    )
    session.add(audit_rec)

    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(case)
    session.refresh(tx)
    return case, tx

def get_transaction_audit(session: Session, transaction_id: str) -> List[AuditEventRecord]:
    return session.query(AuditEventRecord).filter(
        AuditEventRecord.transaction_id == transaction_id
    ).order_by(AuditEventRecord.created_at.asc(), AuditEventRecord.id.asc()).all()
