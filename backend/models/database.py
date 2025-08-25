from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(9), unique=True, index=True)
    total_value = Column(Float)
    total_gain_loss = Column(Float)
    total_gain_loss_percent = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)


class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, index=True)
    symbol = Column(String(10))
    name = Column(String(100))
    shares = Column(Integer)
    current_price = Column(Float)
    market_value = Column(Float)
    gain_loss = Column(Float)
    gain_loss_percent = Column(Float)


SQLITE_DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
