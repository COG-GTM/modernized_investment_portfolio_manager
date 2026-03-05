package com.portfolio.inquiry.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.time.LocalDateTime;

@Schema(description = "Audit / transaction history record — replaces INQHIST cursor-based fetch")
public record TransactionHistoryDto(

        @Schema(description = "History date (YYYYMMDD)", example = "20240320")
        String date,

        @Schema(description = "History time (HHMMSSss)", example = "15304500")
        String time,

        @Schema(description = "Sequence number", example = "0001")
        String seqNo,

        @Schema(description = "Record type: PT=Portfolio, PS=Position, TR=Transaction", example = "TR")
        String recordType,

        @Schema(description = "Action code: A=Add, C=Change, D=Delete", example = "A")
        String actionCode,

        @Schema(description = "State before the change (JSON)")
        String beforeImage,

        @Schema(description = "State after the change (JSON)")
        String afterImage,

        @Schema(description = "Reason code", example = "AUTO")
        String reasonCode,

        @Schema(description = "Processing timestamp")
        LocalDateTime processDate,

        @Schema(description = "User who made the change", example = "SYSTEM")
        String processUser
) {
}
