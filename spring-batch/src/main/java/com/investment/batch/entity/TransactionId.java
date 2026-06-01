package com.investment.batch.entity;

import java.io.Serializable;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Objects;

public class TransactionId implements Serializable {

    private LocalDate date;
    private LocalTime time;
    private String portfolioId;
    private String sequenceNo;

    public TransactionId() {}

    public TransactionId(LocalDate date, LocalTime time, String portfolioId, String sequenceNo) {
        this.date = date;
        this.time = time;
        this.portfolioId = portfolioId;
        this.sequenceNo = sequenceNo;
    }

    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }
    public LocalTime getTime() { return time; }
    public void setTime(LocalTime time) { this.time = time; }
    public String getPortfolioId() { return portfolioId; }
    public void setPortfolioId(String portfolioId) { this.portfolioId = portfolioId; }
    public String getSequenceNo() { return sequenceNo; }
    public void setSequenceNo(String sequenceNo) { this.sequenceNo = sequenceNo; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TransactionId that = (TransactionId) o;
        return Objects.equals(date, that.date) &&
               Objects.equals(time, that.time) &&
               Objects.equals(portfolioId, that.portfolioId) &&
               Objects.equals(sequenceNo, that.sequenceNo);
    }

    @Override
    public int hashCode() {
        return Objects.hash(date, time, portfolioId, sequenceNo);
    }
}
