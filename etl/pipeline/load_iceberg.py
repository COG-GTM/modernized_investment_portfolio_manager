"""
Load Module — Apache Iceberg Table Writer
==========================================
Loads transformed DataFrames into Apache Iceberg tables using PyIceberg.

This module REPLACES:
  - Ab Initio Load to Teradata reporting tables (MultiLoad / TPT)
  - Ab Initio error/reject file handling
  - Teradata-specific DDL for reporting tables

Instead of loading back into Teradata (vendor lock-in), we write to
Apache Iceberg — an open table format that works with any query engine
(Spark, Trino, DuckDB, Snowflake, etc.).

Key advantages over Ab Initio + Teradata:
  - Open format: No vendor lock-in
  - Schema evolution: Add/rename columns without rewriting data
  - Time travel: Query data as of any snapshot
  - Partition evolution: Change partitioning without rewriting
  - Works with any compute engine
"""

import os
import shutil
import time
from pathlib import Path
from typing import Dict

import pandas as pd
import pyarrow as pa
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    StringType,
    DoubleType,
    LongType,
    TimestampType,
    NestedField,
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import MonthTransform


# Default output directory for Iceberg warehouse
DEFAULT_WAREHOUSE_DIR = Path(__file__).parent.parent / "iceberg_warehouse"
DEFAULT_CATALOG_DB = Path(__file__).parent.parent / "iceberg_warehouse" / "catalog.db"


# ---------------------------------------------------------------------------
# Iceberg Schema Definitions
# ---------------------------------------------------------------------------

PORTFOLIO_SCHEMA = Schema(
    NestedField(field_id=1, name="portfolio_id", field_type=StringType(), required=True),
    NestedField(field_id=2, name="account_number", field_type=StringType(), required=True),
    NestedField(field_id=3, name="client_name", field_type=StringType(), required=False),
    NestedField(field_id=4, name="client_type", field_type=StringType(), required=False),
    NestedField(field_id=5, name="create_date", field_type=TimestampType(), required=False),
    NestedField(field_id=6, name="last_maintenance_date", field_type=TimestampType(), required=False),
    NestedField(field_id=7, name="status", field_type=StringType(), required=False),
    NestedField(field_id=8, name="total_value", field_type=DoubleType(), required=False),
    NestedField(field_id=9, name="cash_balance", field_type=DoubleType(), required=False),
    NestedField(field_id=10, name="last_user", field_type=StringType(), required=False),
    NestedField(field_id=11, name="last_transaction_id", field_type=StringType(), required=False),
)

POSITION_SCHEMA = Schema(
    NestedField(field_id=1, name="portfolio_id", field_type=StringType(), required=True),
    NestedField(field_id=2, name="position_date", field_type=TimestampType(), required=False),
    NestedField(field_id=3, name="investment_id", field_type=StringType(), required=True),
    NestedField(field_id=4, name="quantity", field_type=DoubleType(), required=False),
    NestedField(field_id=5, name="cost_basis", field_type=DoubleType(), required=False),
    NestedField(field_id=6, name="market_value", field_type=DoubleType(), required=False),
    NestedField(field_id=7, name="currency", field_type=StringType(), required=False),
    NestedField(field_id=8, name="status", field_type=StringType(), required=False),
    NestedField(field_id=9, name="last_maintenance_timestamp", field_type=StringType(), required=False),
    NestedField(field_id=10, name="last_maintenance_user", field_type=StringType(), required=False),
)

TRANSACTION_SCHEMA = Schema(
    NestedField(field_id=1, name="transaction_date", field_type=TimestampType(), required=False),
    NestedField(field_id=2, name="transaction_time", field_type=StringType(), required=False),
    NestedField(field_id=3, name="portfolio_id", field_type=StringType(), required=True),
    NestedField(field_id=4, name="sequence_number", field_type=StringType(), required=False),
    NestedField(field_id=5, name="investment_id", field_type=StringType(), required=False),
    NestedField(field_id=6, name="transaction_type", field_type=StringType(), required=False),
    NestedField(field_id=7, name="quantity", field_type=DoubleType(), required=False),
    NestedField(field_id=8, name="price", field_type=DoubleType(), required=False),
    NestedField(field_id=9, name="amount", field_type=DoubleType(), required=False),
    NestedField(field_id=10, name="currency", field_type=StringType(), required=False),
    NestedField(field_id=11, name="status", field_type=StringType(), required=False),
    NestedField(field_id=12, name="process_timestamp", field_type=StringType(), required=False),
    NestedField(field_id=13, name="process_user", field_type=StringType(), required=False),
)

# Transaction partition spec: partition by month on transaction_date
TRANSACTION_PARTITION_SPEC = PartitionSpec(
    PartitionField(
        source_id=1,
        field_id=1000,
        transform=MonthTransform(),
        name="transaction_month",
    ),
)

