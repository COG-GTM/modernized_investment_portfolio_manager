package com.investment.batch.repository;

import com.investment.batch.entity.TransactionHistory;
import com.investment.batch.entity.TransactionHistoryId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TransactionHistoryRepository extends JpaRepository<TransactionHistory, TransactionHistoryId> {

    List<TransactionHistory> findByPortfolioId(String portfolioId);

    List<TransactionHistory> findByRecordType(String recordType);

    List<TransactionHistory> findByActionCode(String actionCode);

    @Query("SELECT h FROM TransactionHistory h WHERE h.date = :date ORDER BY h.time, h.seqNo")
    List<TransactionHistory> findByDateOrdered(@Param("date") String date);

    @Query("SELECT COUNT(h) FROM TransactionHistory h WHERE h.date = :date")
    long countByDate(@Param("date") String date);
}
