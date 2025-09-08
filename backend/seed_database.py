"""
Database seeding script to populate the portfolio database with sample data
"""
import sys
import os
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import sessionmaker
from models.database import engine, Base, Portfolio, Position
from models.transactions import Transaction
from datetime import time

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_portfolio_data():
    """Seed the database with sample portfolio data matching the mock data"""
    session = SessionLocal()
    
    try:
        existing_portfolio = session.query(Portfolio).filter_by(port_id="PF-12345", account_no="1234567890").first()
        if existing_portfolio:
            print("Portfolio data already exists. Skipping seeding.")
            return
        
        portfolio = Portfolio(
            port_id="PF-12345",
            account_no="1234567890",
            client_name="Sample Client",
            client_type="I",  # Individual
            create_date=date(2024, 1, 15),
            last_maint=date.today(),
            status="A",  # Active
            total_value=Decimal("125750.50"),
            cash_balance=Decimal("252.00"),
            last_user="SYSTEM",
            last_trans="SEED001"
        )
        
        session.add(portfolio)
        session.flush()  # Get the portfolio ID
        
        positions = [
            Position(
                portfolio_id="PF-12345",
                date=date.today(),
                investment_id="AAPL",
                quantity=Decimal("150.0000"),
                cost_basis=Decimal("25500.00"),
                market_value=Decimal("27787.50"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-12345",
                date=date.today(),
                investment_id="MSFT",
                quantity=Decimal("100.0000"),
                cost_basis=Decimal("34000.00"),
                market_value=Decimal("37885.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-12345",
                date=date.today(),
                investment_id="GOOGL",
                quantity=Decimal("75.0000"),
                cost_basis=Decimal("10000.00"),
                market_value=Decimal("10692.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-12345",
                date=date.today(),
                investment_id="TSLA",
                quantity=Decimal("200.0000"),
                cost_basis=Decimal("47748.00"),
                market_value=Decimal("49134.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            )
        ]
        
        for position in positions:
            session.add(position)
        
        transactions = [
            Transaction(
                date=date(2024, 1, 15),
                time=time(10, 30, 0),
                portfolio_id="PF-12345",
                sequence_no="000001",
                investment_id="AAPL",
                type="BU",  # Buy
                quantity=Decimal("150.0000"),
                price=Decimal("170.0000"),
                amount=Decimal("25500.00"),
                currency="USD",
                status="D",  # Done
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2024, 1, 20),
                time=time(14, 15, 0),
                portfolio_id="PF-12345",
                sequence_no="000002",
                investment_id="MSFT",
                type="BU",  # Buy
                quantity=Decimal("100.0000"),
                price=Decimal("340.0000"),
                amount=Decimal("34000.00"),
                currency="USD",
                status="D",  # Done
                process_date=datetime.now(),
                process_user="SYSTEM"
            )
        ]
        
        for transaction in transactions:
            session.add(transaction)
        
        session.commit()
        print("Successfully seeded database with sample portfolio data!")
        print(f"Created portfolio: {portfolio.port_id} for account: {portfolio.account_no}")
        print(f"Added {len(positions)} positions")
        print(f"Added {len(transactions)} transactions")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()

def verify_seeded_data():
    """Verify that the data was seeded correctly"""
    session = SessionLocal()
    
    try:
        portfolio = session.query(Portfolio).filter_by(account_no="1234567890").first()
        if portfolio:
            print(f"\n✅ Portfolio found: {portfolio.port_id}")
            print(f"   Account: {portfolio.account_no}")
            print(f"   Client: {portfolio.client_name}")
            print(f"   Total Value: ${portfolio.total_value}")
            
            positions = session.query(Position).filter_by(portfolio_id=portfolio.port_id).all()
            print(f"   Positions: {len(positions)}")
            for pos in positions:
                print(f"     - {pos.investment_id}: {pos.quantity} shares, ${pos.market_value}")
            
            transactions = session.query(Transaction).filter_by(portfolio_id=portfolio.port_id).all()
            print(f"   Transactions: {len(transactions)}")
            for trans in transactions:
                print(f"     - {trans.type} {trans.investment_id}: {trans.quantity} @ ${trans.price}")
        else:
            print("❌ No portfolio found!")
            
    except Exception as e:
        print(f"Error verifying data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Seeding database with sample portfolio data...")
    seed_portfolio_data()
    verify_seeded_data()
