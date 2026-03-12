"""
SQLAlchemy ORM model for the RTNCODES (Return Codes) table.

Migrated from DB2 DDL in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/db2/RTNCODES.sql

Original DB2 definition
-----------------------
CREATE TABLE RTNCODES (
    TIMESTAMP       TIMESTAMP NOT NULL,
    PROGRAM_ID      CHAR(8) NOT NULL,
    RETURN_CODE     INTEGER NOT NULL,
    HIGHEST_CODE    INTEGER NOT NULL,
    STATUS_CODE     CHAR(1) NOT NULL,
    MESSAGE_TEXT    VARCHAR(80),
    PRIMARY KEY (TIMESTAMP, PROGRAM_ID)
);

Indexes:
    RTNCODES_PRG_IDX ON (PROGRAM_ID, TIMESTAMP)
    RTNCODES_STS_IDX ON (STATUS_CODE, TIMESTAMP)
"""

from sqlalchemy import Column, String, Integer, DateTime, Index

from app.db.database import Base


class ReturnCode(Base):
    """Return code record — logs program execution return codes.

    Maps to the DB2 RTNCODES table (RTNCODES.sql).  Uses a composite primary
    key (record_timestamp, program_id).

    Note: The column is named ``record_timestamp`` rather than ``timestamp``
    to avoid collisions with the SQL reserved word.
    """

    __tablename__ = "return_codes"

    # --- Composite primary key -------------------------------------------
    record_timestamp = Column("timestamp", DateTime, primary_key=True, nullable=False,
                              comment="Execution timestamp (DB2 TIMESTAMP)")
    program_id = Column(String(8), primary_key=True, nullable=False,
                        comment="Program identifier (DB2 CHAR(8))")

    # --- Data columns -----------------------------------------------------
    return_code = Column(Integer, nullable=False,
                         comment="Program return code (DB2 INTEGER)")
    highest_code = Column(Integer, nullable=False,
                          comment="Highest return code in batch run (DB2 INTEGER)")
    status_code = Column(String(1), nullable=False,
                         comment="Execution status code (DB2 CHAR(1))")
    message_text = Column(String(80), nullable=True,
                          comment="Optional status/error message (DB2 VARCHAR(80))")

    __table_args__ = (
        Index("rtncodes_prg_idx", "program_id", "timestamp"),
        Index("rtncodes_sts_idx", "status_code", "timestamp"),
        {"comment": "Return codes — migrated from DB2 RTNCODES (RTNCODES.sql)"},
    )

    def __repr__(self) -> str:
        return (
            f"<ReturnCode(record_timestamp={self.record_timestamp!r}, "
            f"program_id={self.program_id!r}, "
            f"return_code={self.return_code!r})>"
        )
