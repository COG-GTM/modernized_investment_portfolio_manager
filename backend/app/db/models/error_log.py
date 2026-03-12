"""
SQLAlchemy ORM model for the ERRLOG (Error Log) table.

Migrated from DB2 DDL in:
    COG-GTM/COBOL-Legacy-Benchmark-Suite  src/database/db2/ERRLOG.sql

Original DB2 definition
-----------------------
CREATE TABLE ERRLOG (
    ERROR_TIMESTAMP   TIMESTAMP       NOT NULL,
    PROGRAM_ID        CHAR(8)         NOT NULL,
    ERROR_TYPE        CHAR(1)         NOT NULL,
    ERROR_SEVERITY    INTEGER         NOT NULL,
    ERROR_CODE        CHAR(8)         NOT NULL,
    ERROR_MESSAGE     VARCHAR(200)    NOT NULL,
    PROCESS_DATE      DATE            NOT NULL,
    PROCESS_TIME      TIME            NOT NULL,
    USER_ID           CHAR(8)         NOT NULL,
    ADDITIONAL_INFO   VARCHAR(500)
);

Composite PK: (ERROR_TIMESTAMP, PROGRAM_ID)

Index: ERRLOG_IX1 ON (PROCESS_DATE, ERROR_SEVERITY DESC)

Error types:      S=System, A=Application, D=Data
Error severities: 1=Info, 2=Warning, 3=Error, 4=Severe
"""

from sqlalchemy import Column, String, Integer, Date, Time, DateTime, Index

from app.db.database import Base


class ErrorLog(Base):
    """Error log record — one row per application error or warning.

    Maps to the DB2 ERRLOG table (ERRLOG.sql).  Uses a composite primary key
    (error_timestamp, program_id) matching the original clustered unique index.
    """

    __tablename__ = "error_log"

    # --- Composite primary key -------------------------------------------
    error_timestamp = Column(DateTime, primary_key=True, nullable=False,
                             comment="Error timestamp (DB2 TIMESTAMP)")
    program_id = Column(String(8), primary_key=True, nullable=False,
                        comment="Originating program ID (DB2 CHAR(8))")

    # --- Data columns -----------------------------------------------------
    error_type = Column(String(1), nullable=False,
                        comment="Error type: S=System, A=Application, D=Data (DB2 CHAR(1))")
    error_severity = Column(Integer, nullable=False,
                            comment="Severity: 1=Info, 2=Warning, 3=Error, 4=Severe (DB2 INTEGER)")
    error_code = Column(String(8), nullable=False,
                        comment="Application error code (DB2 CHAR(8))")
    error_message = Column(String(200), nullable=False,
                           comment="Human-readable error description (DB2 VARCHAR(200))")
    process_date = Column(Date, nullable=False,
                          comment="Processing date (DB2 DATE)")
    process_time = Column(Time, nullable=False,
                          comment="Processing time (DB2 TIME)")
    user_id = Column(String(8), nullable=False,
                     comment="User associated with the error (DB2 CHAR(8))")
    additional_info = Column(String(500), nullable=True,
                             comment="Optional additional context (DB2 VARCHAR(500))")

    __table_args__ = (
        Index("errlog_ix1", "process_date", error_severity.desc()),
        {"comment": "Error log — migrated from DB2 ERRLOG (ERRLOG.sql)"},
    )

    def __repr__(self) -> str:
        return (
            f"<ErrorLog(error_timestamp={self.error_timestamp!r}, "
            f"program_id={self.program_id!r}, "
            f"error_severity={self.error_severity!r})>"
        )
