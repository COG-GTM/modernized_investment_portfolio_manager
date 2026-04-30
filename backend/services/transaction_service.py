from sqlalchemy.orm import Session
from fastapi import Depends
from models import Transaction, Portfolio, History
from typing import Optional
from datetime import date, time

from .portfolio_service import get_db


class TransactionService:
    VALID_STATUS_TRANSITIONS = {
        'P': ['D', 'F'],
        'D': ['R'],
        'F': ['P'],
        'R': []
    }

    def __init__(self, db: Session):
        self.db = db

    def get_transactions(self, portfolio_id: str, status: str | None = None) -> list[Transaction]:
        query = self.db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        )
        if status:
            query = query.filter(Transaction.status == status)
        return query.order_by(Transaction.date.desc(), Transaction.time.desc()).all()

    def get_transaction(self, portfolio_id: str, date: date, time: time, sequence_no: str) -> Transaction | None:
        return self.db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id,
            Transaction.date == date,
            Transaction.time == time,
            Transaction.sequence_no == sequence_no
        ).first()

    def can_transition_to(self, current_status: str, new_status: str) -> bool:
        return new_status in self.VALID_STATUS_TRANSITIONS.get(current_status, [])

    @classmethod
    def get_service(cls, db: Session = Depends(get_db)) -> "TransactionService":
        return cls(db)
