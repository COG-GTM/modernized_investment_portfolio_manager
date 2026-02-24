package com.investment.batch.entity;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.Objects;

public class PositionId implements Serializable {

    private String portfolioId;
    private LocalDate date;
    private String investmentId;

    public PositionId() {}

    public PositionId(String portfolioId, LocalDate date, String investmentId) {
        this.portfolioId = portfolioId;
        this.date = date;
        this.investmentId = investmentId;
    }

    public String getPortfolioId() { return portfolioId; }
    public void setPortfolioId(String portfolioId) { this.portfolioId = portfolioId; }
    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }
    public String getInvestmentId() { return investmentId; }
    public void setInvestmentId(String investmentId) { this.investmentId = investmentId; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        PositionId that = (PositionId) o;
        return Objects.equals(portfolioId, that.portfolioId) &&
               Objects.equals(date, that.date) &&
               Objects.equals(investmentId, that.investmentId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(portfolioId, date, investmentId);
    }
}
