# ETL Demo: Ab Initio Displacement + Teradata-to-Iceberg Migration

## Demo Scenario

This demo showcases how **Devin** can automatically generate a production-grade ETL pipeline that:

1. **Displaces Ab Initio** — Replaces the proprietary Ab Initio Co>Operating System ($500K-$1M/year license) with standard Python code that any developer can maintain.
2. **Migrates from Teradata to Apache Iceberg** — Moves data from vendor-locked Teradata tables to the open Apache Iceberg table format, eliminating Teradata licensing costs and enabling queries from any engine (Spark, Trino, DuckDB, Snowflake).

```
  BEFORE                                    AFTER
  ======                                    =====
  Teradata  -->  Ab Initio  -->  Teradata   CSV/Parquet  -->  Python  -->  Apache Iceberg
  (source)      (ETL $$$)       (target)    (source)         (free)       (open format)

  Cost: ~$1M+/year                          Cost: $0 licensing
  Lock-in: Complete                         Lock-in: None
  Developers: Scarce                        Developers: Any Python dev
```

## Directory Structure

```
etl/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
│
├── teradata_source/             # LEGACY: Simulated Teradata source system
│   ├── schema.sql               # Teradata DDL (CREATE MULTISET TABLE, etc.)
│   ├── sample_data.py           # Generates realistic CSV data
│   └── data/                    # Generated CSV files (created by sample_data.py)
│       ├── TD_PORTFOLIO_MASTER.csv
│       ├── TD_POSITION_DETAIL.csv
│       ├── TD_TRANSACTION_LOG.csv
│       └── TD_AUDIT_HISTORY.csv
│
├── abinitio_legacy/             # CURRENT STATE: Ab Initio documentation
│   ├── README.md                # Describes the Ab Initio ETL graphs
│   └── abinitio_graph_spec.yaml # YAML spec of Ab Initio components
│
├── pipeline/                    # TARGET STATE: Devin-generated Python pipeline
│   ├── __init__.py
│   ├── extract.py               # Replaces Ab Initio Teradata Connector
│   ├── transform.py             # Replaces Ab Initio GDE transform graphs
│   ├── load_iceberg.py          # Replaces Ab Initio Load to Teradata
│   └── main.py                  # Orchestrator (replaces Ab Initio Scheduler)
│
├── demo/                        # Demo presentation
│   └── index.html               # Single-page demo presentation
│
└── iceberg_warehouse/           # Generated Iceberg data (created by pipeline)
    ├── catalog.db               # SQLite Iceberg catalog
    └── investment_dwh/          # Iceberg table data files
```

## Quick Start

### 1. Install Dependencies

```bash
cd etl/
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
python teradata_source/sample_data.py
```

This creates realistic CSV files in `teradata_source/data/` simulating Teradata FastExport output:
- 55 portfolios (+ 5 intentional duplicates for dedup demo)
- 220 positions
- 1,100 transactions (+ 3 intentional bad records for validation demo)
- 600 audit history records

### 3. Run the ETL Pipeline

```bash
python -m pipeline.main
```

Or equivalently:

```bash
pip install -r requirements.txt && python -m pipeline.main
```

The pipeline will:
1. **Extract** — Read CSV files (simulating Teradata FastExport)
2. **Transform** — Deduplicate, validate, schema-map, and aggregate
3. **Load** — Write to Apache Iceberg tables with partitioning
4. **Verify** — Read back from Iceberg to confirm data integrity

> **Note:** If sample data doesn't exist yet, the pipeline will auto-generate it on first run.

### 4. View the Demo Presentation

```bash
open demo/index.html
```

The presentation includes:
- "Before" architecture diagram (Ab Initio + Teradata)
- "After" architecture diagram (Python + Iceberg)
- Side-by-side comparison table
- Key metrics and ROI analysis

## What Each Directory Represents

| Directory | Represents | Description |
|---|---|---|
| `teradata_source/` | **Legacy Source** | The Teradata data warehouse tables that currently exist. Schema in Teradata DDL dialect, data exported as CSVs. |
| `abinitio_legacy/` | **Current ETL State** | Documentation of the Ab Initio graphs that currently move and transform the data. This is what Devin displaces. |
| `pipeline/` | **Devin Target State** | The Python pipeline that Devin generates to replace Ab Initio. Reads from source CSVs, writes to Iceberg. |
| `demo/` | **Presentation** | Single-page HTML demo for prospect/stakeholder presentations. |

## Pipeline Architecture

```
  ┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
  │    EXTRACT            │     │    TRANSFORM          │     │    LOAD              │
  │                       │     │                       │     │                       │
  │  extract.py           │     │  transform.py         │     │  load_iceberg.py     │
  │                       │     │                       │     │                       │
  │  - Read CSVs          │────>│  - Deduplicate        │────>│  - Create catalog    │
  │  - Parse columns      │     │  - Validate           │     │  - Define schemas    │
  │  - Return DataFrames  │     │  - Map schema         │     │  - Write to Iceberg  │
  │                       │     │  - Cast types          │     │  - Partition by date │
  │  Replaces:            │     │  - Aggregate positions │     │  - Verify writes     │
  │  BTEQ + FastExport    │     │                       │     │                       │
  │  Ab Initio Connector  │     │  Replaces:            │     │  Replaces:            │
  │                       │     │  6 Ab Initio graphs   │     │  MultiLoad / TPT     │
  └──────────────────────┘     └──────────────────────┘     └──────────────────────┘
```

## Key Comparisons

| Metric | Ab Initio + Teradata | Devin + Iceberg |
|---|---|---|
| **License Cost** | ~$1M+/year | $0 |
| **Runtime** | 75-150 min | Seconds |
| **Components** | 11 proprietary | 4 Python files |
| **Developer Pool** | Ab Initio certified only | Any Python dev |
| **Data Format** | Proprietary/closed | Apache Iceberg (open) |
| **Version Control** | Ab Initio EME | Git |
