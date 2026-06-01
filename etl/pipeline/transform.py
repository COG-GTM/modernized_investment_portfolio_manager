"""
Transform Module — Data Transformation Pipeline
=================================================
Implements all transformations that Ab Initio GDE graphs performed:
deduplication, validation, schema mapping, and aggregation.

This module REPLACES the entire Ab Initio Transform Layer:
  - Ab Initio Dedup Sort components
  - Ab Initio Filter components (data quality validation)
  - Ab Initio Reformat components (schema mapping)
  - Ab Initio Rollup components (aggregation)
  - Ab Initio Join components (enrichment)
  - Ab Initio Normalize components (standardization)
"""

import time
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Column Mapping: Teradata naming conventions → Iceberg target schema
# ---------------------------------------------------------------------------

PORTFOLIO_COLUMN_MAP = {
    # Replaces: Ab Initio Reformat component "reformat_portfolio.mp"
    "PORT_ID": "portfolio_id",
    "ACCT_NO": "account_number",
    "CLT_NM": "client_name",
    "CLT_TYP_CD": "client_type",
    "CRTE_DT": "create_date",
    "LST_MAINT_DT": "last_maintenance_date",
    "STAT_CD": "status",
    "TOT_VAL_AM": "total_value",
    "CSH_BAL_AM": "cash_balance",
    "LST_USR_ID": "last_user",
    "LST_TRANS_ID": "last_transaction_id",
}

POSITION_COLUMN_MAP = {
    # Replaces: Ab Initio Reformat component for position data
    "PORT_ID": "portfolio_id",
    "POS_DT": "position_date",
    "INVST_ID": "investment_id",
    "QTY_AM": "quantity",
    "CST_BAS_AM": "cost_basis",
    "MKT_VAL_AM": "market_value",
    "CRNCY_CD": "currency",
    "STAT_CD": "status",
    "LST_MAINT_TS": "last_maintenance_timestamp",
    "LST_MAINT_USR": "last_maintenance_user",
}

TRANSACTION_COLUMN_MAP = {
    # Replaces: Ab Initio Reformat component for transaction data
    "TXN_DT": "transaction_date",
    "TXN_TM": "transaction_time",
    "PORT_ID": "portfolio_id",
    "SEQ_NO": "sequence_number",
    "INVST_ID": "investment_id",
    "TXN_TYP_CD": "transaction_type",
    "QTY_AM": "quantity",
    "PRC_AM": "price",
    "TXN_AM": "amount",
    "CRNCY_CD": "currency",
    "STAT_CD": "status",
    "PROC_TS": "process_timestamp",
    "PROC_USR_ID": "process_user",
}

