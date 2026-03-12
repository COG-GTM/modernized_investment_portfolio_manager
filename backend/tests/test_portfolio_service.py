"""
Portfolio Service Integration Tests - Migrated from COBOL PORTTEST.cbl

Tests CRUD operations and validation logic for the portfolio service.

The COBOL PORTTEST program generated test portfolio records and verified
that the VSAM file operations (WRITE, READ, REWRITE, DELETE) worked
correctly with proper status codes.

These tests verify the Python equivalents work correctly using an
in-memory SQLite database.
"""

import unittest
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Portfolio, Position
from models.transactions import Transaction
from models.history import History
from app.services.portfolio.portfolio_service import PortfolioCRUDService
from app.services.portfolio.portfolio_validator import PortfolioValidator
from app.services.portfolio.portfolio_transactions import PortfolioTransactionProcessor


class TestPortfolioValidator(unittest.TestCase):
    """Tests for PortfolioValidator (migrated from PORTVALD.cbl)."""

    def setUp(self):
        self.validator = PortfolioValidator()

    # --- ID Validation (COBOL 1000-VALIDATE-ID) ---

    def test_validate_id_valid(self):
        rc, msg = self.validator.validate_id("PORT0001")
        self.assertEqual(rc, 0)

    def test_validate_id_missing_prefix(self):
        rc, msg = self.validator.validate_id("XXXX0001")
        self.assertNotEqual(rc, 0)

    def test_validate_id_non_numeric_suffix(self):
        rc, msg = self.validator.validate_id("PORTABCD")
        self.assertNotEqual(rc, 0)

    def test_validate_id_empty(self):
        rc, msg = self.validator.validate_id("")
        self.assertNotEqual(rc, 0)

    # --- Account Validation (COBOL 2000-VALIDATE-ACCOUNT) ---

    def test_validate_account_valid(self):
        rc, msg = self.validator.validate_account("1234567890")
        self.assertEqual(rc, 0)

    def test_validate_account_non_numeric(self):
        rc, msg = self.validator.validate_account("ABCDEFGHIJ")
        self.assertNotEqual(rc, 0)

    def test_validate_account_all_zeros(self):
        rc, msg = self.validator.validate_account("0000000000")
        self.assertNotEqual(rc, 0)

    def test_validate_account_wrong_length(self):
        rc, msg = self.validator.validate_account("12345")
        self.assertNotEqual(rc, 0)

    # --- Type Validation (COBOL 3000-VALIDATE-TYPE) ---

    def test_validate_type_stk(self):
        rc, msg = self.validator.validate_type("STK")
        self.assertEqual(rc, 0)

    def test_validate_type_bnd(self):
        rc, msg = self.validator.validate_type("BND")
        self.assertEqual(rc, 0)

    def test_validate_type_mmf(self):
        rc, msg = self.validator.validate_type("MMF")
        self.assertEqual(rc, 0)

    def test_validate_type_etf(self):
        rc, msg = self.validator.validate_type("ETF")
        self.assertEqual(rc, 0)

    def test_validate_type_invalid(self):
        rc, msg = self.validator.validate_type("XXX")
        self.assertNotEqual(rc, 0)

    # --- Amount Validation (COBOL 4000-VALIDATE-AMOUNT) ---

    def test_validate_amount_valid(self):
        rc, msg = self.validator.validate_amount("1000.00")
        self.assertEqual(rc, 0)

    def test_validate_amount_negative_valid(self):
        rc, msg = self.validator.validate_amount("-500.00")
        self.assertEqual(rc, 0)

    def test_validate_amount_too_large(self):
        rc, msg = self.validator.validate_amount("99999999999999.99")
        self.assertNotEqual(rc, 0)

    def test_validate_amount_non_numeric(self):
        rc, msg = self.validator.validate_amount("ABC")
        self.assertNotEqual(rc, 0)

    # --- Dispatcher (COBOL main EVALUATE) ---

    def test_validate_dispatcher_id(self):
        rc, msg = self.validator.validate("I", "PORT0001")
        self.assertEqual(rc, 0)

    def test_validate_dispatcher_account(self):
        rc, msg = self.validator.validate("A", "1234567890")
        self.assertEqual(rc, 0)

    def test_validate_dispatcher_type(self):
        rc, msg = self.validator.validate("T", "STK")
        self.assertEqual(rc, 0)

    def test_validate_dispatcher_amount(self):
        rc, msg = self.validator.validate("M", "1000.00")
        self.assertEqual(rc, 0)

    def test_validate_dispatcher_invalid_type(self):
        rc, msg = self.validator.validate("Z", "test")
        self.assertNotEqual(rc, 0)


