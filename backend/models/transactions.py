from sqlalchemy import String, Numeric, Date, Time, DateTime, CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from typing import Optional
from datetime import datetime, date, time

from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    time: Mapped[time] = mapped_column(Time, primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    sequence_no: Mapped[str] = mapped_column(String(6), primary_key=True)

    investment_id: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(
        String(2), CheckConstraint("type IN ('BU', 'SL', 'TR', 'FE')"), nullable=True
    )
    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(
        String(1), CheckConstraint("status IN ('P', 'D', 'F', 'R')"), nullable=True
    )

    process_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    process_user: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="transactions")

    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id"],
            ["portfolios.port_id"],
        ),
        Index("idx_transaction_portfolio_id", "portfolio_id"),
        Index("idx_transaction_date", "date"),
        Index("idx_transaction_investment_id", "investment_id"),
        Index("idx_transaction_type", "type"),
        Index("idx_transaction_status", "status"),
    )
