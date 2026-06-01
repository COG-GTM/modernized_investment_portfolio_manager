-- Flyway Migration V2: Create audit log table
-- Replaces COBOL SECMGR AUDITLOG table (P300-LOG-ACCESS) and ERRHNDL ERRLOG table (P200-LOG-ERROR)
-- Combines both security audit logging and error logging into a unified audit trail

CREATE TABLE audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resource VARCHAR(100),
    result VARCHAR(20) NOT NULL,
    details VARCHAR(500),
    ip_address VARCHAR(45),
    trace_id VARCHAR(36),
    severity VARCHAR(20)
);

-- Index for efficient audit log queries
-- Replaces the implicit DB2 index on AUDITLOG table
CREATE INDEX idx_audit_logs_username ON audit_logs(username);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_trace_id ON audit_logs(trace_id);
