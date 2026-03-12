"""
Database package for the Investment Portfolio Management System.

Provides SQLAlchemy ORM models migrated from the legacy DB2/VSAM COBOL system
(COG-GTM/COBOL-Legacy-Benchmark-Suite) targeting PostgreSQL.
"""

from .database import Base, engine, SessionLocal, get_db, get_database_url