POSITION_ROLLUP_SCHEMA = Schema(
    NestedField(field_id=1, name="portfolio_id", field_type=StringType(), required=True),
    NestedField(field_id=2, name="total_market_value", field_type=DoubleType(), required=False),
    NestedField(field_id=3, name="total_cost_basis", field_type=DoubleType(), required=False),
    NestedField(field_id=4, name="position_count", field_type=LongType(), required=False),
    NestedField(field_id=5, name="total_quantity", field_type=DoubleType(), required=False),
    NestedField(field_id=6, name="total_gain_loss", field_type=DoubleType(), required=False),
    NestedField(field_id=7, name="gain_loss_percent", field_type=DoubleType(), required=False),
)


def _prepare_df_for_arrow(df: pd.DataFrame, schema: Schema) -> pa.Table:
    """
    Convert a pandas DataFrame to a PyArrow Table matching the Iceberg schema.

    Ensures columns are aligned, types are compatible, and missing columns
    are handled gracefully.
    """
    schema_field_names = [field.name for field in schema.fields]

    # Ensure only schema columns are present, in the correct order
    # Copy first to avoid mutating the caller's DataFrame
    df = df.copy()
    for col in schema_field_names:
        if col not in df.columns:
            df[col] = None

    df_aligned = df[schema_field_names].copy()

    # Convert timestamp columns — downcast to microsecond precision for Iceberg
    for field in schema.fields:
        col_name = field.name
        if isinstance(field.field_type, TimestampType):
            df_aligned[col_name] = pd.to_datetime(df_aligned[col_name], errors="coerce")
            # PyIceberg does not support nanosecond precision; downcast to microseconds
            if df_aligned[col_name].dtype == "datetime64[ns]":
                df_aligned[col_name] = df_aligned[col_name].dt.as_unit("us")
        elif isinstance(field.field_type, DoubleType):
            df_aligned[col_name] = pd.to_numeric(df_aligned[col_name], errors="coerce")
        elif isinstance(field.field_type, LongType):
            df_aligned[col_name] = pd.to_numeric(df_aligned[col_name], errors="coerce")
            # Convert to Int64 (nullable integer) to handle NaN
            df_aligned[col_name] = df_aligned[col_name].astype("Int64")
        elif isinstance(field.field_type, StringType):
            df_aligned[col_name] = df_aligned[col_name].astype(str).replace({"nan": None, "None": None, "<NA>": None})

    # Build PyArrow schema with correct nullability to match Iceberg schema
    arrow_fields = []
    for field in schema.fields:
        col_name = field.name
        if isinstance(field.field_type, TimestampType):
            pa_type = pa.timestamp("us")
        elif isinstance(field.field_type, DoubleType):
            pa_type = pa.float64()
        elif isinstance(field.field_type, LongType):
            pa_type = pa.int64()
        else:
            pa_type = pa.string()
        arrow_fields.append(pa.field(col_name, pa_type, nullable=not field.required))

    arrow_schema = pa.schema(arrow_fields)
    arrow_table = pa.Table.from_pandas(df_aligned, schema=arrow_schema, preserve_index=False)
    return arrow_table


def create_catalog(warehouse_dir: Path = DEFAULT_WAREHOUSE_DIR) -> SqlCatalog:
    """
    Create or connect to a local SQLite-backed Iceberg catalog.

    Replaces: Teradata database catalog + Ab Initio target table DDL
    - No Teradata license required
    - No Ab Initio Load utility configuration
    - Works locally with zero cloud dependencies

    Args:
        warehouse_dir: Directory for Iceberg data files

    Returns:
        PyIceberg SqlCatalog instance
    """
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    catalog_db_path = warehouse_dir / "catalog.db"

    catalog = SqlCatalog(
        "investment_catalog",
        **{
            "uri": f"sqlite:///{catalog_db_path}",
            "warehouse": str(warehouse_dir),
        },
    )
    return catalog


def load_table(
    catalog: SqlCatalog,
    namespace: str,
    table_name: str,
    df: pd.DataFrame,
    schema: Schema,
    partition_spec: PartitionSpec = PartitionSpec(),
) -> int:
    """
    Load a DataFrame into an Iceberg table, creating the table if needed.

    Replaces: Ab Initio MultiLoad/TPT component for one target table.
    - Ab Initio required: DML definitions, load scripts, error handling config
    - Here: One function call with schema and data

    Args:
        catalog: PyIceberg catalog
        namespace: Iceberg namespace (like a database/schema)
        table_name: Name of the Iceberg table
        df: Transformed DataFrame to load
        schema: Iceberg schema definition
        partition_spec: Partition specification (optional)

    Returns:
        Number of rows loaded
    """
    full_table_name = f"{namespace}.{table_name}"

    # Ensure namespace exists
    try:
        catalog.create_namespace(namespace)
    except Exception:
        pass  # Namespace already exists

    # Create or replace table
    # Replaces: Ab Initio DDL generation + Teradata CREATE TABLE
    try:
        catalog.drop_table(full_table_name)
    except Exception:
        pass  # Table doesn't exist yet

    table = catalog.create_table(
        full_table_name,
        schema=schema,
        partition_spec=partition_spec,
    )

    if df.empty:
        print(f"    {full_table_name}: 0 rows (empty DataFrame)")
        return 0

    # Convert DataFrame to PyArrow and append to Iceberg table
    arrow_table = _prepare_df_for_arrow(df, schema)
    table.append(arrow_table)

    return len(df)


