package com.investment.batch.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Result of transaction validation, mapping to COBOL TRNVAL00 validation logic.
 */
public class ValidationResult {

    private boolean valid;
    private List<String> errors;

    public ValidationResult() {
        this.valid = true;
        this.errors = new ArrayList<>();
    }

    public ValidationResult(boolean valid, List<String> errors) {
        this.valid = valid;
        this.errors = errors != null ? errors : new ArrayList<>();
    }

    public boolean isValid() { return valid; }
    public void setValid(boolean valid) { this.valid = valid; }
    public List<String> getErrors() { return errors; }
    public void setErrors(List<String> errors) { this.errors = errors; }

    public void addError(String error) {
        this.errors.add(error);
        this.valid = false;
    }

    public static ValidationResult success() {
        return new ValidationResult(true, new ArrayList<>());
    }

    public static ValidationResult failure(String error) {
        ValidationResult result = new ValidationResult();
        result.addError(error);
        return result;
    }
}
