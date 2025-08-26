import pytest
from decimal import Decimal
from validation.portfolio import (
    validate_portfolio_id,
    validate_account_number,
    validate_investment_type,
    validate_amount
)


class TestValidatePortfolioId:
    """Test portfolio ID validation function"""
    
    def test_valid_portfolio_id(self):
        """Test valid portfolio ID format"""
        valid, message = validate_portfolio_id("PORT1234")
        assert valid is True
        assert message == "Valid portfolio ID"
    
    def test_valid_portfolio_id_with_zeros(self):
        """Test valid portfolio ID with zeros"""
        valid, message = validate_portfolio_id("PORT0000")
        assert valid is True
        assert message == "Valid portfolio ID"
    
    def test_empty_portfolio_id(self):
        """Test empty portfolio ID"""
        valid, message = validate_portfolio_id("")
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"
    
    def test_none_portfolio_id(self):
        """Test None portfolio ID"""
        valid, message = validate_portfolio_id(None)
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"
    
    def test_short_portfolio_id(self):
        """Test portfolio ID too short"""
        valid, message = validate_portfolio_id("PORT12")
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"
    
    def test_long_portfolio_id(self):
        """Test portfolio ID too long"""
        valid, message = validate_portfolio_id("PORT12345")
        assert valid is False
        assert message == "Portfolio ID must be exactly 8 characters"
    
    def test_wrong_prefix(self):
        """Test portfolio ID with wrong prefix"""
        valid, message = validate_portfolio_id("FOLIO123")
        assert valid is False
        assert message == "Portfolio ID must start with 'PORT'"
    
    def test_lowercase_prefix(self):
        """Test portfolio ID with lowercase prefix"""
        valid, message = validate_portfolio_id("port1234")
        assert valid is False
        assert message == "Portfolio ID must start with 'PORT'"
    
    def test_non_numeric_suffix(self):
        """Test portfolio ID with non-numeric suffix"""
        valid, message = validate_portfolio_id("PORTABCD")
        assert valid is False
        assert message == "Portfolio ID must have 4 numeric digits after 'PORT'"
    
    def test_mixed_alphanumeric_suffix(self):
        """Test portfolio ID with mixed alphanumeric suffix"""
        valid, message = validate_portfolio_id("PORT12AB")
        assert valid is False
        assert message == "Portfolio ID must have 4 numeric digits after 'PORT'"


class TestValidateAccountNumber:
    """Test account number validation function"""
    
    def test_valid_account_number(self):
        """Test valid 10-digit account number"""
        valid, message = validate_account_number("1234567890")
        assert valid is True
        assert message == "Valid account number"
    
    def test_valid_account_number_with_zeros(self):
        """Test valid account number with some zeros"""
        valid, message = validate_account_number("1234567800")
        assert valid is True
        assert message == "Valid account number"
    
    def test_empty_account_number(self):
        """Test empty account number"""
        valid, message = validate_account_number("")
        assert valid is False
        assert message == "Account number must be exactly 10 digits"
    
    def test_none_account_number(self):
        """Test None account number"""
        valid, message = validate_account_number(None)
        assert valid is False
        assert message == "Account number must be exactly 10 digits"
    
    def test_short_account_number(self):
        """Test account number too short"""
        valid, message = validate_account_number("123456789")
        assert valid is False
        assert message == "Account number must be exactly 10 digits"
    
    def test_long_account_number(self):
        """Test account number too long"""
        valid, message = validate_account_number("12345678901")
        assert valid is False
        assert message == "Account number must be exactly 10 digits"
    
    def test_non_numeric_account_number(self):
        """Test account number with non-numeric characters"""
        valid, message = validate_account_number("123456789A")
        assert valid is False
        assert message == "Account number must contain only numeric characters"
    
    def test_all_zeros_account_number(self):
        """Test account number with all zeros"""
        valid, message = validate_account_number("0000000000")
        assert valid is False
        assert message == "Account number cannot be all zeros"
    
    def test_account_number_with_spaces(self):
        """Test account number with spaces"""
        valid, message = validate_account_number("123 456 789")
        assert valid is False
        assert message == "Account number must contain only numeric characters"
    
    def test_account_number_with_dashes(self):
        """Test account number with dashes"""
        valid, message = validate_account_number("123-456-789")
        assert valid is False
        assert message == "Account number must contain only numeric characters"


