package com.portfolio.inquiry.controller;

import com.portfolio.inquiry.dto.ErrorResponseDto;
import com.portfolio.inquiry.dto.PagedResponseDto;
import com.portfolio.inquiry.dto.PortfolioSummaryDto;
import com.portfolio.inquiry.dto.PositionDto;
import com.portfolio.inquiry.dto.TransactionDto;
import com.portfolio.inquiry.dto.TransactionHistoryDto;
import com.portfolio.inquiry.service.PortfolioService;
import com.portfolio.inquiry.service.TransactionHistoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * REST controller for portfolio inquiries — replaces INQONLN.cbl (CICS main handler).
 *
 * <p>COBOL flow: User -> CICS -> INQONLN -> (INQPORT | INQHIST) -> CURSMGR -> DB2ONLN -> Response</p>
 * <p>Java flow:  Client -> Spring MVC -> InquiryController -> (PortfolioService | TransactionHistoryService) -> JPA -> H2/DB2 -> Response</p>
 *
 * <p>The original INQONLN evaluated WS-COMMAREA-FUNCTION to route between
 * 'INQP' (portfolio inquiry) and 'INQH' (history inquiry). This controller
 * maps those to separate REST endpoints with proper HTTP semantics.</p>
 */
@RestController
@RequestMapping("/api/portfolios")
@Tag(name = "Portfolio Inquiry", description = "Online portfolio inquiry APIs — migrated from CICS/COBOL INQONLN")
public class InquiryController {

    private final PortfolioService portfolioService;
    private final TransactionHistoryService transactionHistoryService;

    public InquiryController(PortfolioService portfolioService,
                             TransactionHistoryService transactionHistoryService) {
        this.portfolioService = portfolioService;
        this.transactionHistoryService = transactionHistoryService;
    }

    /**
     * Portfolio position inquiry — replaces INQONLN 'INQP' -> INQPORT.cbl.
     *
     * <p>Equivalent to CICS LINK PROGRAM('INQPORT') which read from POSFILE VSAM
     * and displayed results via BMS map POSMAP.</p>
     */
    @GetMapping("/{id}")
    @Operation(
            summary = "Get portfolio summary with positions",
            description = "Retrieves portfolio details and all positions. Replaces INQPORT CICS program."
    )
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Portfolio found",
                    content = @Content(schema = @Schema(implementation = PortfolioSummaryDto.class))),
            @ApiResponse(responseCode = "404", description = "Portfolio not found",
                    content = @Content(schema = @Schema(implementation = ErrorResponseDto.class))),
            @ApiResponse(responseCode = "400", description = "Invalid portfolio ID",
                    content = @Content(schema = @Schema(implementation = ErrorResponseDto.class)))
    })
    public ResponseEntity<PortfolioSummaryDto> getPortfolio(
            @Parameter(description = "Portfolio ID (up to 8 characters)", example = "PORT0001")
            @PathVariable("id") String portfolioId) {

        PortfolioSummaryDto summary = portfolioService.getPortfolioSummary(portfolioId);
        return ResponseEntity.ok(summary);
    }

    /**
     * Active positions only — convenience endpoint.
     */
    @GetMapping("/{id}/positions")
    @Operation(
            summary = "Get active positions for a portfolio",
            description = "Returns only active (status=A) positions for the given portfolio."
    )
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Positions found"),
            @ApiResponse(responseCode = "404", description = "Portfolio not found",
                    content = @Content(schema = @Schema(implementation = ErrorResponseDto.class)))
    })
    public ResponseEntity<List<PositionDto>> getPositions(
            @Parameter(description = "Portfolio ID", example = "PORT0001")
            @PathVariable("id") String portfolioId) {

        List<PositionDto> positions = portfolioService.getActivePositions(portfolioId);
        return ResponseEntity.ok(positions);
    }

    /**
     * Transaction history inquiry with pagination — replaces INQONLN 'INQH' -> INQHIST.cbl.
     *
     * <p>The original COBOL used CURSMGR with HISTORY_CURSOR fetching 3000 bytes
     * at a time (see INQHIST.cbl lines 43-50). Spring Data Pageable replaces the
     * cursor-based approach with standard REST pagination parameters.</p>
     */
    @GetMapping("/{id}/history")
    @Operation(
            summary = "Get transaction history with pagination",
            description = "Retrieves paginated audit/transaction history. Replaces INQHIST CICS cursor-based fetch."
    )
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "History retrieved"),
            @ApiResponse(responseCode = "404", description = "Portfolio not found",
                    content = @Content(schema = @Schema(implementation = ErrorResponseDto.class)))
    })
    public ResponseEntity<PagedResponseDto<TransactionHistoryDto>> getHistory(
            @Parameter(description = "Portfolio ID", example = "PORT0001")
            @PathVariable("id") String portfolioId,
            @PageableDefault(size = 20) Pageable pageable) {

        PagedResponseDto<TransactionHistoryDto> history =
                transactionHistoryService.getHistory(portfolioId, pageable);
        return ResponseEntity.ok(history);
    }

    /**
     * Transaction list with pagination — provides detailed transaction view.
     */
    @GetMapping("/{id}/transactions")
    @Operation(
            summary = "Get transactions with pagination",
            description = "Retrieves paginated transactions, optionally filtered by type."
    )
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Transactions retrieved"),
            @ApiResponse(responseCode = "404", description = "Portfolio not found",
                    content = @Content(schema = @Schema(implementation = ErrorResponseDto.class))),
            @ApiResponse(responseCode = "400", description = "Invalid transaction type",
                    content = @Content(schema = @Schema(implementation = ErrorResponseDto.class)))
    })
    public ResponseEntity<PagedResponseDto<TransactionDto>> getTransactions(
            @Parameter(description = "Portfolio ID", example = "PORT0001")
            @PathVariable("id") String portfolioId,
            @Parameter(description = "Filter by transaction type (BU, SL, TR, FE)", example = "BU")
            @RequestParam(value = "type", required = false) String type,
            @PageableDefault(size = 20) Pageable pageable) {

        PagedResponseDto<TransactionDto> transactions;
        if (type != null && !type.isBlank()) {
            transactions = transactionHistoryService.getTransactionsByType(portfolioId, type, pageable);
        } else {
            transactions = transactionHistoryService.getTransactions(portfolioId, pageable);
        }
        return ResponseEntity.ok(transactions);
    }
}
