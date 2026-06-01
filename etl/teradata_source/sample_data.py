"""
Teradata Source Data Generator
==============================
Generates realistic sample CSV files simulating Teradata FastExport output
for the Investment Portfolio Management System.

Produces:
  - TD_PORTFOLIO_MASTER.csv  (50+ portfolios)
  - TD_POSITION_DETAIL.csv   (200+ positions)
  - TD_TRANSACTION_LOG.csv   (1000+ transactions)
  - TD_AUDIT_HISTORY.csv     (audit trail records)

Usage:
    python sample_data.py

Output CSVs are written to etl/teradata_source/data/
"""

import csv
import os
import random
import json
from datetime import datetime, date, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_PORTFOLIOS = 55
NUM_POSITIONS = 220
NUM_TRANSACTIONS = 1100
SEED = 42

random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent / "data"

# Realistic investment universe
INVESTMENTS = [
    ("AAPL", 185.50), ("MSFT", 378.85), ("GOOGL", 142.56), ("TSLA", 245.67),
    ("AMZN", 178.25), ("NVDA", 878.35), ("META", 505.75), ("JPM", 196.42),
    ("V", 279.88), ("JNJ", 156.30), ("WMT", 165.20), ("PG", 162.15),
    ("MA", 457.80), ("UNH", 527.60), ("HD", 368.45), ("DIS", 112.35),
    ("BAC", 35.80), ("XOM", 105.42), ("COST", 725.60), ("PFE", 27.15),
    ("ABBV", 171.85), ("KO", 60.12), ("PEP", 172.40), ("AVGO", 1325.50),
    ("TMO", 572.30), ("MRK", 125.80), ("CSCO", 50.45), ("ACN", 358.20),
    ("LLY", 782.15), ("ABT", 112.65),
]

CLIENT_NAMES = [
    "Blackstone Capital Partners", "Meridian Wealth Advisors", "Citadel Investment Group",
    "Vanguard Retirement Trust", "Fidelity Growth Fund", "Morgan Stanley Private",
    "Goldman Sachs Asset Mgmt", "JP Morgan Institutional", "State Street Global",
    "Northern Trust Corporate", "Wellington Management Co", "Pacific Investment Mgmt",
    "T. Rowe Price Associates", "Capital Research Global", "Invesco Ltd Holdings",
    "Charles Schwab Trust", "Edward Jones Retirement", "Raymond James Financial",
    "Ameriprise Financial Inc", "LPL Financial Holdings",
    "Robert J. Henderson", "Sarah M. Whitfield", "Michael T. Nakamura",
    "Elizabeth K. Patel", "William R. Chen", "Jennifer L. Okafor",
    "David A. Kowalski", "Maria C. Fernandez", "James P. Sullivan",
    "Patricia N. Yamamoto", "Richard B. Goldstein", "Susan E. Mbeki",
    "Thomas W. Johansson", "Linda H. Chakraborty", "Christopher D. Rossi",
    "Karen S. Al-Rashid", "Daniel F. Nguyen", "Michelle A. O'Brien",
    "Andrew G. Petrov", "Laura J. Stein", "John M. Takahashi",
    "Rebecca L. Santos", "Mark E. Lindqvist", "Angela R. Dimitriou",
    "Steven K. Ibrahim", "Catherine P. Walsh", "Brian T. Moreno",
    "Diane V. Andersson", "Paul W. Nakagawa", "Nancy B. Keller",
    "George H. Volkov", "Amy M. Fitzgerald", "Kevin J. Park",
    "Teresa C. Magnusson", "Scott R. Banerjee",
]

CLIENT_TYPES = ["I", "I", "I", "I", "C", "C", "T"]  # Weighted toward Individual
STATUSES = ["A", "A", "A", "A", "A", "C", "S"]  # Weighted toward Active
POSITION_STATUSES = ["A", "A", "A", "A", "C", "P"]
TXN_TYPES = ["BU", "BU", "BU", "SL", "SL", "TR", "FE"]  # Weighted toward buys
TXN_STATUSES = ["D", "D", "D", "D", "P", "F"]  # Mostly done
CURRENCIES = ["USD", "USD", "USD", "USD", "EUR", "GBP", "JPY"]
USERS = ["SYSTEM", "BATCHJB", "ETLPROC", "ADMUSER", "OPSMGR", "SVCACCT"]
REASON_CODES = ["AUTO", "PROC", "TRAN", "FEE", "MANU", "RCNL"]


