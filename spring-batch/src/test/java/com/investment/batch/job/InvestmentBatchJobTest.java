package com.investment.batch.job;

import com.investment.batch.entity.Portfolio;
import com.investment.batch.entity.Transaction;
import com.investment.batch.repository.BatchJobControlRepository;
import com.investment.batch.repository.PortfolioRepository;
import com.investment.batch.repository.PositionRepository;
import com.investment.batch.repository.TransactionHistoryRepository;
import com.investment.batch.repository.TransactionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.test.JobLauncherTestUtils;
import org.springframework.batch.test.context.SpringBatchTest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Integration test for the investment batch pipeline steps.
 * Tests the complete flow: TRNVAL00 -> POSUPD00 -> HISTLD00 -> Reports
 * Uses test data patterns from documentation/operations/test-data-specs.md.
 */
@SpringBatchTest
@SpringBootTest
@ActiveProfiles("test")
class InvestmentBatchJobTest {

    @Autowired
    private JobLauncherTestUtils jobLauncherTestUtils;

    @Autowired
    private Job investmentBatchJob;

    @Autowired
    private PortfolioRepository portfolioRepository;

    @Autowired
    private TransactionRepository transactionRepository;

    @Autowired
    private PositionRepository positionRepository;

    @Autowired
    private TransactionHistoryRepository transactionHistoryRepository;

    @Autowired
    private BatchJobControlRepository batchJobControlRepository;

    @BeforeEach
    void setUp() {
        // Clean up in correct order
        batchJobControlRepository.deleteAll();
        transactionHistoryRepository.deleteAll();
        positionRepository.deleteAll();
        transactionRepository.deleteAll();
        portfolioRepository.deleteAll();

        // Set up the job for testing
        jobLauncherTestUtils.setJob(investmentBatchJob);

        // Create test portfolios (from test-data-specs.md)
        createTestPortfolio("PORT0001", "1234567890", "GROWTH PORTFOLIO", "I", "A");
        createTestPortfolio("PORT0002", "9876543210", "INCOME PORTFOLIO", "I", "A");
        createTestPortfolio("PORT0003", "5555555555", "BALANCED PORTFOLIO", "C", "A");
    }

    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    void testTransactionValidationStep() throws Exception {
        // Create a valid and an invalid transaction
        createTestTransaction("PORT0001", "000001", "IBM0000001", "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"), "USD");

        // Invalid: missing investment ID for buy
        Transaction invalid = new Transaction();
        invalid.setDate(LocalDate.now());
        invalid.setTime(LocalTime.of(10, 30, 0));
        invalid.setPortfolioId("PORT0001");
        invalid.setSequenceNo("000002");
        invalid.setType("BU");
        invalid.setQuantity(new BigDecimal("50.0000"));
        invalid.setPrice(new BigDecimal("100.0000"));
        invalid.setStatus("P");
        invalid.setCurrency("USD");
        transactionRepository.save(invalid);

        JobExecution stepExecution = jobLauncherTestUtils.launchStep("transactionValidationStep",
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());

        assertEquals(BatchStatus.COMPLETED, stepExecution.getStatus());

