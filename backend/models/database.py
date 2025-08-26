from sqlalchemy import create_engine, Column, String, Numeric, Date, DateTime, CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, date

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    port_id = Column(String(8), primary_key=True)
    account_no = Column(String(10), primary_key=True)
    
    client_name = Column(String(30))
    client_type = Column(String(1), CheckConstraint("client_type IN ('I', 'C', 'T')"))
    
    create_date = Column(Date)
    last_maint = Column(Date)
    status = Column(String(1), CheckConstraint("status IN ('A', 'C', 'S')"))
    
    total_value = Column(Numeric(15, 2))
    cash_balance = Column(Numeric(15, 2))
    
    last_user = Column(String(8))
    last_trans = Column(String(8))
    
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    history_records = relationship("History", back_populates="portfolio", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_portfolio_status', 'status'),
        Index('idx_portfolio_client_type', 'client_type'),
    )
    
    def validate_portfolio(self) -> Dict[str, bool]:
        errors = []
        
        if not self.port_id or len(self.port_id) != 8:
            errors.append("Portfolio ID must be 8 characters")
        
        if not self.account_no or len(self.account_no) != 10:
            errors.append("Account number must be 10 characters")
            
        if self.client_type not in ['I', 'C', 'T']:
            errors.append("Invalid client type")
            
        if self.status not in ['A', 'C', 'S']:
            errors.append("Invalid status")
            
        return {"valid": len(errors) == 0, "errors": errors}
    
    def calculate_total_value(self) -> Decimal:
        total = Decimal('0.00')
        for position in self.positions:
            if position.status == 'A':
                total += position.market_value or Decimal('0.00')
        
        total += self.cash_balance or Decimal('0.00')
        return total
    
    def update_total_value(self):
        self.total_value = self.calculate_total_value()
        self.last_maint = date.today()
    
    def to_dict(self) -> Dict:
        return {
            "port_id": self.port_id,
            "account_no": self.account_no,
            "client_name": self.client_name,
            "client_type": self.client_type,
            "create_date": self.create_date.isoformat() if self.create_date else None,
            "last_maint": self.last_maint.isoformat() if self.last_maint else None,
            "status": self.status,
            "total_value": float(self.total_value) if self.total_value else 0.0,
            "cash_balance": float(self.cash_balance) if self.cash_balance else 0.0,
            "last_user": self.last_user,
            "last_trans": self.last_trans
        }


class Position(Base):
    __tablename__ = "positions"
    
    portfolio_id = Column(String(8), primary_key=True)
    date = Column(Date, primary_key=True)
    investment_id = Column(String(10), primary_key=True)
    
    quantity = Column(Numeric(15, 4))
    cost_basis = Column(Numeric(15, 2))
    market_value = Column(Numeric(15, 2))
    currency = Column(String(3))
    status = Column(String(1), CheckConstraint("status IN ('A', 'C', 'P')"))
    
    last_maint_date = Column(DateTime)
    last_maint_user = Column(String(8))
    
    portfolio = relationship("Portfolio", back_populates="positions")
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['portfolio_id'], 
            ['portfolios.port_id']
        ),
        Index('idx_position_portfolio_id', 'portfolio_id'),
        Index('idx_position_date', 'date'),
        Index('idx_position_investment_id', 'investment_id'),
        Index('idx_position_status', 'status'),
    )
    
    def calculate_gain_loss(self) -> Dict[str, Decimal]:
        if not self.cost_basis or not self.market_value:
            return {"gain_loss": Decimal('0.00'), "gain_loss_percent": Decimal('0.00')}
        
        gain_loss = self.market_value - self.cost_basis
        gain_loss_percent = (gain_loss / self.cost_basis) * 100 if self.cost_basis != 0 else Decimal('0.00')
        
        return {
            "gain_loss": gain_loss,
            "gain_loss_percent": gain_loss_percent
        }
    
    def validate_position(self) -> Dict[str, bool]:
        errors = []
        
        if not self.portfolio_id or len(self.portfolio_id) != 8:
            errors.append("Portfolio ID must be 8 characters")
            
        if not self.investment_id or len(self.investment_id) != 10:
            errors.append("Investment ID must be 10 characters")
            
        if self.status not in ['A', 'C', 'P']:
            errors.append("Invalid status")
            
        if self.quantity and self.quantity < 0:
            errors.append("Quantity cannot be negative")
            
        return {"valid": len(errors) == 0, "errors": errors}
    
    def to_dict(self) -> Dict:
        gain_loss_data = self.calculate_gain_loss()
        return {
            "portfolio_id": self.portfolio_id,
            "date": self.date.isoformat() if self.date else None,
            "investment_id": self.investment_id,
            "quantity": float(self.quantity) if self.quantity else 0.0,
            "cost_basis": float(self.cost_basis) if self.cost_basis else 0.0,
            "market_value": float(self.market_value) if self.market_value else 0.0,
            "currency": self.currency,
            "status": self.status,
            "gain_loss": float(gain_loss_data["gain_loss"]),
            "gain_loss_percent": float(gain_loss_data["gain_loss_percent"]),
            "last_maint_date": self.last_maint_date.isoformat() if self.last_maint_date else None,
            "last_maint_user": self.last_maint_user
        }


SQLITE_DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
