"""FraudShield API with scoring, PostgreSQL persistence, state machine, and RBAC."""
import math
import os
import logging
import uuid
from typing import Literal
from fastapi.responses import JSONResponse
from pydantic import model_validator
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .features import RAW_FEATURES, RAW_NUMERIC, CATEGORICAL
from .scoring import Scorer
from .config import (
    AuthConfig, Actor, ROLE_SERVICE, ROLE_ANALYST, ROLE_LEGACY,
    get_database_url, get_artifact_dir
)
from .db.session import (
    get_db, is_database_configured, check_database_connection
)
from .db.models import TransactionRecord
from .db.repository import (
    submit_transaction, get_transaction_by_id, list_cases, get_case_by_id,
    execute_analyst_action, get_transaction_audit,
    IdempotencyConflictError, VersionConflictError, InvalidStateTransitionError
)

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

def validate_features_dict(value: dict) -> dict:
    unknown = set(value) - set(RAW_FEATURES)
    if unknown:
        raise ValueError('Unknown or forbidden features: ' + ', '.join(sorted(unknown)))
    for required in ['TransactionAmt', 'TransactionDT', 'ProductCD']:
        if value.get(required) is None:
            raise ValueError('Required replay feature missing: ' + required)
    for name in RAW_NUMERIC:
        item = value.get(name)
        if item is not None and (
            isinstance(item, bool) or not isinstance(item, (int, float)) or
            not math.isfinite(item) or not 0 <= item <= 1e12
        ):
            raise ValueError(name + ' must be a finite number between 0 and 1e12, or null')
    for name in CATEGORICAL:
        item = value.get(name)
        if item is not None:
            if isinstance(item, bool) or not isinstance(item, (str, int, float)):
                raise ValueError(name + ' must be a category value or null')
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError(name + ' must be finite')
            if len(str(item)) > 256:
                raise ValueError(name + ' exceeds 256 characters')
    if value['ProductCD'] not in ['W', 'C', 'R', 'H', 'S']:
        raise ValueError('Unsupported IEEE-CIS ProductCD')
    return value

class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    transaction_id: str = Field(min_length=1, max_length=100)
    features: dict[str, object]

    @field_validator('features')
    @classmethod
    def valid_features(cls, value):
        return validate_features_dict(value)

class CreateTransactionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    client_transaction_id: Optional[str] = Field(None, min_length=1, max_length=100)
    transaction_id: Optional[str] = Field(None, min_length=1, max_length=100)
    features: dict[str, object]

    @field_validator('features')
    @classmethod
    def valid_features(cls, value):
        return validate_features_dict(value)

    @model_validator(mode='after')
    def validate_reference(self):
        if not (self.client_transaction_id or self.transaction_id):
            raise ValueError('A transaction reference is required')
        if (self.client_transaction_id and self.transaction_id and
                self.client_transaction_id != self.transaction_id):
            raise ValueError('Transaction reference aliases must agree')
        return self

    def get_client_id(self) -> str:
        tid = self.client_transaction_id or self.transaction_id
        if not tid:
            raise ValueError("Either 'client_transaction_id' or 'transaction_id' is required.")
        return tid

class AnalystActionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    action: str = Field(..., pattern="^(release|reject)$")
    reason: str = Field(..., min_length=3, max_length=1000)
    expected_version: int = Field(..., ge=1)

