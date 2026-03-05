package com.investment.batch.model;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Report entry for statistics reports, mapping to COBOL RPTSTA00 detail line.
 */
public class StatisticsReportEntry {

    private String metricName;
    private long totalCount;
    private long successCount;
    private long failureCount;
    private BigDecimal successRate;
    private BigDecimal averageResponseTime;
    private long totalRecordsProcessed;

    public StatisticsReportEntry() {}

    public String getMetricName() { return metricName; }
    public void setMetricName(String metricName) { this.metricName = metricName; }
    public long getTotalCount() { return totalCount; }
    public void setTotalCount(long totalCount) { this.totalCount = totalCount; }
    public long getSuccessCount() { return successCount; }
    public void setSuccessCount(long successCount) { this.successCount = successCount; }
    public long getFailureCount() { return failureCount; }
    public void setFailureCount(long failureCount) { this.failureCount = failureCount; }
    public BigDecimal getSuccessRate() { return successRate; }
    public void setSuccessRate(BigDecimal successRate) { this.successRate = successRate; }
    public BigDecimal getAverageResponseTime() { return averageResponseTime; }
    public void setAverageResponseTime(BigDecimal averageResponseTime) { this.averageResponseTime = averageResponseTime; }
    public long getTotalRecordsProcessed() { return totalRecordsProcessed; }
    public void setTotalRecordsProcessed(long totalRecordsProcessed) { this.totalRecordsProcessed = totalRecordsProcessed; }

    public void calculateSuccessRate() {
        if (totalCount > 0) {
            this.successRate = BigDecimal.valueOf(successCount)
                    .divide(BigDecimal.valueOf(totalCount), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
        } else {
            this.successRate = BigDecimal.ZERO;
        }
    }

    @Override
    public String toString() {
        return String.format("%-30s Total: %,d  Success: %,d  Failed: %,d  Rate: %s%%",
                metricName, totalCount, successCount, failureCount,
                successRate != null ? successRate.setScale(2, RoundingMode.HALF_UP).toPlainString() : "0.00");
    }
}
