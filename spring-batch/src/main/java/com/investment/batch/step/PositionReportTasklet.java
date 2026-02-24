package com.investment.batch.step;

import com.investment.batch.entity.Position;
import com.investment.batch.model.PositionReportEntry;
import com.investment.batch.repository.PositionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.batch.core.StepContribution;
import org.springframework.batch.core.scope.context.ChunkContext;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.repeat.RepeatStatus;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Tasklet implementing COBOL RPTPOS00 - Daily Position Report Generator.
 * Generates position reports including portfolio position summary,
 * transaction activity, exception reporting, and performance metrics.
 */
public class PositionReportTasklet implements Tasklet {

    private static final Logger log = LoggerFactory.getLogger(PositionReportTasklet.class);

    private final PositionRepository positionRepository;
    private final List<String> reportLines = new ArrayList<>();

    public PositionReportTasklet(PositionRepository positionRepository) {
        this.positionRepository = positionRepository;
    }

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) throws Exception {
        log.info("Generating Daily Position Report (RPTPOS00)");

        LocalDate reportDate = LocalDate.now();
        List<Position> positions = positionRepository.findByDateOrdered(reportDate);

        // Write headers (maps to RPTPOS00 1200-WRITE-HEADERS)
        writeHeaders(reportDate);

        // Process positions (maps to RPTPOS00 2100-READ-POSITIONS / 2110-FORMAT-POSITION)
        BigDecimal totalMarketValue = BigDecimal.ZERO;
        BigDecimal totalCostBasis = BigDecimal.ZERO;
        int positionCount = 0;
        int exceptionCount = 0;

        for (Position position : positions) {
            PositionReportEntry entry = new PositionReportEntry();
            entry.setPortfolioId(position.getPortfolioId());
            entry.setInvestmentId(position.getInvestmentId());
            entry.setQuantity(position.getQuantity());
            entry.setMarketValue(position.getMarketValue());
            entry.setCostBasis(position.getCostBasis());
            entry.calculateDerivedFields();

            reportLines.add(entry.toString());
            positionCount++;

            if (position.getMarketValue() != null) {
                totalMarketValue = totalMarketValue.add(position.getMarketValue());
            }
            if (position.getCostBasis() != null) {
                totalCostBasis = totalCostBasis.add(position.getCostBasis());
            }

            // Exception check: positions with >10% loss
            if (entry.getChangePercent() != null && entry.getChangePercent().compareTo(BigDecimal.valueOf(-10)) < 0) {
                exceptionCount++;
                reportLines.add("  ** EXCEPTION: Significant loss detected **");
            }
        }

        // Write summary (maps to RPTPOS00 2300-WRITE-SUMMARY)
        writeSummary(positionCount, totalMarketValue, totalCostBasis, exceptionCount);

        contribution.incrementReadCount();
        contribution.incrementWriteCount(1);

        log.info("Position Report generated: {} positions, total market value: {}",
                positionCount, totalMarketValue.toPlainString());
        return RepeatStatus.FINISHED;
    }

    private void writeHeaders(LocalDate reportDate) {
        reportLines.add(String.format("%s", "*".repeat(132)));
        reportLines.add(String.format("%40s%s", "", "DAILY POSITION REPORT"));
        reportLines.add(String.format("REPORT DATE: %s", reportDate.format(DateTimeFormatter.ISO_LOCAL_DATE)));
        reportLines.add(String.format("%s", "-".repeat(132)));
        reportLines.add(String.format("%-10s %-10s %15s %15s %15s %8s",
                "PORTFOLIO", "INVESTMENT", "QUANTITY", "MARKET VALUE", "GAIN/LOSS", "CHG %"));
        reportLines.add(String.format("%s", "-".repeat(132)));
    }

    private void writeSummary(int positionCount, BigDecimal totalMarketValue,
                               BigDecimal totalCostBasis, int exceptionCount) {
        reportLines.add(String.format("%s", "-".repeat(132)));
        reportLines.add(String.format("TOTAL POSITIONS: %d", positionCount));
        reportLines.add(String.format("TOTAL MARKET VALUE: %s", totalMarketValue.toPlainString()));
        reportLines.add(String.format("TOTAL COST BASIS: %s", totalCostBasis.toPlainString()));
        reportLines.add(String.format("TOTAL GAIN/LOSS: %s", totalMarketValue.subtract(totalCostBasis).toPlainString()));
        reportLines.add(String.format("EXCEPTIONS: %d", exceptionCount));
        reportLines.add(String.format("%s", "*".repeat(132)));
    }

    public List<String> getReportLines() {
        return reportLines;
    }
}
