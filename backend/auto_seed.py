"""
Auto-seeding functionality that can be integrated into the main application
to automatically populate the database with sample data if it's empty.
"""
from sqlalchemy.orm import sessionmaker
from models.database import engine, Portfolio
from seed_database import seed_portfolio_data

def should_auto_seed():
    """Check if database needs seeding (empty portfolio table)"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        portfolio_count = session.query(Portfolio).count()
        return portfolio_count == 0
    except Exception:
        return True
    finally:
        session.close()

def auto_seed_if_needed():
    """Automatically seed database if it's empty"""
    if should_auto_seed():
        print("🌱 Database is empty, auto-seeding with sample data...")
        seed_portfolio_data()
        print("✅ Auto-seeding completed!")
    else:
        print("📊 Database already contains data, skipping auto-seed")

if __name__ == "__main__":
    auto_seed_if_needed()
