package com.investment.batch.model;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Report entry for position reports, mapping to COBOL RPTPOS00 detail line.
 */
public class PositionReportEntry {

    private String portfolioId;
    private String investmentId;
    private BigDecimal quantity;
    private BigDecimal marketValue;
    private BigDecimal costBasis;
    private BigDecimal gainLoss;
    private BigDecimal changePercent;

    public PositionReportEntry() {}

    public String getPortfolioId() { return portfolioId; }
    public void setPortfolioId(String portfolioId) { this.portfolioId = portfolioId; }
    public String getInvestmentId() { return investmentId; }
    public void setInvestmentId(String investmentId) { this.investmentId = investmentId; }
    public BigDecimal getQuantity() { return quantity; }
    public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
    public BigDecimal getMarketValue() { return marketValue; }
    public void setMarketValue(BigDecimal marketValue) { this.marketValue = marketValue; }
    public BigDecimal getCostBasis() { return costBasis; }
    public void setCostBasis(BigDecimal costBasis) { this.costBasis = costBasis; }
    public BigDecimal getGainLoss() { return gainLoss; }
    public void setGainLoss(BigDecimal gainLoss) { this.gainLoss = gainLoss; }
    public BigDecimal getChangePercent() { return changePercent; }
    public void setChangePercent(BigDecimal changePercent) { this.changePercent = changePercent; }

    public void calculateDerivedFields() {
        if (marketValue != null && costBasis != null) {
            this.gainLoss = marketValue.subtract(costBasis);
            if (costBasis.compareTo(BigDecimal.ZERO) != 0) {
                this.changePercent = gainLoss.divide(costBasis, 4, RoundingMode.HALF_UP)
                        .multiply(BigDecimal.valueOf(100));
            } else {
                this.changePercent = BigDecimal.ZERO;
            }
        }
    }

    @Override
    public String toString() {
        return String.format("%-10s %-10s %15s %15s %15s %8s%%",
                portfolioId, investmentId,
                quantity != null ? quantity.toPlainString() : "0",
                marketValue != null ? marketValue.toPlainString() : "0.00",
                gainLoss != null ? gainLoss.toPlainString() : "0.00",
                changePercent != null ? changePercent.setScale(2, RoundingMode.HALF_UP).toPlainString() : "0.00");
    }
}
