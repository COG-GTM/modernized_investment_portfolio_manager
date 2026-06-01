from fastapi import APIRouter, HTTPException, Depends
from models.portfolio import (
    CreateTransactionRequest,
    TransactionDBResponse,
    UpdateTransactionStatusRequest,
)
from models.database import Portfolio, SessionLocal, Base, engine
from models.transactions import Transaction
from sqlalchemy.orm import Session
from datetime import datetime, date, time
from decimal import Decimal
from typing import Generator

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["transactions"])


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_sequence_no(db: Session, portfolio_id: str, txn_date: date, txn_time: time) -> str:
    count = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.date == txn_date,
        Transaction.time == txn_time,
    ).count()
    return f"{count + 1:06d}"


@router.post("/transactions", response_model=TransactionDBResponse, status_code=201)
async def create_transaction(request: CreateTransactionRequest, db: Session = Depends(get_db)):
    """Record a new transaction"""
    portfolio = db.query(Portfolio).filter(Portfolio.port_id == request.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    now = datetime.now()
    txn_date = now.date()
    txn_time = now.time()
    seq_no = _generate_sequence_no(db, request.portfolio_id, txn_date, txn_time)

    quantity = Decimal(str(request.quantity)) if request.quantity is not None else None
    price = Decimal(str(request.price)) if request.price is not None else None
    amount = (quantity * price) if quantity is not None and price is not None else Decimal("0.00")

    transaction = Transaction(
        date=txn_date,
        time=txn_time,
        portfolio_id=request.portfolio_id,
        sequence_no=seq_no,
        investment_id=request.investment_id,
        type=request.type,
        quantity=quantity,
        price=price,
        amount=amount,
        currency=request.currency,
        status="P",
    )

    validation = transaction.validate_transaction()
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return TransactionDBResponse(
        date=transaction.date.isoformat() if transaction.date else None,
        time=transaction.time.isoformat() if transaction.time else None,
        portfolio_id=transaction.portfolio_id,
        sequence_no=transaction.sequence_no,
        investment_id=transaction.investment_id,
        type=transaction.type,
        quantity=float(transaction.quantity) if transaction.quantity else 0.0,
        price=float(transaction.price) if transaction.price else 0.0,
        amount=float(transaction.amount) if transaction.amount else 0.0,
        currency=transaction.currency,
        status=transaction.status,
        process_date=transaction.process_date.isoformat() if transaction.process_date else None,
        process_user=transaction.process_user,
    )


@router.put("/transactions/{portfolio_id}/{sequence_no}/status", response_model=TransactionDBResponse)
async def update_transaction_status(
    portfolio_id: str,
    sequence_no: str,
    request: UpdateTransactionStatusRequest,
    db: Session = Depends(get_db),
):
    """Update transaction status using state machine validation"""
    transaction = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.sequence_no == sequence_no,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if not transaction.can_transition_to(request.new_status):
        allowed = Transaction.VALID_STATUS_TRANSITIONS.get(transaction.status, [])
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{transaction.status}' to '{request.new_status}'. "
                   f"Valid transitions: {allowed}",
        )

    transaction.transition_status(request.new_status, request.user)
    db.commit()
    db.refresh(transaction)

    return TransactionDBResponse(
        date=transaction.date.isoformat() if transaction.date else None,
        time=transaction.time.isoformat() if transaction.time else None,
        portfolio_id=transaction.portfolio_id,
        sequence_no=transaction.sequence_no,
        investment_id=transaction.investment_id,
        type=transaction.type,
        quantity=float(transaction.quantity) if transaction.quantity else 0.0,
        price=float(transaction.price) if transaction.price else 0.0,
        amount=float(transaction.amount) if transaction.amount else 0.0,
        currency=transaction.currency,
        status=transaction.status,
        process_date=transaction.process_date.isoformat() if transaction.process_date else None,
        process_user=transaction.process_user,
    )
