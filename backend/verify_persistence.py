"""
Additional verification script to confirm database persistence and data integrity
"""
import sqlite3
import os
from decimal import Decimal

def verify_database_persistence():
    """Verify that data persists across connections and matches expected values"""
    db_file = "portfolio.db"
    
    if not os.path.exists(db_file):
        print("❌ Database file does not exist!")
        return False
    
    print(f"✅ Database file exists: {db_file}")
    print(f"   File size: {os.path.getsize(db_file)} bytes")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tables found: {tables}")
        
        cursor.execute("SELECT port_id, account_no, client_name, total_value, cash_balance FROM portfolios;")
        portfolios = cursor.fetchall()
        print(f"\n📊 Portfolio Records ({len(portfolios)}):")
        for portfolio in portfolios:
            print(f"   - ID: {portfolio[0]}, Account: {portfolio[1]}, Client: {portfolio[2]}")
            print(f"     Total Value: ${portfolio[3]}, Cash Balance: ${portfolio[4]}")
        
        cursor.execute("SELECT portfolio_id, investment_id, quantity, cost_basis, market_value FROM positions ORDER BY investment_id;")
        positions = cursor.fetchall()
        print(f"\n📈 Position Records ({len(positions)}):")
        total_market_value = 0
        for position in positions:
            print(f"   - {position[1]}: {position[2]} shares")
            print(f"     Cost Basis: ${position[3]}, Market Value: ${position[4]}")
            total_market_value += float(position[4])
        print(f"   Total Market Value: ${total_market_value}")
        
        cursor.execute("SELECT date, time, portfolio_id, investment_id, type, quantity, price, amount FROM transactions ORDER BY date, time;")
        transactions = cursor.fetchall()
        print(f"\n💰 Transaction Records ({len(transactions)}):")
        for transaction in transactions:
            print(f"   - {transaction[0]} {transaction[1]}: {transaction[4]} {transaction[3]}")
            print(f"     Quantity: {transaction[5]}, Price: ${transaction[6]}, Amount: ${transaction[7]}")
        
        expected_total = 125750.50
        if portfolios and abs(float(portfolios[0][3]) - expected_total) < 0.01:
            print(f"\n✅ Data integrity check PASSED - Total value matches expected: ${expected_total}")
        else:
            print(f"\n❌ Data integrity check FAILED - Expected ${expected_total}, got ${portfolios[0][3] if portfolios else 'N/A'}")
        
        expected_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        found_symbols = [pos[1] for pos in positions]
        missing_symbols = set(expected_symbols) - set(found_symbols)
        
        if not missing_symbols:
            print(f"✅ All expected positions found: {expected_symbols}")
        else:
            print(f"❌ Missing positions: {missing_symbols}")
        
        return len(portfolios) > 0 and len(positions) == 4 and len(transactions) >= 2
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Database Persistence Verification ===")
    success = verify_database_persistence()
    print(f"\n{'✅ VERIFICATION PASSED' if success else '❌ VERIFICATION FAILED'}")