        long done = transactionRepository.countByDateAndStatus(LocalDate.now(), "D");
        long failed = transactionRepository.countByDateAndStatus(LocalDate.now(), "F");
        assertTrue(done >= 1, "Expected at least one validated transaction");
        assertTrue(failed >= 1, "Expected at least one failed transaction");
    }

    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    void testPositionUpdateStep() throws Exception {
        createValidatedTransaction("PORT0001", "000001", "IBM0000001", "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"),
                new BigDecimal("12500.00"), "USD");

        JobExecution stepExecution = jobLauncherTestUtils.launchStep("positionUpdateStep",
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());

        assertEquals(BatchStatus.COMPLETED, stepExecution.getStatus());

        var positions = positionRepository.findByPortfolioId("PORT0001");
        assertTrue(positions.size() > 0, "Expected position for PORT0001");
    }

    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    void testHistoryLoadStep() throws Exception {
        createValidatedTransaction("PORT0001", "000001", "IBM0000001", "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"),
                new BigDecimal("12500.00"), "USD");

        JobExecution stepExecution = jobLauncherTestUtils.launchStep("historyLoadStep",
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());

        assertEquals(BatchStatus.COMPLETED, stepExecution.getStatus());

        assertTrue(transactionHistoryRepository.count() > 0,
                "Expected history records to be created");
    }

    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    void testPositionReportStep() throws Exception {
        JobExecution stepExecution = jobLauncherTestUtils.launchStep("positionReportStep",
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());
        assertEquals(BatchStatus.COMPLETED, stepExecution.getStatus());
    }

    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    void testAuditReportStep() throws Exception {
        JobExecution stepExecution = jobLauncherTestUtils.launchStep("auditReportStep",
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());
        assertEquals(BatchStatus.COMPLETED, stepExecution.getStatus());
    }

    @Test
    @Timeout(value = 30, unit = TimeUnit.SECONDS)
    void testStatisticsReportStep() throws Exception {
        JobExecution stepExecution = jobLauncherTestUtils.launchStep("statisticsReportStep",
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());
        assertEquals(BatchStatus.COMPLETED, stepExecution.getStatus());
    }

    @Test
    @Timeout(value = 60, unit = TimeUnit.SECONDS)
    void testFullBatchPipeline() throws Exception {
        // Create pending BUY transactions (from test-data-specs.md patterns)
        createTestTransaction("PORT0001", "000001", "IBM0000001", "BU",
                new BigDecimal("100.0000"), new BigDecimal("125.0000"), "USD");
        createTestTransaction("PORT0002", "000001", "MSFT000001", "BU",
                new BigDecimal("50.0000"), new BigDecimal("100.0000"), "USD");
        createTestTransaction("PORT0003", "000001", "AAPL000001", "BU",
                new BigDecimal("75.0000"), new BigDecimal("150.0000"), "USD");

        JobExecution jobExecution = jobLauncherTestUtils.launchJob(
                new JobParametersBuilder()
                        .addString("processDate", LocalDate.now().toString())
                        .addLong("run.id", System.currentTimeMillis())
                        .toJobParameters());

        // Wait for async completion
        while (jobExecution.isRunning()) {
            Thread.sleep(200);
        }

        assertEquals(BatchStatus.COMPLETED, jobExecution.getStatus(),
                "Job should complete. Exit: " + jobExecution.getExitStatus().getExitCode());

        long doneTransactions = transactionRepository.countByDateAndStatus(LocalDate.now(), "D");
        assertTrue(doneTransactions > 0, "Expected validated transactions");
        assertTrue(positionRepository.count() > 0, "Expected positions to be created");
        assertTrue(transactionHistoryRepository.count() > 0, "Expected history records");
        assertTrue(batchJobControlRepository.count() > 0, "Expected batch control records");
    }

    // ===== Helper Methods =====

    private void createTestPortfolio(String portId, String accountNo, String name, String type, String status) {
        Portfolio portfolio = new Portfolio();
        portfolio.setPortId(portId);
        portfolio.setAccountNo(accountNo);
        portfolio.setClientName(name);
        portfolio.setClientType(type);
        portfolio.setCreateDate(LocalDate.now());
        portfolio.setStatus(status);
        portfolio.setTotalValue(BigDecimal.ZERO);
        portfolio.setCashBalance(BigDecimal.ZERO);
        portfolioRepository.save(portfolio);
    }

    private void createTestTransaction(String portfolioId, String seqNo, String investmentId,
                                        String type, BigDecimal quantity, BigDecimal price, String currency) {
        Transaction txn = new Transaction();
        txn.setDate(LocalDate.now());
        txn.setTime(LocalTime.now());
        txn.setPortfolioId(portfolioId);
        txn.setSequenceNo(seqNo);
        txn.setInvestmentId(investmentId);
        txn.setType(type);
        txn.setQuantity(quantity);
        txn.setPrice(price);
        txn.setAmount(quantity.multiply(price));
        txn.setCurrency(currency);
        txn.setStatus("P");
        transactionRepository.save(txn);
    }

    private void createValidatedTransaction(String portfolioId, String seqNo, String investmentId,
                                             String type, BigDecimal quantity, BigDecimal price,
                                             BigDecimal amount, String currency) {
        Transaction txn = new Transaction();
        txn.setDate(LocalDate.now());
        txn.setTime(LocalTime.now());
        txn.setPortfolioId(portfolioId);
        txn.setSequenceNo(seqNo);
        txn.setInvestmentId(investmentId);
        txn.setType(type);
        txn.setQuantity(quantity);
        txn.setPrice(price);
        txn.setAmount(amount);
        txn.setCurrency(currency);
        txn.setStatus("D");
        txn.setProcessDate(LocalDateTime.now());
        txn.setProcessUser("TRNVAL00");
        transactionRepository.save(txn);
    }
}
