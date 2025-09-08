import sqlite3
import os
from models.database import engine, Base
from sqlalchemy.orm import sessionmaker
from models.database import Portfolio, Position

db_file = "portfolio.db"
print(f"Database file exists: {os.path.exists(db_file)}")

if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        portfolio_count = cursor.fetchone()[0]
        print(f"Number of portfolios: {portfolio_count}")
        
        if portfolio_count > 0:
            cursor.execute("SELECT port_id, client_name, total_value FROM portfolios LIMIT 5")
            sample_portfolios = cursor.fetchall()
            print(f"Sample portfolios: {sample_portfolios}")
    except Exception as e:
        print(f"Error querying portfolios: {e}")
    
    conn.close()
else:
    print("No database file found. Need to run migrations first.")
