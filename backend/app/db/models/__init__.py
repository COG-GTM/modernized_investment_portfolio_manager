"""
SQLAlchemy ORM models for the Investment Portfolio Management System.

All models are migrated from the legacy DB2 and VSAM definitions found in
COG-GTM/COBOL-Legacy-Benchmark-Suite under src/database/db2/ and
src/database/vsam/.

DB2 source tables
-----------------
- PORTFOLIO_MASTER   -> PortfolioMaster      (db2-definitions.sql)
- INVESTMENT_POSITIONS -> InvestmentPosition  (db2-definitions.sql)
- TRANSACTION_HISTORY -> TransactionHistory   (db2-definitions.sql)
- POSHIST            -> PositionHistory       (POSHIST.sql)
- ERRLOG             -> ErrorLog              (ERRLOG.sql)
- RTNCODES           -> ReturnCode            (RTNCODES.sql)

VSAM replacement tables
-----------------------
- PORTMSTR (KSDS)    -> PositionMaster        (vsam-definitions.txt)
- TRANHIST (KSDS)    -> TransactionFile        (vsam-definitions.txt)
"""

from .portfolio_master import PortfolioMaster
from .investment_positions import InvestmentPosition
from .transaction_history import TransactionHistory
from .position_history import PositionHistory
from .error_log import ErrorLog
from .return_codes import ReturnCode
from .position_master import PositionMaster
from .transaction_file import TransactionFile

__all__ = [
    "PortfolioMaster",
    "InvestmentPosition",
    "TransactionHistory",
    "PositionHistory",
    "ErrorLog",
    "ReturnCode",
    "PositionMaster",
    "TransactionFile",
]