def generate_port_id(index: int) -> str:
    """Generate an 8-character portfolio ID."""
    return f"PF-{index:05d}"


def generate_account_no(index: int) -> str:
    """Generate a 10-digit account number."""
    base = 1000000000 + index * 17 + random.randint(0, 9)
    return str(base)[:10]


def random_date(start: date, end: date) -> date:
    """Generate a random date between start and end."""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def random_time() -> time:
    """Generate a random trading time (market hours)."""
    hour = random.randint(9, 16)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return time(hour, minute, second)


def decimal_str(value: float, places: int = 2) -> str:
    """Format a float as a fixed-decimal string."""
    fmt = f"%.{places}f"
    return fmt % value


# ---------------------------------------------------------------------------
# Portfolio Generation
# ---------------------------------------------------------------------------
def generate_portfolios() -> list:
    """Generate portfolio master records."""
    portfolios = []
    start_date = date(2020, 1, 1)
    end_date = date(2025, 12, 31)

    for i in range(NUM_PORTFOLIOS):
        port_id = generate_port_id(i)
        acct_no = generate_account_no(i)
        client_name = CLIENT_NAMES[i % len(CLIENT_NAMES)]
        client_type = random.choice(CLIENT_TYPES)
        create_dt = random_date(start_date, date(2024, 6, 30))
        last_maint = random_date(create_dt, end_date)
        status = random.choice(STATUSES)
        total_value = round(random.uniform(10000, 5000000), 2)
        cash_balance = round(random.uniform(100, total_value * 0.1), 2)
        last_user = random.choice(USERS)
        last_trans = f"TX{random.randint(100000, 999999)}"

        portfolios.append({
            "PORT_ID": port_id,
            "ACCT_NO": acct_no,
            "CLT_NM": client_name,
            "CLT_TYP_CD": client_type,
            "CRTE_DT": create_dt.isoformat(),
            "LST_MAINT_DT": last_maint.isoformat(),
            "STAT_CD": status,
            "TOT_VAL_AM": decimal_str(total_value),
            "CSH_BAL_AM": decimal_str(cash_balance),
            "LST_USR_ID": last_user,
            "LST_TRANS_ID": last_trans[:8],
        })

    return portfolios


# ---------------------------------------------------------------------------
# Position Generation
# ---------------------------------------------------------------------------
def generate_positions(portfolios: list) -> list:
    """Generate position detail records linked to portfolios."""
    positions = []
    active_ports = [p for p in portfolios if p["STAT_CD"] == "A"]

    for i in range(NUM_POSITIONS):
        port = random.choice(active_ports)
        inv_ticker, base_price = random.choice(INVESTMENTS)
        pos_date = random_date(date(2024, 1, 1), date(2025, 12, 31))
        quantity = round(random.uniform(10, 1000), 4)
        cost_basis = round(quantity * base_price * random.uniform(0.85, 1.05), 2)
        market_value = round(quantity * base_price * random.uniform(0.9, 1.2), 2)
        currency = random.choice(CURRENCIES[:4])  # Mostly USD for positions
        status = random.choice(POSITION_STATUSES)
        last_maint_ts = datetime.combine(
            pos_date, random_time()
        ).strftime("%Y-%m-%d %H:%M:%S.%f")
        last_maint_user = random.choice(USERS)

        positions.append({
            "PORT_ID": port["PORT_ID"],
            "POS_DT": pos_date.isoformat(),
            "INVST_ID": inv_ticker,
            "QTY_AM": decimal_str(quantity, 4),
            "CST_BAS_AM": decimal_str(cost_basis),
            "MKT_VAL_AM": decimal_str(market_value),
            "CRNCY_CD": currency,
            "STAT_CD": status,
            "LST_MAINT_TS": last_maint_ts,
            "LST_MAINT_USR": last_maint_user,
        })

    return positions


