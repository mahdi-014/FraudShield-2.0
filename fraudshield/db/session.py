"""Database session and engine management."""
from contextlib import contextmanager
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from ..config import get_database_url

_ENGINES = {}
_SESSION_MAKERS = {}

def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://") or url.startswith("postgresql://"):
        try:
            import psycopg2
        except (ImportError, Exception):
            if url.startswith("postgresql+psycopg2://"):
                return url.replace("postgresql+psycopg2://", "postgresql+pg8000://", 1)
            elif url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+pg8000://", 1)
    return url

def get_engine(database_url: Optional[str] = None):
    raw_url = database_url or get_database_url()
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not configured")
    url = normalize_database_url(raw_url)
    if url not in _ENGINES:
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
            connect_args=connect_args
        )
        _ENGINES[url] = engine
        _SESSION_MAKERS[url] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _ENGINES[url]

def get_session_maker(database_url: Optional[str] = None):
    raw_url = database_url or get_database_url()
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not configured")
    url = normalize_database_url(raw_url)
    get_engine(url)
    return _SESSION_MAKERS[url]

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
    except (OperationalError, Exception):
        return False
