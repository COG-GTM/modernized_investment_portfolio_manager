from sqlalchemy.orm import Session
from models import Portfolio, Position, Transaction, History
from models.portfolio import StatusUpdateRequest, ClientNameUpdateRequest, ValueUpdateRequest
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
    
    def update_portfolio_status(self, request: StatusUpdateRequest) -> Dict[str, any]:
        """Update portfolio status (COBOL UPDT-STATUS equivalent)"""
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.port_id == request.portfolio_id,
                Portfolio.account_no == request.account_no
            ).first()
            
            if not portfolio:
                return {"success": False, "errors": ["Portfolio not found"], "portfolio_id": request.portfolio_id}
            
            before_data = portfolio.to_dict()
            
            portfolio.status = request.new_status
            portfolio.last_maint = date.today()
            portfolio.last_user = request.user
            
            audit_record = History.create_audit_record(
                portfolio_id=request.portfolio_id,
                record_type="PT",
                action_code="C",
                before_data=before_data,
                after_data=portfolio.to_dict(),
                reason_code="STAT",
                user=request.user,
                db_session=self.db
            )
            self.db.add(audit_record)
            
            self.db.commit()
            return {"success": True, "errors": [], "portfolio_id": request.portfolio_id}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "errors": [str(e)], "portfolio_id": request.portfolio_id}
    
    def update_portfolio_client_name(self, request: ClientNameUpdateRequest) -> Dict[str, any]:
        """Update portfolio client name (COBOL UPDT-NAME equivalent)"""
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.port_id == request.portfolio_id,
                Portfolio.account_no == request.account_no
            ).first()
            
            if not portfolio:
                return {"success": False, "errors": ["Portfolio not found"], "portfolio_id": request.portfolio_id}
            
            before_data = portfolio.to_dict()
            
            portfolio.client_name = request.new_client_name
            portfolio.last_maint = date.today()
            portfolio.last_user = request.user
            
            audit_record = History.create_audit_record(
                portfolio_id=request.portfolio_id,
                record_type="PT",
                action_code="C",
                before_data=before_data,
                after_data=portfolio.to_dict(),
                reason_code="NAME",
                user=request.user,
                db_session=self.db
            )
            self.db.add(audit_record)
            
            self.db.commit()
            return {"success": True, "errors": [], "portfolio_id": request.portfolio_id}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "errors": [str(e)], "portfolio_id": request.portfolio_id}
    
    def update_portfolio_value(self, request: ValueUpdateRequest) -> Dict[str, any]:
        """Update portfolio total value (COBOL UPDT-VALUE equivalent)"""
        try:
            portfolio = self.db.query(Portfolio).filter(
                Portfolio.port_id == request.portfolio_id,
                Portfolio.account_no == request.account_no
            ).first()
            
            if not portfolio:
                return {"success": False, "errors": ["Portfolio not found"], "portfolio_id": request.portfolio_id}
            
            before_data = portfolio.to_dict()
            
            portfolio.total_value = Decimal(str(request.new_total_value))
            portfolio.last_maint = date.today()
            portfolio.last_user = request.user
            
            audit_record = History.create_audit_record(
                portfolio_id=request.portfolio_id,
                record_type="PT",
                action_code="C",
                before_data=before_data,
                after_data=portfolio.to_dict(),
                reason_code="VALU",
                user=request.user,
                db_session=self.db
            )
            self.db.add(audit_record)
            
            self.db.commit()
            return {"success": True, "errors": [], "portfolio_id": request.portfolio_id}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "errors": [str(e)], "portfolio_id": request.portfolio_id}
