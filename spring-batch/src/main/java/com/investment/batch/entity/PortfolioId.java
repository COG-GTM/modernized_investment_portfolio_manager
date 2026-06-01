package com.investment.batch.entity;

import java.io.Serializable;
import java.util.Objects;

public class PortfolioId implements Serializable {

    private String portId;
    private String accountNo;

    public PortfolioId() {}

    public PortfolioId(String portId, String accountNo) {
        this.portId = portId;
        this.accountNo = accountNo;
    }

    public String getPortId() { return portId; }
    public void setPortId(String portId) { this.portId = portId; }
    public String getAccountNo() { return accountNo; }
    public void setAccountNo(String accountNo) { this.accountNo = accountNo; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        PortfolioId that = (PortfolioId) o;
        return Objects.equals(portId, that.portId) && Objects.equals(accountNo, that.accountNo);
    }

    @Override
    public int hashCode() {
        return Objects.hash(portId, accountNo);
    }
}
