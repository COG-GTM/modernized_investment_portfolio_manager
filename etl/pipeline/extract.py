"""
Extract Module — Teradata Source Data Extraction
=================================================
Reads CSV files that simulate Teradata FastExport output.

This module REPLACES:
  - Ab Initio Teradata Connector component
  - BTEQ extraction scripts for TD_PORTFOLIO_MASTER and TD_AUDIT_HISTORY
  - FastExport utility scripts for TD_POSITION_DETAIL and TD_TRANSACTION_LOG

In the Ab Initio world, extraction required:
  1. BTEQ login scripts with Teradata credentials
  2. FastExport job definitions (DML + control files)
  3. Ab Initio Teradata Connector configuration (pset files)
  4. Parallel dataset serialization to .dat files

With Devin: A single Python module using pandas to read pipe-delimited CSVs.
"""

import time
from pathlib import Path
from typing import Dict

import pandas as pd


# Default data directory (Teradata FastExport simulation output)
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "teradata_source" / "data"


def extract_table(table_name: str, data_dir: Path = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """
    Extract a single table from CSV.

    Replaces: Ab Initio Teradata Connector + BTEQ/FastExport for one table.

    Args:
        table_name: Name of the Teradata table (e.g., 'TD_PORTFOLIO_MASTER')
        data_dir: Directory containing the CSV exports

    Returns:
        pandas DataFrame with the extracted data
    """
    csv_path = data_dir / f"{table_name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_path}\n"
            f"Run 'python teradata_source/sample_data.py' first to generate sample data."
        )

    # Replaces: Ab Initio Teradata Connector reading via ODBC/FastExport
    # The pipe delimiter matches typical Teradata export format
    df = pd.read_csv(csv_path, delimiter="|", dtype=str)
    return df


def extract_all(data_dir: Path = DEFAULT_DATA_DIR) -> Dict[str, pd.DataFrame]:
    """
    Extract all source tables from CSV files.

    Replaces: The entire Ab Initio Extract graph that runs BTEQ and FastExport
    for all four source tables in sequence/parallel.

    In Ab Initio this required:
      - 4 separate BTEQ/FastExport scripts
      - Ab Initio Teradata Connector configurations (4 pset files)
      - Ab Initio graph wiring for parallel extraction
      - Estimated runtime: 45-90 minutes on Teradata

    With Devin: One function call, ~1 second for local CSVs.

    Args:
        data_dir: Directory containing the CSV exports

    Returns:
        Dictionary mapping table names to DataFrames
    """
    tables = [
        "TD_PORTFOLIO_MASTER",
        "TD_POSITION_DETAIL",
        "TD_TRANSACTION_LOG",
        "TD_AUDIT_HISTORY",
    ]

    results = {}
    total_rows = 0

    print("\n--- EXTRACT PHASE ---")
    print(f"Source: {data_dir}")
    print(f"{'Table':<30} {'Rows':>8} {'Columns':>8} {'Time':>10}")
    print("-" * 60)

    for table_name in tables:
        start = time.time()
        df = extract_table(table_name, data_dir)
        elapsed = time.time() - start

        results[table_name] = df
        total_rows += len(df)

        print(f"{table_name:<30} {len(df):>8,} {len(df.columns):>8} {elapsed:>9.3f}s")

    print("-" * 60)
    print(f"{'TOTAL':<30} {total_rows:>8,}")
    print()

    return results
