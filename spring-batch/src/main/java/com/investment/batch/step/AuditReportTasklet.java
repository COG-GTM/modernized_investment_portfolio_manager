package com.investment.batch.step;

import com.investment.batch.entity.TransactionHistory;
import com.investment.batch.model.AuditReportEntry;
import com.investment.batch.repository.TransactionHistoryRepository;
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
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Tasklet implementing COBOL RPTAUD00 - Audit Report Generator.
 * Generates comprehensive audit reports including security audit trails,
 * process audit reporting, error summary, and control verification.
 */
public class AuditReportTasklet implements Tasklet {

    private static final Logger log = LoggerFactory.getLogger(AuditReportTasklet.class);

    private final TransactionHistoryRepository transactionHistoryRepository;
    private final List<String> reportLines = new ArrayList<>();

    public AuditReportTasklet(TransactionHistoryRepository transactionHistoryRepository) {
        this.transactionHistoryRepository = transactionHistoryRepository;
    }

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) throws Exception {
        log.info("Generating Audit Report (RPTAUD00)");

        String dateStr = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        List<TransactionHistory> historyRecords = transactionHistoryRepository.findByDateOrdered(dateStr);

        // Write headers (maps to RPTAUD00 1200-WRITE-HEADERS)
        writeHeaders(LocalDate.now());

        // Process audit trail (maps to RPTAUD00 2100-PROCESS-AUDIT-TRAIL)
        reportLines.add("SECTION: AUDIT TRAIL");
        reportLines.add(String.format("%-26s %-8s %-10s %-10s %s",
                "TIMESTAMP", "PROGRAM", "TYPE", "ACTION", "PORTFOLIO"));
        reportLines.add(String.format("%s", "-".repeat(100)));

        int auditCount = 0;
        Map<String, Long> actionCounts = historyRecords.stream()
                .collect(Collectors.groupingBy(
                        h -> h.getActionCode() != null ? h.getActionCode() : "?",
                        Collectors.counting()));

        for (TransactionHistory history : historyRecords) {
            AuditReportEntry entry = new AuditReportEntry();
            entry.setTimestamp(history.getDate() + " " + history.getTime());
            entry.setProgram(history.getProcessUser());
            entry.setAuditType(history.getRecordType());
            entry.setPortfolioId(history.getPortfolioId());
            entry.setActionCode(history.getActionCode());

            reportLines.add(String.format("%-26s %-8s %-10s %-10s %s",
                    entry.getTimestamp(), nullSafe(entry.getProgram()),
                    nullSafe(entry.getAuditType()), nullSafe(entry.getActionCode()),
                    nullSafe(entry.getPortfolioId())));
            auditCount++;
        }

        // Write summary (maps to RPTAUD00 2300-WRITE-SUMMARY)
        writeSummary(auditCount, actionCounts);

        contribution.incrementReadCount();
        contribution.incrementWriteCount(1);

        log.info("Audit Report generated: {} audit records", auditCount);
        return RepeatStatus.FINISHED;
    }

    private void writeHeaders(LocalDate reportDate) {
        reportLines.add(String.format("%s", "*".repeat(132)));
        reportLines.add(String.format("%40s%s", "", "SYSTEM AUDIT REPORT"));
        reportLines.add(String.format("REPORT DATE: %s", reportDate.format(DateTimeFormatter.ISO_LOCAL_DATE)));
        reportLines.add(String.format("%s", "-".repeat(132)));
    }

    private void writeSummary(int auditCount, Map<String, Long> actionCounts) {
        reportLines.add(String.format("%s", "-".repeat(100)));
        reportLines.add("AUDIT SUMMARY");
        reportLines.add(String.format("Total Audit Records: %d", auditCount));
        for (Map.Entry<String, Long> entry : actionCounts.entrySet()) {
            String actionName = switch (entry.getKey()) {
                case "A" -> "Add";
                case "C" -> "Change";
                case "D" -> "Delete";
                default -> "Unknown";
            };
            reportLines.add(String.format("  %s (%s): %d", actionName, entry.getKey(), entry.getValue()));
        }
        reportLines.add(String.format("%s", "*".repeat(132)));
    }

    private String nullSafe(String value) {
        return value != null ? value : "";
    }

    public List<String> getReportLines() {
        return reportLines;
    }
}
