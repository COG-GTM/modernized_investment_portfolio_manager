from sqlalchemy.orm import Session
from models.database import Portfolio, Position
from models.transactions import Transaction
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional


class InquiryService:

    def __init__(self, db: Session):
        self.db = db

    def get_portfolio_positions(self, account_number: str) -> Optional[Dict]:
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.account_no == account_number
        ).first()

        if not portfolio:
            return None

        positions = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.port_id,
            Position.status == 'A'
        ).all()

        total_cost_basis = Decimal('0.00')
        total_market_value = Decimal('0.00')
        position_details = []

        for pos in positions:
            cost_basis = pos.cost_basis or Decimal('0.00')
            market_value = pos.market_value or Decimal('0.00')
            gain_loss = market_value - cost_basis
            gain_loss_percent = (
                (gain_loss / cost_basis) * Decimal('100')
                if cost_basis != Decimal('0.00')
                else Decimal('0.00')
            )

            total_cost_basis += cost_basis
            total_market_value += market_value

            position_details.append({
                "portfolioId": pos.portfolio_id,
                "investmentId": pos.investment_id,
                "positionDate": pos.date.isoformat() if pos.date else None,
                "quantity": float(pos.quantity) if pos.quantity else 0.0,
                "costBasis": float(cost_basis),
                "marketValue": float(market_value),
                "currency": pos.currency or "USD",
                "status": pos.status or "A",
                "gainLoss": float(gain_loss),
                "gainLossPercent": float(gain_loss_percent),
                "lastMaintDate": pos.last_maint_date.isoformat() if pos.last_maint_date else None,
                "lastMaintUser": pos.last_maint_user,
            })

        total_gain_loss = total_market_value - total_cost_basis
        total_gain_loss_percent = (
            (total_gain_loss / total_cost_basis) * Decimal('100')
            if total_cost_basis != Decimal('0.00')
            else Decimal('0.00')
        )

        return {
            "accountNumber": account_number,
            "portfolioId": portfolio.port_id,
            "portfolioName": None,
            "clientName": portfolio.client_name,
            "clientType": portfolio.client_type,
            "status": portfolio.status,
            "totalValue": float(portfolio.total_value) if portfolio.total_value else float(total_market_value),
            "totalCostBasis": float(total_cost_basis),
            "totalGainLoss": float(total_gain_loss),
            "totalGainLossPercent": float(total_gain_loss_percent),
            "cashBalance": float(portfolio.cash_balance) if portfolio.cash_balance else 0.0,
            "currency": "USD",
            "positions": position_details,
            "lastUpdated": datetime.now().strftime("%B %d, %Y, %I:%M %p"),
        }

    def get_transaction_history(self, account_number: str, limit: int = 10) -> Optional[Dict]:
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.account_no == account_number
        ).first()

        if not portfolio:
            return None

        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.port_id)
            .order_by(Transaction.date.desc())
            .limit(limit)
            .all()
        )

        total_count = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.port_id)
            .count()
        )

        entries = []
        for txn in transactions:
            entries.append({
                "transactionDate": txn.date.isoformat() if txn.date else None,
                "transactionType": txn.type or "",
                "quantity": float(txn.quantity) if txn.quantity else 0.0,
                "price": float(txn.price) if txn.price else 0.0,
                "amount": float(txn.amount) if txn.amount else 0.0,
                "investmentId": txn.investment_id,
                "status": txn.status,
            })

        return {
            "accountNumber": account_number,
            "portfolioId": portfolio.port_id,
            "entries": entries,
            "totalEntries": total_count,
            "hasMore": total_count > limit,
            "message": f"Retrieved {len(entries)} of {total_count} transactions",
        }
