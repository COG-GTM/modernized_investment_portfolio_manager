package com.investment.batch.repository;

import com.investment.batch.entity.Position;
import com.investment.batch.entity.PositionId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface PositionRepository extends JpaRepository<Position, PositionId> {

    List<Position> findByPortfolioId(String portfolioId);

    List<Position> findByPortfolioIdAndDate(String portfolioId, LocalDate date);

    Optional<Position> findByPortfolioIdAndDateAndInvestmentId(String portfolioId, LocalDate date, String investmentId);

    @Query("SELECT p FROM Position p WHERE p.date = :date AND p.status = :status")
    List<Position> findByDateAndStatus(@Param("date") LocalDate date, @Param("status") String status);

    @Query("SELECT p FROM Position p WHERE p.date = :date ORDER BY p.portfolioId, p.investmentId")
    List<Position> findByDateOrdered(@Param("date") LocalDate date);
}
