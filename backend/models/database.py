from sqlalchemy import String, Numeric, Date, DateTime, CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from decimal import Decimal
from typing import Optional
from datetime import datetime, date


class Base(DeclarativeBase):
    pass


class Portfolio(Base):
    __tablename__ = "portfolios"

    port_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    account_no: Mapped[str] = mapped_column(String(10), primary_key=True)

    client_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    client_type: Mapped[Optional[str]] = mapped_column(
        String(1), CheckConstraint("client_type IN ('I', 'C', 'T')"), nullable=True
    )

    create_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_maint: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(
        String(1), CheckConstraint("status IN ('A', 'C', 'S')"), nullable=True
    )

    total_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    cash_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    last_user: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    last_trans: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    positions: Mapped[list["Position"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    history_records: Mapped[list["History"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_portfolio_status", "status"),
        Index("idx_portfolio_client_type", "client_type"),
    )


class Position(Base):
    __tablename__ = "positions"

    portfolio_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    investment_id: Mapped[str] = mapped_column(String(10), primary_key=True)

    quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    cost_basis: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(
        String(1), CheckConstraint("status IN ('A', 'C', 'P')"), nullable=True
    )

    last_maint_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_maint_user: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")

    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id"],
            ["portfolios.port_id"],
        ),
        Index("idx_position_portfolio_id", "portfolio_id"),
        Index("idx_position_date", "date"),
        Index("idx_position_investment_id", "investment_id"),
        Index("idx_position_status", "status"),
    )
