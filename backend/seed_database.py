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
        
        portfolios = [
            Portfolio(
                port_id="PF-12345",
                account_no="1234567890",
                client_name="Sample Client",
                client_type="I",
                create_date=date(2024, 1, 15),
                last_maint=date.today(),
                status="A",
                total_value=Decimal("125750.50"),
                cash_balance=Decimal("252.00"),
                last_user="SYSTEM",
                last_trans="SEED001"
            ),
            Portfolio(
                port_id="PF-67890",
                account_no="9876543210",
                client_name="Corporate Holdings LLC",
                client_type="C",
                create_date=date(2023, 6, 1),
                last_maint=date.today(),
                status="A",
                total_value=Decimal("500250.75"),
                cash_balance=Decimal("15000.00"),
                last_user="SYSTEM",
                last_trans="SEED002"
            ),
            Portfolio(
                port_id="PF-11111",
                account_no="5551234567",
                client_name="Trust Fund Alpha",
                client_type="T",
                create_date=date(2024, 3, 10),
                last_maint=date.today(),
                status="A",
                total_value=Decimal("75000.00"),
                cash_balance=Decimal("5000.00"),
                last_user="SYSTEM",
                last_trans="SEED003"
            ),
        ]

        for portfolio in portfolios:
            session.add(portfolio)
        session.flush()

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
            ),
            Position(
                portfolio_id="PF-67890",
                date=date.today(),
                investment_id="AMZN",
                quantity=Decimal("300.0000"),
                cost_basis=Decimal("105000.00"),
                market_value=Decimal("127500.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-67890",
                date=date.today(),
                investment_id="NVDA",
                quantity=Decimal("250.0000"),
                cost_basis=Decimal("200000.00"),
                market_value=Decimal("237500.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-67890",
                date=date.today(),
                investment_id="META",
                quantity=Decimal("175.0000"),
                cost_basis=Decimal("87500.00"),
                market_value=Decimal("120250.75"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-11111",
                date=date.today(),
                investment_id="JPM",
                quantity=Decimal("100.0000"),
                cost_basis=Decimal("35000.00"),
                market_value=Decimal("40000.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
            Position(
                portfolio_id="PF-11111",
                date=date.today(),
                investment_id="V",
                quantity=Decimal("120.0000"),
                cost_basis=Decimal("25000.00"),
                market_value=Decimal("30000.00"),
                currency="USD",
                status="A",
                last_maint_date=datetime.now(),
                last_maint_user="SYSTEM"
            ),
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
                type="BU",
                quantity=Decimal("150.0000"),
                price=Decimal("170.0000"),
                amount=Decimal("25500.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2024, 1, 20),
                time=time(14, 15, 0),
                portfolio_id="PF-12345",
                sequence_no="000002",
                investment_id="MSFT",
                type="BU",
                quantity=Decimal("100.0000"),
                price=Decimal("340.0000"),
                amount=Decimal("34000.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2024, 2, 1),
                time=time(9, 0, 0),
                portfolio_id="PF-12345",
                sequence_no="000003",
                investment_id="GOOGL",
                type="BU",
                quantity=Decimal("75.0000"),
                price=Decimal("133.3333"),
                amount=Decimal("10000.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2024, 2, 10),
                time=time(11, 45, 0),
                portfolio_id="PF-12345",
                sequence_no="000004",
                investment_id="TSLA",
                type="BU",
                quantity=Decimal("200.0000"),
                price=Decimal("238.7400"),
                amount=Decimal("47748.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2023, 6, 15),
                time=time(10, 0, 0),
                portfolio_id="PF-67890",
                sequence_no="000001",
                investment_id="AMZN",
                type="BU",
                quantity=Decimal("300.0000"),
                price=Decimal("350.0000"),
                amount=Decimal("105000.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2023, 7, 1),
                time=time(14, 30, 0),
                portfolio_id="PF-67890",
                sequence_no="000002",
                investment_id="NVDA",
                type="BU",
                quantity=Decimal("250.0000"),
                price=Decimal("800.0000"),
                amount=Decimal("200000.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
            Transaction(
                date=date(2024, 3, 15),
                time=time(9, 30, 0),
                portfolio_id="PF-11111",
                sequence_no="000001",
                investment_id="JPM",
                type="BU",
                quantity=Decimal("100.0000"),
                price=Decimal("350.0000"),
                amount=Decimal("35000.00"),
                currency="USD",
                status="D",
                process_date=datetime.now(),
                process_user="SYSTEM"
            ),
        ]
        
        for transaction in transactions:
            session.add(transaction)
        
        session.commit()
        print("Successfully seeded database with sample portfolio data!")
        for p in portfolios:
            print(f"Created portfolio: {p.port_id} for account: {p.account_no}")
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
        all_portfolios = session.query(Portfolio).all()
        print(f"\nFound {len(all_portfolios)} portfolios:")
        
        for portfolio in all_portfolios:
            print(f"\n  Portfolio: {portfolio.port_id}")
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
            
    except Exception as e:
        print(f"Error verifying data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Seeding database with sample portfolio data...")
    seed_portfolio_data()
    verify_seeded_data()
