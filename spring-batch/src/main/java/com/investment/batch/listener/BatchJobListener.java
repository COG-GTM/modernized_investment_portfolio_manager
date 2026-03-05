package com.investment.batch.listener;

import com.investment.batch.service.BatchControlService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobExecutionListener;

import java.time.LocalDate;

/**
 * Job-level listener implementing Start of Day / End of Day logic.
 * Maps to COBOL batch control flow initialization and termination.
 */
public class BatchJobListener implements JobExecutionListener {

    private static final Logger log = LoggerFactory.getLogger(BatchJobListener.class);

    private final BatchControlService batchControlService;

    public BatchJobListener(BatchControlService batchControlService) {
        this.batchControlService = batchControlService;
    }

    @Override
    public void beforeJob(JobExecution jobExecution) {
        log.info("========================================");
        log.info("START OF DAY - Investment Batch Pipeline");
        log.info("Job: {}", jobExecution.getJobInstance().getJobName());
        log.info("Process Date: {}", LocalDate.now());
        log.info("========================================");
    }

    @Override
    public void afterJob(JobExecution jobExecution) {
        log.info("========================================");
        log.info("END OF DAY - Investment Batch Pipeline");
        log.info("Job: {}", jobExecution.getJobInstance().getJobName());
        log.info("Status: {}", jobExecution.getStatus());
        log.info("Exit Status: {}", jobExecution.getExitStatus().getExitCode());
        log.info("Duration: {} ms",
                jobExecution.getEndTime() != null && jobExecution.getStartTime() != null
                        ? java.time.Duration.between(jobExecution.getStartTime(), jobExecution.getEndTime()).toMillis()
                        : "N/A");
        log.info("========================================");
    }
}
