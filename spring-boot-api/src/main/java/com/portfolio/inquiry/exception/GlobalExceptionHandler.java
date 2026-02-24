package com.portfolio.inquiry.exception;

import com.portfolio.inquiry.dto.ErrorResponseDto;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.time.LocalDateTime;

/**
 * Centralized exception handler — replaces ERRHNDL.cbl.
 * Maps application exceptions to proper HTTP status codes and error DTOs.
 */
@ControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(PortfolioNotFoundException.class)
    public ResponseEntity<ErrorResponseDto> handlePortfolioNotFound(
            PortfolioNotFoundException ex, HttpServletRequest request) {

        log.warn("Portfolio not found: {}", ex.getPortfolioId());

        ErrorResponseDto error = new ErrorResponseDto(
                HttpStatus.NOT_FOUND.value(),
                ex.getMessage(),
                "Portfolio ID: " + ex.getPortfolioId(),
                LocalDateTime.now(),
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    @ExceptionHandler(InvalidInquiryRequestException.class)
    public ResponseEntity<ErrorResponseDto> handleInvalidRequest(
            InvalidInquiryRequestException ex, HttpServletRequest request) {

        log.warn("Invalid inquiry request: {}", ex.getMessage());

        ErrorResponseDto error = new ErrorResponseDto(
                HttpStatus.BAD_REQUEST.value(),
                ex.getMessage(),
                null,
                LocalDateTime.now(),
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<ErrorResponseDto> handleDataAccessError(
            DataAccessException ex, HttpServletRequest request) {

        log.error("Data access error in {}: {}", ex.getProgram(), ex.getMessage(), ex);

        ErrorResponseDto error = new ErrorResponseDto(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "An error occurred while accessing portfolio data",
                "Program: " + ex.getProgram(),
                LocalDateTime.now(),
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ErrorResponseDto> handleTypeMismatch(
            MethodArgumentTypeMismatchException ex, HttpServletRequest request) {

        ErrorResponseDto error = new ErrorResponseDto(
                HttpStatus.BAD_REQUEST.value(),
                "Invalid parameter: " + ex.getName(),
                ex.getMessage(),
                LocalDateTime.now(),
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponseDto> handleGenericException(
            Exception ex, HttpServletRequest request) {

        log.error("Unexpected error: {}", ex.getMessage(), ex);

        ErrorResponseDto error = new ErrorResponseDto(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "An unexpected error occurred",
                ex.getClass().getSimpleName(),
                LocalDateTime.now(),
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
