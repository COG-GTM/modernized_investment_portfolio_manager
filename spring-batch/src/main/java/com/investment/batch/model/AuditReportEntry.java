package com.investment.batch.model;

import java.time.LocalDateTime;

/**
 * Report entry for audit reports, mapping to COBOL RPTAUD00 detail line.
 */
public class AuditReportEntry {

    private String timestamp;
    private String program;
    private String auditType;
    private String message;
    private String portfolioId;
    private String actionCode;

    public AuditReportEntry() {}

    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }
    public String getProgram() { return program; }
    public void setProgram(String program) { this.program = program; }
    public String getAuditType() { return auditType; }
    public void setAuditType(String auditType) { this.auditType = auditType; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public String getPortfolioId() { return portfolioId; }
    public void setPortfolioId(String portfolioId) { this.portfolioId = portfolioId; }
    public String getActionCode() { return actionCode; }
    public void setActionCode(String actionCode) { this.actionCode = actionCode; }

    @Override
    public String toString() {
        return String.format("%-26s %-8s %-10s %s",
                timestamp != null ? timestamp : "",
                program != null ? program : "",
                auditType != null ? auditType : "",
                message != null ? message : "");
    }
}