def create_app(artifact_dir=None, database_url=None):
    auth_config = AuthConfig()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Validate authentication configuration
        auth_config.load_credentials()
        key = os.environ.get('FRAUDSHIELD_API_KEY', '')
        if len(key) < 24:
            raise RuntimeError('Set FRAUDSHIELD_API_KEY to a secret of at least 24 characters')

        app.state.auth_config = auth_config
        app.state.api_key = key
        target_art = artifact_dir or get_artifact_dir()
        app.state.scorer = Scorer(target_art)
        app.state.database_url = database_url or get_database_url()
        yield

    app = FastAPI(
        title='FraudShield Research Scoring & Decision API',
        version='0.3.1',
        lifespan=lifespan
    )

    origins = [origin.strip() for origin in
               os.environ.get('FRAUDSHIELD_CORS_ORIGINS', '').split(',') if origin.strip()]
    if '*' in origins:
        raise ValueError('Configure explicit CORS origins; wildcard origins are not supported')
    app.add_middleware(
        CORSMiddleware, allow_origins=origins, allow_credentials=False,
        allow_methods=['GET', 'POST'],
        allow_headers=['Authorization', 'Content-Type', 'Idempotency-Key'],
    )

    def report_failure(exc: Exception, database: bool):
        request_id = uuid.uuid4().hex
        # Do not log exception text, SQL parameters, tokens or request bodies.
        logger.error('request_id=%s failure_type=%s', request_id, type(exc).__name__)
        return JSONResponse(
            status_code=503 if database else 500,
            content={'detail': 'Database service is unavailable.' if database
                     else 'Internal service error.', 'request_id': request_id},
            headers={'X-Request-ID': request_id},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request, exc):
        return report_failure(exc, database=True)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request, exc):
        return report_failure(exc, database=False)

    def get_current_actor(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> Actor:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Missing bearer credential',
                headers={'WWW-Authenticate': 'Bearer'}
            )
        actor = app.state.auth_config.authenticate(credentials.credentials)
        if actor is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid bearer credential',
                headers={'WWW-Authenticate': 'Bearer'}
            )
        return actor

    def require_role(*allowed_roles: str):
        def role_checker(actor: Actor = Depends(get_current_actor)) -> Actor:
            # Legacy scorer key is allowed for legacy endpoints
            if actor.role in allowed_roles:
                return actor
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: role '{actor.role}' cannot access this resource."
            )
        return role_checker

    def get_db_session():
        db_url = app.state.database_url
        if not db_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Database persistence is not configured.'
            )
        try:
            with get_db(db_url) as session:
                yield session
        except HTTPException:
            raise
        except SQLAlchemyError:
            raise


    # -------------------------------------------------------------
    # Existing Baseline Endpoints (Preserved)
    # -------------------------------------------------------------
    @app.get('/health/ready')
    def ready():
        db_ok = check_database_connection(app.state.database_url)
        return JSONResponse(status_code=200 if db_ok else 503, content={
            'status': 'ready' if db_ok else 'not_ready',
            'mode': 'historical_dataset_replay',
            'database': 'connected' if db_ok else ('unconfigured' if not app.state.database_url else 'disconnected')
        })

    @app.get('/health/scorer')
    def scorer_ready():
        return {'status': 'ready', 'mode': 'historical_dataset_replay'}

    @app.get('/v1/auth/me')
    def me(actor: Actor = Depends(get_current_actor)):
        return {
            'identity': actor.identity,
            'role': actor.role
        }

    @app.get('/v1/schema', dependencies=[Depends(require_role(ROLE_LEGACY, ROLE_SERVICE, ROLE_ANALYST))])
    def schema():
        return {
            'features': RAW_FEATURES,
            'required': ['TransactionAmt', 'TransactionDT', 'ProductCD'],
            'schema_version': app.state.scorer.metadata['schema_version']
        }

    @app.post('/v1/score', dependencies=[Depends(require_role(ROLE_LEGACY, ROLE_SERVICE))])
    def score(request: ScoreRequest):
        return app.state.scorer.score(request.transaction_id, request.features)

    # -------------------------------------------------------------
    # Milestone 2: Persistent Transaction Submission
    # -------------------------------------------------------------
    @app.post('/v1/transactions', status_code=status.HTTP_201_CREATED)
    def create_transaction(
        request: CreateTransactionRequest,
        idempotency_key: str = Header(..., alias='Idempotency-Key', min_length=1, max_length=255),
        actor: Actor = Depends(require_role(ROLE_SERVICE)),
        db: Session = Depends(get_db_session)
    ):
        if not idempotency_key.strip():
            raise HTTPException(status_code=422, detail='Idempotency-Key must not be blank')
        try:
            client_id = request.get_client_id()
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))

        try:
            tx, is_new = submit_transaction(
                session=db,
                service_actor=actor.identity,
                idempotency_key=idempotency_key,
                client_transaction_id=client_id,
                features=request.features,
                scorer=app.state.scorer
            )
        except IdempotencyConflictError as conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(conflict))
        except HTTPException:
            raise
        except SQLAlchemyError:
            raise

        return tx.to_dict()

    @app.get('/v1/transactions/{transaction_id}')
    def get_transaction(
        transaction_id: str,
        actor: Actor = Depends(require_role(ROLE_SERVICE, ROLE_ANALYST)),
        db: Session = Depends(get_db_session)
    ):
        tx = get_transaction_by_id(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

        # Isolation: Service callers can only view their own transactions
        if actor.role == ROLE_SERVICE and tx.service_actor != actor.identity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

        return tx.to_dict()

    # -------------------------------------------------------------
    # Milestone 2: Review Cases & Analyst Decisions
    # -------------------------------------------------------------
    @app.get('/v1/cases')
    def get_cases(
        status_filter: Optional[Literal['open', 'resolved']] = Query(None, alias='status'),
        resolution_filter: Optional[Literal['released', 'rejected']] = Query(None, alias='resolution'),
        action_filter: Optional[Literal['allow', 'warn', 'pause', 'hold']] = Query(None, alias='recommended_action'),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        actor: Actor = Depends(require_role(ROLE_ANALYST)),
        db: Session = Depends(get_db_session)
    ):
        items, total = list_cases(
            db,
            status=status_filter,
            resolution=resolution_filter,
            recommended_action=action_filter,
            limit=limit,
            offset=offset
        )
        return {
            'items': [item.to_dict() for item in items],
            'total': total,
            'limit': limit,
            'offset': offset
        }

    @app.get('/v1/cases/{case_id}')
    def get_case(
        case_id: str,
        actor: Actor = Depends(require_role(ROLE_ANALYST)),
        db: Session = Depends(get_db_session)
    ):
        case = get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Case not found')
        return case.to_dict()

    @app.post('/v1/cases/{case_id}/actions')
    def perform_case_action(
        case_id: str,
        request: AnalystActionRequest,
        actor: Actor = Depends(require_role(ROLE_ANALYST)),
        db: Session = Depends(get_db_session)
    ):
        try:
            case, tx = execute_analyst_action(
                session=db,
                case_id=case_id,
                analyst_actor=actor.identity,
                action=request.action,
                reason=request.reason,
                expected_version=request.expected_version
            )
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
        except VersionConflictError as conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(conflict))
        except InvalidStateTransitionError as inv:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(inv))

        return {
            'case': case.to_dict(),
            'transaction': tx.to_dict(),
            'message': f"Case successfully resolved with action '{request.action}'."
        }

    # -------------------------------------------------------------
    # Milestone 2: Audit History
    # -------------------------------------------------------------
    @app.get('/v1/transactions/{transaction_id}/audit')
    def get_transaction_audit_events(
        transaction_id: str,
        actor: Actor = Depends(require_role(ROLE_SERVICE, ROLE_ANALYST)),
        db: Session = Depends(get_db_session)
    ):
        tx = get_transaction_by_id(db, transaction_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

        # Service caller access control: can only view own transaction audit
        if actor.role == ROLE_SERVICE and tx.service_actor != actor.identity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Transaction not found')

        events = get_transaction_audit(db, transaction_id)
        return {
            'transaction_id': transaction_id,
            'audit_events': [e.to_dict() for e in events]
        }

    return app

app = create_app()