class TestPortfolioCRUDService(unittest.TestCase):
    """Tests for PortfolioCRUDService (migrated from PORTMSTR, PORTADD, PORTREAD, PORTUPDT, PORTDEL)."""

    def setUp(self):
        """Set up in-memory database for testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.service = PortfolioCRUDService(self.db)

    def tearDown(self):
        self.db.close()

    # --- CREATE (PORTADD / PORTMSTR 2000-CREATE-PORTFOLIO) ---

    def test_create_portfolio_success(self):
        success, result = self.service.create_portfolio(
            port_id="PORT0001",
            account_no="1000000001",
            client_name="Test Client",
            client_type="I",
            status="A",
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("10000.00"),
        )
        self.assertTrue(success)
        self.assertIn("portfolio", result)
        self.assertEqual(result["portfolio"]["port_id"], "PORT0001")

    def test_create_portfolio_duplicate(self):
        """Mirrors COBOL PORT-DUP-KEY (file status '22')."""
        self.service.create_portfolio(
            port_id="PORT0001",
            account_no="1000000001",
            client_name="Test Client",
        )
        success, result = self.service.create_portfolio(
            port_id="PORT0001",
            account_no="1000000001",
            client_name="Duplicate Client",
        )
        self.assertFalse(success)
        self.assertIn("errors", result)

    def test_create_portfolio_invalid_id(self):
        success, result = self.service.create_portfolio(
            port_id="XXXX0001",
            account_no="1000000001",
            client_name="Test Client",
        )
        self.assertFalse(success)

    def test_create_portfolio_empty_name(self):
        success, result = self.service.create_portfolio(
            port_id="PORT0002",
            account_no="1000000002",
            client_name="   ",
        )
        self.assertFalse(success)

    # --- READ (PORTREAD / PORTMSTR 3000-READ-PORTFOLIO) ---

    def test_get_portfolio_success(self):
        self.service.create_portfolio(
            port_id="PORT0001",
            account_no="1000000001",
            client_name="Test Client",
        )
        success, result = self.service.get_portfolio("PORT0001")
        self.assertTrue(success)
        self.assertEqual(result["portfolio"]["port_id"], "PORT0001")

    def test_get_portfolio_not_found(self):
        """Mirrors COBOL PORT-NOT-FOUND (file status '23')."""
        success, result = self.service.get_portfolio("PORT9999")
        self.assertFalse(success)

    def test_list_portfolios(self):
        for i in range(1, 6):
            self.service.create_portfolio(
                port_id=f"PORT{i:04d}",
                account_no=f"{1000000000 + i}",
                client_name=f"Client {i}",
            )
        success, result = self.service.list_portfolios()
        self.assertTrue(success)
        self.assertEqual(result["total_count"], 5)
        self.assertEqual(len(result["portfolios"]), 5)

    def test_list_portfolios_with_filter(self):
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="Active", status="A",
        )
        self.service.create_portfolio(
            port_id="PORT0002", account_no="1000000002",
            client_name="Closed", status="C",
        )
        success, result = self.service.list_portfolios(status="A")
        self.assertTrue(success)
        self.assertEqual(result["total_count"], 1)

    # --- UPDATE (PORTUPDT / PORTMSTR 4000-UPDATE-PORTFOLIO) ---

    def test_update_portfolio_name(self):
        """Mirrors COBOL UPDT-ACTION 'N' (name update)."""
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="Old Name",
        )
        success, result = self.service.update_portfolio(
            port_id="PORT0001",
            client_name="New Name",
        )
        self.assertTrue(success)
        self.assertEqual(result["portfolio"]["client_name"], "New Name")

    def test_update_portfolio_status(self):
        """Mirrors COBOL UPDT-ACTION 'S' (status update)."""
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="Test", status="A",
        )
        success, result = self.service.update_portfolio(
            port_id="PORT0001",
            status="S",
        )
        self.assertTrue(success)
        self.assertEqual(result["portfolio"]["status"], "S")

    def test_update_portfolio_value(self):
        """Mirrors COBOL UPDT-ACTION 'V' (value update)."""
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="Test",
        )
        success, result = self.service.update_portfolio(
            port_id="PORT0001",
            total_value=Decimal("500000.00"),
        )
        self.assertTrue(success)
        self.assertEqual(result["portfolio"]["total_value"], 500000.00)

    def test_update_portfolio_not_found(self):
        success, result = self.service.update_portfolio(
            port_id="PORT9999",
            client_name="Missing",
        )
        self.assertFalse(success)

    def test_update_portfolio_invalid_status(self):
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="Test",
        )
        success, result = self.service.update_portfolio(
            port_id="PORT0001",
            status="X",
        )
        self.assertFalse(success)

    # --- DELETE (PORTDEL / PORTMSTR 5000-DELETE-PORTFOLIO) ---

    def test_delete_portfolio_success(self):
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="To Delete",
        )
        success, result = self.service.delete_portfolio(
            port_id="PORT0001",
            reason_code="03",
        )
        self.assertTrue(success)
        self.assertIn("deleted_portfolio", result)

        # Verify portfolio is gone
        success2, result2 = self.service.get_portfolio("PORT0001")
        self.assertFalse(success2)

    def test_delete_portfolio_not_found(self):
        """Mirrors COBOL WS-REC-NOT-FND."""
        success, result = self.service.delete_portfolio(port_id="PORT9999")
        self.assertFalse(success)

    def test_delete_portfolio_audit_trail(self):
        """Verify audit record is created (mirrors COBOL 2300-WRITE-AUDIT)."""
        self.service.create_portfolio(
            port_id="PORT0001", account_no="1000000001",
            client_name="Audit Test",
        )
        self.service.delete_portfolio(
            port_id="PORT0001",
            reason_code="01",
        )
        # Check that audit records exist
        audits = self.db.query(History).filter(
            History.portfolio_id == "PORT0001",
            History.action_code == "D",
        ).all()
        self.assertGreater(len(audits), 0)


class TestPortfolioTransactions(unittest.TestCase):
    """Tests for PortfolioTransactionProcessor (migrated from PORTTRAN.cbl)."""

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.service = PortfolioCRUDService(self.db)
        self.processor = PortfolioTransactionProcessor(self.db)

        # Create a test portfolio
        self.service.create_portfolio(
            port_id="PORT0001",
            account_no="1000000001",
            client_name="Test Client",
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("50000.00"),
        )

    def tearDown(self):
        self.db.close()

    def test_buy_transaction(self):
        """Mirrors COBOL 2210-PROCESS-BUY."""
        success, result = self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="BU",
            investment_id="AAPL000001",
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            amount=Decimal("15000.00"),
        )
        self.assertTrue(success)

    def test_sell_transaction(self):
        """Mirrors COBOL 2220-PROCESS-SELL."""
        # First buy some shares
        self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="BU",
            investment_id="AAPL000001",
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            amount=Decimal("15000.00"),
        )
        # Then sell some
        success, result = self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="SL",
            investment_id="AAPL000001",
            quantity=Decimal("50"),
            price=Decimal("160.00"),
            amount=Decimal("8000.00"),
        )
        self.assertTrue(success)

    def test_sell_insufficient_units(self):
        """Mirrors COBOL: IF PORT-TOTAL-UNITS < TRN-QUANTITY."""
        success, result = self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="SL",
            investment_id="AAPL000001",
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            amount=Decimal("15000.00"),
        )
        self.assertFalse(success)

    def test_fee_transaction(self):
        """Mirrors COBOL 2240-PROCESS-FEE."""
        success, result = self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="FE",
            amount=Decimal("25.00"),
        )
        self.assertTrue(success)

    def test_transfer_not_implemented(self):
        """Mirrors COBOL 2230-PROCESS-TRANSFER placeholder."""
        success, result = self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="TR",
        )
        self.assertFalse(success)

    def test_invalid_portfolio_id(self):
        """Mirrors COBOL 2110-CHECK-PORTFOLIO failure."""
        success, result = self.processor.process_transaction(
            portfolio_id="PORT9999",
            transaction_type="BU",
            investment_id="AAPL000001",
            quantity=Decimal("100"),
            price=Decimal("150.00"),
        )
        self.assertFalse(success)

    def test_invalid_transaction_type(self):
        """Mirrors COBOL 2120-CHECK-TRANSACTION-TYPE failure."""
        success, result = self.processor.process_transaction(
            portfolio_id="PORT0001",
            transaction_type="XX",
        )
        self.assertFalse(success)

    def test_batch_processing(self):
        """Mirrors COBOL 2000-PROCESS-TRANSACTIONS loop."""
        transactions = [
            {
                "portfolio_id": "PORT0001",
                "transaction_type": "BU",
                "investment_id": "AAPL000001",
                "quantity": Decimal("100"),
                "price": Decimal("150.00"),
                "amount": Decimal("15000.00"),
            },
            {
                "portfolio_id": "PORT0001",
                "transaction_type": "FE",
                "amount": Decimal("25.00"),
            },
        ]
        result = self.processor.process_batch(transactions)
        self.assertEqual(result["transactions_read"], 2)
        self.assertEqual(result["transactions_processed"], 2)
        self.assertEqual(result["errors_encountered"], 0)


if __name__ == "__main__":
    unittest.main()
