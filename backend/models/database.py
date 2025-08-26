from sqlalchemy import create_engine, Column, String, Numeric, Date, DateTime, CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
    
    __table_args__ = (
        Index('idx_portfolio_status', 'status'),
        Index('idx_portfolio_client_type', 'client_type'),
    )


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


SQLITE_DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
