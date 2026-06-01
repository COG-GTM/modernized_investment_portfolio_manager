package com.portfolio.inquiry.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalTime;

@Schema(description = "Transaction record")
public record TransactionDto(

        @Schema(description = "Transaction date", example = "2024-03-20")
        LocalDate date,

        @Schema(description = "Transaction time", example = "15:30:45")
        LocalTime time,

        @Schema(description = "Sequence number", example = "000001")
        String sequenceNo,

        @Schema(description = "Investment security identifier", example = "IBM0000001")
        String investmentId,

        @Schema(description = "Transaction type: BU=Buy, SL=Sell, TR=Transfer, FE=Fee", example = "BU")
        String type,

        @Schema(description = "Share quantity", example = "500.0000")
        BigDecimal quantity,

        @Schema(description = "Price per share", example = "125.0000")
        BigDecimal price,

        @Schema(description = "Total transaction amount", example = "62500.00")
        BigDecimal amount,

        @Schema(description = "Currency code", example = "USD")
        String currency,

        @Schema(description = "Status: P=Pending, D=Done, F=Failed, R=Reversed", example = "D")
        String status
) {
}
