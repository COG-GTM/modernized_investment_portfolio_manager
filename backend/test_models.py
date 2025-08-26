from models import Portfolio, Position, Transaction, History, SessionLocal, engine, Base
from services import PortfolioService
from decimal import Decimal
from datetime import date, datetime, time

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    portfolio = Portfolio(
        port_id="TEST0001",
        account_no="1234567890",
        client_name="Test Client",
        client_type="I",
        create_date=date.today(),
        status="A",
        cash_balance=Decimal('10000.00')
    )
    db.add(portfolio)
    
    validation = portfolio.validate_portfolio()
    print(f"Portfolio validation: {validation}")
    
    portfolio_dict = portfolio.to_dict()
    print(f"Portfolio serialization: {portfolio_dict}")
    
    transaction = Transaction(
        date=date.today(),
        time=time(9, 30, 0),
        portfolio_id="TEST0001",
        sequence_no="000001",
        investment_id="AAPL123456",
        type="BU",
        quantity=Decimal('100.0000'),
        price=Decimal('150.0000'),
        currency="USD",
        status="P"
    )
    transaction.update_amount()
    db.add(transaction)
    
    service = PortfolioService(db)
    result = service.process_transaction(transaction)
    print(f"Transaction processing result: {result}")
    
    db.commit()
    print("All tests passed!")
    
except Exception as e:
    db.rollback()
    print(f"Test failed: {e}")
finally:
    db.close()
