"""
Database connection manager.

Translated from COBOL program: src/programs/common/DB2CONN.cbl

The original COBOL program:
  - Manages DB2 connections via EXEC SQL CONNECT/DISCONNECT
  - Supports CONN, DISC, STAT functions (via LS-FUNCTION)
  - Retries connections up to 3 times with delay
  - Handles specific SQLCODE errors (-30081 max connections, -99999 network)

Python equivalent uses SQLAlchemy's connection pool which handles pooling,
retries, and connection lifecycle natively.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger("portfolio.db.connection")

# Module-level engine and session factory, initialized lazily
_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None  # type: ignore[type-arg]


class DatabaseConnection:
    """SQLAlchemy-based database connection manager.

    Translated from COBOL program DB2CONN.cbl.

    The COBOL program flow:
      0000-MAIN dispatches to:
        1000-CONNECT   (FUNC-CONN) -> retry loop with EXEC SQL CONNECT
        2000-DISCONNECT (FUNC-DISC) -> COMMIT + CONNECT RESET
        3000-CHECK-STATUS (FUNC-STAT) -> SELECT CURRENT SERVER

    SQLAlchemy pool settings map to the COBOL connection pool:
      - pool_size=20 (COBOL supported up to 100 connections)
      - max_overflow=80 (allows burst to 100 total, matching COBOL capacity)
      - pool_pre_ping=True (replaces 3000-CHECK-STATUS health check)
      - pool_recycle=3600 (1 hour, prevents stale connections)
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        self._database_url = database_url or settings.database_url
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None  # type: ignore[type-arg]

    def connect(self) -> Engine:
        """Establish database connection (mirrors 1000-CONNECT).

        Returns:
            SQLAlchemy Engine with connection pool.
        """
        if self._engine is not None:
            return self._engine

        logger.info("Connecting to database...")

        connect_args = {}
        if self._database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self._engine = create_engine(
            self._database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            pool_recycle=settings.db_pool_recycle,
            echo=settings.db_echo,
            connect_args=connect_args,
        )

        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

        logger.info("Database connection established.")
        return self._engine

    def disconnect(self) -> None:
        """Disconnect from database (mirrors 2000-DISCONNECT).

        Disposes of the connection pool.
        """
        if self._engine is not None:
            logger.info("Disconnecting from database...")
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database disconnected.")

    def check_status(self) -> bool:
        """Check database connection status (mirrors 3000-CHECK-STATUS).

        Returns:
            True if connection is active.
        """
        if self._engine is None:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning("Database connection check failed: %s", exc)
            return False

    def get_session(self) -> Session:
        """Get a new database session."""
        if self._session_factory is None:
            self.connect()
        assert self._session_factory is not None
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations.

        Automatically commits on success or rolls back on error.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def _get_global_engine() -> Engine:
    """Get or create the global engine singleton."""
    global _engine, _SessionFactory
    if _engine is None:
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        _engine = create_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            pool_recycle=settings.db_pool_recycle,
            echo=settings.db_echo,
            connect_args=connect_args,
        )
        _SessionFactory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )
    return _engine


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_session)):
            ...
    """
    _get_global_engine()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()
