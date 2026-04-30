from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Portfolio, Position, Transaction, SessionLocal
from validation.portfolio import validate_account_number

router = APIRouter(prefix="/api", tags=["portfolio"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/portfolio/{account_number}")
async def get_portfolio(account_number: str, db: Session = Depends(get_db)):
    """Get portfolio summary and holdings for an account"""
    is_valid, message = validate_account_number(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    portfolio = db.query(Portfolio).filter(
        Portfolio.account_no == account_number
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    positions = db.query(Position).filter(
        Position.portfolio_id == portfolio.port_id,
        Position.status == 'A'
    ).all()

    holdings = []
    total_gain_loss = 0.0
    total_cost = 0.0
    for pos in positions:
        mv = float(pos.market_value or 0)
        cb = float(pos.cost_basis or 0)
        gl = mv - cb
        gl_pct = (gl / cb * 100) if cb else 0.0
        holdings.append({
            "symbol": pos.investment_id,
            "name": pos.investment_id,
            "shares": int(pos.quantity or 0),
            "currentPrice": round(mv / float(pos.quantity), 2) if pos.quantity else 0.0,
            "marketValue": mv,
            "gainLoss": round(gl, 2),
            "gainLossPercent": round(gl_pct, 2),
        })
        total_gain_loss += gl
        total_cost += cb

    total_value = float(portfolio.total_value or 0)
    total_gl_pct = (total_gain_loss / total_cost * 100) if total_cost else 0.0

    return {
        "accountNumber": portfolio.account_no,
        "totalValue": total_value,
        "totalGainLoss": round(total_gain_loss, 2),
        "totalGainLossPercent": round(total_gl_pct, 2),
        "holdings": holdings,
        "lastUpdated": portfolio.last_maint.strftime("%B %d, %Y") if portfolio.last_maint else "N/A",
    }


@router.get("/transactions/{account_number}")
async def get_transactions(account_number: str, db: Session = Depends(get_db)):
    """Get transaction history for an account"""
    is_valid, message = validate_account_number(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    portfolio = db.query(Portfolio).filter(
        Portfolio.account_no == account_number
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio.port_id
    ).order_by(Transaction.date.desc()).all()

    return {
        "accountNumber": account_number,
        "transactions": [
            {
                "date": t.date.isoformat() if t.date else None,
                "type": t.type,
                "investment_id": t.investment_id,
                "quantity": float(t.quantity or 0),
                "price": float(t.price or 0),
                "amount": float(t.amount or 0),
                "status": t.status,
            }
            for t in transactions
        ],
        "message": f"Found {len(transactions)} transactions"
    }
