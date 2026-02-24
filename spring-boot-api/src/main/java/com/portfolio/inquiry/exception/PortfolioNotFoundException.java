package com.portfolio.inquiry.exception;

public class PortfolioNotFoundException extends RuntimeException {

    private final String portfolioId;

    public PortfolioNotFoundException(String portfolioId) {
        super("Portfolio not found: " + portfolioId);
        this.portfolioId = portfolioId;
    }

    public String getPortfolioId() {
        return portfolioId;
    }
}
