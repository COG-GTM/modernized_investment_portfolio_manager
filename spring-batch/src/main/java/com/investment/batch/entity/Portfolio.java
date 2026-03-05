package com.investment.batch.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "portfolios")
@IdClass(PortfolioId.class)
public class Portfolio {

    @Id
    @Column(name = "port_id", length = 8)
    private String portId;

    @Id
    @Column(name = "account_no", length = 10)
    private String accountNo;

    @Column(name = "client_name", length = 30)
    private String clientName;

    @Column(name = "client_type", length = 1)
    private String clientType;

    @Column(name = "create_date")
    private LocalDate createDate;

    @Column(name = "last_maint")
    private LocalDate lastMaint;

    @Column(name = "status", length = 1)
    private String status;

    @Column(name = "total_value", precision = 15, scale = 2)
    private BigDecimal totalValue;

    @Column(name = "cash_balance", precision = 15, scale = 2)
    private BigDecimal cashBalance;

    @Column(name = "last_user", length = 8)
    private String lastUser;

    @Column(name = "last_trans", length = 8)
    private String lastTrans;

    public Portfolio() {}

    public String getPortId() { return portId; }
    public void setPortId(String portId) { this.portId = portId; }
    public String getAccountNo() { return accountNo; }
    public void setAccountNo(String accountNo) { this.accountNo = accountNo; }
    public String getClientName() { return clientName; }
    public void setClientName(String clientName) { this.clientName = clientName; }
    public String getClientType() { return clientType; }
    public void setClientType(String clientType) { this.clientType = clientType; }
    public LocalDate getCreateDate() { return createDate; }
    public void setCreateDate(LocalDate createDate) { this.createDate = createDate; }
    public LocalDate getLastMaint() { return lastMaint; }
    public void setLastMaint(LocalDate lastMaint) { this.lastMaint = lastMaint; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public BigDecimal getTotalValue() { return totalValue; }
    public void setTotalValue(BigDecimal totalValue) { this.totalValue = totalValue; }
    public BigDecimal getCashBalance() { return cashBalance; }
    public void setCashBalance(BigDecimal cashBalance) { this.cashBalance = cashBalance; }
    public String getLastUser() { return lastUser; }
    public void setLastUser(String lastUser) { this.lastUser = lastUser; }
    public String getLastTrans() { return lastTrans; }
    public void setLastTrans(String lastTrans) { this.lastTrans = lastTrans; }
}
