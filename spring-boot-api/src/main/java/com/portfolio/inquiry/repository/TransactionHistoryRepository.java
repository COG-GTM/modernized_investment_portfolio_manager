package com.portfolio.inquiry.repository;

import com.portfolio.inquiry.entity.TransactionHistory;
import com.portfolio.inquiry.entity.TransactionHistoryId;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TransactionHistoryRepository extends JpaRepository<TransactionHistory, TransactionHistoryId> {

    Page<TransactionHistory> findByPortfolioIdOrderByDateDescTimeDesc(String portfolioId, Pageable pageable);

    Page<TransactionHistory> findByPortfolioIdAndRecordTypeOrderByDateDescTimeDesc(
            String portfolioId, String recordType, Pageable pageable);

    Page<TransactionHistory> findByPortfolioIdAndActionCodeOrderByDateDescTimeDesc(
            String portfolioId, String actionCode, Pageable pageable);
}
