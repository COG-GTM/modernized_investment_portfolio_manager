package com.portfolio.inquiry.service;

import com.portfolio.inquiry.dto.PagedResponseDto;
import com.portfolio.inquiry.dto.TransactionDto;
import com.portfolio.inquiry.dto.TransactionHistoryDto;
import com.portfolio.inquiry.entity.Transaction;
import com.portfolio.inquiry.entity.TransactionHistory;
import com.portfolio.inquiry.exception.DataAccessException;
import com.portfolio.inquiry.exception.InvalidInquiryRequestException;
import com.portfolio.inquiry.exception.PortfolioNotFoundException;
import com.portfolio.inquiry.repository.PortfolioRepository;
import com.portfolio.inquiry.repository.TransactionHistoryRepository;
import com.portfolio.inquiry.repository.TransactionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Transaction history retrieval with pagination — replaces INQHIST.cbl.
 *
 * <p>The original COBOL program used CURSMGR with HISTORY_CURSOR to fetch
 * up to 3000 bytes at a time from DB2 (see INQHIST.cbl lines 43-50).
 * This service replaces that cursor-based fetch with standard Spring Data
 * {@link Pageable} pagination, providing the same scrolling capability
 * with proper REST semantics.</p>
 */
@Service
public class TransactionHistoryService {

    private static final Logger log = LoggerFactory.getLogger(TransactionHistoryService.class);

    private final TransactionRepository transactionRepository;
    private final TransactionHistoryRepository historyRepository;
    private final PortfolioRepository portfolioRepository;

    public TransactionHistoryService(TransactionRepository transactionRepository,
                                     TransactionHistoryRepository historyRepository,
                                     PortfolioRepository portfolioRepository) {
        this.transactionRepository = transactionRepository;
        this.historyRepository = historyRepository;
        this.portfolioRepository = portfolioRepository;
    }

    /**
     * Retrieve paginated transaction history — replaces INQHIST P200-GET-HISTORY cursor fetch.
     *
     * <p>In the original COBOL, CURSMGR would declare, open, fetch, and close a
     * DB2 cursor named HISTORY_CURSOR. Each fetch retrieved up to 3000 bytes
     * (approximately 10 rows). Spring Data pagination replaces this entirely.</p>
     *
     * @param portfolioId the portfolio identifier
     * @param pageable    pagination parameters (page, size, sort)
     * @return paginated transaction list
     */
    @Transactional(readOnly = true)
    public PagedResponseDto<TransactionDto> getTransactions(String portfolioId, Pageable pageable) {
        validatePortfolioId(portfolioId);
        ensurePortfolioExists(portfolioId);

        try {
            Page<Transaction> page = transactionRepository
                    .findByPortfolioIdOrderByDateDescTimeDesc(portfolioId, pageable);

            log.debug("Retrieved {} transactions for portfolio {} (page {}/{})",
                    page.getNumberOfElements(), portfolioId, page.getNumber(), page.getTotalPages());

            return toPagedResponse(page);
        } catch (PortfolioNotFoundException e) {
            throw e;
        } catch (Exception e) {
            throw new DataAccessException("TransactionHistoryService",
                    "Error retrieving transactions for portfolio: " + portfolioId, e);
        }
    }

    /**
     * Retrieve paginated audit history records.
     *
     * @param portfolioId the portfolio identifier
     * @param pageable    pagination parameters
     * @return paginated history records
     */
    @Transactional(readOnly = true)
    public PagedResponseDto<TransactionHistoryDto> getHistory(String portfolioId, Pageable pageable) {
        validatePortfolioId(portfolioId);
        ensurePortfolioExists(portfolioId);

        try {
            Page<TransactionHistory> page = historyRepository
                    .findByPortfolioIdOrderByDateDescTimeDesc(portfolioId, pageable);

            log.debug("Retrieved {} history records for portfolio {} (page {}/{})",
                    page.getNumberOfElements(), portfolioId, page.getNumber(), page.getTotalPages());

            return toHistoryPagedResponse(page);
        } catch (PortfolioNotFoundException e) {
            throw e;
        } catch (Exception e) {
            throw new DataAccessException("TransactionHistoryService",
                    "Error retrieving history for portfolio: " + portfolioId, e);
        }
    }

    /**
     * Retrieve paginated transactions filtered by type.
     */
    @Transactional(readOnly = true)
    public PagedResponseDto<TransactionDto> getTransactionsByType(
            String portfolioId, String type, Pageable pageable) {
        validatePortfolioId(portfolioId);
        validateTransactionType(type);
        ensurePortfolioExists(portfolioId);

        Page<Transaction> page = transactionRepository
                .findByPortfolioIdAndTypeOrderByDateDescTimeDesc(portfolioId, type, pageable);

        return toPagedResponse(page);
    }

    private void validatePortfolioId(String portfolioId) {
        if (portfolioId == null || portfolioId.isBlank()) {
            throw new InvalidInquiryRequestException("Portfolio ID is required");
        }
        if (portfolioId.length() > 8) {
            throw new InvalidInquiryRequestException("Portfolio ID must not exceed 8 characters");
        }
    }

    private void validateTransactionType(String type) {
        if (type != null && !type.matches("BU|SL|TR|FE")) {
            throw new InvalidInquiryRequestException(
                    "Invalid transaction type: " + type + ". Must be one of: BU, SL, TR, FE");
        }
    }

    private void ensurePortfolioExists(String portfolioId) {
        if (portfolioRepository.findByPortId(portfolioId).isEmpty()) {
            throw new PortfolioNotFoundException(portfolioId);
        }
    }

    private PagedResponseDto<TransactionDto> toPagedResponse(Page<Transaction> page) {
        return new PagedResponseDto<>(
                page.getContent().stream().map(this::toTransactionDto).toList(),
                page.getNumber(),
                page.getSize(),
                page.getTotalElements(),
                page.getTotalPages(),
                page.isLast()
        );
    }

    private PagedResponseDto<TransactionHistoryDto> toHistoryPagedResponse(Page<TransactionHistory> page) {
        return new PagedResponseDto<>(
                page.getContent().stream().map(this::toHistoryDto).toList(),
                page.getNumber(),
                page.getSize(),
                page.getTotalElements(),
                page.getTotalPages(),
                page.isLast()
        );
    }

    private TransactionDto toTransactionDto(Transaction txn) {
        return new TransactionDto(
                txn.getDate(),
                txn.getTime(),
                txn.getSequenceNo(),
                txn.getInvestmentId(),
                txn.getType(),
                txn.getQuantity(),
                txn.getPrice(),
                txn.getAmount(),
                txn.getCurrency(),
                txn.getStatus()
        );
    }

    private TransactionHistoryDto toHistoryDto(TransactionHistory hist) {
        return new TransactionHistoryDto(
                hist.getDate(),
                hist.getTime(),
                hist.getSeqNo(),
                hist.getRecordType(),
                hist.getActionCode(),
                hist.getBeforeImage(),
                hist.getAfterImage(),
                hist.getReasonCode(),
                hist.getProcessDate(),
                hist.getProcessUser()
        );
    }
}
