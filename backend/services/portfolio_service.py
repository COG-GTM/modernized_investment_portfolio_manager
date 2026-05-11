from sqlalchemy.orm import Session
from models import Portfolio, Position, Transaction, History
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, date

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
        dest_portfolio_id = getattr(transaction, '_dest_portfolio_id', None)
        if not dest_portfolio_id:
            raise ValueError("Transfer transaction missing destination portfolio id")
        if dest_portfolio_id == transaction.portfolio_id:
            raise ValueError("Source and destination portfolios must differ")
        if not transaction.investment_id:
            raise ValueError("Investment ID required for transfer transaction")
        if not transaction.quantity or transaction.quantity <= 0:
            raise ValueError("Positive quantity required for transfer transaction")

        source_position = self.db.query(Position).filter(
            Position.portfolio_id == transaction.portfolio_id,
            Position.investment_id == transaction.investment_id,
            Position.status == 'A'
        ).order_by(Position.date.desc()).first()

        if not source_position:
            raise ValueError(
                f"No active source position found for portfolio {transaction.portfolio_id} "
                f"and investment {transaction.investment_id}"
            )

        if (source_position.quantity or Decimal('0.0000')) < transaction.quantity:
            raise ValueError(
                f"Insufficient quantity in source position: have "
                f"{source_position.quantity}, requested {transaction.quantity}"
            )

        source_before = source_position.to_dict()

        original_quantity = source_position.quantity or Decimal('0.0000')
        transfer_ratio = transaction.quantity / original_quantity if original_quantity > 0 else Decimal('0')
        transferred_cost_basis = (source_position.cost_basis or Decimal('0.00')) * transfer_ratio
        transferred_market_value = (source_position.market_value or Decimal('0.00')) * transfer_ratio

        source_position.quantity = original_quantity - transaction.quantity
        source_position.cost_basis = (source_position.cost_basis or Decimal('0.00')) - transferred_cost_basis
        source_position.market_value = (source_position.market_value or Decimal('0.00')) - transferred_market_value
        source_position.last_maint_date = datetime.now()
        source_position.last_maint_user = transaction.process_user

        source_audit = History.create_audit_record(
            portfolio_id=transaction.portfolio_id,
            record_type="PS",
            action_code="C",
            before_data=source_before,
            after_data=source_position.to_dict(),
            reason_code="XFER",
            user=transaction.process_user or "SYSTEM",
            db_session=self.db
        )
        self.db.add(source_audit)

        dest_position = self.db.query(Position).filter(
            Position.portfolio_id == dest_portfolio_id,
            Position.investment_id == transaction.investment_id,
            Position.date == transaction.date
        ).first()

        dest_before = dest_position.to_dict() if dest_position else None

        if not dest_position:
            dest_position = Position(
                portfolio_id=dest_portfolio_id,
                investment_id=transaction.investment_id,
                date=transaction.date,
                quantity=Decimal('0.0000'),
                cost_basis=Decimal('0.00'),
                market_value=Decimal('0.00'),
                currency=transaction.currency or source_position.currency,
                status='A',
                last_maint_date=datetime.now(),
                last_maint_user=transaction.process_user
            )
            self.db.add(dest_position)

        dest_position.quantity = (dest_position.quantity or Decimal('0.0000')) + transaction.quantity
        dest_position.cost_basis = (dest_position.cost_basis or Decimal('0.00')) + transferred_cost_basis
        dest_position.market_value = (dest_position.market_value or Decimal('0.00')) + transferred_market_value
        dest_position.last_maint_date = datetime.now()
        dest_position.last_maint_user = transaction.process_user

        dest_audit = History.create_audit_record(
            portfolio_id=dest_portfolio_id,
            record_type="PS",
            action_code="C" if dest_before else "A",
            before_data=dest_before,
            after_data=dest_position.to_dict(),
            reason_code="XFER",
            user=transaction.process_user or "SYSTEM",
            db_session=self.db
        )
        self.db.add(dest_audit)

        dest_portfolio = self.db.query(Portfolio).filter(
            Portfolio.port_id == dest_portfolio_id
        ).first()
        if dest_portfolio:
            dest_portfolio.update_total_value()
    
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
