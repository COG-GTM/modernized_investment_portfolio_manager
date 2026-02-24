package com.investment.batch.repository;

import com.investment.batch.entity.BatchJobControl;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface BatchJobControlRepository extends JpaRepository<BatchJobControl, Long> {

    Optional<BatchJobControl> findByJobNameAndProcessDateAndSequenceNo(String jobName, LocalDate processDate, int sequenceNo);

    List<BatchJobControl> findByProcessDate(LocalDate processDate);

    List<BatchJobControl> findByProcessDateAndStatus(LocalDate processDate, String status);

    List<BatchJobControl> findByJobNameAndProcessDate(String jobName, LocalDate processDate);

    List<BatchJobControl> findByStatus(String status);
}
