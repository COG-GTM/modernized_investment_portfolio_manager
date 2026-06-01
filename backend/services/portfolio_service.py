from sqlalchemy.orm import Session, joinedload
from fastapi import Depends
from models import Portfolio, Position, Transaction, History, SessionLocal
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, date
import json


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PortfolioService:

    VALID_STATUS_TRANSITIONS = {
        'P': ['D', 'F'],
        'D': ['R'],
        'F': ['P'],
        'R': []
    }

    def __init__(self, db: Session):
        self.db = db

    # ── Query methods ────────────────────────────────────────────────

    def get_portfolio(self, port_id: str, account_no: str | None = None) -> Portfolio | None:
        query = self.db.query(Portfolio).filter(Portfolio.port_id == port_id)
        if account_no:
            query = query.filter(Portfolio.account_no == account_no)
        return query.first()

    def get_portfolio_with_positions(self, port_id: str) -> Portfolio | None:
        return self.db.query(Portfolio).options(
            joinedload(Portfolio.positions)
        ).filter(Portfolio.port_id == port_id).first()

    def list_portfolios(self, status: str | None = None) -> list[Portfolio]:
        query = self.db.query(Portfolio)
        if status:
            query = query.filter(Portfolio.status == status)
        return query.all()

    def get_positions(self, portfolio_id: str) -> list[Position]:
        return self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.status == 'A'
        ).all()

    # ── Business-logic helpers (service-owned equivalents) ───────────

    def validate_transaction(self, transaction: Transaction) -> Dict[str, bool]:
        errors: List[str] = []

        if not transaction.portfolio_id or len(transaction.portfolio_id) != 8:
            errors.append("Portfolio ID must be 8 characters")

        if not transaction.sequence_no or len(transaction.sequence_no) != 6:
            errors.append("Sequence number must be 6 characters")

        if transaction.type not in ['BU', 'SL', 'TR', 'FE']:
            errors.append("Invalid transaction type")

        if transaction.status not in ['P', 'D', 'F', 'R']:
            errors.append("Invalid status")

        if transaction.type in ['BU', 'SL'] and not transaction.investment_id:
            errors.append("Investment ID required for buy/sell transactions")

        if transaction.type in ['BU', 'SL'] and (not transaction.quantity or transaction.quantity <= 0):
            errors.append("Positive quantity required for buy/sell transactions")

        if transaction.type in ['BU', 'SL'] and (not transaction.price or transaction.price <= 0):
            errors.append("Positive price required for buy/sell transactions")

        return {"valid": len(errors) == 0, "errors": errors}

    def calculate_total_value(self, portfolio: Portfolio) -> Decimal:
        total = Decimal('0.00')
        for position in portfolio.positions:
            if position.status == 'A':
                total += position.market_value or Decimal('0.00')
        total += portfolio.cash_balance or Decimal('0.00')
        return total

    def create_audit_record(
        self,
        portfolio_id: str,
        record_type: str,
        action_code: str,
        before_data: Optional[Dict] = None,
        after_data: Optional[Dict] = None,
        reason_code: str = "AUTO",
        user: str = "SYSTEM",
    ) -> History:
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S%f")[:8]

        existing_count = self.db.query(History).filter(
            History.portfolio_id == portfolio_id,
            History.date == date_str,
            History.time == time_str
        ).count()
        seq_no = f"{existing_count + 1:04d}"

        return History(
            portfolio_id=portfolio_id,
            date=date_str,
            time=time_str,
            seq_no=seq_no,
            record_type=record_type,
            action_code=action_code,
            before_image=json.dumps(before_data) if before_data else None,
            after_image=json.dumps(after_data) if after_data else None,
            reason_code=reason_code,
            process_date=now,
            process_user=user,
        )

    # ── Transaction processing ───────────────────────────────────────

    def process_transaction(self, transaction: Transaction) -> Dict[str, bool]:
        try:
            validation = transaction.validate_transaction()
            if not validation["valid"]:
                return {"success": False, "errors": validation["errors"]}

            audit_record = History.create_audit_record(
                portfolio_id=transaction.portfolio_id,
                record_type="TR",
                action_code="A",
                after_data=transaction.to_dict(),
                reason_code="PROC",
                user=transaction.process_user or "SYSTEM",
                db_session=self.db
            )
            self.db.add(audit_record)

            if transaction.type in ['BU', 'SL']:
                self._process_buy_sell_transaction(transaction)
            elif transaction.type == 'TR':
                self._process_transfer_transaction(transaction)
            elif transaction.type == 'FE':
                self._process_fee_transaction(transaction)

            transaction.transition_status('D', transaction.process_user or "SYSTEM")

            portfolio = self.db.query(Portfolio).filter(
                Portfolio.port_id == transaction.portfolio_id
            ).first()
            if portfolio:
                portfolio.update_total_value()

            self.db.commit()
            return {"success": True, "errors": []}

        except Exception as e:
            self.db.rollback()
            transaction.transition_status('F', transaction.process_user or "SYSTEM")
            return {"success": False, "errors": [str(e)]}

    def _process_buy_sell_transaction(self, transaction: Transaction):
        position = self.db.query(Position).filter(
            Position.portfolio_id == transaction.portfolio_id,
            Position.investment_id == transaction.investment_id,
            Position.date == transaction.date
        ).first()

        if not position:
            position = Position(
                portfolio_id=transaction.portfolio_id,
                investment_id=transaction.investment_id,
                date=transaction.date,
                quantity=Decimal('0.00'),
                cost_basis=Decimal('0.00'),
                market_value=Decimal('0.00'),
                currency=transaction.currency,
                status='A',
                last_maint_date=datetime.now(),
                last_maint_user=transaction.process_user
            )
            self.db.add(position)

        before_data = position.to_dict() if position.quantity else None

        if transaction.type == 'BU':
            new_quantity = (position.quantity or Decimal('0.00')) + transaction.quantity
            new_cost_basis = (position.cost_basis or Decimal('0.00')) + transaction.amount
            position.quantity = new_quantity
            position.cost_basis = new_cost_basis
        elif transaction.type == 'SL':
            new_quantity = (position.quantity or Decimal('0.00')) - transaction.quantity
            if position.quantity and position.quantity > 0:
                cost_per_share = position.cost_basis / position.quantity
                cost_reduction = transaction.quantity * cost_per_share
                position.cost_basis = (position.cost_basis or Decimal('0.00')) - cost_reduction
            position.quantity = new_quantity

        position.last_maint_date = datetime.now()
        position.last_maint_user = transaction.process_user

        audit_record = History.create_audit_record(
            portfolio_id=transaction.portfolio_id,
            record_type="PS",
            action_code="C",
            before_data=before_data,
            after_data=position.to_dict(),
            reason_code="TRAN",
            user=transaction.process_user or "SYSTEM",
            db_session=self.db
        )
        self.db.add(audit_record)

    def _process_transfer_transaction(self, transaction: Transaction):
        pass

    def _process_fee_transaction(self, transaction: Transaction):
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.port_id == transaction.portfolio_id
        ).first()

        if portfolio:
            before_data = portfolio.to_dict()
            portfolio.cash_balance = (portfolio.cash_balance or Decimal('0.00')) - transaction.amount
            portfolio.last_maint = date.today()
            portfolio.last_user = transaction.process_user

            audit_record = History.create_audit_record(
                portfolio_id=transaction.portfolio_id,
                record_type="PT",
                action_code="C",
                before_data=before_data,
                after_data=portfolio.to_dict(),
                reason_code="FEE",
                user=transaction.process_user or "SYSTEM",
                db_session=self.db
            )
            self.db.add(audit_record)

    # ── FastAPI Dependency Injection ─────────────────────────────────

    @classmethod
    def get_service(cls, db: Session = Depends(get_db)) -> "PortfolioService":
        return cls(db)
