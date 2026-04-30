from sqlalchemy import String, DateTime, CheckConstraint, ForeignKeyConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

from .database import Base


class History(Base):
    __tablename__ = "history"

    portfolio_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    date: Mapped[str] = mapped_column(String(8), primary_key=True)
    time: Mapped[str] = mapped_column(String(8), primary_key=True)
    seq_no: Mapped[str] = mapped_column(String(4), primary_key=True)

    record_type: Mapped[Optional[str]] = mapped_column(
        String(2), CheckConstraint("record_type IN ('PT', 'PS', 'TR')"), nullable=True
    )
    action_code: Mapped[Optional[str]] = mapped_column(
        String(1), CheckConstraint("action_code IN ('A', 'C', 'D')"), nullable=True
    )
    before_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)

    process_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    process_user: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="history_records")

    __table_args__ = (
        ForeignKeyConstraint(
            ["portfolio_id"],
            ["portfolios.port_id"],
        ),
        Index("idx_history_portfolio_id", "portfolio_id"),
        Index("idx_history_date", "date"),
        Index("idx_history_record_type", "record_type"),
        Index("idx_history_action_code", "action_code"),
    )
