package com.investment.batch.service;

import com.investment.batch.entity.BatchJobControl;
import com.investment.batch.repository.BatchJobControlRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Optional;

/**
 * Service implementing COBOL BCHCTL00 batch control logic.
 * Manages process dependency, checkpoint/restart capabilities.
 */
@Service
public class BatchControlService {

    private static final Logger log = LoggerFactory.getLogger(BatchControlService.class);

    private final BatchJobControlRepository batchJobControlRepository;

    public BatchControlService(BatchJobControlRepository batchJobControlRepository) {
        this.batchJobControlRepository = batchJobControlRepository;
    }

    /**
     * Initialize a batch control record (BCHCTL00 1000-PROCESS-INITIALIZE).
     */
    @Transactional
    public BatchJobControl initializeJob(String jobName, LocalDate processDate, int sequenceNo) {
        Optional<BatchJobControl> existing = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo(jobName, processDate, sequenceNo);

        if (existing.isPresent()) {
            BatchJobControl control = existing.get();
            if (BatchJobControl.STATUS_ERROR.equals(control.getStatus()) && control.isRestartable()) {
                log.info("Restarting job {} from checkpoint", jobName);
                control.setStatus(BatchJobControl.STATUS_ACTIVE);
                control.setStartTime(LocalDateTime.now());
                control.setRestartCount(control.getRestartCount() + 1);
                return batchJobControlRepository.save(control);
            } else if (BatchJobControl.STATUS_DONE.equals(control.getStatus())) {
                log.info("Job {} already completed for date {}", jobName, processDate);
                return control;
            }
            control.setStatus(BatchJobControl.STATUS_ACTIVE);
            control.setStartTime(LocalDateTime.now());
            return batchJobControlRepository.save(control);
        }

        BatchJobControl control = new BatchJobControl();
        control.setJobName(jobName);
        control.setProcessDate(processDate);
        control.setSequenceNo(sequenceNo);
        control.setStatus(BatchJobControl.STATUS_ACTIVE);
        control.setStartTime(LocalDateTime.now());
        log.info("Initialized batch control for job {} on {}", jobName, processDate);
        return batchJobControlRepository.save(control);
    }

    /**
     * Update checkpoint data (BCHCTL00 3000-UPDATE-STATUS / HISTLD00 2310-UPDATE-CHECKPOINT).
     */
    @Transactional
    public void updateCheckpoint(String jobName, LocalDate processDate, int sequenceNo,
                                  long recordsRead, long recordsWritten, String checkpointData) {
        Optional<BatchJobControl> existing = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo(jobName, processDate, sequenceNo);
        if (existing.isPresent()) {
            BatchJobControl control = existing.get();
            control.setRecordsRead(recordsRead);
            control.setRecordsWritten(recordsWritten);
            control.setCheckpointData(checkpointData);
            control.setUpdatedAt(LocalDateTime.now());
            batchJobControlRepository.save(control);
        }
    }

    /**
     * Complete a job (BCHCTL00 4000-PROCESS-TERMINATE).
     */
    @Transactional
    public void completeJob(String jobName, LocalDate processDate, int sequenceNo,
                            int returnCode, long recordsRead, long recordsWritten, long errorCount) {
        Optional<BatchJobControl> existing = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo(jobName, processDate, sequenceNo);
        if (existing.isPresent()) {
            BatchJobControl control = existing.get();
            control.setStatus(returnCode <= BatchJobControl.RC_WARNING
                    ? BatchJobControl.STATUS_DONE : BatchJobControl.STATUS_ERROR);
            control.setReturnCode(returnCode);
            control.setRecordsRead(recordsRead);
            control.setRecordsWritten(recordsWritten);
            control.setErrorCount(errorCount);
            control.setEndTime(LocalDateTime.now());
            batchJobControlRepository.save(control);
            log.info("Completed job {} with RC={}, read={}, written={}, errors={}",
                    jobName, returnCode, recordsRead, recordsWritten, errorCount);
        }
    }

    /**
     * Check prerequisites (BCHCTL00 2000-CHECK-PREREQUISITES / PRCSEQ00 2200-CHECK-DEPENDENCIES).
     * Returns true if the previous step completed with RC <= maxReturnCode.
     */
    public boolean checkPrerequisites(String dependencyJobName, LocalDate processDate, int maxReturnCode) {
        if (dependencyJobName == null || dependencyJobName.isEmpty()) {
            return true;
        }
        var controls = batchJobControlRepository.findByJobNameAndProcessDate(dependencyJobName, processDate);
        if (controls.isEmpty()) {
            log.warn("No control record found for dependency {}", dependencyJobName);
            return false;
        }
        BatchJobControl latest = controls.get(controls.size() - 1);
        boolean met = BatchJobControl.STATUS_DONE.equals(latest.getStatus())
                && latest.getReturnCode() <= maxReturnCode;
        if (!met) {
            log.warn("Prerequisite not met: {} status={} rc={}",
                    dependencyJobName, latest.getStatus(), latest.getReturnCode());
        }
        return met;
    }

    /**
     * Mark a job as failed with error description.
     */
    @Transactional
    public void failJob(String jobName, LocalDate processDate, int sequenceNo, String errorDesc) {
        Optional<BatchJobControl> existing = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo(jobName, processDate, sequenceNo);
        if (existing.isPresent()) {
            BatchJobControl control = existing.get();
            control.setStatus(BatchJobControl.STATUS_ERROR);
            control.setReturnCode(BatchJobControl.RC_ERROR);
            control.setErrorDesc(errorDesc);
            control.setEndTime(LocalDateTime.now());
            batchJobControlRepository.save(control);
            log.error("Job {} failed: {}", jobName, errorDesc);
        }
    }
}
