package com.investment.batch.config;

import com.investment.batch.entity.Position;
import com.investment.batch.entity.Transaction;
import com.investment.batch.entity.TransactionHistory;
import com.investment.batch.listener.BatchJobListener;
import com.investment.batch.listener.StepExecutionReportListener;
import com.investment.batch.processor.HistoryLoadProcessor;
import com.investment.batch.processor.PositionUpdateProcessor;
import com.investment.batch.processor.TransactionValidationProcessor;
import com.investment.batch.repository.BatchJobControlRepository;
import com.investment.batch.repository.PositionRepository;
import com.investment.batch.repository.TransactionHistoryRepository;
import com.investment.batch.repository.TransactionRepository;
import com.investment.batch.service.BatchControlService;
import com.investment.batch.service.TransactionValidationService;
import com.investment.batch.step.AuditReportTasklet;
import com.investment.batch.step.PositionReportTasklet;
import com.investment.batch.step.StatisticsReportTasklet;
import jakarta.persistence.EntityManagerFactory;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.job.builder.FlowBuilder;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.job.flow.Flow;
import org.springframework.batch.core.job.flow.support.SimpleFlow;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.database.JpaCursorItemReader;
import org.springframework.batch.item.database.JpaItemWriter;
import org.springframework.batch.item.database.JpaPagingItemReader;
import org.springframework.batch.item.database.builder.JpaCursorItemReaderBuilder;
import org.springframework.batch.item.database.builder.JpaItemWriterBuilder;
import org.springframework.batch.item.database.builder.JpaPagingItemReaderBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

/**
 * Main Spring Batch configuration.
 * Implements the COBOL batch pipeline:
 *   Start of Day -> TRNVAL00 (RC<=4) -> POSUPD00 (RC<=4) -> HISTLD00 (RC<=4) -> Reports -> End of Day
 */
@Configuration
public class BatchConfiguration {

    @Value("${batch.chunk-size:100}")
    private int chunkSize;

    @Value("${batch.max-return-code:4}")
    private int maxReturnCode;

    // =====================================================
    // JOB DEFINITION
    // =====================================================

    @Bean
    public Job investmentBatchJob(JobRepository jobRepository,
                                   BatchControlService batchControlService,
                                   Step transactionValidationStep,
                                   Step positionUpdateStep,
                                   Step historyLoadStep,
                                   Step positionReportStep,
                                   Step auditReportStep,
                                   Step statisticsReportStep) {

        // Build the flow with conditional progression (RC <= 4)
        // Each step's StepExecutionReportListener sets exit status to FAILED_RC
        // when the return code exceeds maxReturnCode, which stops the pipeline.
        Flow batchFlow = new FlowBuilder<SimpleFlow>("investmentBatchFlow")
                .start(transactionValidationStep)
                .on("FAILED_RC").fail()
                .from(transactionValidationStep).on("*").to(positionUpdateStep)
                .from(positionUpdateStep).on("FAILED_RC").fail()
                .from(positionUpdateStep).on("*").to(historyLoadStep)
                .from(historyLoadStep).on("FAILED_RC").fail()
                .from(historyLoadStep).on("*").to(positionReportStep)
                .from(positionReportStep).next(auditReportStep)
                .next(statisticsReportStep)
                .end();

        return new JobBuilder("investmentBatchJob", jobRepository)
                .listener(new BatchJobListener(batchControlService))
                .start(batchFlow)
                .end()
                .build();
    }

    // =====================================================
    // STEP 1: TRANSACTION VALIDATION (TRNVAL00)
    // =====================================================

    @Bean
    public JpaCursorItemReader<Transaction> pendingTransactionReader(EntityManagerFactory entityManagerFactory) {
        return new JpaCursorItemReaderBuilder<Transaction>()
                .name("pendingTransactionReader")
                .entityManagerFactory(entityManagerFactory)
                .queryString("SELECT t FROM Transaction t WHERE t.status = 'P' ORDER BY t.date, t.time, t.sequenceNo")
                .build();
    }

    @Bean
    public TransactionValidationProcessor transactionValidationProcessor(
            TransactionValidationService validationService) {
        return new TransactionValidationProcessor(validationService);
    }

    @Bean
    public JpaItemWriter<Transaction> transactionWriter(EntityManagerFactory entityManagerFactory) {
        return new JpaItemWriterBuilder<Transaction>()
                .entityManagerFactory(entityManagerFactory)
                .build();
    }

    @Bean
    public Step transactionValidationStep(JobRepository jobRepository,
                                           PlatformTransactionManager transactionManager,
                                           JpaCursorItemReader<Transaction> pendingTransactionReader,
                                           TransactionValidationProcessor transactionValidationProcessor,
                                           JpaItemWriter<Transaction> transactionWriter,
                                           BatchControlService batchControlService) {
        return new StepBuilder("transactionValidationStep", jobRepository)
                .<Transaction, Transaction>chunk(chunkSize, transactionManager)
                .reader(pendingTransactionReader)
                .processor(transactionValidationProcessor)
                .writer(transactionWriter)
                .listener(new StepExecutionReportListener(batchControlService, "TRNVAL00", maxReturnCode))
                .build();
    }

    // =====================================================
    // STEP 2: POSITION UPDATE (POSUPD00)
    // =====================================================

