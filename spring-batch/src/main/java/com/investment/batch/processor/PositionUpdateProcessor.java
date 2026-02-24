package com.investment.batch.processor;

import com.investment.batch.entity.Position;
import com.investment.batch.entity.Transaction;
import com.investment.batch.repository.PositionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.StepExecution;
import org.springframework.batch.core.StepExecutionListener;
import org.springframework.batch.item.ItemProcessor;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Item processor for position update step (POSUPD00).
 * Reads validated transactions and updates position records.
 * Maps to COBOL POSUPDT logic: updates quantity, cost basis, market value.
 */
public class PositionUpdateProcessor implements ItemProcessor<Transaction, Position>, StepExecutionListener {

    private static final Logger log = LoggerFactory.getLogger(PositionUpdateProcessor.class);

    private final PositionRepository positionRepository;
    private long updatedCount;
    private long createdCount;

    // In-memory cache to aggregate multiple transactions for the same position within a chunk.
    // Without this, the second transaction for the same position would create a duplicate Position
    // object (since the first hasn't been written yet), and merge() would overwrite the first.
    private final Map<String, Position> positionCache = new HashMap<>();

    public PositionUpdateProcessor(PositionRepository positionRepository) {
        this.positionRepository = positionRepository;
        this.updatedCount = 0;
        this.createdCount = 0;
    }

    @Override
    public void beforeStep(StepExecution stepExecution) {
        positionCache.clear();
        log.debug("Position cache cleared at start of step: {}", stepExecution.getStepName());
    }

    private String cacheKey(String portfolioId, LocalDate date, String investmentId) {
        return portfolioId + "|" + date + "|" + investmentId;
    }

    @Override
    public Position process(Transaction transaction) throws Exception {
        // Only process done (validated) transactions with buy/sell types
        if (!Transaction.STATUS_DONE.equals(transaction.getStatus())) {
            return null;
        }
        if (transaction.getInvestmentId() == null || transaction.getInvestmentId().trim().isEmpty()) {
            return null;
        }

        LocalDate positionDate = transaction.getDate() != null ? transaction.getDate() : LocalDate.now();

        String key = cacheKey(transaction.getPortfolioId(), positionDate, transaction.getInvestmentId());

        // Check in-memory cache first (handles multiple txns for same position in one chunk)
        Position position = positionCache.get(key);

        if (position != null) {
            // Already processed in this chunk — aggregate onto the cached position
            applyTransaction(position, transaction);
            updatedCount++;
            log.debug("Aggregated onto cached position: portfolio={}, investment={}",
                    position.getPortfolioId(), position.getInvestmentId());
        } else {
            // Check the database
            Optional<Position> existingOpt = positionRepository
                    .findByPortfolioIdAndDateAndInvestmentId(
                            transaction.getPortfolioId(), positionDate, transaction.getInvestmentId());

            if (existingOpt.isPresent()) {
                position = existingOpt.get();
                applyTransaction(position, transaction);
                updatedCount++;
                log.debug("Updated position: portfolio={}, investment={}",
                        position.getPortfolioId(), position.getInvestmentId());
            } else {
                position = createNewPosition(transaction, positionDate);
                if (position == null) {
                    return null;
                }
                createdCount++;
                log.debug("Created new position: portfolio={}, investment={}",
                        position.getPortfolioId(), position.getInvestmentId());
            }
            positionCache.put(key, position);
        }

        position.setLastMaintDate(LocalDateTime.now());
        position.setLastMaintUser("POSUPD00");
        return position;
    }

    private void applyTransaction(Position position, Transaction transaction) {
        BigDecimal quantity = position.getQuantity() != null ? position.getQuantity() : BigDecimal.ZERO;
        BigDecimal costBasis = position.getCostBasis() != null ? position.getCostBasis() : BigDecimal.ZERO;
        BigDecimal txnAmount = transaction.getAmount() != null ? transaction.getAmount() : BigDecimal.ZERO;
        BigDecimal txnQuantity = transaction.getQuantity() != null ? transaction.getQuantity() : BigDecimal.ZERO;

        String txnType = transaction.getType() != null ? transaction.getType() : "";
        switch (txnType) {
            case Transaction.TYPE_BUY:
                position.setQuantity(quantity.add(txnQuantity));
                position.setCostBasis(costBasis.add(txnAmount));
                position.setMarketValue(position.getQuantity().multiply(
                        transaction.getPrice() != null ? transaction.getPrice() : BigDecimal.ZERO));
                break;
            case Transaction.TYPE_SELL:
                position.setQuantity(quantity.subtract(txnQuantity));
                // Proportional cost basis reduction: (sellQty / totalQty) * totalCostBasis
                BigDecimal costBasisReduction = quantity.compareTo(BigDecimal.ZERO) > 0
                        ? costBasis.multiply(txnQuantity).divide(quantity, 2, RoundingMode.HALF_UP)
                        : BigDecimal.ZERO;
                position.setCostBasis(costBasis.subtract(costBasisReduction));
                position.setMarketValue(position.getQuantity().multiply(
                        transaction.getPrice() != null ? transaction.getPrice() : BigDecimal.ZERO));
                if (position.getQuantity().compareTo(BigDecimal.ZERO) <= 0) {
                    position.setStatus(Position.STATUS_CLOSED);
                }
                break;
            default:
                // Transfer and fee transactions: update market value only
                position.setMarketValue(position.getMarketValue() != null
                        ? position.getMarketValue() : BigDecimal.ZERO);
                break;
        }
    }

    private Position createNewPosition(Transaction transaction, LocalDate positionDate) {
        Position position = new Position();
        position.setPortfolioId(transaction.getPortfolioId());
        position.setDate(positionDate);
        position.setInvestmentId(transaction.getInvestmentId());
        position.setCurrency(transaction.getCurrency());
        position.setStatus(Position.STATUS_ACTIVE);

        BigDecimal txnQuantity = transaction.getQuantity() != null ? transaction.getQuantity() : BigDecimal.ZERO;
        BigDecimal txnAmount = transaction.getAmount() != null ? transaction.getAmount() : BigDecimal.ZERO;
        BigDecimal txnPrice = transaction.getPrice() != null ? transaction.getPrice() : BigDecimal.ZERO;

        if (Transaction.TYPE_BUY.equals(transaction.getType())) {
            position.setQuantity(txnQuantity);
            position.setCostBasis(txnAmount);
            position.setMarketValue(txnQuantity.multiply(txnPrice));
        } else if (Transaction.TYPE_SELL.equals(transaction.getType())) {
            // Sell with no existing position: skip and log warning
            log.warn("Sell transaction for non-existent position: portfolio={}, investment={}",
                    transaction.getPortfolioId(), transaction.getInvestmentId());
            return null;
        } else {
            position.setQuantity(BigDecimal.ZERO);
            position.setCostBasis(BigDecimal.ZERO);
            position.setMarketValue(BigDecimal.ZERO);
        }

        return position;
    }

    public long getUpdatedCount() { return updatedCount; }
    public long getCreatedCount() { return createdCount; }
}