def load_all(
    transformed_data: Dict[str, pd.DataFrame],
    warehouse_dir: Path = DEFAULT_WAREHOUSE_DIR,
) -> Dict[str, int]:
    """
    Load all transformed data into Iceberg tables.

    Replaces: The entire Ab Initio Load graph including:
      - MultiLoad to RPT_PORTFOLIO_SUMMARY
      - MultiLoad to RPT_POSITION_ROLLUP
      - TPT to RPT_TRANSACTION_DETAIL
      - Error/reject file handling

    In Ab Initio, the Load phase required:
      - Teradata MultiLoad/TPT scripts
      - Ab Initio Load utility configurations
      - Error table setup in Teradata
      - DMP archive management
      - Estimated runtime: 30-60 minutes

    With Devin + Iceberg: Direct DataFrame-to-Iceberg writes, ~seconds.

    Args:
        transformed_data: Dictionary of transformed DataFrames
        warehouse_dir: Directory for Iceberg warehouse files

    Returns:
        Dictionary of table names to row counts loaded
    """
    print("\n--- LOAD PHASE (Apache Iceberg) ---")
    print(f"Warehouse: {warehouse_dir}")

    # Clean previous run
    if warehouse_dir.exists():
        shutil.rmtree(warehouse_dir)

    catalog = create_catalog(warehouse_dir)
    namespace = "investment_dwh"
    row_counts = {}
    total_start = time.time()

    # -----------------------------------------------------------------------
    # Load Portfolios
    # Replaces: Ab Initio MultiLoad to RPT_PORTFOLIO_SUMMARY
    # -----------------------------------------------------------------------
    print("\n  Loading portfolios...")
    start = time.time()
    count = load_table(
        catalog, namespace, "portfolios",
        transformed_data["portfolios"],
        PORTFOLIO_SCHEMA,
    )
    row_counts["portfolios"] = count
    print(f"    portfolios: {count:,} rows loaded in {time.time() - start:.3f}s")

    # -----------------------------------------------------------------------
    # Load Positions
    # Replaces: Ab Initio MultiLoad to position reporting tables
    # -----------------------------------------------------------------------
    print("  Loading positions...")
    start = time.time()
    count = load_table(
        catalog, namespace, "positions",
        transformed_data["positions"],
        POSITION_SCHEMA,
    )
    row_counts["positions"] = count
    print(f"    positions: {count:,} rows loaded in {time.time() - start:.3f}s")

    # -----------------------------------------------------------------------
    # Load Transactions (with monthly partitioning)
    # Replaces: Ab Initio TPT to RPT_TRANSACTION_DETAIL
    # -----------------------------------------------------------------------
    print("  Loading transactions (partitioned by month)...")
    start = time.time()
    count = load_table(
        catalog, namespace, "transactions",
        transformed_data["transactions"],
        TRANSACTION_SCHEMA,
        TRANSACTION_PARTITION_SPEC,
    )
    row_counts["transactions"] = count
    print(f"    transactions: {count:,} rows loaded in {time.time() - start:.3f}s")

    # -----------------------------------------------------------------------
    # Load Position Rollup (aggregated summary)
    # Replaces: Ab Initio MultiLoad to RPT_POSITION_ROLLUP
    # -----------------------------------------------------------------------
    print("  Loading position rollup...")
    start = time.time()
    count = load_table(
        catalog, namespace, "position_rollup",
        transformed_data["position_rollup"],
        POSITION_ROLLUP_SCHEMA,
    )
    row_counts["position_rollup"] = count
    print(f"    position_rollup: {count:,} rows loaded in {time.time() - start:.3f}s")

    total_elapsed = time.time() - total_start
    total_rows = sum(row_counts.values())

    print(f"\n  Load complete: {total_rows:,} total rows across {len(row_counts)} tables")
    print(f"  Total load time: {total_elapsed:.3f}s")
    print(f"  Warehouse location: {warehouse_dir}")

    # -----------------------------------------------------------------------
    # Verify loaded data (read back from Iceberg)
    # -----------------------------------------------------------------------
    print("\n  Verification (reading back from Iceberg):")
    for table_name, expected_count in row_counts.items():
        try:
            table = catalog.load_table(f"{namespace}.{table_name}")
            scan = table.scan()
            arrow_result = scan.to_arrow()
            actual_count = len(arrow_result)
            status = "OK" if actual_count == expected_count else "MISMATCH"
            print(f"    {table_name}: {actual_count:,} rows read back [{status}]")
        except Exception as e:
            print(f"    {table_name}: verification failed - {e}")

    return row_counts
