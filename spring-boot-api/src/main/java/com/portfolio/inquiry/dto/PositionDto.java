package com.portfolio.inquiry.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Schema(description = "Portfolio position holding details")
public record PositionDto(

        @Schema(description = "Investment security identifier", example = "IBM0000001")
        String investmentId,

        @Schema(description = "Position date", example = "2024-03-20")
        LocalDate date,

        @Schema(description = "Number of shares/units held", example = "500.0000")
        BigDecimal quantity,

        @Schema(description = "Original cost basis", example = "62500.00")
        BigDecimal costBasis,

        @Schema(description = "Current market value", example = "68750.00")
        BigDecimal marketValue,

        @Schema(description = "Currency code", example = "USD")
        String currency,

        @Schema(description = "Position status: A=Active, C=Closed, P=Pending", example = "A")
        String status,

        @Schema(description = "Unrealized gain/loss amount", example = "6250.00")
        BigDecimal gainLoss,

        @Schema(description = "Unrealized gain/loss percentage", example = "10.00")
        BigDecimal gainLossPercent,

        @Schema(description = "Last maintenance timestamp")
        LocalDateTime lastMaintDate,

        @Schema(description = "Last maintenance user", example = "SYSTEM")
        String lastMaintUser
) {
}
