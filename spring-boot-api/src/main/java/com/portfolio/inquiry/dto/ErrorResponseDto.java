package com.portfolio.inquiry.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.time.LocalDateTime;

@Schema(description = "Error response — replaces ERRHNDL COBOL error handling")
public record ErrorResponseDto(

        @Schema(description = "HTTP status code", example = "404")
        int status,

        @Schema(description = "Error message", example = "Portfolio not found")
        String message,

        @Schema(description = "Error detail or trace identifier")
        String detail,

        @Schema(description = "Timestamp of the error")
        LocalDateTime timestamp,

        @Schema(description = "Request path that caused the error", example = "/api/portfolios/INVALID")
        String path
) {
}
