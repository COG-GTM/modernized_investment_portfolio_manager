package com.investment.batch.listener;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.StepExecution;
import org.springframework.batch.core.job.flow.FlowExecutionStatus;
import org.springframework.batch.core.job.flow.JobExecutionDecider;

/**
 * Job execution decider implementing COBOL RC <= 4 conditional progression.
 * Maps to the batch flow: TRNVAL00 (RC<=4) -> POSUPD00 (RC<=4) -> HISTLD00 (RC<=4) -> Reports
 */
public class ReturnCodeDecider implements JobExecutionDecider {

    private static final Logger log = LoggerFactory.getLogger(ReturnCodeDecider.class);

    private static final String STATUS_CONTINUE = "CONTINUE";
    private static final String STATUS_STOP = "STOP";

    private final int maxReturnCode;

    public ReturnCodeDecider(int maxReturnCode) {
        this.maxReturnCode = maxReturnCode;
    }

    @Override
    public FlowExecutionStatus decide(JobExecution jobExecution, StepExecution stepExecution) {
        if (stepExecution == null) {
            log.warn("No step execution available for decision");
            return new FlowExecutionStatus(STATUS_CONTINUE);
        }

        String exitCode = stepExecution.getExitStatus().getExitCode();

        if ("FAILED_RC".equals(exitCode) || "FAILED".equals(exitCode)) {
            log.error("Step {} failed with exit code {}. Pipeline will stop.",
                    stepExecution.getStepName(), exitCode);
            return new FlowExecutionStatus(STATUS_STOP);
        }

        log.info("Step {} completed with exit code {}. Pipeline will continue.",
                stepExecution.getStepName(), exitCode);
        return new FlowExecutionStatus(STATUS_CONTINUE);
    }
}