# ---------------------------------------------------------------------------
# Transaction Generation
# ---------------------------------------------------------------------------
def generate_transactions(portfolios: list) -> list:
    """Generate transaction log records."""
    transactions = []
    active_ports = [p for p in portfolios if p["STAT_CD"] == "A"]

    for i in range(NUM_TRANSACTIONS):
        port = random.choice(active_ports)
        txn_date = random_date(date(2024, 1, 1), date(2025, 12, 31))
        txn_time = random_time()
        seq_no = f"{(i % 999999) + 1:06d}"
        inv_ticker, base_price = random.choice(INVESTMENTS)
        txn_type = random.choice(TXN_TYPES)
        currency = random.choice(CURRENCIES[:4])
        status = random.choice(TXN_STATUSES)

        if txn_type in ("BU", "SL"):
            quantity = round(random.uniform(1, 500), 4)
            price = round(base_price * random.uniform(0.95, 1.05), 4)
            amount = round(quantity * price, 2)
        elif txn_type == "FE":
            quantity = 0.0
            price = 0.0
            amount = round(random.uniform(5, 500), 2)
            inv_ticker = ""
        else:  # TR
            quantity = round(random.uniform(10, 200), 4)
            price = round(base_price, 4)
            amount = round(quantity * price, 2)

        proc_ts = datetime.combine(txn_date, txn_time).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        proc_user = random.choice(USERS)

        transactions.append({
            "TXN_DT": txn_date.isoformat(),
            "TXN_TM": txn_time.strftime("%H:%M:%S"),
            "PORT_ID": port["PORT_ID"],
            "SEQ_NO": seq_no,
            "INVST_ID": inv_ticker,
            "TXN_TYP_CD": txn_type,
            "QTY_AM": decimal_str(quantity, 4),
            "PRC_AM": decimal_str(price, 4),
            "TXN_AM": decimal_str(amount),
            "CRNCY_CD": currency,
            "STAT_CD": status,
            "PROC_TS": proc_ts,
            "PROC_USR_ID": proc_user,
        })

    return transactions


# ---------------------------------------------------------------------------
# Audit History Generation
# ---------------------------------------------------------------------------
def generate_audit_history(portfolios: list, transactions: list) -> list:
    """Generate audit history records from transactions."""
    history = []
    record_types = ["PT", "PS", "TR"]
    action_codes = ["A", "C", "D"]

    # Generate ~2 audit records per transaction (before + after images)
    for i, txn in enumerate(transactions[:600]):
        port_id = txn["PORT_ID"]
        aud_date = txn["TXN_DT"].replace("-", "")
        now = datetime.strptime(txn["PROC_TS"], "%Y-%m-%d %H:%M:%S.%f")
        aud_time = now.strftime("%H%M%S") + f"{random.randint(10, 99)}"
        seq_no = f"{(i % 9999) + 1:04d}"
        rec_type = random.choice(record_types)
        act_code = random.choice(action_codes)

        before_data = {
            "PORT_ID": port_id,
            "status": "A",
            "value": decimal_str(random.uniform(10000, 500000)),
        }
        after_data = {
            "PORT_ID": port_id,
            "status": "A",
            "value": decimal_str(random.uniform(10000, 500000)),
        }

        history.append({
            "PORT_ID": port_id,
            "AUD_DT": aud_date,
            "AUD_TM": aud_time,
            "SEQ_NO": seq_no,
            "REC_TYP_CD": rec_type,
            "ACT_CD": act_code,
            "BEF_IMG_TX": json.dumps(before_data),
            "AFT_IMG_TX": json.dumps(after_data),
            "RSN_CD": random.choice(REASON_CODES),
            "PROC_TS": txn["PROC_TS"],
            "PROC_USR_ID": random.choice(USERS),
        })

    return history


