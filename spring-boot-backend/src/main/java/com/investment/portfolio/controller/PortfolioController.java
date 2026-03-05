package com.investment.portfolio.controller;

import com.investment.portfolio.audit.AuditService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Portfolio Controller with role-based access control.
 * Replaces COBOL INQONLN/INQPORT inquiry flow where SECMGR
 * validated access before any portfolio data was returned.
 * Uses @PreAuthorize to enforce authorization at the method level,
 * replacing the SECMGR P200-CHECK-AUTH AUTHFILE lookup.
 */
@RestController
@RequestMapping("/api/portfolio")
public class PortfolioController {

    private final AuditService auditService;

    public PortfolioController(AuditService auditService) {
        this.auditService = auditService;
    }

    @GetMapping("/positions")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<Map<String, Object>> getPositions(
            Authentication authentication, HttpServletRequest request) {
        auditService.logAccess(authentication.getName(), "/api/portfolio/positions",
                request.getRemoteAddr());
        return ResponseEntity.ok(Map.of(
                "message", "Portfolio positions retrieved successfully",
                "user", authentication.getName()
        ));
    }

    @GetMapping("/summary")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    public ResponseEntity<Map<String, Object>> getPortfolioSummary(
            Authentication authentication, HttpServletRequest request) {
        auditService.logAccess(authentication.getName(), "/api/portfolio/summary",
                request.getRemoteAddr());
        return ResponseEntity.ok(Map.of(
                "message", "Portfolio summary retrieved successfully",
                "user", authentication.getName()
        ));
    }
}
