package com.portfolio.inquiry.controller;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for InquiryController — validates the full CICS-to-REST migration.
 *
 * <p>Test data is seeded via Flyway migration V2__seed_test_data.sql, which contains
 * sample portfolios, positions, transactions, and history records matching the patterns
 * described in documentation/operations/test-data-specs.md.</p>
 */
@SpringBootTest
@AutoConfigureMockMvc
class InquiryControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    // ========================================================================
    // Portfolio Inquiry tests (replaces INQPORT.cbl)
    // ========================================================================

    @Nested
    @DisplayName("GET /api/portfolios/{id} — Portfolio Position Inquiry (INQPORT)")
    class PortfolioInquiryTests {

        @Test
        @DisplayName("Should return portfolio summary with positions for valid portfolio")
        void shouldReturnPortfolioWithPositions() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.portId", is("PORT0001")))
                    .andExpect(jsonPath("$.accountNo", is("1000000001")))
                    .andExpect(jsonPath("$.clientName", is("GROWTH PORTFOLIO")))
                    .andExpect(jsonPath("$.clientType", is("I")))
                    .andExpect(jsonPath("$.status", is("A")))
                    .andExpect(jsonPath("$.totalValue", is(12345678.99)))
                    .andExpect(jsonPath("$.cashBalance", is(50000.00)))
                    .andExpect(jsonPath("$.positions", hasSize(3)))
                    .andExpect(jsonPath("$.positions[0].investmentId", notNullValue()))
                    .andExpect(jsonPath("$.positions[0].quantity", notNullValue()))
                    .andExpect(jsonPath("$.positions[0].costBasis", notNullValue()))
                    .andExpect(jsonPath("$.positions[0].marketValue", notNullValue()))
                    .andExpect(jsonPath("$.positions[0].gainLoss", notNullValue()))
                    .andExpect(jsonPath("$.positions[0].gainLossPercent", notNullValue()));
        }

        @Test
        @DisplayName("Should return portfolio with single position")
        void shouldReturnPortfolioWithSinglePosition() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0002")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.portId", is("PORT0002")))
                    .andExpect(jsonPath("$.clientType", is("C")))
                    .andExpect(jsonPath("$.positions", hasSize(1)))
                    .andExpect(jsonPath("$.positions[0].investmentId", is("MSFT000001")));
        }

        @Test
        @DisplayName("Should return 404 for non-existent portfolio — equivalent to INQPORT P900-NOT-FOUND")
        void shouldReturn404ForNonExistentPortfolio() throws Exception {
            mockMvc.perform(get("/api/portfolios/INVALID1")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound())
                    .andExpect(jsonPath("$.status", is(404)))
                    .andExpect(jsonPath("$.message", is("Portfolio not found: INVALID1")))
                    .andExpect(jsonPath("$.timestamp", notNullValue()))
                    .andExpect(jsonPath("$.path", is("/api/portfolios/INVALID1")));
        }

        @Test
        @DisplayName("Should return 400 for invalid portfolio ID format")
        void shouldReturn400ForInvalidPortfolioId() throws Exception {
            mockMvc.perform(get("/api/portfolios/TOOLONGID1")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.status", is(400)))
                    .andExpect(jsonPath("$.message", is("Portfolio ID must not exceed 8 characters")));
        }
    }

    // ========================================================================
    // Active Positions tests
    // ========================================================================

    @Nested
    @DisplayName("GET /api/portfolios/{id}/positions — Active Positions")
    class PositionTests {

        @Test
        @DisplayName("Should return active positions for valid portfolio")
        void shouldReturnActivePositions() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001/positions")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$", hasSize(3)))
                    .andExpect(jsonPath("$[0].status", is("A")));
        }

        @Test
        @DisplayName("Should return 404 for positions of non-existent portfolio")
        void shouldReturn404ForNonExistentPortfolio() throws Exception {
            mockMvc.perform(get("/api/portfolios/NOEXIST1/positions")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound());
        }
    }

    // ========================================================================
    // Transaction History tests (replaces INQHIST.cbl cursor-based fetch)
    // ========================================================================

    @Nested
    @DisplayName("GET /api/portfolios/{id}/history — History Inquiry (INQHIST)")
    class HistoryInquiryTests {

        @Test
        @DisplayName("Should return paginated history — replaces CURSMGR HISTORY_CURSOR 3000-byte fetch")
        void shouldReturnPaginatedHistory() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001/history")
                            .param("page", "0")
                            .param("size", "10")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content", hasSize(greaterThan(0))))
                    .andExpect(jsonPath("$.page", is(0)))
                    .andExpect(jsonPath("$.size", is(10)))
                    .andExpect(jsonPath("$.totalElements", greaterThan(0)))
                    .andExpect(jsonPath("$.totalPages", greaterThan(0)))
                    .andExpect(jsonPath("$.content[0].recordType", notNullValue()))
                    .andExpect(jsonPath("$.content[0].actionCode", notNullValue()))
                    .andExpect(jsonPath("$.content[0].afterImage", notNullValue()));
        }

        @Test
        @DisplayName("Should return history for portfolio with single record")
        void shouldReturnHistoryForPortfolioWithSingleRecord() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0002/history")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content", hasSize(1)))
                    .andExpect(jsonPath("$.totalElements", is(1)));
        }

        @Test
        @DisplayName("Should return 404 for history of non-existent portfolio")
        void shouldReturn404ForNonExistentPortfolio() throws Exception {
            mockMvc.perform(get("/api/portfolios/NOPORT01/history")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound());
        }

        @Test
        @DisplayName("Should return empty page for suspended portfolio with no history")
        void shouldReturnEmptyPageForPortfolioWithNoHistory() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0003/history")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content", hasSize(0)))
                    .andExpect(jsonPath("$.totalElements", is(0)));
        }

        @Test
        @DisplayName("Should respect pagination size parameter")
        void shouldRespectPaginationSize() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001/history")
                            .param("size", "2")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content", hasSize(2)))
                    .andExpect(jsonPath("$.size", is(2)));
        }
    }

    // ========================================================================
    // Transaction list tests
    // ========================================================================

    @Nested
    @DisplayName("GET /api/portfolios/{id}/transactions — Transaction List")
    class TransactionTests {

        @Test
        @DisplayName("Should return paginated transactions")
        void shouldReturnPaginatedTransactions() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001/transactions")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content", hasSize(greaterThan(0))))
                    .andExpect(jsonPath("$.content[0].investmentId", notNullValue()))
                    .andExpect(jsonPath("$.content[0].type", notNullValue()))
                    .andExpect(jsonPath("$.content[0].amount", notNullValue()));
        }

        @Test
        @DisplayName("Should filter transactions by type")
        void shouldFilterTransactionsByType() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001/transactions")
                            .param("type", "BU")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.content", hasSize(greaterThan(0))));
        }

        @Test
        @DisplayName("Should return 400 for invalid transaction type")
        void shouldReturn400ForInvalidTransactionType() throws Exception {
            mockMvc.perform(get("/api/portfolios/PORT0001/transactions")
                            .param("type", "XX")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.message", is("Invalid transaction type: XX. Must be one of: BU, SL, TR, FE")));
        }

        @Test
        @DisplayName("Should return 404 for transactions of non-existent portfolio")
        void shouldReturn404ForNonExistentPortfolio() throws Exception {
            mockMvc.perform(get("/api/portfolios/NOPORT01/transactions")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound());
        }
    }

    // ========================================================================
    // Error handling tests (replaces ERRHNDL.cbl)
    // ========================================================================

    @Nested
    @DisplayName("Error Handling — replaces ERRHNDL.cbl")
    class ErrorHandlingTests {

        @Test
        @DisplayName("Error response should contain timestamp and path")
        void errorResponseShouldContainTimestampAndPath() throws Exception {
            mockMvc.perform(get("/api/portfolios/NOEXIST1")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound())
                    .andExpect(jsonPath("$.timestamp", notNullValue()))
                    .andExpect(jsonPath("$.path", is("/api/portfolios/NOEXIST1")))
                    .andExpect(jsonPath("$.detail", notNullValue()));
        }
    }
}
