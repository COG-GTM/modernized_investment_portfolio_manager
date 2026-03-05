package com.investment.batch.listener;

import com.investment.batch.entity.BatchJobControl;
import com.investment.batch.service.BatchControlService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.ExitStatus;
import org.springframework.batch.core.StepExecution;
import org.springframework.batch.core.StepExecutionListener;

import java.time.LocalDate;

/**
 * Step-level listener that tracks execution metrics and implements
 * the RC <= 4 conditional progression from the COBOL batch flow.
 * Maps to COBOL return code checking and checkpoint update logic.
 */
public class StepExecutionReportListener implements StepExecutionListener {

    private static final Logger log = LoggerFactory.getLogger(StepExecutionReportListener.class);

    private final BatchControlService batchControlService;
    private final String stepJobName;
    private final int maxReturnCode;

    public StepExecutionReportListener(BatchControlService batchControlService, String stepJobName, int maxReturnCode) {
        this.batchControlService = batchControlService;
        this.stepJobName = stepJobName;
        this.maxReturnCode = maxReturnCode;
    }

    @Override
    public void beforeStep(StepExecution stepExecution) {
        log.info("--- Starting step: {} (maps to COBOL {}) ---", stepExecution.getStepName(), stepJobName);
        batchControlService.initializeJob(stepJobName, LocalDate.now(), 0);
    }

    @Override
    public ExitStatus afterStep(StepExecution stepExecution) {
        long readCount = stepExecution.getReadCount();
        long writeCount = stepExecution.getWriteCount();
        long errorCount = stepExecution.getProcessSkipCount() + stepExecution.getWriteSkipCount();

        int returnCode = calculateReturnCode(stepExecution);

        batchControlService.completeJob(stepJobName, LocalDate.now(), 0,
                returnCode, readCount, writeCount, errorCount);

        log.info("--- Step completed: {} | RC={} | Read={} | Written={} | Errors={} ---",
                stepExecution.getStepName(), returnCode, readCount, writeCount, errorCount);

        // Implement RC <= maxReturnCode conditional progression
        if (returnCode > maxReturnCode) {
            log.error("Step {} exceeded max return code ({} > {}). Stopping pipeline.",
                    stepExecution.getStepName(), returnCode, maxReturnCode);
            return new ExitStatus("FAILED_RC");
        }

        return stepExecution.getExitStatus();
    }

    private int calculateReturnCode(StepExecution stepExecution) {
        if (stepExecution.getStatus().isUnsuccessful()) {
            return BatchJobControl.RC_ERROR;
        }
        long errors = stepExecution.getProcessSkipCount() + stepExecution.getWriteSkipCount();
        if (errors > 0) {
            return BatchJobControl.RC_WARNING;
        }
        return BatchJobControl.RC_SUCCESS;
    }
}
