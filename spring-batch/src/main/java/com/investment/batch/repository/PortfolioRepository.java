package com.investment.batch.repository;

import com.investment.batch.entity.Portfolio;
import com.investment.batch.entity.PortfolioId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PortfolioRepository extends JpaRepository<Portfolio, PortfolioId> {

    List<Portfolio> findByStatus(String status);

    Optional<Portfolio> findByPortId(String portId);
}
