package com.investment.portfolio.exception;

import com.investment.portfolio.audit.AuditService;
import com.investment.portfolio.dto.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Centralized Exception Handler replacing COBOL ERRHNDL.
 * Maps to the ERRHNDL program flow:
 * - P100-INIT-ERROR-HANDLER: trace ID generation
 * - P200-LOG-ERROR: error logging via AuditService
 * - P300-FORMAT-MESSAGE: structured ErrorResponse creation
 * - P400-DETERMINE-ACTION: HTTP status code mapping
 *
 * Severity mapping from COBOL:
 * - ERR-FATAL (ABEND) -> 500 Internal Server Error
 * - ERR-WARNING (CONTINUE) -> 400 Bad Request
 * - ERR-INFO (CONTINUE) -> 200 with warning message
 */
@ControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    private final AuditService auditService;

    public GlobalExceptionHandler(AuditService auditService) {
        this.auditService = auditService;
    }

    /**
     * Handle authentication errors.
     * Replaces SECMGR response code 8 (User validation failed).
     */
    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ErrorResponse> handleBadCredentials(
            BadCredentialsException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        logger.error("Authentication failed [traceId={}]: {}", traceId, ex.getMessage());

        // Note: Failed login audit logging with the actual username is handled
        // in AuthService.login() where the username from the JSON body is available.
        // The GlobalExceptionHandler cannot reliably extract the username from a
        // JSON request body since the input stream is already consumed by @RequestBody.

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.UNAUTHORIZED.value(),
                "Authentication Failed",
                "Invalid username or password",
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
    }

    /**
     * Handle general authentication errors.
     * Replaces SECMGR response code 12 (Unable to obtain user credentials).
     */
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ErrorResponse> handleAuthenticationException(
            AuthenticationException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        logger.error("Authentication error [traceId={}]: {}", traceId, ex.getMessage());

        tryLogAuditError("unknown", request.getRequestURI(),
                ex.getMessage(), "ERROR");

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.UNAUTHORIZED.value(),
                "Authentication Error",
                "Unable to authenticate: " + ex.getMessage(),
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(errorResponse);
    }

    /**
     * Handle authorization errors.
     * Replaces SECMGR P200-CHECK-AUTH response code 8 (Access denied).
     */
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDenied(
            AccessDeniedException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        String username = getCurrentUsername();
        logger.error("Access denied [traceId={}] for user '{}': {}",
                traceId, username, ex.getMessage());

        try {
            auditService.logAuthorizationFailure(username, request.getRequestURI(),
                    request.getRemoteAddr());
        } catch (Exception auditEx) {
            logger.error("Failed to write audit log for access denied [traceId={}]: {}",
                    traceId, auditEx.getMessage());
        }

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.FORBIDDEN.value(),
                "Access Denied",
                "You do not have permission to access this resource",
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(errorResponse);
    }

    /**
     * Handle account locked errors.
     * Replaces SECMGR user validation with locked account detection.
     */
    @ExceptionHandler(LockedException.class)
    public ResponseEntity<ErrorResponse> handleLockedException(
            LockedException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        logger.error("Account locked [traceId={}]: {}", traceId, ex.getMessage());

        tryLogAuditError("unknown", request.getRequestURI(),
                "Account locked", "WARNING");

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.FORBIDDEN.value(),
                "Account Locked",
                "Your account has been locked. Please contact an administrator.",
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(errorResponse);
    }

    /**
     * Handle database errors.
     * Replaces ERRHNDL handling of DB2 SQLCODE errors and DB2RECV recovery logic.
     * Maps to ERR-FATAL severity which triggered ABEND in COBOL.
     */
    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<ErrorResponse> handleDatabaseException(
            DataAccessException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        String username = getCurrentUsername();
        logger.error("Database error [traceId={}]: {}", traceId, ex.getMessage());

        tryLogAuditError(username, request.getRequestURI(),
                "Database error: " + ex.getMostSpecificCause().getMessage(), "FATAL");

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "Database Error",
                "A database error occurred. Please try again later.",
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
    }

    /**
     * Handle validation errors.
     * Replaces COBOL input validation checks that returned specific error messages.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        logger.warn("Validation error [traceId={}]: {}", traceId, ex.getMessage());

        List<String> details = ex.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.toList());

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.BAD_REQUEST.value(),
                "Validation Failed",
                "Input validation failed",
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        errorResponse.setDetails(details);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * Handle illegal argument errors (e.g., duplicate username/email during registration).
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgument(
            IllegalArgumentException ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        logger.warn("Illegal argument [traceId={}]: {}", traceId, ex.getMessage());

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.BAD_REQUEST.value(),
                "Bad Request",
                ex.getMessage(),
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    /**
     * Handle all other unhandled exceptions.
     * Replaces ERRHNDL P400-DETERMINE-ACTION OTHER case (ERR-RETURN).
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneralException(
            Exception ex, HttpServletRequest request) {
        String traceId = generateTraceId();
        String username = getCurrentUsername();
        logger.error("Unexpected error [traceId={}]: {}", traceId, ex.getMessage(), ex);

        tryLogAuditError(username, request.getRequestURI(),
                ex.getMessage(), "FATAL");

        ErrorResponse errorResponse = new ErrorResponse(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "Internal Server Error",
                "An unexpected error occurred. Please try again later.",
                request.getRequestURI()
        );
        errorResponse.setTraceId(traceId);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
    }

    private String generateTraceId() {
        return UUID.randomUUID().toString();
    }

    /**
     * Safely attempt to write an audit error log.
     * If the database is unavailable, the audit write itself will fail;
     * catching that ensures the caller still returns a structured ErrorResponse.
     */
    private void tryLogAuditError(String username, String resource, String errorDetails, String severity) {
        try {
            auditService.logError(username, resource, errorDetails, severity);
        } catch (Exception auditEx) {
            logger.error("Failed to write audit log: {}", auditEx.getMessage());
        }
    }

    private String getCurrentUsername() {
        var auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getName() != null) {
            return auth.getName();
        }
        return "anonymous";
    }
}
