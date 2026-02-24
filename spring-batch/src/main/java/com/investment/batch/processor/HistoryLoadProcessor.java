package com.investment.batch.processor;

import com.investment.batch.entity.Transaction;
import com.investment.batch.entity.TransactionHistory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.item.ItemProcessor;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Item processor for history load step (HISTLD00).
 * Converts validated transactions into history records for DB2 load.
 * Maps COBOL HISTLD00 2200-LOAD-TO-DB2 field mapping.
 */
public class HistoryLoadProcessor implements ItemProcessor<Transaction, TransactionHistory> {

    private static final Logger log = LoggerFactory.getLogger(HistoryLoadProcessor.class);
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HHmmssnn");

    private long processedCount;

    public HistoryLoadProcessor() {
        this.processedCount = 0;
    }

    @Override
    public TransactionHistory process(Transaction transaction) throws Exception {
        // Only load completed transactions to history
        if (!Transaction.STATUS_DONE.equals(transaction.getStatus())) {
            return null;
        }

        TransactionHistory history = new TransactionHistory();

        // Map fields per COBOL HISTLD00 2200-LOAD-TO-DB2
        history.setPortfolioId(transaction.getPortfolioId());
        history.setDate(transaction.getDate() != null ? transaction.getDate().format(DATE_FMT) : "");
        history.setTime(transaction.getTime() != null ? transaction.getTime().format(TIME_FMT) : "");

        // Generate sequence number
        String seqNo = String.format("%04d", (processedCount % 9999) + 1);
        history.setSeqNo(seqNo);

        history.setRecordType(TransactionHistory.RECORD_TYPE_TRANSACTION);
        history.setActionCode(TransactionHistory.ACTION_ADD);

        // Build after-image JSON with transaction details
        String afterImage = String.format(
                "{\"investmentId\":\"%s\",\"type\":\"%s\",\"quantity\":\"%s\",\"price\":\"%s\",\"amount\":\"%s\"}",
                nullSafe(transaction.getInvestmentId()),
                nullSafe(transaction.getType()),
                transaction.getQuantity() != null ? transaction.getQuantity().toPlainString() : "0",
                transaction.getPrice() != null ? transaction.getPrice().toPlainString() : "0",
                transaction.getAmount() != null ? transaction.getAmount().toPlainString() : "0");
        history.setAfterImage(afterImage);

        history.setReasonCode("AUTO");
        history.setProcessDate(LocalDateTime.now());
        history.setProcessUser("HISTLD00");

        processedCount++;
        log.debug("Created history record for portfolio={}, date={}",
                transaction.getPortfolioId(), history.getDate());

        return history;
    }

    private String nullSafe(String value) {
        return value != null ? value : "";
    }

    public long getProcessedCount() { return processedCount; }
}
