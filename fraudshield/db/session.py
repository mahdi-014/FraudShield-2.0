"""Database session and engine management."""
from contextlib import contextmanager
from typing import Optional
import os
import re
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from ..config import get_database_url

_ENGINES = {}
_SESSION_MAKERS = {}

def normalize_database_url(url: str) -> str:
    # Respect the selected driver. Import/security errors must remain visible.
    # Operators can explicitly select postgresql+pg8000 for its real Python driver.
    return url

def get_engine(database_url: Optional[str] = None):
    raw_url = database_url or get_database_url()
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not configured")
    url = normalize_database_url(raw_url)
    schema = os.environ.get('FRAUDSHIELD_DB_SCHEMA', 'public')
    if not re.fullmatch(r'[a-z_][a-z0-9_]{0,62}', schema):
        raise ValueError('Invalid database schema identifier')
    cache_key = (url, schema)
    if cache_key not in _ENGINES:
        # Standard configuration for PostgreSQL with connection pooling
        connect_args = {}
        if "psycopg2" in url:
            connect_args["connect_timeout"] = 3
        elif "pg8000" in url:
            connect_args["timeout"] = 3

        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args=connect_args,
            hide_parameters=True,
        )
        @event.listens_for(engine, 'connect')
        def set_schema(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute(f'SET SESSION search_path TO "{schema}"')
                dbapi_connection.commit()
            finally:
                cursor.close()
        _ENGINES[cache_key] = engine
        _SESSION_MAKERS[cache_key] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _ENGINES[cache_key]

def get_session_maker(database_url: Optional[str] = None):
    raw_url = database_url or get_database_url()
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not configured")
    url = normalize_database_url(raw_url)
    get_engine(url)
    return _SESSION_MAKERS[(url, os.environ.get('FRAUDSHIELD_DB_SCHEMA', 'public'))]

@contextmanager
def get_db(database_url: Optional[str] = None):
    session_maker = get_session_maker(database_url)
    session: Session = session_maker()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def is_database_configured() -> bool:
    return bool(get_database_url())

def check_database_connection(database_url: Optional[str] = None) -> bool:
    url = database_url or get_database_url()
    if not url:
        return False
    try:
        engine = get_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
