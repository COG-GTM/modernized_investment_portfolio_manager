from sqlalchemy.orm import Session
from models.database import Portfolio, Position
from models.transactions import Transaction
from models.inquiry import (
    PositionResponse,
    PortfolioInquiryResponse,
    PortfolioSummaryInfo,
    HistoryInquiryResponse,
    TransactionDetail,
    MenuOption,
    MenuResponse,
)
from decimal import Decimal
from typing import List


class InquiryService:

    def __init__(self, db: Session):
        self.db = db

    def get_portfolio_positions(self, account_number: str) -> PortfolioInquiryResponse:
        portfolio = (
            self.db.query(Portfolio)
            .filter(Portfolio.account_no == account_number)
            .first()
        )

        if not portfolio:
            return PortfolioInquiryResponse(
                account_number=account_number,
                positions=[],
                portfolio_summary=None,
                message=f"Position not found for account {account_number}",
            )

        positions = (
            self.db.query(Position)
            .filter(
                Position.portfolio_id == portfolio.port_id,
                Position.status == "A",
            )
            .all()
        )

        position_responses: List[PositionResponse] = []
        for pos in positions:
            gl = pos.calculate_gain_loss()
            position_responses.append(
                PositionResponse(
                    portfolio_id=pos.portfolio_id,
                    date=pos.date.isoformat() if pos.date else None,
                    investment_id=pos.investment_id,
                    quantity=pos.quantity or Decimal("0"),
                    cost_basis=pos.cost_basis or Decimal("0"),
                    market_value=pos.market_value or Decimal("0"),
                    currency=pos.currency or "USD",
                    status=pos.status or "A",
                    gain_loss=gl["gain_loss"],
                    gain_loss_percent=gl["gain_loss_percent"],
                    last_maint_date=(
                        pos.last_maint_date.isoformat() if pos.last_maint_date else None
                    ),
                    last_maint_user=pos.last_maint_user,
                )
            )

        summary = PortfolioSummaryInfo(
            portfolio_id=portfolio.port_id,
            client_name=portfolio.client_name,
            total_value=portfolio.total_value or Decimal("0"),
            cash_balance=portfolio.cash_balance or Decimal("0"),
            status=portfolio.status,
        )

        return PortfolioInquiryResponse(
            account_number=account_number,
            positions=position_responses,
            portfolio_summary=summary,
            message="Portfolio inquiry successful",
        )

    def get_transaction_history(self, account_number: str) -> HistoryInquiryResponse:
        portfolio = (
            self.db.query(Portfolio)
            .filter(Portfolio.account_no == account_number)
            .first()
        )

        if not portfolio:
            return HistoryInquiryResponse(
                account_number=account_number,
                transactions=[],
                message=f"No portfolio found for account {account_number}",
            )

        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio.port_id)
            .order_by(Transaction.date.desc())
            .all()
        )

        transaction_details: List[TransactionDetail] = []
        for txn in transactions:
            transaction_details.append(
                TransactionDetail(
                    date=txn.date.isoformat() if txn.date else None,
                    time=txn.time.isoformat() if txn.time else None,
                    portfolio_id=txn.portfolio_id,
                    sequence_no=txn.sequence_no,
                    investment_id=txn.investment_id,
                    type=txn.type,
                    quantity=txn.quantity,
                    price=txn.price,
                    amount=txn.amount,
                    currency=txn.currency,
                    status=txn.status,
                    process_date=(
                        txn.process_date.isoformat() if txn.process_date else None
                    ),
                    process_user=txn.process_user,
                )
            )

        return HistoryInquiryResponse(
            account_number=account_number,
            transactions=transaction_details,
            message="Transaction history inquiry successful",
        )

    def get_menu_options(self) -> MenuResponse:
        options = [
            MenuOption(code="INQP", description="Portfolio Position Inquiry"),
            MenuOption(code="INQH", description="Transaction History Inquiry"),
            MenuOption(code="EXIT", description="Exit Application"),
        ]
        return MenuResponse(options=options)