    @Bean
    public JpaPagingItemReader<Transaction> validatedTransactionReader(EntityManagerFactory entityManagerFactory) {
        return new JpaPagingItemReaderBuilder<Transaction>()
                .name("validatedTransactionReader")
                .entityManagerFactory(entityManagerFactory)
                .queryString("SELECT t FROM Transaction t WHERE t.status = 'D' ORDER BY t.date, t.time, t.sequenceNo")
                .pageSize(chunkSize)
                .build();
    }

    @Bean
    public PositionUpdateProcessor positionUpdateProcessor(PositionRepository positionRepository) {
        return new PositionUpdateProcessor(positionRepository);
    }

    @Bean
    public JpaItemWriter<Position> positionWriter(EntityManagerFactory entityManagerFactory) {
        return new JpaItemWriterBuilder<Position>()
                .entityManagerFactory(entityManagerFactory)
                .build();
    }

    @Bean
    public Step positionUpdateStep(JobRepository jobRepository,
                                    PlatformTransactionManager transactionManager,
                                    JpaPagingItemReader<Transaction> validatedTransactionReader,
                                    PositionUpdateProcessor positionUpdateProcessor,
                                    JpaItemWriter<Position> positionWriter,
                                    BatchControlService batchControlService) {
        return new StepBuilder("positionUpdateStep", jobRepository)
                .<Transaction, Position>chunk(chunkSize, transactionManager)
                .reader(validatedTransactionReader)
                .processor(positionUpdateProcessor)
                .writer(positionWriter)
                .listener(new StepExecutionReportListener(batchControlService, "POSUPD00", maxReturnCode))
                .build();
    }

    // =====================================================
    // STEP 3: HISTORY LOAD (HISTLD00)
    // =====================================================

    @Bean
    public JpaPagingItemReader<Transaction> historyTransactionReader(EntityManagerFactory entityManagerFactory) {
        return new JpaPagingItemReaderBuilder<Transaction>()
                .name("historyTransactionReader")
                .entityManagerFactory(entityManagerFactory)
                .queryString("SELECT t FROM Transaction t WHERE t.status = 'D' ORDER BY t.date, t.time, t.sequenceNo")
                .pageSize(chunkSize)
                .build();
    }

    @Bean
    public HistoryLoadProcessor historyLoadProcessor() {
        return new HistoryLoadProcessor();
    }

    @Bean
    public JpaItemWriter<TransactionHistory> historyWriter(EntityManagerFactory entityManagerFactory) {
        return new JpaItemWriterBuilder<TransactionHistory>()
                .entityManagerFactory(entityManagerFactory)
                .build();
    }

    @Bean
    public Step historyLoadStep(JobRepository jobRepository,
                                 PlatformTransactionManager transactionManager,
                                 JpaPagingItemReader<Transaction> historyTransactionReader,
                                 HistoryLoadProcessor historyLoadProcessor,
                                 JpaItemWriter<TransactionHistory> historyWriter,
                                 BatchControlService batchControlService) {
        return new StepBuilder("historyLoadStep", jobRepository)
                .<Transaction, TransactionHistory>chunk(chunkSize, transactionManager)
                .reader(historyTransactionReader)
                .processor(historyLoadProcessor)
                .writer(historyWriter)
                .listener(new StepExecutionReportListener(batchControlService, "HISTLD00", maxReturnCode))
                .build();
    }

    // =====================================================
    // STEP 4: POSITION REPORT (RPTPOS00)
    // =====================================================

    @Bean
    public Step positionReportStep(JobRepository jobRepository,
                                    PlatformTransactionManager transactionManager,
                                    PositionRepository positionRepository,
                                    BatchControlService batchControlService) {
        return new StepBuilder("positionReportStep", jobRepository)
                .tasklet(new PositionReportTasklet(positionRepository), transactionManager)
                .listener(new StepExecutionReportListener(batchControlService, "RPTPOS00", maxReturnCode))
                .build();
    }

    // =====================================================
    // STEP 5: AUDIT REPORT (RPTAUD00)
    // =====================================================

    @Bean
    public Step auditReportStep(JobRepository jobRepository,
                                 PlatformTransactionManager transactionManager,
                                 TransactionHistoryRepository transactionHistoryRepository,
                                 BatchControlService batchControlService) {
        return new StepBuilder("auditReportStep", jobRepository)
                .tasklet(new AuditReportTasklet(transactionHistoryRepository), transactionManager)
                .listener(new StepExecutionReportListener(batchControlService, "RPTAUD00", maxReturnCode))
                .build();
    }

    // =====================================================
    // STEP 6: STATISTICS REPORT (RPTSTA00)
    // =====================================================

    @Bean
    public Step statisticsReportStep(JobRepository jobRepository,
                                      PlatformTransactionManager transactionManager,
                                      BatchJobControlRepository batchJobControlRepository,
                                      TransactionRepository transactionRepository,
                                      TransactionHistoryRepository transactionHistoryRepository,
                                      BatchControlService batchControlService) {
        return new StepBuilder("statisticsReportStep", jobRepository)
                .tasklet(new StatisticsReportTasklet(batchJobControlRepository, transactionRepository,
                        transactionHistoryRepository), transactionManager)
                .listener(new StepExecutionReportListener(batchControlService, "RPTSTA00", maxReturnCode))
                .build();
    }

}
