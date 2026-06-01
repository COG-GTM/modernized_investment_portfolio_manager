package com.investment.batch.repository;

import com.investment.batch.entity.BatchProcessSequence;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface BatchProcessSequenceRepository extends JpaRepository<BatchProcessSequence, Long> {

    List<BatchProcessSequence> findByProcessDateAndSequenceTypeOrderBySequenceOrder(LocalDate processDate, String sequenceType);

    List<BatchProcessSequence> findByProcessDateOrderBySequenceOrder(LocalDate processDate);
}
