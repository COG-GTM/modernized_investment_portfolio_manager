package com.portfolio.inquiry.service;

import com.portfolio.inquiry.dto.PortfolioSummaryDto;
import com.portfolio.inquiry.exception.InvalidInquiryRequestException;
import com.portfolio.inquiry.exception.PortfolioNotFoundException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

@SpringBootTest
class PortfolioServiceTest {

    @Autowired
    private PortfolioService portfolioService;

    @Test
    @DisplayName("Should retrieve portfolio summary with positions")
    void shouldRetrievePortfolioSummary() {
        PortfolioSummaryDto summary = portfolioService.getPortfolioSummary("PORT0001");

        assertNotNull(summary);
        assertEquals("PORT0001", summary.portId());
        assertEquals("1000000001", summary.accountNo());
        assertEquals("GROWTH PORTFOLIO", summary.clientName());
        assertEquals("A", summary.status());
        assertNotNull(summary.positions());
        assertEquals(3, summary.positions().size());
    }

    @Test
    @DisplayName("Should throw PortfolioNotFoundException for missing portfolio")
    void shouldThrowNotFoundForMissingPortfolio() {
        assertThrows(PortfolioNotFoundException.class,
                () -> portfolioService.getPortfolioSummary("MISSING1"));
    }

    @Test
    @DisplayName("Should throw InvalidInquiryRequestException for blank ID")
    void shouldThrowInvalidForBlankId() {
        assertThrows(InvalidInquiryRequestException.class,
                () -> portfolioService.getPortfolioSummary(""));
    }

    @Test
    @DisplayName("Should throw InvalidInquiryRequestException for ID exceeding 8 chars")
    void shouldThrowInvalidForLongId() {
        assertThrows(InvalidInquiryRequestException.class,
                () -> portfolioService.getPortfolioSummary("TOOLONGID"));
    }

    @Test
    @DisplayName("Should return active positions only")
    void shouldReturnActivePositions() {
        var positions = portfolioService.getActivePositions("PORT0001");

        assertNotNull(positions);
        assertEquals(3, positions.size());
        positions.forEach(p -> assertEquals("A", p.status()));
    }
}