# ---------------------------------------------------------------------------
# CSV Writer
# ---------------------------------------------------------------------------
def write_csv(filename: str, rows: list) -> None:
    """Write rows to a CSV file in the output directory."""
    filepath = OUTPUT_DIR / filename
    if not rows:
        print(f"  WARNING: No data to write for {filename}")
        return

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter="|")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {filename}: {len(rows)} rows written")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Teradata Source Data Generator")
    print("Simulating FastExport output from TD_* tables")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nGenerating portfolios...")
    portfolios = generate_portfolios()

    print("Generating positions...")
    positions = generate_positions(portfolios)

    print("Generating transactions...")
    transactions = generate_transactions(portfolios)

    print("Generating audit history...")
    audit_history = generate_audit_history(portfolios, transactions)

    print(f"\nWriting CSVs to {OUTPUT_DIR}/")
    write_csv("TD_PORTFOLIO_MASTER.csv", portfolios)
    write_csv("TD_POSITION_DETAIL.csv", positions)
    write_csv("TD_TRANSACTION_LOG.csv", transactions)
    write_csv("TD_AUDIT_HISTORY.csv", audit_history)

    # Also generate some intentional duplicates for dedup testing
    print("\nAdding duplicate records for dedup testing...")
    dupes = []
    for row in portfolios[:5]:
        dupe = row.copy()
        dupe["LST_MAINT_DT"] = "2025-06-15"  # Slightly different maintenance date
        dupes.append(dupe)
    # Append dupes to portfolio file
    filepath = OUTPUT_DIR / "TD_PORTFOLIO_MASTER.csv"
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=dupes[0].keys(), delimiter="|")
        writer.writerows(dupes)
    print(f"  Added {len(dupes)} duplicate portfolio rows for dedup demo")

    # Add some records with null/invalid values for validation testing
    print("Adding records with data quality issues for validation testing...")
    bad_txns = [
        {
            "TXN_DT": "2025-03-15", "TXN_TM": "10:30:00", "PORT_ID": portfolios[0]["PORT_ID"],
            "SEQ_NO": "900001", "INVST_ID": "AAPL", "TXN_TYP_CD": "BU",
            "QTY_AM": "-50.0000", "PRC_AM": "185.5000", "TXN_AM": "-9275.00",
            "CRNCY_CD": "USD", "STAT_CD": "P", "PROC_TS": "2025-03-15 10:30:00.000000",
            "PROC_USR_ID": "SYSTEM",
        },
        {
            "TXN_DT": "2025-03-16", "TXN_TM": "11:00:00", "PORT_ID": portfolios[1]["PORT_ID"],
            "SEQ_NO": "900002", "INVST_ID": "", "TXN_TYP_CD": "BU",
            "QTY_AM": "100.0000", "PRC_AM": "0.0000", "TXN_AM": "0.00",
            "CRNCY_CD": "USD", "STAT_CD": "P", "PROC_TS": "2025-03-16 11:00:00.000000",
            "PROC_USR_ID": "SYSTEM",
        },
        {
            "TXN_DT": "", "TXN_TM": "09:00:00", "PORT_ID": portfolios[2]["PORT_ID"],
            "SEQ_NO": "900003", "INVST_ID": "MSFT", "TXN_TYP_CD": "SL",
            "QTY_AM": "25.0000", "PRC_AM": "378.8500", "TXN_AM": "9471.25",
            "CRNCY_CD": "USD", "STAT_CD": "P", "PROC_TS": "",
            "PROC_USR_ID": "SYSTEM",
        },
    ]
    filepath = OUTPUT_DIR / "TD_TRANSACTION_LOG.csv"
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=bad_txns[0].keys(), delimiter="|")
        writer.writerows(bad_txns)
    print(f"  Added {len(bad_txns)} bad transaction rows for validation demo")

    print("\n" + "=" * 60)
    print("Data generation complete!")
    print(f"  Portfolios:    {len(portfolios) + len(dupes)} rows (incl. {len(dupes)} dupes)")
    print(f"  Positions:     {len(positions)} rows")
    print(f"  Transactions:  {len(transactions) + len(bad_txns)} rows (incl. {len(bad_txns)} bad)")
    print(f"  Audit History: {len(audit_history)} rows")
    print("=" * 60)


if __name__ == "__main__":
    main()
