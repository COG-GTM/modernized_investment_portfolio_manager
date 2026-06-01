package com.investment.batch.step;

import com.investment.batch.entity.BatchJobControl;
import com.investment.batch.model.StatisticsReportEntry;
import com.investment.batch.repository.BatchJobControlRepository;
import com.investment.batch.repository.TransactionHistoryRepository;
import com.investment.batch.repository.TransactionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.StepContribution;
import org.springframework.batch.core.scope.context.ChunkContext;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.repeat.RepeatStatus;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Tasklet implementing COBOL RPTSTA00 - Statistics Report Generator.
 * Generates system performance and statistics reports including
 * processing statistics, performance metrics, resource utilization, and trend analysis.
 */
public class StatisticsReportTasklet implements Tasklet {

    private static final Logger log = LoggerFactory.getLogger(StatisticsReportTasklet.class);

    private final BatchJobControlRepository batchJobControlRepository;
    private final TransactionRepository transactionRepository;
    private final TransactionHistoryRepository transactionHistoryRepository;
    private final List<String> reportLines = new ArrayList<>();

    public StatisticsReportTasklet(BatchJobControlRepository batchJobControlRepository,
                                    TransactionRepository transactionRepository,
                                    TransactionHistoryRepository transactionHistoryRepository) {
        this.batchJobControlRepository = batchJobControlRepository;
        this.transactionRepository = transactionRepository;
        this.transactionHistoryRepository = transactionHistoryRepository;
    }

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) throws Exception {
        log.info("Generating Statistics Report (RPTSTA00)");

        LocalDate reportDate = LocalDate.now();

        // Write headers (maps to RPTSTA00 1200-WRITE-HEADERS)
        writeHeaders(reportDate);

        // Process batch stats (maps to RPTSTA00 2200-PROCESS-BATCH-STATS)
        List<BatchJobControl> batchJobs = batchJobControlRepository.findByProcessDate(reportDate);
        StatisticsReportEntry batchEntry = new StatisticsReportEntry();
        batchEntry.setMetricName("Batch Processing");
        batchEntry.setTotalCount(batchJobs.size());
        batchEntry.setSuccessCount(batchJobs.stream()
                .filter(j -> BatchJobControl.STATUS_DONE.equals(j.getStatus())).count());
        batchEntry.setFailureCount(batchJobs.stream()
                .filter(j -> BatchJobControl.STATUS_ERROR.equals(j.getStatus())).count());
        batchEntry.calculateSuccessRate();

        long totalRead = batchJobs.stream().mapToLong(BatchJobControl::getRecordsRead).sum();
        long totalWritten = batchJobs.stream().mapToLong(BatchJobControl::getRecordsWritten).sum();
        batchEntry.setTotalRecordsProcessed(totalRead + totalWritten);

        // Process transaction stats
        long pendingTxns = transactionRepository.countByDateAndStatus(reportDate, "P");
        long completedTxns = transactionRepository.countByDateAndStatus(reportDate, "D");
        long failedTxns = transactionRepository.countByDateAndStatus(reportDate, "F");

        StatisticsReportEntry txnEntry = new StatisticsReportEntry();
        txnEntry.setMetricName("Transaction Processing");
        txnEntry.setTotalCount(pendingTxns + completedTxns + failedTxns);
        txnEntry.setSuccessCount(completedTxns);
        txnEntry.setFailureCount(failedTxns);
        txnEntry.calculateSuccessRate();

        // Process history stats
        String dateStr = reportDate.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        long historyCount = transactionHistoryRepository.countByDate(dateStr);

        StatisticsReportEntry histEntry = new StatisticsReportEntry();
        histEntry.setMetricName("History Records Loaded");
        histEntry.setTotalCount(historyCount);
        histEntry.setSuccessCount(historyCount);
        histEntry.setFailureCount(0);
        histEntry.calculateSuccessRate();

        // Write report sections
        writeSection("BATCH PROCESSING STATISTICS", batchEntry, batchJobs);
        writeSection("TRANSACTION PROCESSING STATISTICS", txnEntry, null);
        writeSection("HISTORY LOAD STATISTICS", histEntry, null);

        // Write footer
        reportLines.add(String.format("%s", "-".repeat(132)));
        reportLines.add(String.format("Total Records Processed: %,d", totalRead + totalWritten));
        reportLines.add(String.format("%s", "*".repeat(132)));

        contribution.incrementReadCount();
        contribution.incrementWriteCount(1);

        log.info("Statistics Report generated: {} batch jobs, {} transactions, {} history records",
                batchJobs.size(), txnEntry.getTotalCount(), historyCount);
        return RepeatStatus.FINISHED;
    }

    private void writeHeaders(LocalDate reportDate) {
        reportLines.add(String.format("%s", "*".repeat(132)));
        reportLines.add(String.format("%35s%s", "", "SYSTEM STATISTICS AND PERFORMANCE REPORT"));
        reportLines.add(String.format("REPORT DATE: %s", reportDate.format(DateTimeFormatter.ISO_LOCAL_DATE)));
        reportLines.add(String.format("%s", "-".repeat(132)));
    }

    private void writeSection(String sectionTitle, StatisticsReportEntry entry,
                               List<BatchJobControl> jobs) {
        reportLines.add("");
        reportLines.add(sectionTitle);
        reportLines.add(String.format("%s", "-".repeat(80)));
        reportLines.add(entry.toString());

        if (jobs != null) {
            reportLines.add("");
            reportLines.add(String.format("  %-20s %-16s %6s %10s %10s %10s",
                    "JOB NAME", "STATUS", "RC", "READ", "WRITTEN", "ERRORS"));
            for (BatchJobControl job : jobs) {
                reportLines.add(String.format("  %-20s %-16s %6d %,10d %,10d %,10d",
                        job.getJobName(), job.getStatus(), job.getReturnCode(),
                        job.getRecordsRead(), job.getRecordsWritten(), job.getErrorCount()));
            }
        }
    }

    public List<String> getReportLines() {
        return reportLines;
    }
}
