"""
Application configuration management.

Consolidates configuration from multiple COBOL sources:
  - Database connection string (PostgreSQL) — from DB2CONN.cbl connection parameters
  - Connection pool settings — from DB2CONN.cbl (up to 100 connections)
  - Logging configuration — from ERRPROC.cbl logging setup
  - Batch processing constants — from BCHCON.cpy
  - Return code definitions — from COMMON.cpy and RTNCODE.cpy

Uses environment variables with sensible defaults for local development.
"""

import logging
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables.

    Attributes map to COBOL configuration sources:
      - database_url: DB2 connection string -> PostgreSQL connection string
      - db_pool_size: COBOL supported 100 connections; default pool = 20
      - db_max_overflow: Allows burst to 100 total (20 + 80)
      - db_pool_recycle: Connection recycle interval (seconds)
      - db_echo: SQL echo for debugging
      - log_level: Logging level
      - batch_max_prereq: From BCHCON.cpy BCT-MAX-PREREQ (10)
      - batch_max_restarts: From BCHCON.cpy BCT-MAX-RESTARTS (3)
      - batch_wait_interval: From BCHCON.cpy BCT-WAIT-INTERVAL (300s)
      - batch_max_wait_time: From BCHCON.cpy BCT-MAX-WAIT-TIME (3600s)
      - batch_commit_freq: From CKPRST.cpy CK-COMMIT-FREQ (1000)
      - batch_max_errors: From CKPRST.cpy CK-MAX-ERRORS (100)
    """

    def __init__(self) -> None:
        # ----------------------------------------------------------------
        # Database settings (from DB2CONN.cbl)
        # ----------------------------------------------------------------
        self.database_url: str = os.environ.get(
            "DATABASE_URL",
            "sqlite:///./portfolio.db",
        )
        self.db_pool_size: int = int(os.environ.get("DB_POOL_SIZE", "20"))
        self.db_max_overflow: int = int(os.environ.get("DB_MAX_OVERFLOW", "80"))
        self.db_pool_recycle: int = int(os.environ.get("DB_POOL_RECYCLE", "3600"))
        self.db_echo: bool = os.environ.get("DB_ECHO", "false").lower() == "true"

        # ----------------------------------------------------------------
        # Logging settings (from ERRPROC.cbl)
        # ----------------------------------------------------------------
        self.log_level: str = os.environ.get("LOG_LEVEL", "INFO")

        # ----------------------------------------------------------------
        # Batch processing constants (from BCHCON.cpy)
        # ----------------------------------------------------------------
        self.batch_max_prereq: int = int(os.environ.get("BATCH_MAX_PREREQ", "10"))
        self.batch_max_restarts: int = int(os.environ.get("BATCH_MAX_RESTARTS", "3"))
        self.batch_wait_interval: int = int(os.environ.get("BATCH_WAIT_INTERVAL", "300"))
        self.batch_max_wait_time: int = int(os.environ.get("BATCH_MAX_WAIT_TIME", "3600"))
        self.batch_commit_freq: int = int(os.environ.get("BATCH_COMMIT_FREQ", "1000"))
        self.batch_max_errors: int = int(os.environ.get("BATCH_MAX_ERRORS", "100"))

        # ----------------------------------------------------------------
        # Return code definitions (from COMMON.cpy / RTNCODE.cpy)
        # ----------------------------------------------------------------
        self.rc_success: int = 0
        self.rc_warning: int = 4
        self.rc_error: int = 8
        self.rc_severe: int = 12
        self.rc_critical: int = 16

    def configure_logging(self) -> None:
        """Configure Python logging based on settings.

        Replaces the COBOL sequential log file approach from ERRPROC.cbl
        with structured Python logging.
        """
        log_format = (
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Set specific loggers
        logging.getLogger("portfolio").setLevel(
            getattr(logging, self.log_level.upper(), logging.INFO)
        )
        logging.getLogger("sqlalchemy.engine").setLevel(
            logging.DEBUG if self.db_echo else logging.WARNING
        )


# Module-level singleton
settings = Settings()
