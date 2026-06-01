package com.portfolio.inquiry.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Schema(description = "Portfolio summary with positions — replaces INQPORT CICS screen output")
public record PortfolioSummaryDto(

        @Schema(description = "Portfolio identifier", example = "PORT0001")
        String portId,

        @Schema(description = "Account number", example = "1000000001")
        String accountNo,

        @Schema(description = "Client name", example = "GROWTH PORTFOLIO")
        String clientName,

        @Schema(description = "Client type: I=Individual, C=Corporate, T=Trust", example = "I")
        String clientType,

        @Schema(description = "Portfolio status: A=Active, C=Closed, S=Suspended", example = "A")
        String status,

        @Schema(description = "Total portfolio value", example = "12345678.99")
        BigDecimal totalValue,

        @Schema(description = "Available cash balance", example = "50000.00")
        BigDecimal cashBalance,

        @Schema(description = "Portfolio creation date", example = "2024-03-20")
        LocalDate createDate,

        @Schema(description = "Last maintenance date", example = "2024-03-20")
        LocalDate lastMaint,

        @Schema(description = "List of current positions")
        List<PositionDto> positions
) {
}
