# Ab Initio Legacy ETL Documentation

## Overview

This directory documents the **existing Ab Initio ETL pipeline** that manages data movement and transformation within the Teradata-based Investment Portfolio Management System. This represents the **"before" state** that Devin will displace.

## Current Architecture

The Ab Initio Co>Operating System runs three primary ETL graphs managed via the Ab Initio GDE (Graphical Development Environment):

### Graph 1: Teradata Extract (BTEQ/FastExport)

- **Component**: Ab Initio Teradata Connector
- **Method**: BTEQ scripts + FastExport utility
- **Source Tables**: `TD_PORTFOLIO_MASTER`, `TD_POSITION_DETAIL`, `TD_TRANSACTION_LOG`, `TD_AUDIT_HISTORY`
- **Output**: Ab Initio serial/parallel datasets (.dat files)
- **Schedule**: Daily batch at 02:00 AM EST
- **Estimated Runtime**: 45-90 minutes depending on data volume

### Graph 2: Transform & Enrich (GDE Graphs)

Multiple Ab Initio transform components chained together:

1. **Dedup Component** - Removes duplicate portfolio records using `PORT_ID` as key
2. **Reformat Component** - Maps Teradata column names to reporting schema
3. **Filter Component** - Removes invalid/null records (data quality gate)
4. **Rollup Component** - Aggregates positions by portfolio, calculates totals
5. **Join Component** - Enriches transaction data with portfolio metadata
6. **Normalize Component** - Standardizes currency codes, date formats

### Graph 3: Load to Reporting (Teradata Load)

- **Component**: Ab Initio Teradata Load utility
- **Target Tables**: `RPT_PORTFOLIO_SUMMARY`, `RPT_POSITION_ROLLUP`, `RPT_TRANSACTION_DETAIL`
- **Method**: MultiLoad / TPT (Teradata Parallel Transporter)
- **Error Handling**: Reject file + error log to Ab Initio DMP

## Data Flow Diagram

```mermaid
graph LR
    subgraph "Teradata Source"
        TD1[TD_PORTFOLIO_MASTER]
        TD2[TD_POSITION_DETAIL]
        TD3[TD_TRANSACTION_LOG]
        TD4[TD_AUDIT_HISTORY]
    end

    subgraph "Ab Initio Extract Layer"
        BTEQ[BTEQ Scripts]
        FE[FastExport Utility]
        TC[Ab Initio<br/>Teradata Connector]
    end

    subgraph "Ab Initio Transform Layer (GDE)"
        DD[Dedup Component]
        RF[Reformat Component]
        FLT[Filter Component]
        RU[Rollup Component]
        JN[Join Component]
        NRM[Normalize Component]
    end

    subgraph "Ab Initio Load Layer"
        ML[MultiLoad / TPT]
        ERR[Error/Reject Files]
    end

    subgraph "Teradata Reporting"
        RPT1[RPT_PORTFOLIO_SUMMARY]
        RPT2[RPT_POSITION_ROLLUP]
        RPT3[RPT_TRANSACTION_DETAIL]
    end

    TD1 --> BTEQ --> TC
    TD2 --> FE --> TC
    TD3 --> FE --> TC
    TD4 --> BTEQ --> TC

    TC --> DD --> RF --> FLT --> RU
    FLT --> JN
    RU --> NRM

    NRM --> ML
    JN --> ML
    ML --> RPT1
    ML --> RPT2
    ML --> RPT3
    ML --> ERR
```

## Cost & Complexity Analysis

| Dimension | Current State (Ab Initio) |
|---|---|
| **License Cost** | ~$500K-$1M/year (Ab Initio Co>Operating System) |
| **Infrastructure** | Dedicated Ab Initio servers + Teradata appliance |
| **Development Tool** | Ab Initio GDE (proprietary graphical IDE) |
| **Skills Required** | Ab Initio certified developers (scarce, expensive) |
| **Vendor Lock-in** | Complete - proprietary data format, runtime, IDE |
| **Deployment** | Manual graph promotion through Ab Initio EME |
| **Monitoring** | Ab Initio Operations Console (separate license) |
| **Data Format** | Proprietary Ab Initio serial/parallel datasets |
| **Change Velocity** | 2-4 weeks per graph change (dev + test + promote) |
| **Testing** | Ab Initio Component Test Framework (limited) |

## Known Issues

1. **Performance degradation** during month-end when transaction volumes spike 3x
2. **Single point of failure** - Ab Initio server outage stops all ETL
3. **No version control** - GDE graphs stored in Ab Initio EME, not Git
4. **Limited observability** - Monitoring requires Ab Initio Operations Console access
5. **Teradata lock-in** - All data stays within Teradata ecosystem, no open format support

## Files in This Directory

| File | Description |
|---|---|
| `README.md` | This document |
| `abinitio_graph_spec.yaml` | Detailed YAML specification of all Ab Initio graph components |
