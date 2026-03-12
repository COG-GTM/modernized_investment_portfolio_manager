"""
Test Data Generator - Migrated from COBOL TSTGEN00.cbl and PORTTEST.cbl

Generates synthetic test data for system testing:
- Portfolio test data with realistic names, types, and values
- Transaction test scenarios (buys, sells, transfers, fees)
- Error condition data for negative testing
- Performance/volume test data

The COBOL TSTGEN00 program:
1. Read a config file specifying test type (PORTFOLIO, TRANSACTN, ERROR, VOLUME)
   and volume (number of records)
2. Used a random seed file for reproducible generation
3. Generated records in a loop, writing to output files
4. Tracked records written and errors

The COBOL PORTTEST program:
1. Generated portfolio records with sequential IDs (PORT00001, etc.)
2. Used FUNCTION RANDOM for client type, status, and financial values
3. Set CREATE-DATE and LAST-MAINT to current date
4. Computed TOTAL-VALUE as random * 1000000
5. Computed CASH-BALANCE as 10% of TOTAL-VALUE

This module can be run as a CLI script:
    python -m app.testing.test_data_generator --portfolios 100 --transactions 500
"""

import argparse
import logging
import random
import string
import sys
from datetime import datetime, date, timedelta, time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.database import Portfolio, Position, SessionLocal
from models.transactions import Transaction
from models.history import History

logger = logging.getLogger(__name__)


# Test types (from COBOL WS-TEST-TYPES)
TEST_PORTFOLIO = "PORTFOLIO"
TEST_TRANSACTION = "TRANSACTN"
TEST_ERROR = "ERROR"
TEST_VOLUME = "VOLUME"

# Client types (from COBOL WS-CLIENT-TYPES 'ICT')
CLIENT_TYPES = ["I", "C", "T"]

# Portfolio statuses (from COBOL WS-STATUS-TYPES 'ACS')
PORTFOLIO_STATUSES = ["A", "C", "S"]

# Transaction types
TRANSACTION_TYPES = ["BU", "SL", "FE"]

# Transaction statuses
TRANSACTION_STATUSES = ["P", "D"]

# Sample company names for realistic data
SAMPLE_NAMES = [
    "Acme Corporation", "Global Investments LLC", "Pacific Holdings",
    "Atlantic Capital Group", "Mountain View Partners", "Riverside Trust",
    "Northern Star Fund", "Southern Cross Capital", "Eastern Promise Inc",
    "Western Frontier LLC", "Summit Financial Group", "Valley Investments",
    "Coastal Asset Management", "Prairie Capital Partners", "Metro Holdings",
    "Heritage Trust Company", "Pinnacle Advisors", "Horizon Capital",
    "Landmark Investment Corp", "Beacon Financial Group",
]

# Sample investment symbols
SAMPLE_INVESTMENTS = [
    ("AAPL0001", "STK"), ("MSFT0001", "STK"), ("GOOGL001", "STK"),
    ("AMZN0001", "STK"), ("TSLA0001", "STK"), ("BND10001", "BND"),
    ("BND20001", "BND"), ("MMF10001", "MMF"), ("ETF10001", "ETF"),
    ("ETF20001", "ETF"),
]

# Maximum errors before aborting (from COBOL WS-ERROR-COUNT > 100)
MAX_ERRORS = 100


