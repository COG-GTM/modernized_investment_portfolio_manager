from sqlalchemy.orm import Session
from models import Portfolio, Position, Transaction, History
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, date
import uuid

class PortfolioService:
    
    def __init__(self, db: Session):
        self.db = db
    
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
        """Apply a single transfer transaction to its portfolio's position.

        This is invoked by `process_transaction` when a Transaction with
        type='TR' is processed individually. A positive quantity adds
        shares to the portfolio (incoming transfer); a negative quantity
        removes shares (outgoing transfer).
        """
        position = self.db.query(Position).filter(
            Position.portfolio_id == transaction.portfolio_id,
            Position.investment_id == transaction.investment_id,
            Position.date == transaction.date,
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
                last_maint_user=transaction.process_user,
            )
            self.db.add(position)

        before_data = position.to_dict() if position.quantity else None

        delta_quantity = transaction.quantity or Decimal('0.00')
        delta_amount = transaction.amount or Decimal('0.00')

        position.quantity = (position.quantity or Decimal('0.00')) + delta_quantity
        position.cost_basis = (position.cost_basis or Decimal('0.00')) + delta_amount
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
            db_session=self.db,
        )
        self.db.add(audit_record)

    def transfer_positions(
        self,
        source_account: str,
        destination_account: str,
        positions: List[Dict],
        user: str = "SYSTEM",
    ) -> Dict:
        """Transfer the given positions from `source_account` to `destination_account`.

        Each entry in `positions` must have `symbol` (investment id) and
        `shares` (positive quantity). The transfer is atomic: any error
        rolls back every change and returns `success=False` with errors.
        """
        try:
            source_portfolio = self.db.query(Portfolio).filter(
                Portfolio.account_no == source_account
            ).first()
            if not source_portfolio:
                return {
                    "success": False,
                    "errors": [f"Source account {source_account} not found"],
                    "transfer_id": "",
                }

            destination_portfolio = self.db.query(Portfolio).filter(
                Portfolio.account_no == destination_account
            ).first()
            if not destination_portfolio:
                return {
                    "success": False,
                    "errors": [f"Destination account {destination_account} not found"],
                    "transfer_id": "",
                }

            today = date.today()
            now = datetime.now()
            transfer_id = uuid.uuid4().hex[:12].upper()

            for idx, entry in enumerate(positions, start=1):
                symbol = entry["symbol"]
                shares = Decimal(str(entry["shares"]))

                source_position = self.db.query(Position).filter(
                    Position.portfolio_id == source_portfolio.port_id,
                    Position.investment_id == symbol,
                    Position.status == 'A',
                ).order_by(Position.date.desc()).first()

                if not source_position:
                    raise ValueError(
                        f"Source account {source_account} has no position for {symbol}"
                    )

                if (source_position.quantity or Decimal('0.00')) < shares:
                    raise ValueError(
                        f"Insufficient shares of {symbol} in account {source_account}"
                    )

                cost_per_share = Decimal('0.00')
                if source_position.quantity and source_position.quantity > 0:
                    cost_per_share = (
                        source_position.cost_basis or Decimal('0.00')
                    ) / source_position.quantity
                transfer_cost = (cost_per_share * shares).quantize(Decimal('0.01'))
                price_per_share = Decimal('0.00')
                if source_position.market_value and source_position.quantity:
                    price_per_share = (
                        source_position.market_value / source_position.quantity
                    ).quantize(Decimal('0.0001'))

                outgoing_seq = f"{idx:06d}"
                incoming_seq = f"{idx + len(positions):06d}"

                outgoing = Transaction(
                    date=today,
                    time=now.time(),
                    portfolio_id=source_portfolio.port_id,
                    sequence_no=outgoing_seq,
                    investment_id=symbol,
                    type='TR',
                    quantity=-shares,
                    price=price_per_share,
                    amount=-transfer_cost,
                    currency=source_position.currency,
                    status='P',
                    process_date=now,
                    process_user=user,
                )
                incoming = Transaction(
                    date=today,
                    time=now.time(),
                    portfolio_id=destination_portfolio.port_id,
                    sequence_no=incoming_seq,
                    investment_id=symbol,
                    type='TR',
                    quantity=shares,
                    price=price_per_share,
                    amount=transfer_cost,
                    currency=source_position.currency,
                    status='P',
                    process_date=now,
                    process_user=user,
                )
                self.db.add_all([outgoing, incoming])

                self._apply_transfer_leg(outgoing, today, user)
                self._apply_transfer_leg(incoming, today, user)

                outgoing.transition_status('D', user)
                incoming.transition_status('D', user)

            source_portfolio.update_total_value()
            destination_portfolio.update_total_value()
            source_portfolio.last_user = user
            destination_portfolio.last_user = user

            self.db.commit()
            return {"success": True, "errors": [], "transfer_id": transfer_id}

        except Exception as exc:
            self.db.rollback()
            return {"success": False, "errors": [str(exc)], "transfer_id": ""}

    def _apply_transfer_leg(self, transaction: Transaction, position_date: date, user: str):
        """Apply one leg of a transfer (outgoing or incoming) to its position."""
        position = self.db.query(Position).filter(
            Position.portfolio_id == transaction.portfolio_id,
            Position.investment_id == transaction.investment_id,
            Position.date == position_date,
        ).first()

        if not position:
            position = Position(
                portfolio_id=transaction.portfolio_id,
                investment_id=transaction.investment_id,
                date=position_date,
                quantity=Decimal('0.00'),
                cost_basis=Decimal('0.00'),
                market_value=Decimal('0.00'),
                currency=transaction.currency,
                status='A',
                last_maint_date=datetime.now(),
                last_maint_user=user,
            )
            self.db.add(position)

        before_data = position.to_dict() if position.quantity else None

        delta_quantity = transaction.quantity or Decimal('0.00')
        delta_amount = transaction.amount or Decimal('0.00')
        delta_market = (
            (transaction.price or Decimal('0.00')) * delta_quantity
        ).quantize(Decimal('0.01'))

        position.quantity = (position.quantity or Decimal('0.00')) + delta_quantity
        position.cost_basis = (position.cost_basis or Decimal('0.00')) + delta_amount
        position.market_value = (position.market_value or Decimal('0.00')) + delta_market
        position.last_maint_date = datetime.now()
        position.last_maint_user = user

        audit_record = History.create_audit_record(
            portfolio_id=transaction.portfolio_id,
            record_type="PS",
            action_code="C",
            before_data=before_data,
            after_data=position.to_dict(),
            reason_code="TRAN",
            user=user,
            db_session=self.db,
        )
        self.db.add(audit_record)

    
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
