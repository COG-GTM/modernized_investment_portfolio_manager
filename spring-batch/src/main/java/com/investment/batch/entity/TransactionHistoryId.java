package com.investment.batch.entity;

import java.io.Serializable;
import java.util.Objects;

public class TransactionHistoryId implements Serializable {

    private String portfolioId;
    private String date;
    private String time;
    private String seqNo;

    public TransactionHistoryId() {}

    public TransactionHistoryId(String portfolioId, String date, String time, String seqNo) {
        this.portfolioId = portfolioId;
        this.date = date;
        this.time = time;
        this.seqNo = seqNo;
    }

    public String getPortfolioId() { return portfolioId; }
    public void setPortfolioId(String portfolioId) { this.portfolioId = portfolioId; }
    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }
    public String getTime() { return time; }
    public void setTime(String time) { this.time = time; }
    public String getSeqNo() { return seqNo; }
    public void setSeqNo(String seqNo) { this.seqNo = seqNo; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TransactionHistoryId that = (TransactionHistoryId) o;
        return Objects.equals(portfolioId, that.portfolioId) &&
               Objects.equals(date, that.date) &&
               Objects.equals(time, that.time) &&
               Objects.equals(seqNo, that.seqNo);
    }

    @Override
    public int hashCode() {
        return Objects.hash(portfolioId, date, time, seqNo);
    }
}