class TestDataGenerator:
    """
    Synthetic test data generator.

    Migrated from COBOL TSTGEN00 and PORTTEST.

    TSTGEN00 was a general-purpose generator that read config records
    specifying what type and volume of data to create.

    PORTTEST specifically generated portfolio records with:
    - Sequential IDs (PORT + counter)
    - Account numbers computed as counter + 1000000000
    - Random client types from 'ICT'
    - Random statuses from 'ACS'
    - TOTAL-VALUE = RANDOM * 1000000
    - CASH-BALANCE = TOTAL-VALUE * 0.10
    """

    def __init__(self, db: Optional[Session] = None, seed: Optional[int] = None):
        self._db = db
        self.records_written: int = 0
        self.error_count: int = 0

        # Initialize random seed (mirrors COBOL 1200-INIT-RANDOM)
        if seed is not None:
            random.seed(seed)

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def generate(
        self,
        portfolios: int = 0,
        transactions: int = 0,
        include_errors: bool = False,
        volume_test: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate test data based on configuration.

        Mirrors COBOL TSTGEN00 2000-PROCESS which dispatched based on
        CFG-TEST-TYPE to the appropriate generation paragraph.

        Args:
            portfolios: Number of portfolio records to generate
            transactions: Number of transaction records to generate
            include_errors: Whether to include error condition data
            volume_test: Whether to generate volume test data

        Returns:
            Summary of generated data.
        """
        self.records_written = 0
        self.error_count = 0
        results: Dict[str, Any] = {}

        if portfolios > 0:
            results["portfolios"] = self._generate_portfolios(portfolios)

        if transactions > 0:
            results["transactions"] = self._generate_transactions(transactions)

        if include_errors:
            results["error_data"] = self._generate_error_data()

        if volume_test:
            results["volume_data"] = self._generate_volume_data()

        results["total_records_written"] = self.records_written
        results["total_errors"] = self.error_count

        logger.info("Test data generation complete. Records: %d, Errors: %d",
                     self.records_written, self.error_count)
        return results

    def _generate_portfolios(self, count: int) -> Dict[str, Any]:
        """
        Generate synthetic portfolio records.

        Mirrors COBOL TSTGEN00 2200-GEN-PORTFOLIO and PORTTEST 2000-GENERATE-RECORDS:

        PORTTEST logic:
        - 2100-GENERATE-KEY: STRING 'PORT' WS-RECORD-COUNT INTO PORT-ID
          COMPUTE PORT-ACCOUNT-NO = WS-RECORD-COUNT + 1000000000
        - 2200-GENERATE-CLIENT-INFO: STRING WS-NAME-PREFIX WS-RECORD-COUNT
          INTO PORT-CLIENT-NAME
        - 2300-GENERATE-PORTFOLIO-INFO: Set dates and random status
        - 2400-GENERATE-FINANCIAL-INFO:
          COMPUTE PORT-TOTAL-VALUE = FUNCTION RANDOM * 1000000
          COMPUTE PORT-CASH-BALANCE = PORT-TOTAL-VALUE * .10

        Args:
            count: Number of portfolios to generate.

        Returns:
            Generation result summary.
        """
        generated = 0
        today = date.today()

        for i in range(1, count + 1):
            if self.error_count > MAX_ERRORS:
                break

            try:
                # 2100-GENERATE-KEY (mirrors COBOL)
                port_id = f"PORT{i:04d}"
                account_no = f"{1000000000 + i}"

                # 2200-GENERATE-CLIENT-INFO
                client_name = random.choice(SAMPLE_NAMES)
                client_type = random.choice(CLIENT_TYPES)

                # 2300-GENERATE-PORTFOLIO-INFO
                create_date = today - timedelta(days=random.randint(0, 365 * 3))
                status = random.choice(PORTFOLIO_STATUSES)

                # 2400-GENERATE-FINANCIAL-INFO
                # Mirrors COBOL: COMPUTE PORT-TOTAL-VALUE = FUNCTION RANDOM * 1000000
                total_value = Decimal(str(round(random.random() * 1000000, 2)))
                # Mirrors COBOL: COMPUTE PORT-CASH-BALANCE = PORT-TOTAL-VALUE * .10
                cash_balance = (total_value * Decimal("0.10")).quantize(Decimal("0.01"))

                portfolio = Portfolio(
                    port_id=port_id,
                    account_no=account_no,
                    client_name=client_name,
                    client_type=client_type,
                    create_date=create_date,
                    last_maint=today,
                    status=status,
                    total_value=total_value,
                    cash_balance=cash_balance,
                    last_user="TSTGEN",
                    last_trans="CREATE",
                )

                self.db.add(portfolio)
                generated += 1
                self.records_written += 1

            except Exception as e:
                self.error_count += 1
                logger.error("Error generating portfolio %d: %s", i, e)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error("Error committing portfolios: %s", e)
            self.error_count += 1

        return {"generated": generated, "requested": count}

    def _generate_transactions(self, count: int) -> Dict[str, Any]:
        """
        Generate synthetic transaction records.

        Mirrors COBOL TSTGEN00 2300-GEN-TRANSACTION:
        - Generated transaction records in a loop up to CFG-VOLUME
        - Called 2310-GEN-TRAN-DATA to populate fields
        - Called 2320-WRITE-TRAN-RECORD to write output

        Transactions reference existing portfolios and use realistic
        financial values.

        Args:
            count: Number of transactions to generate.

        Returns:
            Generation result summary.
        """
        generated = 0

        # Get existing portfolio IDs
        portfolios = self.db.query(Portfolio.port_id).all()
        if not portfolios:
            logger.warning("No portfolios found; generating 10 portfolios first")
            self._generate_portfolios(10)
            portfolios = self.db.query(Portfolio.port_id).all()

        portfolio_ids = [p.port_id for p in portfolios]

        for i in range(1, count + 1):
            if self.error_count > MAX_ERRORS:
                break

            try:
                portfolio_id = random.choice(portfolio_ids)
                txn_type = random.choice(TRANSACTION_TYPES)
                investment_id, _ = random.choice(SAMPLE_INVESTMENTS)

                quantity = Decimal(str(round(random.uniform(1, 1000), 4)))
                price = Decimal(str(round(random.uniform(1, 500), 4)))
                amount = (quantity * price).quantize(Decimal("0.01"))

                txn_date = date.today() - timedelta(days=random.randint(0, 365))
                txn_time = time(
                    hour=random.randint(9, 16),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )

                transaction = Transaction(
                    date=txn_date,
                    time=txn_time,
                    portfolio_id=portfolio_id,
                    sequence_no=f"{i:06d}",
                    investment_id=investment_id,
                    type=txn_type,
                    quantity=quantity,
                    price=price,
                    amount=amount,
                    currency="USD",
                    status=random.choice(TRANSACTION_STATUSES),
                    process_date=datetime.now(),
                    process_user="TSTGEN",
                )

                self.db.add(transaction)
                generated += 1
                self.records_written += 1

            except Exception as e:
                self.error_count += 1
                logger.error("Error generating transaction %d: %s", i, e)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error("Error committing transactions: %s", e)
            self.error_count += 1

        return {"generated": generated, "requested": count}

    def _generate_error_data(self) -> Dict[str, Any]:
        """
        Generate error condition test data.

        Mirrors COBOL TSTGEN00 2400-GEN-ERROR-DATA:
        - 2410-GEN-DATA-ERRORS: Generate records with invalid data
        - 2420-GEN-PROCESS-ERRORS: Generate records that trigger processing errors

        Creates portfolios and transactions with deliberately invalid data
        for negative testing.
        """
        error_records: List[Dict[str, str]] = []

        # Invalid portfolio IDs (doesn't start with PORT)
        error_records.append({"type": "invalid_port_id", "port_id": "XXXX0001", "expected_error": "Invalid Portfolio ID format"})
        # Empty client name
        error_records.append({"type": "empty_name", "port_id": "PORT9901", "client_name": "", "expected_error": "Portfolio Name is required"})
        # Invalid status
        error_records.append({"type": "invalid_status", "port_id": "PORT9902", "status": "X", "expected_error": "Invalid Portfolio Status"})
        # Invalid account (non-numeric)
        error_records.append({"type": "invalid_account", "account_no": "ABCDEFGHIJ", "expected_error": "Invalid Account Number"})
        # Zero account
        error_records.append({"type": "zero_account", "account_no": "0000000000", "expected_error": "Invalid Account Number"})
        # Negative transaction amount
        error_records.append({"type": "negative_amount", "amount": "-100.00", "expected_error": "Amount must be greater than zero"})

        return {"error_test_cases": error_records, "count": len(error_records)}

    def _generate_volume_data(self) -> Dict[str, Any]:
        """
        Generate large-volume test data.

        Mirrors COBOL TSTGEN00 2500-GEN-VOLUME-DATA:
        - 2510-GEN-LARGE-PORTFOLIO: Generate large set of portfolios
        - 2520-GEN-LARGE-TRANSACTION: Generate large set of transactions
        """
        portfolio_result = self._generate_portfolios(1000)
        transaction_result = self._generate_transactions(5000)

        return {
            "portfolios": portfolio_result,
            "transactions": transaction_result,
        }

    def close(self) -> None:
        """Close database session if we created one."""
        if self._db is not None:
            self._db.close()


def main():
    """CLI entry point for test data generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data for the Investment Portfolio Management System"
    )
    parser.add_argument("--portfolios", type=int, default=100, help="Number of portfolios to generate")
    parser.add_argument("--transactions", type=int, default=500, help="Number of transactions to generate")
    parser.add_argument("--errors", action="store_true", help="Include error condition test data")
    parser.add_argument("--volume", action="store_true", help="Generate volume test data")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible generation")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    generator = TestDataGenerator(seed=args.seed)
    try:
        results = generator.generate(
            portfolios=args.portfolios,
            transactions=args.transactions,
            include_errors=args.errors,
            volume_test=args.volume,
        )

        print(f"\nTest Data Generation Complete:")
        print(f"  Total records written: {results['total_records_written']}")
        print(f"  Total errors: {results['total_errors']}")
        for key, value in results.items():
            if key not in ("total_records_written", "total_errors"):
                print(f"  {key}: {value}")
    finally:
        generator.close()


if __name__ == "__main__":
    main()
