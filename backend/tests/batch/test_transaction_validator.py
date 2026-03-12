"""
Unit tests for the TransactionValidator module.

Tests validation logic for incoming transactions including:
- Required field validation
- Field format validation
- Transaction type validation
- Amount/quantity/price validation
- Duplicate detection
- Batch processing with mixed valid/invalid records
"""

import unittest
from decimal import Decimal

from app.batch.transaction_validator import (
    TransactionValidator,
    ValidationResult,
    VALID_TRANSACTION_TYPES,
)
from app.batch.return_codes import ReturnCode


class TestTransactionValidatorSingleRecord(unittest.TestCase):
    """Test validation of individual transaction records."""

    def setUp(self) -> None:
        self.validator = TransactionValidator()
        self.valid_buy = {
            "date": "20260312",
            "time": "143000",
            "portfolio_id": "PORT0001",
            "sequence_no": "000001",
            "type": "BU",
            "investment_id": "AAPL000001",
            "quantity": 100,
            "price": "150.50",
            "amount": "15050.00",
            "currency": "USD",
        }

    def test_valid_buy_transaction(self) -> None:
        result = self.validator.validate_transaction(self.valid_buy)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.return_code, ReturnCode.SUCCESS)

    def test_valid_sell_transaction(self) -> None:
        sell = {**self.valid_buy, "type": "SL"}
        result = self.validator.validate_transaction(sell)
        self.assertTrue(result.valid)

    def test_valid_transfer_transaction(self) -> None:
        transfer = {
            "date": "20260312",
            "portfolio_id": "PORT0001",
            "type": "TR",
            "amount": "5000.00",
        }
        result = self.validator.validate_transaction(transfer)
        self.assertTrue(result.valid)

    def test_valid_fee_transaction(self) -> None:
        fee = {
            "date": "20260312",
            "portfolio_id": "PORT0001",
            "type": "FE",
            "amount": "25.00",
        }
        result = self.validator.validate_transaction(fee)
        self.assertTrue(result.valid)

    def test_missing_required_date(self) -> None:
        txn = {**self.valid_buy}
        del txn["date"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        field_names = [e.field for e in result.errors]
        self.assertIn("date", field_names)

    def test_missing_required_portfolio_id(self) -> None:
        txn = {**self.valid_buy}
        del txn["portfolio_id"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        field_names = [e.field for e in result.errors]
        self.assertIn("portfolio_id", field_names)

    def test_missing_required_type(self) -> None:
        txn = {**self.valid_buy}
        del txn["type"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        field_names = [e.field for e in result.errors]
        self.assertIn("type", field_names)

    def test_missing_required_amount(self) -> None:
        txn = {**self.valid_buy}
        del txn["amount"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        field_names = [e.field for e in result.errors]
        self.assertIn("amount", field_names)

    def test_empty_required_fields(self) -> None:
        txn = {**self.valid_buy, "date": "", "portfolio_id": "  "}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_invalid_date_format_non_numeric(self) -> None:
        txn = {**self.valid_buy, "date": "2026-03-12"}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        error_fields = [e.field for e in result.errors]
        self.assertIn("date", error_fields)

    def test_invalid_date_format_short(self) -> None:
        txn = {**self.valid_buy, "date": "202603"}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_portfolio_id_too_long(self) -> None:
        txn = {**self.valid_buy, "portfolio_id": "TOOLONGID"}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_investment_id_too_long(self) -> None:
        txn = {**self.valid_buy, "investment_id": "TOOLONGIDXX1"}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_invalid_transaction_type(self) -> None:
        txn = {**self.valid_buy, "type": "XX"}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        error_fields = [e.field for e in result.errors]
        self.assertIn("type", error_fields)

    def test_buy_missing_quantity(self) -> None:
        txn = {**self.valid_buy}
        del txn["quantity"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        error_fields = [e.field for e in result.errors]
        self.assertIn("quantity", error_fields)

    def test_buy_missing_price(self) -> None:
        txn = {**self.valid_buy}
        del txn["price"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        error_fields = [e.field for e in result.errors]
        self.assertIn("price", error_fields)

    def test_buy_zero_quantity(self) -> None:
        txn = {**self.valid_buy, "quantity": 0}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_buy_negative_price(self) -> None:
        txn = {**self.valid_buy, "price": "-10.00"}
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_buy_missing_investment_id(self) -> None:
        txn = {**self.valid_buy}
        del txn["investment_id"]
        result = self.validator.validate_transaction(txn)
        self.assertFalse(result.valid)
        error_fields = [e.field for e in result.errors]
        self.assertIn("investment_id", error_fields)

    def test_amount_mismatch_warning(self) -> None:
        txn = {**self.valid_buy, "amount": "99999.99"}
        result = self.validator.validate_transaction(txn)
        # Amount mismatch is a warning, not an error
        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)
        self.assertEqual(result.return_code, ReturnCode.WARNING)

    def test_unrecognized_currency_warning(self) -> None:
        txn = {**self.valid_buy, "currency": "XYZ"}
        result = self.validator.validate_transaction(txn)
        self.assertTrue(result.valid)
        self.assertGreater(len(result.warnings), 0)

    def test_duplicate_detection(self) -> None:
        validator = TransactionValidator()
        result1 = validator.validate_transaction(self.valid_buy)
        self.assertTrue(result1.valid)

        result2 = validator.validate_transaction(self.valid_buy)
        self.assertFalse(result2.valid)
        error_fields = [e.field for e in result2.errors]
        self.assertIn("_key", error_fields)


class TestTransactionValidatorBatch(unittest.TestCase):
    """Test batch validation of multiple transactions."""

    def setUp(self) -> None:
        self.validator = TransactionValidator()

    def test_all_valid_batch(self) -> None:
        transactions = [
            {
                "date": "20260312",
                "portfolio_id": "PORT0001",
                "sequence_no": f"{i:06d}",
                "type": "BU",
                "investment_id": "AAPL000001",
                "quantity": 100,
                "price": "150.00",
                "amount": "15000.00",
            }
            for i in range(5)
        ]
        valid, invalid, rc = self.validator.validate_batch(transactions)
        self.assertEqual(len(valid), 5)
        self.assertEqual(len(invalid), 0)
        self.assertEqual(rc, ReturnCode.SUCCESS)

    def test_mixed_valid_invalid_batch(self) -> None:
        transactions = [
            {
                "date": "20260312",
                "portfolio_id": "PORT0001",
                "sequence_no": "000001",
                "type": "BU",
                "investment_id": "AAPL000001",
                "quantity": 100,
                "price": "150.00",
                "amount": "15000.00",
            },
            {
                # Missing required fields
                "date": "",
                "portfolio_id": "",
                "type": "",
                "amount": "",
            },
            {
                "date": "20260312",
                "portfolio_id": "PORT0002",
                "sequence_no": "000001",
                "type": "SL",
                "investment_id": "GOOG000001",
                "quantity": 50,
                "price": "200.00",
                "amount": "10000.00",
            },
        ]
        valid, invalid, rc = self.validator.validate_batch(transactions)
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(invalid), 1)
        # Some errors but not all -> WARNING
        self.assertEqual(rc, ReturnCode.WARNING)

    def test_all_invalid_batch(self) -> None:
        transactions = [
            {"date": "", "portfolio_id": "", "type": "", "amount": ""},
            {"date": "", "portfolio_id": "", "type": "", "amount": ""},
        ]
        valid, invalid, rc = self.validator.validate_batch(transactions)
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(invalid), 2)
        self.assertEqual(rc, ReturnCode.ERROR)

    def test_empty_batch(self) -> None:
        valid, invalid, rc = self.validator.validate_batch([])
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(invalid), 0)
        self.assertEqual(rc, ReturnCode.SUCCESS)

    def test_summary_counts(self) -> None:
        transactions = [
            {
                "date": "20260312",
                "portfolio_id": "PORT0001",
                "sequence_no": "000001",
                "type": "BU",
                "investment_id": "AAPL000001",
                "quantity": 100,
                "price": "150.00",
                "amount": "15000.00",
            },
        ]
        self.validator.validate_batch(transactions)
        summary = self.validator.get_summary()
        self.assertEqual(summary.total_transactions, 1)
        self.assertEqual(summary.valid_count, 1)
        self.assertEqual(summary.error_count, 0)


class TestTransactionValidatorEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_sequence_no_max_length(self) -> None:
        validator = TransactionValidator()
        txn = {
            "date": "20260312",
            "portfolio_id": "PORT0001",
            "sequence_no": "123456",  # Exactly 6 chars
            "type": "FE",
            "amount": "25.00",
        }
        result = validator.validate_transaction(txn)
        self.assertTrue(result.valid)

    def test_sequence_no_too_long(self) -> None:
        validator = TransactionValidator()
        txn = {
            "date": "20260312",
            "portfolio_id": "PORT0001",
            "sequence_no": "1234567",  # 7 chars - too long
            "type": "FE",
            "amount": "25.00",
        }
        result = validator.validate_transaction(txn)
        self.assertFalse(result.valid)

    def test_all_valid_transaction_types(self) -> None:
        validator = TransactionValidator()
        for idx, txn_type in enumerate(sorted(VALID_TRANSACTION_TYPES)):
            txn = {
                "date": "20260312",
                "portfolio_id": "PORT0001",
                "sequence_no": f"{idx:06d}",
                "type": txn_type,
                "amount": "100.00",
            }
            if txn_type in ("BU", "SL"):
                txn["investment_id"] = "SEC0000001"
                txn["quantity"] = 10
                txn["price"] = "10.00"
            result = validator.validate_transaction(txn)
            self.assertTrue(
                result.valid,
                f"Transaction type '{txn_type}' should be valid but got errors: "
                f"{[e.message for e in result.errors]}",
            )


if __name__ == "__main__":
    unittest.main()
