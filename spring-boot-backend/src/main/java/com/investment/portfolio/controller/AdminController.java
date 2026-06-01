package com.investment.portfolio.controller;

import com.investment.portfolio.audit.AuditService;
import com.investment.portfolio.entity.AuditLog;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

/**
 * Admin Controller with ADMIN role-based access control.
 * Replaces COBOL SECMGR system-level security for maintenance transactions.
 * Only users with ADMIN role can access audit logs and system management.
 */
@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AuditService auditService;

    public AdminController(AuditService auditService) {
        this.auditService = auditService;
    }

    @GetMapping("/audit-logs")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<AuditLog>> getAuditLogs(
            Authentication authentication, HttpServletRequest request) {
        auditService.logAccess(authentication.getName(), "/api/admin/audit-logs",
                request.getRemoteAddr());
        List<AuditLog> logs = auditService.getAllAuditLogs();
        return ResponseEntity.ok(logs);
    }

    @GetMapping("/audit-logs/user/{username}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<AuditLog>> getAuditLogsForUser(
            @PathVariable String username,
            Authentication authentication, HttpServletRequest request) {
        auditService.logAccess(authentication.getName(),
                "/api/admin/audit-logs/user/" + username, request.getRemoteAddr());
        List<AuditLog> logs = auditService.getAuditLogsForUser(username);
        return ResponseEntity.ok(logs);
    }

    @GetMapping("/system/status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> getSystemStatus(
            Authentication authentication, HttpServletRequest request) {
        auditService.logAccess(authentication.getName(), "/api/admin/system/status",
                request.getRemoteAddr());
        return ResponseEntity.ok(Map.of(
                "status", "ACTIVE",
                "message", "Investment Portfolio Management System is running"
        ));
    }
}
