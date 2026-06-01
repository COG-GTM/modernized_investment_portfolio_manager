package com.investment.batch.processor;

import com.investment.batch.entity.Transaction;
import com.investment.batch.model.ValidationResult;
import com.investment.batch.service.TransactionValidationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.item.ItemProcessor;

import java.time.LocalDateTime;

/**
 * Item processor for transaction validation step (TRNVAL00).
 * Validates each transaction and marks it as done or failed.
 */
public class TransactionValidationProcessor implements ItemProcessor<Transaction, Transaction> {

    private static final Logger log = LoggerFactory.getLogger(TransactionValidationProcessor.class);

    private final TransactionValidationService validationService;
    private long validCount;
    private long invalidCount;

    public TransactionValidationProcessor(TransactionValidationService validationService) {
        this.validationService = validationService;
        this.validCount = 0;
        this.invalidCount = 0;
    }

    @Override
    public Transaction process(Transaction transaction) throws Exception {
        ValidationResult result = validationService.validate(transaction);

        if (result.isValid()) {
            transaction.setStatus(Transaction.STATUS_DONE);
            transaction.setProcessDate(LocalDateTime.now());
            transaction.setProcessUser("TRNVAL00");
            // Calculate amount if not set
            if (transaction.getAmount() == null || transaction.getAmount().signum() == 0) {
                transaction.setAmount(transaction.calculateAmount());
            }
            validCount++;
            log.debug("Transaction validated: portfolio={}, seq={}",
                    transaction.getPortfolioId(), transaction.getSequenceNo());
        } else {
            transaction.setStatus(Transaction.STATUS_FAILED);
            transaction.setProcessDate(LocalDateTime.now());
            transaction.setProcessUser("TRNVAL00");
            invalidCount++;
            log.warn("Transaction validation failed: portfolio={}, seq={}, errors={}",
                    transaction.getPortfolioId(), transaction.getSequenceNo(), result.getErrors());
        }

        return transaction;
    }

    public long getValidCount() { return validCount; }
    public long getInvalidCount() { return invalidCount; }
}
