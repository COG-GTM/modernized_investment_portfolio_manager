package com.portfolio.inquiry.exception;

/**
 * Replaces ERRHNDL DB2 error handling from the COBOL online layer.
 * Thrown when a database-level error occurs during inquiry processing.
 */
public class DataAccessException extends RuntimeException {

    private final String program;

    public DataAccessException(String program, String message, Throwable cause) {
        super(message, cause);
        this.program = program;
    }

    public String getProgram() {
        return program;
    }
}
