package com.portfolio.inquiry.service;

import com.portfolio.inquiry.dto.PagedResponseDto;
import com.portfolio.inquiry.dto.TransactionDto;
import com.portfolio.inquiry.dto.TransactionHistoryDto;
import com.portfolio.inquiry.exception.InvalidInquiryRequestException;
import com.portfolio.inquiry.exception.PortfolioNotFoundException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.PageRequest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
class TransactionHistoryServiceTest {

    @Autowired
    private TransactionHistoryService service;

    @Test
    @DisplayName("Should retrieve paginated transactions for portfolio")
    void shouldRetrieveTransactions() {
        PagedResponseDto<TransactionDto> result =
                service.getTransactions("PORT0001", PageRequest.of(0, 10));

        assertNotNull(result);
        assertFalse(result.content().isEmpty());
        assertEquals(0, result.page());
        assertEquals(10, result.size());
        assertTrue(result.totalElements() > 0);
    }

    @Test
    @DisplayName("Should retrieve paginated history records")
    void shouldRetrieveHistory() {
        PagedResponseDto<TransactionHistoryDto> result =
                service.getHistory("PORT0001", PageRequest.of(0, 10));

        assertNotNull(result);
        assertFalse(result.content().isEmpty());
        assertTrue(result.totalElements() > 0);
    }

    @Test
    @DisplayName("Should filter transactions by type")
    void shouldFilterByType() {
        PagedResponseDto<TransactionDto> result =
                service.getTransactionsByType("PORT0001", "BU", PageRequest.of(0, 10));

        assertNotNull(result);
        assertFalse(result.content().isEmpty());
        result.content().forEach(txn -> assertEquals("BU", txn.type()));
    }

    @Test
    @DisplayName("Should paginate with small page size")
    void shouldPaginateWithSmallPageSize() {
        PagedResponseDto<TransactionDto> page0 =
                service.getTransactions("PORT0001", PageRequest.of(0, 2));

        assertEquals(2, page0.content().size());
        assertEquals(2, page0.size());
        assertTrue(page0.totalElements() > 2);
    }

    @Test
    @DisplayName("Should throw PortfolioNotFoundException for missing portfolio")
    void shouldThrowNotFoundForMissingPortfolio() {
        assertThrows(PortfolioNotFoundException.class,
                () -> service.getTransactions("MISSING1", PageRequest.of(0, 10)));
    }

    @Test
    @DisplayName("Should throw InvalidInquiryRequestException for invalid type")
    void shouldThrowInvalidForBadType() {
        assertThrows(InvalidInquiryRequestException.class,
                () -> service.getTransactionsByType("PORT0001", "XX", PageRequest.of(0, 10)));
    }

    @Test
    @DisplayName("Should return empty results for portfolio with no transactions")
    void shouldReturnEmptyForNoTransactions() {
        PagedResponseDto<TransactionDto> result =
                service.getTransactions("PORT0003", PageRequest.of(0, 10));

        assertNotNull(result);
        assertTrue(result.content().isEmpty());
        assertEquals(0, result.totalElements());
    }
}
