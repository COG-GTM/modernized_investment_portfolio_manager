package com.investment.portfolio.audit;

import com.investment.portfolio.entity.AuditLog;
import com.investment.portfolio.repository.AuditLogRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Audit Service replacing COBOL SECMGR P300-LOG-ACCESS and ERRHNDL P200-LOG-ERROR.
 * Logs all security events including login attempts, access checks,
 * authorization failures, and error occurrences.
 * Uses a separate transaction to ensure audit logs are persisted
 * even when the parent transaction rolls back (matching COBOL behavior
 * where audit inserts were independent of business transaction outcomes).
 */
@Service
public class AuditService {

    private static final Logger logger = LoggerFactory.getLogger(AuditService.class);

    private final AuditLogRepository auditLogRepository;

    public AuditService(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    /**
     * Log a successful login event.
     * Replaces SECMGR SEC-VALIDATE with response code 0.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logLogin(String username, String ipAddress) {
        AuditLog auditLog = createAuditLog(username, "LOGIN", "/api/auth/login",
                "SUCCESS", "User logged in successfully", ipAddress, "INFO");
        auditLogRepository.save(auditLog);
        logger.info("Audit: User '{}' logged in from {}", username, ipAddress);
    }

    /**
     * Log a failed login attempt.
     * Replaces SECMGR SEC-VALIDATE with response code 8 (validation failed).
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logLoginFailure(String username, String ipAddress, String reason) {
        AuditLog auditLog = createAuditLog(username, "LOGIN_FAILURE", "/api/auth/login",
                "FAILURE", reason, ipAddress, "WARNING");
        auditLogRepository.save(auditLog);
        logger.warn("Audit: Failed login attempt for user '{}' from {}: {}", username, ipAddress, reason);
    }

    /**
     * Log a successful resource access.
     * Replaces SECMGR SEC-AUTHORIZE with response code 0.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logAccess(String username, String resource, String ipAddress) {
        AuditLog auditLog = createAuditLog(username, "ACCESS", resource,
                "SUCCESS", "Resource accessed successfully", ipAddress, "INFO");
        auditLogRepository.save(auditLog);
        logger.info("Audit: User '{}' accessed resource '{}'", username, resource);
    }

    /**
     * Log an authorization failure.
     * Replaces SECMGR SEC-AUTHORIZE with response code 8 (access denied).
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logAuthorizationFailure(String username, String resource, String ipAddress) {
        AuditLog auditLog = createAuditLog(username, "AUTHORIZATION_FAILURE", resource,
                "FAILURE", "Access denied - insufficient privileges", ipAddress, "WARNING");
        auditLogRepository.save(auditLog);
        logger.warn("Audit: Authorization failure for user '{}' on resource '{}'", username, resource);
    }

    /**
     * Log a user registration event.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logRegistration(String username, String ipAddress) {
        AuditLog auditLog = createAuditLog(username, "REGISTRATION", "/api/auth/register",
                "SUCCESS", "New user registered", ipAddress, "INFO");
        auditLogRepository.save(auditLog);
        logger.info("Audit: New user '{}' registered from {}", username, ipAddress);
    }

    /**
     * Log an application error.
     * Replaces ERRHNDL P200-LOG-ERROR which inserted into ERRLOG table.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logError(String username, String resource, String errorDetails, String severity) {
        AuditLog auditLog = createAuditLog(username, "ERROR", resource,
                "ERROR", errorDetails, null, severity);
        auditLogRepository.save(auditLog);
        logger.error("Audit: Error for user '{}' on resource '{}': {}", username, resource, errorDetails);
    }

    /**
     * Retrieve all audit logs (admin overview).
     * Replaces SECMGR system-level audit trail review.
     */
    @Transactional(readOnly = true)
    public List<AuditLog> getAllAuditLogs() {
        return auditLogRepository.findAll();
    }

    /**
     * Retrieve audit logs for a specific user.
     */
    @Transactional(readOnly = true)
    public List<AuditLog> getAuditLogsForUser(String username) {
        return auditLogRepository.findByUsername(username);
    }

    /**
     * Retrieve audit logs within a date range.
     */
    @Transactional(readOnly = true)
    public List<AuditLog> getAuditLogsBetween(LocalDateTime start, LocalDateTime end) {
        return auditLogRepository.findByTimestampBetween(start, end);
    }

    private AuditLog createAuditLog(String username, String action, String resource,
                                     String result, String details, String ipAddress, String severity) {
        AuditLog auditLog = new AuditLog(username, action, resource, result, details);
        auditLog.setIpAddress(ipAddress);
        auditLog.setTraceId(UUID.randomUUID().toString());
        auditLog.setSeverity(severity);
        return auditLog;
    }
}
