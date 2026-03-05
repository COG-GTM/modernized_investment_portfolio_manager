package com.portfolio.inquiry.repository;

import com.portfolio.inquiry.entity.Portfolio;
import com.portfolio.inquiry.entity.PortfolioId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PortfolioRepository extends JpaRepository<Portfolio, PortfolioId> {

    List<Portfolio> findByPortId(String portId);

    Optional<Portfolio> findByPortIdAndAccountNo(String portId, String accountNo);

    List<Portfolio> findByStatus(String status);
}
