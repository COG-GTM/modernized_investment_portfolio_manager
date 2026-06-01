package com.investment.batch.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * Maps to COBOL PRCSEQ00 process sequence record.
 * Defines the order and dependencies of batch processes.
 */
@Entity
@Table(name = "batch_process_sequence")
public class BatchProcessSequence {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "process_date", nullable = false)
    private LocalDate processDate;

    @Column(name = "sequence_type", length = 8, nullable = false)
    private String sequenceType = "DAILY";

    @Column(name = "process_id", length = 64, nullable = false)
    private String processId;

    @Column(name = "sequence_order", nullable = false)
    private int sequenceOrder;

    @Column(name = "dependency_ids", length = 512)
    private String dependencyIds;

    @Column(name = "max_return_code")
    private int maxReturnCode = 4;

    @Column(name = "restartable")
    private boolean restartable = true;

    @Column(name = "status", length = 16, nullable = false)
    private String status = "READY";

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    public BatchProcessSequence() {
        this.createdAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public LocalDate getProcessDate() { return processDate; }
    public void setProcessDate(LocalDate processDate) { this.processDate = processDate; }
    public String getSequenceType() { return sequenceType; }
    public void setSequenceType(String sequenceType) { this.sequenceType = sequenceType; }
    public String getProcessId() { return processId; }
    public void setProcessId(String processId) { this.processId = processId; }
    public int getSequenceOrder() { return sequenceOrder; }
    public void setSequenceOrder(int sequenceOrder) { this.sequenceOrder = sequenceOrder; }
    public String getDependencyIds() { return dependencyIds; }
    public void setDependencyIds(String dependencyIds) { this.dependencyIds = dependencyIds; }
    public int getMaxReturnCode() { return maxReturnCode; }
    public void setMaxReturnCode(int maxReturnCode) { this.maxReturnCode = maxReturnCode; }
    public boolean isRestartable() { return restartable; }
    public void setRestartable(boolean restartable) { this.restartable = restartable; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