class TestValidateInvestmentType:
    """Test investment type validation function"""
    
    def test_valid_stock_type(self):
        """Test valid STK investment type"""
        valid, message = validate_investment_type("STK")
        assert valid is True
        assert message == "Valid investment type"
    
    def test_valid_bond_type(self):
        """Test valid BND investment type"""
        valid, message = validate_investment_type("BND")
        assert valid is True
        assert message == "Valid investment type"
    
    def test_valid_mmf_type(self):
        """Test valid MMF investment type"""
        valid, message = validate_investment_type("MMF")
        assert valid is True
        assert message == "Valid investment type"
    
    def test_valid_etf_type(self):
        """Test valid ETF investment type"""
        valid, message = validate_investment_type("ETF")
        assert valid is True
        assert message == "Valid investment type"
    
    def test_empty_investment_type(self):
        """Test empty investment type"""
        valid, message = validate_investment_type("")
        assert valid is False
        assert message == "Investment type is required"
    
    def test_none_investment_type(self):
        """Test None investment type"""
        valid, message = validate_investment_type(None)
        assert valid is False
        assert message == "Investment type is required"
    
    def test_invalid_investment_type(self):
        """Test invalid investment type"""
        valid, message = validate_investment_type("INVALID")
        assert valid is False
        assert "Investment type must be one of: BND, ETF, MMF, STK" in message
    
    def test_lowercase_investment_type(self):
        """Test lowercase investment type"""
        valid, message = validate_investment_type("stk")
        assert valid is False
        assert "Investment type must be one of: BND, ETF, MMF, STK" in message
    
    def test_mixed_case_investment_type(self):
        """Test mixed case investment type"""
        valid, message = validate_investment_type("Stk")
        assert valid is False
        assert "Investment type must be one of: BND, ETF, MMF, STK" in message


class TestValidateAmount:
    """Test amount validation function"""
    
    def test_valid_positive_amount_string(self):
        """Test valid positive amount as string"""
        valid, message = validate_amount("1000.50")
        assert valid is True
        assert message == "Valid amount"
    
    def test_valid_negative_amount_string(self):
        """Test valid negative amount as string"""
        valid, message = validate_amount("-1000.50")
        assert valid is True
        assert message == "Valid amount"
    
    def test_valid_zero_amount(self):
        """Test valid zero amount"""
        valid, message = validate_amount("0.00")
        assert valid is True
        assert message == "Valid amount"
    
    def test_valid_amount_float(self):
        """Test valid amount as float"""
        valid, message = validate_amount(1000.50)
        assert valid is True
        assert message == "Valid amount"
    
    def test_valid_amount_decimal(self):
        """Test valid amount as Decimal"""
        valid, message = validate_amount(Decimal("1000.50"))
        assert valid is True
        assert message == "Valid amount"
    
    def test_valid_max_amount(self):
        """Test valid maximum amount"""
        valid, message = validate_amount("9999999999999.99")
        assert valid is True
        assert message == "Valid amount"
    
    def test_valid_min_amount(self):
        """Test valid minimum amount"""
        valid, message = validate_amount("-9999999999999.99")
        assert valid is True
        assert message == "Valid amount"
    
    def test_amount_too_large(self):
        """Test amount exceeding maximum"""
        valid, message = validate_amount("10000000000000.00")
        assert valid is False
        assert "Amount must be between -9999999999999.99 and 9999999999999.99" in message
    
    def test_amount_too_small(self):
        """Test amount below minimum"""
        valid, message = validate_amount("-10000000000000.00")
        assert valid is False
        assert "Amount must be between -9999999999999.99 and 9999999999999.99" in message
    
    def test_invalid_amount_string(self):
        """Test invalid amount string"""
        valid, message = validate_amount("not_a_number")
        assert valid is False
        assert message == "Amount must be a valid number"
    
    def test_empty_amount_string(self):
        """Test empty amount string"""
        valid, message = validate_amount("")
        assert valid is False
        assert message == "Amount must be a valid number"
    
    def test_none_amount(self):
        """Test None amount"""
        valid, message = validate_amount(None)
        assert valid is False
        assert message == "Amount must be a valid number"
    
    def test_amount_with_currency_symbol(self):
        """Test amount with currency symbol"""
        valid, message = validate_amount("$1000.50")
        assert valid is False
        assert message == "Amount must be a valid number"
    
    def test_amount_with_commas(self):
        """Test amount with commas"""
        valid, message = validate_amount("1,000.50")
        assert valid is False
        assert message == "Amount must be a valid number"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_portfolio_id_boundary_cases(self):
        """Test portfolio ID boundary cases"""
        valid, _ = validate_portfolio_id("PORT9999")
        assert valid is True
        
        valid, _ = validate_portfolio_id("PORT0001")
        assert valid is True
    
    def test_account_number_boundary_cases(self):
        """Test account number boundary cases"""
        valid, _ = validate_account_number("9999999999")
        assert valid is True
        
        valid, _ = validate_account_number("1000000000")
        assert valid is True
    
    def test_amount_precision_cases(self):
        """Test amount precision cases"""
        valid, _ = validate_amount("0.01")
        assert valid is True
        
        valid, _ = validate_amount("-0.01")
        assert valid is True
        
        valid, _ = validate_amount("9999999999999.99")
        assert valid is True
        
        valid, _ = validate_amount("-9999999999999.99")
        assert valid is True
