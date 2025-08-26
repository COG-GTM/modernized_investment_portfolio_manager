from sqlalchemy import Column, String, Numeric, CheckConstraint, ForeignKeyConstraint, Index
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    date = Column(String(8), primary_key=True)
    time = Column(String(6), primary_key=True)
    portfolio_id = Column(String(8), primary_key=True)
    sequence_no = Column(String(6), primary_key=True)
    
    investment_id = Column(String(10))
    type = Column(String(2), CheckConstraint("type IN ('BU', 'SL', 'TR', 'FE')"))
    quantity = Column(Numeric(15, 4))
    price = Column(Numeric(15, 4))
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    status = Column(String(1), CheckConstraint("status IN ('P', 'D', 'F', 'R')"))
    
    process_date = Column(String(26))
    process_user = Column(String(8))
    
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