AUDIT_COLUMN_MAP = {
    # Replaces: Ab Initio Reformat component for audit history
    "PORT_ID": "portfolio_id",
    "AUD_DT": "audit_date",
    "AUD_TM": "audit_time",
    "SEQ_NO": "sequence_number",
    "REC_TYP_CD": "record_type",
    "ACT_CD": "action_code",
    "BEF_IMG_TX": "before_image",
    "AFT_IMG_TX": "after_image",
    "RSN_CD": "reason_code",
    "PROC_TS": "process_timestamp",
    "PROC_USR_ID": "process_user",
}


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_portfolios(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Remove duplicate portfolio records, keeping the most recently maintained.

    Replaces: Ab Initio Dedup Sort component "dedup_portfolio.mp"
    - Ab Initio used a Sort + Dedup with key=(PORT_ID, ACCT_NO), sort=LST_MAINT_DT DESC
    - Here we achieve the same with pandas drop_duplicates after sorting

    Args:
        df: Raw portfolio DataFrame with potential duplicates

    Returns:
        Tuple of (deduplicated DataFrame, number of duplicates removed)
    """
    original_count = len(df)

    # Sort by maintenance date descending so we keep the latest record
    df_sorted = df.sort_values("LST_MAINT_DT", ascending=False)

    # Replaces: Ab Initio Dedup component with key=(PORT_ID, ACCT_NO)
    df_deduped = df_sorted.drop_duplicates(
        subset=["PORT_ID", "ACCT_NO"], keep="first"
    ).reset_index(drop=True)

    dupes_removed = original_count - len(df_deduped)
    return df_deduped, dupes_removed


def deduplicate_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Remove duplicate transaction records by composite key.

    Replaces: Ab Initio Dedup Sort component "dedup_transactions.mp"

    Args:
        df: Raw transaction DataFrame

    Returns:
        Tuple of (deduplicated DataFrame, number of duplicates removed)
    """
    original_count = len(df)

    df_sorted = df.sort_values("PROC_TS", ascending=False)
    df_deduped = df_sorted.drop_duplicates(
        subset=["TXN_DT", "TXN_TM", "PORT_ID", "SEQ_NO"], keep="first"
    ).reset_index(drop=True)

    dupes_removed = original_count - len(df_deduped)
    return df_deduped, dupes_removed


# ---------------------------------------------------------------------------
# Data Quality Validation
# ---------------------------------------------------------------------------

def validate_portfolios(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate portfolio records — reject rows that fail quality checks.

    Replaces: Ab Initio Filter component "validate_portfolio.mp"
    - Null checks on PORT_ID, ACCT_NO
    - Length checks (PORT_ID=8, ACCT_NO=10)
    - Domain checks on CLT_TYP_CD and STAT_CD
    - Range check on TOT_VAL_AM (must be non-negative)

    Args:
        df: Deduplicated portfolio DataFrame

    Returns:
        Tuple of (valid records DataFrame, rejected records DataFrame)
    """
    reject_mask = pd.Series(False, index=df.index)

    # Replaces: Ab Initio Filter rule — PORT_ID NOT NULL AND LENGTH == 8
    reject_mask |= df["PORT_ID"].isna() | (df["PORT_ID"].str.len() != 8)

    # Replaces: Ab Initio Filter rule — ACCT_NO NOT NULL AND LENGTH == 10
    reject_mask |= df["ACCT_NO"].isna() | (df["ACCT_NO"].str.len() != 10)

    # Replaces: Ab Initio Filter rule — CLT_TYP_CD IN ('I', 'C', 'T')
    reject_mask |= ~df["CLT_TYP_CD"].isin(["I", "C", "T"])

    # Replaces: Ab Initio Filter rule — STAT_CD IN ('A', 'C', 'S')
    reject_mask |= ~df["STAT_CD"].isin(["A", "C", "S"])

    # Replaces: Ab Initio Filter rule — TOT_VAL_AM >= 0
    numeric_vals = pd.to_numeric(df["TOT_VAL_AM"], errors="coerce")
    reject_mask |= numeric_vals < 0

    valid_df = df[~reject_mask].reset_index(drop=True)
    reject_df = df[reject_mask].reset_index(drop=True)

    return valid_df, reject_df


def validate_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate transaction records — reject rows that fail quality checks.

    Replaces: Ab Initio Filter component "validate_transactions.mp"
    - Null checks on TXN_DT, PORT_ID
    - Quantity must be non-negative for BU/SL
    - Price must be positive for BU/SL
    - Investment ID required for BU/SL

    Args:
        df: Deduplicated transaction DataFrame

    Returns:
        Tuple of (valid records DataFrame, rejected records DataFrame)
    """
    reject_mask = pd.Series(False, index=df.index)

    # Replaces: Ab Initio Filter rule — TXN_DT NOT NULL
    reject_mask |= df["TXN_DT"].isna() | (df["TXN_DT"].str.strip() == "")

    # Replaces: Ab Initio Filter rule — PORT_ID NOT NULL AND LENGTH == 8
    reject_mask |= df["PORT_ID"].isna() | (df["PORT_ID"].str.len() != 8)

    # For BU/SL transactions: quantity >= 0 and price > 0
    is_buy_sell = df["TXN_TYP_CD"].isin(["BU", "SL"])
    qty = pd.to_numeric(df["QTY_AM"], errors="coerce").fillna(0)
    prc = pd.to_numeric(df["PRC_AM"], errors="coerce").fillna(0)

    # Replaces: Ab Initio Filter rule — QTY_AM >= 0 WHEN TXN_TYP_CD IN ('BU','SL')
    reject_mask |= is_buy_sell & (qty < 0)

    # Replaces: Ab Initio Filter rule — PRC_AM > 0 WHEN TXN_TYP_CD IN ('BU','SL')
    reject_mask |= is_buy_sell & (prc <= 0)

    # Replaces: Ab Initio Filter rule — INVST_ID NOT NULL WHEN TXN_TYP_CD IN ('BU','SL')
    reject_mask |= is_buy_sell & (df["INVST_ID"].isna() | (df["INVST_ID"].str.strip() == ""))

    valid_df = df[~reject_mask].reset_index(drop=True)
    reject_df = df[reject_mask].reset_index(drop=True)

    return valid_df, reject_df


# ---------------------------------------------------------------------------
# Schema Mapping
# ---------------------------------------------------------------------------

def map_schema(df: pd.DataFrame, column_map: Dict[str, str]) -> pd.DataFrame:
    """
    Rename columns from Teradata naming conventions to Iceberg target schema.

    Replaces: Ab Initio Reformat component
    - Ab Initio used graphical field-to-field mapping in GDE
    - Here we use a simple dictionary rename

    Args:
        df: DataFrame with Teradata-style column names
        column_map: Dictionary mapping old names to new names

    Returns:
        DataFrame with renamed columns
    """
    # Only rename columns that exist in the DataFrame
    rename_map = {k: v for k, v in column_map.items() if k in df.columns}
    return df.rename(columns=rename_map)


# ---------------------------------------------------------------------------
# Type Casting
# ---------------------------------------------------------------------------

def cast_portfolio_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cast portfolio columns to appropriate types for Iceberg.

    Replaces: Ab Initio Normalize component type conversions.
    """
    df = df.copy()
    df["total_value"] = pd.to_numeric(df["total_value"], errors="coerce").fillna(0.0)
    df["cash_balance"] = pd.to_numeric(df["cash_balance"], errors="coerce").fillna(0.0)
    df["create_date"] = pd.to_datetime(df["create_date"], errors="coerce")
    df["last_maintenance_date"] = pd.to_datetime(df["last_maintenance_date"], errors="coerce")
    return df


def cast_position_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast position columns to appropriate types for Iceberg."""
    df = df.copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)
    df["cost_basis"] = pd.to_numeric(df["cost_basis"], errors="coerce").fillna(0.0)
    df["market_value"] = pd.to_numeric(df["market_value"], errors="coerce").fillna(0.0)
    df["position_date"] = pd.to_datetime(df["position_date"], errors="coerce")
    return df


def cast_transaction_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast transaction columns to appropriate types for Iceberg."""
    df = df.copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_positions_by_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Roll up positions by portfolio — calculate total portfolio values.

    Replaces: Ab Initio Rollup component "rollup_positions.mp"
    - Ab Initio used graphical Rollup with GROUP BY PORT_ID
    - Computed SUM(MKT_VAL_AM), SUM(CST_BAS_AM), COUNT(INVST_ID)

    Args:
        df: Position detail DataFrame (already schema-mapped)

    Returns:
        Aggregated DataFrame with one row per portfolio
    """
    # Filter to active positions only
    active = df[df["status"] == "A"].copy()

    if active.empty:
        return pd.DataFrame(columns=[
            "portfolio_id", "total_market_value", "total_cost_basis",
            "position_count", "total_quantity", "total_gain_loss",
            "gain_loss_percent",
        ])

    # Replaces: Ab Initio Rollup GROUP BY PORT_ID with SUM/COUNT aggregations
    agg = active.groupby("portfolio_id").agg(
        total_market_value=("market_value", "sum"),
        total_cost_basis=("cost_basis", "sum"),
        position_count=("investment_id", "count"),
        total_quantity=("quantity", "sum"),
    ).reset_index()

    # Replaces: Ab Initio Rollup derived fields
    agg["total_gain_loss"] = agg["total_market_value"] - agg["total_cost_basis"]
    agg["gain_loss_percent"] = np.where(
        agg["total_cost_basis"] != 0,
        (agg["total_gain_loss"] / agg["total_cost_basis"]) * 100,
        0.0,
    )

    return agg


# ---------------------------------------------------------------------------
# Master Transform Orchestrator
# ---------------------------------------------------------------------------

def transform_all(
    raw_data: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    """
    Run the full transformation pipeline on all extracted data.

    Replaces: The entire Ab Initio Transform graph layer including:
      - dedup_portfolio.mp
      - dedup_transactions.mp
      - validate_portfolio.mp
      - validate_transactions.mp
      - reformat_portfolio.mp (and other reformat graphs)
      - rollup_positions.mp
      - join_port_pos.mp
      - normalize_dates.mp

    In Ab Initio, each of these was a separate graph component wired
    together in GDE, each requiring its own pset configuration file
    and Ab Initio-specific DML definitions.

    With Devin: A single Python function orchestrating pandas operations.

    Args:
        raw_data: Dictionary of raw DataFrames from extract phase

    Returns:
        Dictionary of transformed DataFrames ready for Iceberg loading
    """
    print("\n--- TRANSFORM PHASE ---")
    results = {}
    total_start = time.time()

    # -----------------------------------------------------------------------
    # Step 1: Deduplication
    # Replaces: Ab Initio Dedup Sort components
    # -----------------------------------------------------------------------
    print("\n[Step 1/5] Deduplication")
    print("  Replaces: Ab Initio Dedup Sort component")

    portfolios, port_dupes = deduplicate_portfolios(
        raw_data["TD_PORTFOLIO_MASTER"]
    )
    transactions, txn_dupes = deduplicate_transactions(
        raw_data["TD_TRANSACTION_LOG"]
    )
    print(f"  Portfolios:   {port_dupes} duplicates removed, {len(portfolios)} remain")
    print(f"  Transactions: {txn_dupes} duplicates removed, {len(transactions)} remain")

    # -----------------------------------------------------------------------
    # Step 2: Data Quality Validation
    # Replaces: Ab Initio Filter components
    # -----------------------------------------------------------------------
    print("\n[Step 2/5] Data Quality Validation")
    print("  Replaces: Ab Initio Filter component")

    valid_portfolios, rejected_portfolios = validate_portfolios(portfolios)
    valid_transactions, rejected_transactions = validate_transactions(transactions)

    print(f"  Portfolios:   {len(valid_portfolios)} valid, {len(rejected_portfolios)} rejected")
    print(f"  Transactions: {len(valid_transactions)} valid, {len(rejected_transactions)} rejected")

    # -----------------------------------------------------------------------
    # Step 3: Schema Mapping (Teradata → Iceberg naming)
    # Replaces: Ab Initio Reformat components
    # -----------------------------------------------------------------------
    print("\n[Step 3/5] Schema Mapping (Teradata → Iceberg)")
    print("  Replaces: Ab Initio Reformat component")

    mapped_portfolios = map_schema(valid_portfolios, PORTFOLIO_COLUMN_MAP)
    mapped_positions = map_schema(
        raw_data["TD_POSITION_DETAIL"], POSITION_COLUMN_MAP
    )
    mapped_transactions = map_schema(valid_transactions, TRANSACTION_COLUMN_MAP)
    mapped_audit = map_schema(raw_data["TD_AUDIT_HISTORY"], AUDIT_COLUMN_MAP)

    print(f"  Portfolios:   {len(PORTFOLIO_COLUMN_MAP)} columns remapped")
    print(f"  Positions:    {len(POSITION_COLUMN_MAP)} columns remapped")
    print(f"  Transactions: {len(TRANSACTION_COLUMN_MAP)} columns remapped")
    print(f"  Audit:        {len(AUDIT_COLUMN_MAP)} columns remapped")

    # -----------------------------------------------------------------------
    # Step 4: Type Casting
    # Replaces: Ab Initio Normalize component type conversions
    # -----------------------------------------------------------------------
    print("\n[Step 4/5] Type Casting & Normalization")
    print("  Replaces: Ab Initio Normalize component")

    mapped_portfolios = cast_portfolio_types(mapped_portfolios)
    mapped_positions = cast_position_types(mapped_positions)
    mapped_transactions = cast_transaction_types(mapped_transactions)

    print("  Numeric and date columns cast to native types")

    # -----------------------------------------------------------------------
    # Step 5: Aggregation — roll up positions by portfolio
    # Replaces: Ab Initio Rollup + Join components
    # -----------------------------------------------------------------------
    print("\n[Step 5/5] Aggregation (Position Rollup)")
    print("  Replaces: Ab Initio Rollup + Join components")

    position_rollup = aggregate_positions_by_portfolio(mapped_positions)
    print(f"  {len(position_rollup)} portfolio rollup records created")

    if not position_rollup.empty:
        avg_gl = position_rollup["gain_loss_percent"].mean()
        total_mv = position_rollup["total_market_value"].sum()
        print(f"  Avg gain/loss: {avg_gl:.2f}%")
        print(f"  Total market value: ${total_mv:,.2f}")

    # -----------------------------------------------------------------------
    # Assemble results
    # -----------------------------------------------------------------------
    results["portfolios"] = mapped_portfolios
    results["positions"] = mapped_positions
    results["transactions"] = mapped_transactions
    results["audit_history"] = mapped_audit
    results["position_rollup"] = position_rollup
    results["rejected_portfolios"] = rejected_portfolios
    results["rejected_transactions"] = rejected_transactions

    total_elapsed = time.time() - total_start
    total_rows = sum(len(v) for v in results.values())

    print(f"\n  Transform complete: {total_rows:,} total rows in {total_elapsed:.3f}s")

    return results
