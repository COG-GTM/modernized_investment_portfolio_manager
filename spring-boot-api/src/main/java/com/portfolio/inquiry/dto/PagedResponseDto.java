package com.portfolio.inquiry.dto;

import io.swagger.v3.oas.annotations.media.Schema;

import java.util.List;

@Schema(description = "Paginated response wrapper — replaces COBOL cursor-based 3000-byte array fetch")
public record PagedResponseDto<T>(

        @Schema(description = "Page content")
        List<T> content,

        @Schema(description = "Current page number (0-based)", example = "0")
        int page,

        @Schema(description = "Page size", example = "20")
        int size,

        @Schema(description = "Total number of elements", example = "42")
        long totalElements,

        @Schema(description = "Total number of pages", example = "3")
        int totalPages,

        @Schema(description = "Whether this is the last page", example = "false")
        boolean last
) {
}
