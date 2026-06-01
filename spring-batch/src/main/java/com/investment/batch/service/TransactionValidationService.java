package com.investment.batch.service;

import com.investment.batch.entity.Transaction;
import com.investment.batch.model.ValidationResult;
import com.investment.batch.repository.PortfolioRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Set;

/**
 * Implements validation logic from COBOL TRNVAL00.
 * Validates input transactions, performs error checking,
 * and prepares transactions for processing.
 */
@Service
public class TransactionValidationService {

    private static final Logger log = LoggerFactory.getLogger(TransactionValidationService.class);
    private static final Set<String> VALID_TYPES = Set.of(
            Transaction.TYPE_BUY, Transaction.TYPE_SELL,
            Transaction.TYPE_TRANSFER, Transaction.TYPE_FEE);
    private static final Set<String> VALID_STATUSES = Set.of(
            Transaction.STATUS_PENDING, Transaction.STATUS_DONE,
            Transaction.STATUS_FAILED, Transaction.STATUS_REVERSED);

    private final PortfolioRepository portfolioRepository;

    public TransactionValidationService(PortfolioRepository portfolioRepository) {
        this.portfolioRepository = portfolioRepository;
    }

    /**
     * Validate a transaction record (mirrors TRNVAL00 validation logic).
     */
    public ValidationResult validate(Transaction transaction) {
        ValidationResult result = new ValidationResult();

        // Validate portfolio ID
        if (transaction.getPortfolioId() == null || transaction.getPortfolioId().trim().isEmpty()) {
            result.addError("Portfolio ID is required");
        } else if (transaction.getPortfolioId().length() > 8) {
            result.addError("Portfolio ID must not exceed 8 characters");
        } else {
            boolean portfolioExists = portfolioRepository.findByPortId(transaction.getPortfolioId()).isPresent();
            if (!portfolioExists) {
                result.addError("Portfolio ID not found: " + transaction.getPortfolioId());
            }
        }

        // Validate sequence number
        if (transaction.getSequenceNo() == null || transaction.getSequenceNo().trim().isEmpty()) {
            result.addError("Sequence number is required");
        } else if (transaction.getSequenceNo().length() > 6) {
            result.addError("Sequence number must not exceed 6 characters");
        }

        // Validate transaction type
        if (transaction.getType() == null || !VALID_TYPES.contains(transaction.getType())) {
            result.addError("Invalid transaction type: " + transaction.getType());
        }

        // Validate status
        if (transaction.getStatus() != null && !VALID_STATUSES.contains(transaction.getStatus())) {
            result.addError("Invalid status: " + transaction.getStatus());
        }

        // Validate buy/sell specifics (from COBOL: investment ID and quantity required)
        if (transaction.getType() != null &&
                (Transaction.TYPE_BUY.equals(transaction.getType()) || Transaction.TYPE_SELL.equals(transaction.getType()))) {
            if (transaction.getInvestmentId() == null || transaction.getInvestmentId().trim().isEmpty()) {
                result.addError("Investment ID required for buy/sell transactions");
            }
            if (transaction.getQuantity() == null || transaction.getQuantity().compareTo(BigDecimal.ZERO) <= 0) {
                result.addError("Positive quantity required for buy/sell transactions");
            }
            if (transaction.getPrice() == null || transaction.getPrice().compareTo(BigDecimal.ZERO) <= 0) {
                result.addError("Positive price required for buy/sell transactions");
            }
        }

        // Validate date
        if (transaction.getDate() == null) {
            result.addError("Transaction date is required");
        }

        return result;
    }
}
