package com.portfolio.inquiry.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Index;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

@Entity
@Table(name = "history", indexes = {
        @Index(name = "idx_history_portfolio_id", columnList = "portfolio_id"),
        @Index(name = "idx_history_date", columnList = "date"),
        @Index(name = "idx_history_record_type", columnList = "record_type"),
        @Index(name = "idx_history_action_code", columnList = "action_code")
})
@IdClass(TransactionHistoryId.class)
public class TransactionHistory {

    @Id
    @Column(name = "portfolio_id", length = 8, nullable = false)
    private String portfolioId;

    @Id
    @Column(name = "date", length = 8, nullable = false)
    private String date;

    @Id
    @Column(name = "time", length = 8, nullable = false)
    private String time;

    @Id
    @Column(name = "seq_no", length = 4, nullable = false)
    private String seqNo;

    @Column(name = "record_type", length = 2)
    private String recordType;

    @Column(name = "action_code", length = 1)
    private String actionCode;

    @Lob
    @Column(name = "before_image")
    private String beforeImage;

    @Lob
    @Column(name = "after_image")
    private String afterImage;

    @Column(name = "reason_code", length = 4)
    private String reasonCode;

    @Column(name = "process_date")
    private LocalDateTime processDate;

    @Column(name = "process_user", length = 8)
    private String processUser;

    public TransactionHistory() {
    }

    public String getPortfolioId() {
        return portfolioId;
    }

    public void setPortfolioId(String portfolioId) {
        this.portfolioId = portfolioId;
    }

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public String getTime() {
        return time;
    }

    public void setTime(String time) {
        this.time = time;
    }

    public String getSeqNo() {
        return seqNo;
    }

    public void setSeqNo(String seqNo) {
        this.seqNo = seqNo;
    }

    public String getRecordType() {
        return recordType;
    }

    public void setRecordType(String recordType) {
        this.recordType = recordType;
    }

    public String getActionCode() {
        return actionCode;
    }

    public void setActionCode(String actionCode) {
        this.actionCode = actionCode;
    }

    public String getBeforeImage() {
        return beforeImage;
    }

    public void setBeforeImage(String beforeImage) {
        this.beforeImage = beforeImage;
    }

    public String getAfterImage() {
        return afterImage;
    }

    public void setAfterImage(String afterImage) {
        this.afterImage = afterImage;
    }

    public String getReasonCode() {
        return reasonCode;
    }

    public void setReasonCode(String reasonCode) {
        this.reasonCode = reasonCode;
    }

    public LocalDateTime getProcessDate() {
        return processDate;
    }

    public void setProcessDate(LocalDateTime processDate) {
        this.processDate = processDate;
    }

    public String getProcessUser() {
        return processUser;
    }

    public void setProcessUser(String processUser) {
        this.processUser = processUser;
    }

}
