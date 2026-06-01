package com.portfolio.inquiry.service;

import com.portfolio.inquiry.dto.PortfolioSummaryDto;
import com.portfolio.inquiry.dto.PositionDto;
import com.portfolio.inquiry.entity.Portfolio;
import com.portfolio.inquiry.entity.Position;
import com.portfolio.inquiry.exception.DataAccessException;
import com.portfolio.inquiry.exception.InvalidInquiryRequestException;
import com.portfolio.inquiry.exception.PortfolioNotFoundException;
import com.portfolio.inquiry.repository.PortfolioRepository;
import com.portfolio.inquiry.repository.PositionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Portfolio position lookup service — replaces INQPORT.cbl.
 *
 * <p>The original COBOL program read position data from a VSAM KSDS file
 * (POSFILE) keyed by account number, then formatted results for BMS screen
 * display. This service queries Spring Data JPA repositories and returns DTOs.</p>
 */
@Service
public class PortfolioService {

    private static final Logger log = LoggerFactory.getLogger(PortfolioService.class);

    private final PortfolioRepository portfolioRepository;
    private final PositionRepository positionRepository;

    public PortfolioService(PortfolioRepository portfolioRepository,
                            PositionRepository positionRepository) {
        this.portfolioRepository = portfolioRepository;
        this.positionRepository = positionRepository;
    }

    /**
     * Retrieve portfolio summary with positions — equivalent to INQPORT P200-GET-POSITION.
     *
     * @param portfolioId the portfolio identifier (PORT_ID)
     * @return portfolio summary with all active positions
     */
    @Transactional(readOnly = true)
    public PortfolioSummaryDto getPortfolioSummary(String portfolioId) {
        validatePortfolioId(portfolioId);

        try {
            List<Portfolio> portfolios = portfolioRepository.findByPortId(portfolioId);

            if (portfolios.isEmpty()) {
                throw new PortfolioNotFoundException(portfolioId);
            }

            Portfolio portfolio = portfolios.get(0);
            List<Position> positions = positionRepository.findByPortfolioId(portfolioId);

            List<PositionDto> positionDtos = positions.stream()
                    .map(this::toPositionDto)
                    .toList();

            log.debug("Retrieved portfolio {} with {} positions", portfolioId, positionDtos.size());

            return new PortfolioSummaryDto(
                    portfolio.getPortId(),
                    portfolio.getAccountNo(),
                    portfolio.getClientName(),
                    portfolio.getClientType(),
                    portfolio.getStatus(),
                    portfolio.getTotalValue(),
                    portfolio.getCashBalance(),
                    portfolio.getCreateDate(),
                    portfolio.getLastMaint(),
                    positionDtos
            );
        } catch (PortfolioNotFoundException e) {
            throw e;
        } catch (Exception e) {
            throw new DataAccessException("PortfolioService", "Error accessing position data for portfolio: " + portfolioId, e);
        }
    }

    /**
     * Retrieve only the active positions for a portfolio.
     *
     * @param portfolioId the portfolio identifier
     * @return list of active positions
     */
    @Transactional(readOnly = true)
    public List<PositionDto> getActivePositions(String portfolioId) {
        validatePortfolioId(portfolioId);

        List<Portfolio> portfolios = portfolioRepository.findByPortId(portfolioId);
        if (portfolios.isEmpty()) {
            throw new PortfolioNotFoundException(portfolioId);
        }

        return positionRepository.findByPortfolioIdAndStatus(portfolioId, "A")
                .stream()
                .map(this::toPositionDto)
                .toList();
    }

    private void validatePortfolioId(String portfolioId) {
        if (portfolioId == null || portfolioId.isBlank()) {
            throw new InvalidInquiryRequestException("Portfolio ID is required");
        }
        if (portfolioId.length() > 8) {
            throw new InvalidInquiryRequestException("Portfolio ID must not exceed 8 characters");
        }
    }

    private PositionDto toPositionDto(Position position) {
        return new PositionDto(
                position.getInvestmentId(),
                position.getDate(),
                position.getQuantity(),
                position.getCostBasis(),
                position.getMarketValue(),
                position.getCurrency(),
                position.getStatus(),
                position.getGainLoss(),
                position.getGainLossPercent(),
                position.getLastMaintDate(),
                position.getLastMaintUser()
        );
    }
}
