package com.portfolio.inquiry.repository;

import com.portfolio.inquiry.entity.Transaction;
import com.portfolio.inquiry.entity.TransactionId;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, TransactionId> {

    Page<Transaction> findByPortfolioIdOrderByDateDescTimeDesc(String portfolioId, Pageable pageable);

    Page<Transaction> findByPortfolioIdAndTypeOrderByDateDescTimeDesc(String portfolioId, String type, Pageable pageable);

    Page<Transaction> findByPortfolioIdAndStatusOrderByDateDescTimeDesc(String portfolioId, String status, Pageable pageable);
}
