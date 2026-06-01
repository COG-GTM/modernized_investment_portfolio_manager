package com.portfolio.inquiry.repository;

import com.portfolio.inquiry.entity.Position;
import com.portfolio.inquiry.entity.PositionId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PositionRepository extends JpaRepository<Position, PositionId> {

    List<Position> findByPortfolioId(String portfolioId);

    List<Position> findByPortfolioIdAndStatus(String portfolioId, String status);
}
