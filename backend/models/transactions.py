from sqlalchemy import Column, String, Numeric, Date, Time, DateTime, CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, date

class Transaction(Base):
    __tablename__ = "transactions"
    
    date = Column(Date, primary_key=True)
    time = Column(Time, primary_key=True)
    portfolio_id = Column(String(8), primary_key=True)
    sequence_no = Column(String(6), primary_key=True)
    
    investment_id = Column(String(10))
    type = Column(String(2), CheckConstraint("type IN ('BU', 'SL', 'TR', 'FE')"))
    quantity = Column(Numeric(15, 4))
    price = Column(Numeric(15, 4))
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    status = Column(String(1), CheckConstraint("status IN ('P', 'D', 'F', 'R')"))
    
    process_date = Column(DateTime)
    process_user = Column(String(8))
    
    portfolio = relationship("Portfolio", back_populates="transactions")
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['portfolio_id'], 
            ['portfolios.port_id']
        ),
        Index('idx_transaction_portfolio_id', 'portfolio_id'),
        Index('idx_transaction_date', 'date'),
        Index('idx_transaction_investment_id', 'investment_id'),
        Index('idx_transaction_type', 'type'),
        Index('idx_transaction_status', 'status'),
    )
    
    VALID_STATUS_TRANSITIONS = {
        'P': ['D', 'F'],
        'D': ['R'],
        'F': ['P'],
        'R': []
    }
    
    def validate_transaction(self) -> Dict[str, bool]:
        errors = []
        
        if not self.portfolio_id or len(self.portfolio_id) != 8:
            errors.append("Portfolio ID must be 8 characters")
            
        if not self.sequence_no or len(self.sequence_no) != 6:
            errors.append("Sequence number must be 6 characters")
            
        if self.type not in ['BU', 'SL', 'TR', 'FE']:
            errors.append("Invalid transaction type")
            
        if self.status not in ['P', 'D', 'F', 'R']:
            errors.append("Invalid status")
            
        if self.type in ['BU', 'SL'] and not self.investment_id:
            errors.append("Investment ID required for buy/sell transactions")
            
        if self.type in ['BU', 'SL'] and (not self.quantity or self.quantity <= 0):
            errors.append("Positive quantity required for buy/sell transactions")
            
        if self.type in ['BU', 'SL'] and (not self.price or self.price <= 0):
            errors.append("Positive price required for buy/sell transactions")
            
        return {"valid": len(errors) == 0, "errors": errors}
    
    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.VALID_STATUS_TRANSITIONS.get(self.status, [])
    
    def transition_status(self, new_status: str, user: str) -> bool:
        if not self.can_transition_to(new_status):
            return False
            
        self.status = new_status
        self.process_date = datetime.now()
        self.process_user = user
        return True
    
    def calculate_transaction_amount(self) -> Decimal:
        if self.quantity and self.price:
            return self.quantity * self.price
        return Decimal('0.00')
    
    def update_amount(self):
        self.amount = self.calculate_transaction_amount()
    
    def to_dict(self) -> Dict:
        return {
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.isoformat() if self.time else None,
            "portfolio_id": self.portfolio_id,
            "sequence_no": self.sequence_no,
            "investment_id": self.investment_id,
            "type": self.type,
            "quantity": float(self.quantity) if self.quantity else 0.0,
            "price": float(self.price) if self.price else 0.0,
            "amount": float(self.amount) if self.amount else 0.0,
            "currency": self.currency,
            "status": self.status,
            "process_date": self.process_date.isoformat() if self.process_date else None,
            "process_user": self.process_user
        }
