package com.investment.batch.step;

import com.investment.batch.entity.Portfolio;
import com.investment.batch.entity.Transaction;
import com.investment.batch.processor.TransactionValidationProcessor;
import com.investment.batch.repository.PortfolioRepository;
import com.investment.batch.service.TransactionValidationService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalTime;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/**
 * Unit-style tests for TransactionValidationProcessor (TRNVAL00).
 * Validates transaction processing rules from COBOL TRNVAL00.
 */
@SpringBootTest
@ActiveProfiles("test")
class TransactionValidationProcessorTest {

    @Autowired
    private TransactionValidationService validationService;

    @Autowired
    private PortfolioRepository portfolioRepository;

    private TransactionValidationProcessor processor;

    @BeforeEach
    void setUp() {
        portfolioRepository.deleteAll();

        // Create test portfolio
        Portfolio portfolio = new Portfolio();
        portfolio.setPortId("PORT0001");
        portfolio.setAccountNo("1234567890");
        portfolio.setClientName("TEST PORTFOLIO");
        portfolio.setClientType("I");
        portfolio.setCreateDate(LocalDate.now());
        portfolio.setStatus("A");
        portfolio.setTotalValue(BigDecimal.ZERO);
        portfolio.setCashBalance(BigDecimal.ZERO);
        portfolioRepository.save(portfolio);

        processor = new TransactionValidationProcessor(validationService);
    }

    @Test
    void testValidBuyTransaction() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", "IBM0000001", "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("D", result.getStatus(), "Valid buy transaction should be marked as Done");
        assertEquals("TRNVAL00", result.getProcessUser());
        assertNotNull(result.getAmount(), "Amount should be calculated");
    }

    @Test
    void testValidSellTransaction() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", "MSFT000001", "SL",
                new BigDecimal("50.0000"), new BigDecimal("200.0000"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("D", result.getStatus(), "Valid sell transaction should be marked as Done");
    }

    @Test
    void testInvalidTransactionType() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", "IBM0000001", "XX",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("F", result.getStatus(), "Invalid type should mark transaction as Failed");
    }

    @Test
    void testMissingInvestmentIdForBuy() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", null, "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("F", result.getStatus(), "Missing investment ID for buy should fail");
    }

    @Test
    void testInvalidPortfolioId() throws Exception {
        Transaction txn = createTransaction("INVALID1", "000001", "IBM0000001", "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("F", result.getStatus(), "Non-existent portfolio should fail");
    }

    @Test
    void testZeroQuantityForBuy() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", "IBM0000001", "BU",
                BigDecimal.ZERO, new BigDecimal("125.0000"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("F", result.getStatus(), "Zero quantity for buy should fail");
    }

    @Test
    void testValidTransferTransaction() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", null, "TR",
                null, null);
        txn.setAmount(new BigDecimal("5000.00"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("D", result.getStatus(), "Transfer transaction should be valid without investment ID");
    }

    @Test
    void testValidFeeTransaction() throws Exception {
        Transaction txn = createTransaction("PORT0001", "000001", null, "FE",
                null, null);
        txn.setAmount(new BigDecimal("25.00"));

        Transaction result = processor.process(txn);

        assertNotNull(result);
        assertEquals("D", result.getStatus(), "Fee transaction should be valid without investment ID");
    }

    private Transaction createTransaction(String portfolioId, String seqNo, String investmentId,
                                           String type, BigDecimal quantity, BigDecimal price) {
        Transaction txn = new Transaction();
        txn.setDate(LocalDate.now());
        txn.setTime(LocalTime.of(10, 30, 0));
        txn.setPortfolioId(portfolioId);
        txn.setSequenceNo(seqNo);
        txn.setInvestmentId(investmentId);
        txn.setType(type);
        txn.setQuantity(quantity);
        txn.setPrice(price);
        txn.setStatus("P");
        txn.setCurrency("USD");
        return txn;
    }
}
