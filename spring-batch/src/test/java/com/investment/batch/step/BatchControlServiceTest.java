package com.investment.batch.step;

import com.investment.batch.entity.BatchJobControl;
import com.investment.batch.repository.BatchJobControlRepository;
import com.investment.batch.service.BatchControlService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDate;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Tests for BatchControlService (BCHCTL00 equivalent).
 * Validates process dependency management and checkpoint/restart.
 */
@SpringBootTest
@ActiveProfiles("test")
class BatchControlServiceTest {

    @Autowired
    private BatchControlService batchControlService;

    @Autowired
    private BatchJobControlRepository batchJobControlRepository;

    @BeforeEach
    void setUp() {
        batchJobControlRepository.deleteAll();
    }

    @Test
    void testInitializeJob() {
        BatchJobControl control = batchControlService.initializeJob("TRNVAL00", LocalDate.now(), 0);

        assertNotNull(control);
        assertNotNull(control.getId());
        assertEquals("TRNVAL00", control.getJobName());
        assertEquals(BatchJobControl.STATUS_ACTIVE, control.getStatus());
        assertNotNull(control.getStartTime());
    }

    @Test
    void testCompleteJobSuccess() {
        batchControlService.initializeJob("TRNVAL00", LocalDate.now(), 0);
        batchControlService.completeJob("TRNVAL00", LocalDate.now(), 0, 0, 100, 95, 5);

        Optional<BatchJobControl> completed = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo("TRNVAL00", LocalDate.now(), 0);

        assertTrue(completed.isPresent());
        assertEquals(BatchJobControl.STATUS_DONE, completed.get().getStatus());
        assertEquals(0, completed.get().getReturnCode());
        assertEquals(100, completed.get().getRecordsRead());
        assertEquals(95, completed.get().getRecordsWritten());
        assertEquals(5, completed.get().getErrorCount());
    }

    @Test
    void testCompleteJobWithWarning() {
        batchControlService.initializeJob("POSUPD00", LocalDate.now(), 0);
        batchControlService.completeJob("POSUPD00", LocalDate.now(), 0, 4, 50, 48, 2);

        Optional<BatchJobControl> completed = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo("POSUPD00", LocalDate.now(), 0);

        assertTrue(completed.isPresent());
        assertEquals(BatchJobControl.STATUS_DONE, completed.get().getStatus());
        assertEquals(4, completed.get().getReturnCode());
    }

    @Test
    void testCompleteJobWithError() {
        batchControlService.initializeJob("HISTLD00", LocalDate.now(), 0);
        batchControlService.completeJob("HISTLD00", LocalDate.now(), 0, 8, 100, 0, 100);

        Optional<BatchJobControl> completed = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo("HISTLD00", LocalDate.now(), 0);

        assertTrue(completed.isPresent());
        assertEquals(BatchJobControl.STATUS_ERROR, completed.get().getStatus());
        assertEquals(8, completed.get().getReturnCode());
    }

    @Test
    void testCheckPrerequisitesMet() {
        batchControlService.initializeJob("TRNVAL00", LocalDate.now(), 0);
        batchControlService.completeJob("TRNVAL00", LocalDate.now(), 0, 0, 100, 100, 0);

        boolean met = batchControlService.checkPrerequisites("TRNVAL00", LocalDate.now(), 4);
        assertTrue(met, "Prerequisites should be met when RC=0 and status=DONE");
    }

    @Test
    void testCheckPrerequisitesNotMet() {
        batchControlService.initializeJob("TRNVAL00", LocalDate.now(), 0);
        batchControlService.completeJob("TRNVAL00", LocalDate.now(), 0, 8, 100, 0, 100);

        boolean met = batchControlService.checkPrerequisites("TRNVAL00", LocalDate.now(), 4);
        assertFalse(met, "Prerequisites should not be met when RC=8 > maxRC=4");
    }

    @Test
    void testCheckPrerequisitesNoDependency() {
        boolean met = batchControlService.checkPrerequisites(null, LocalDate.now(), 4);
        assertTrue(met, "Null dependency should return true");
    }

    @Test
    void testUpdateCheckpoint() {
        batchControlService.initializeJob("HISTLD00", LocalDate.now(), 0);
        batchControlService.updateCheckpoint("HISTLD00", LocalDate.now(), 0, 500, 450, "{\"lastKey\":\"12345\"}");

        Optional<BatchJobControl> updated = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo("HISTLD00", LocalDate.now(), 0);

        assertTrue(updated.isPresent());
        assertEquals(500, updated.get().getRecordsRead());
        assertEquals(450, updated.get().getRecordsWritten());
        assertEquals("{\"lastKey\":\"12345\"}", updated.get().getCheckpointData());
    }

    @Test
    void testFailJob() {
        batchControlService.initializeJob("RPTPOS00", LocalDate.now(), 0);
        batchControlService.failJob("RPTPOS00", LocalDate.now(), 0, "File open error");

        Optional<BatchJobControl> failed = batchJobControlRepository
                .findByJobNameAndProcessDateAndSequenceNo("RPTPOS00", LocalDate.now(), 0);

        assertTrue(failed.isPresent());
        assertEquals(BatchJobControl.STATUS_ERROR, failed.get().getStatus());
        assertEquals(BatchJobControl.RC_ERROR, failed.get().getReturnCode());
        assertEquals("File open error", failed.get().getErrorDesc());
    }

    @Test
    void testRestartAfterFailure() {
        // First run - fails
        batchControlService.initializeJob("TRNVAL00", LocalDate.now(), 0);
        batchControlService.failJob("TRNVAL00", LocalDate.now(), 0, "Connection error");

        // Restart
        BatchJobControl restarted = batchControlService.initializeJob("TRNVAL00", LocalDate.now(), 0);

        assertNotNull(restarted);
        assertEquals(BatchJobControl.STATUS_ACTIVE, restarted.getStatus());
        assertEquals(1, restarted.getRestartCount());
    }
}
