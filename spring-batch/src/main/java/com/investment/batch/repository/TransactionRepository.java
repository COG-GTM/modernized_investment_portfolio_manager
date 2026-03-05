package com.investment.batch.repository;

import com.investment.batch.entity.Transaction;
import com.investment.batch.entity.TransactionId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, TransactionId> {

    List<Transaction> findByStatus(String status);

    List<Transaction> findByDateAndStatus(LocalDate date, String status);

    List<Transaction> findByPortfolioId(String portfolioId);

    @Query("SELECT t FROM Transaction t WHERE t.date = :date AND t.status = :status ORDER BY t.time, t.sequenceNo")
    List<Transaction> findByDateAndStatusOrdered(@Param("date") LocalDate date, @Param("status") String status);

    @Query("SELECT COUNT(t) FROM Transaction t WHERE t.date = :date AND t.status = :status")
    long countByDateAndStatus(@Param("date") LocalDate date, @Param("status") String status);
}
