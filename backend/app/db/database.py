"""
Database configuration for the Investment Portfolio Management System.

Provides SQLAlchemy engine creation with connection pooling, session factory,
and Base model class. Supports PostgreSQL (production) and SQLite (development).

Configuration is driven by the DATABASE_URL environment variable:
    - PostgreSQL: postgresql+psycopg://user:pass@host:5432/dbname
    - SQLite (dev fallback): sqlite:///./portfolio.db

Migrated from legacy DB2 COBOL system (COG-GTM/COBOL-Legacy-Benchmark-Suite).
The original system used DB2 with application plan bindings (PORTPLAN.sql)
and cursor-based connection management (DB2ONLN.cbl / CURSMGR.cbl).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


def get_database_url() -> str:
    """Resolve the database URL from environment variables.

    Returns the value of DATABASE_URL if set, otherwise falls back to a local
    SQLite database for development convenience.
    """
    return os.environ.get(
        "DATABASE_URL",
        "sqlite:///./portfolio.db",
    )


def _build_engine(url: str):
    """Create a SQLAlchemy engine with appropriate settings for the dialect."""
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
        )
    # PostgreSQL (production) — use connection pooling
    return create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )


Base = declarative_base()

engine = _build_engine(get_database_url())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a database session and ensures cleanup."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
