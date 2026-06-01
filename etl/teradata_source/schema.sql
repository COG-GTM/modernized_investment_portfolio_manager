-- ============================================================================
-- Teradata DDL: Investment Portfolio Management System
-- Source system schema (legacy Teradata environment)
--
-- These tables represent the existing Teradata data warehouse tables that
-- are currently loaded/maintained by Ab Initio ETL graphs. This schema
-- will be migrated to Apache Iceberg open table format.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- PORTFOLIO_MASTER: Core portfolio/account master table
-- Mirrors: backend/models/database.py -> Portfolio ORM model
-- ---------------------------------------------------------------------------
CREATE MULTISET TABLE TD_PORTFOLIO_MASTER, NO FALLBACK,
     NO BEFORE JOURNAL,
     NO AFTER JOURNAL,
     CHECKSUM = DEFAULT,
     DEFAULT MERGEBLOCKRATIO
(
    PORT_ID         VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    ACCT_NO         VARCHAR(10) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    CLT_NM          VARCHAR(30) CHARACTER SET LATIN NOT CASESPECIFIC,
    CLT_TYP_CD      CHAR(1) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (CLT_TYP_CD IN ('I', 'C', 'T')),
    CRTE_DT         DATE FORMAT 'YYYY-MM-DD',
    LST_MAINT_DT    DATE FORMAT 'YYYY-MM-DD',
    STAT_CD         CHAR(1) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (STAT_CD IN ('A', 'C', 'S')),
    TOT_VAL_AM      DECIMAL(15,2),
    CSH_BAL_AM      DECIMAL(15,2),
    LST_USR_ID      VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC,
    LST_TRANS_ID    VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC
)
PRIMARY INDEX (PORT_ID)
PARTITION BY RANGE_N(STAT_CD BETWEEN 'A' AND 'S' EACH 1);

COMMENT ON TABLE TD_PORTFOLIO_MASTER IS 'Master portfolio table - one row per portfolio/account combination';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.PORT_ID IS 'Portfolio identifier - 8 character alphanumeric';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.ACCT_NO IS 'Account number - 10 digit numeric string';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.CLT_NM IS 'Client full name';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.CLT_TYP_CD IS 'Client type: I=Individual, C=Corporate, T=Trust';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.STAT_CD IS 'Portfolio status: A=Active, C=Closed, S=Suspended';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.TOT_VAL_AM IS 'Total portfolio value including cash and positions';
COMMENT ON COLUMN TD_PORTFOLIO_MASTER.CSH_BAL_AM IS 'Cash balance available in portfolio';

-- Collect statistics for optimizer
COLLECT STATISTICS ON TD_PORTFOLIO_MASTER INDEX (PORT_ID);
COLLECT STATISTICS ON TD_PORTFOLIO_MASTER COLUMN (STAT_CD);
COLLECT STATISTICS ON TD_PORTFOLIO_MASTER COLUMN (CLT_TYP_CD);


-- ---------------------------------------------------------------------------
-- POSITION_DETAIL: Investment position holdings
-- Mirrors: backend/models/database.py -> Position ORM model
-- ---------------------------------------------------------------------------
CREATE MULTISET TABLE TD_POSITION_DETAIL, NO FALLBACK,
     NO BEFORE JOURNAL,
     NO AFTER JOURNAL,
     CHECKSUM = DEFAULT,
     DEFAULT MERGEBLOCKRATIO
(
    PORT_ID         VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    POS_DT          DATE FORMAT 'YYYY-MM-DD' NOT NULL,
    INVST_ID        VARCHAR(10) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    QTY_AM          DECIMAL(15,4),
    CST_BAS_AM      DECIMAL(15,2),
    MKT_VAL_AM      DECIMAL(15,2),
    CRNCY_CD        CHAR(3) CHARACTER SET LATIN NOT CASESPECIFIC,
    STAT_CD         CHAR(1) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (STAT_CD IN ('A', 'C', 'P')),
    LST_MAINT_TS    TIMESTAMP(6),
    LST_MAINT_USR   VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC
)
PRIMARY INDEX (PORT_ID, POS_DT, INVST_ID)
PARTITION BY RANGE_N(POS_DT BETWEEN DATE '2020-01-01' AND DATE '2030-12-31' EACH INTERVAL '1' MONTH);

COMMENT ON TABLE TD_POSITION_DETAIL IS 'Position detail - tracks investment holdings per portfolio per date';
COMMENT ON COLUMN TD_POSITION_DETAIL.PORT_ID IS 'Foreign key to TD_PORTFOLIO_MASTER.PORT_ID';
COMMENT ON COLUMN TD_POSITION_DETAIL.POS_DT IS 'Position date - date the position snapshot was taken';
COMMENT ON COLUMN TD_POSITION_DETAIL.INVST_ID IS 'Investment/security identifier (ticker symbol)';
COMMENT ON COLUMN TD_POSITION_DETAIL.QTY_AM IS 'Number of shares/units held';
COMMENT ON COLUMN TD_POSITION_DETAIL.CST_BAS_AM IS 'Original cost basis of the position';
COMMENT ON COLUMN TD_POSITION_DETAIL.MKT_VAL_AM IS 'Current market value of the position';
COMMENT ON COLUMN TD_POSITION_DETAIL.STAT_CD IS 'Position status: A=Active, C=Closed, P=Pending';

COLLECT STATISTICS ON TD_POSITION_DETAIL INDEX (PORT_ID, POS_DT, INVST_ID);
COLLECT STATISTICS ON TD_POSITION_DETAIL COLUMN (PORT_ID);
COLLECT STATISTICS ON TD_POSITION_DETAIL COLUMN (STAT_CD);


-- ---------------------------------------------------------------------------
-- TRANSACTION_LOG: Trade and transaction records
-- Mirrors: backend/models/transactions.py -> Transaction ORM model
-- ---------------------------------------------------------------------------
CREATE MULTISET TABLE TD_TRANSACTION_LOG, NO FALLBACK,
     NO BEFORE JOURNAL,
     NO AFTER JOURNAL,
     CHECKSUM = DEFAULT,
     DEFAULT MERGEBLOCKRATIO
(
    TXN_DT          DATE FORMAT 'YYYY-MM-DD' NOT NULL,
    TXN_TM          TIME(6) NOT NULL,
    PORT_ID         VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    SEQ_NO          VARCHAR(6) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    INVST_ID        VARCHAR(10) CHARACTER SET LATIN NOT CASESPECIFIC,
    TXN_TYP_CD     CHAR(2) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (TXN_TYP_CD IN ('BU', 'SL', 'TR', 'FE')),
    QTY_AM          DECIMAL(15,4),
    PRC_AM          DECIMAL(15,4),
    TXN_AM          DECIMAL(15,2),
    CRNCY_CD        CHAR(3) CHARACTER SET LATIN NOT CASESPECIFIC,
    STAT_CD         CHAR(1) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (STAT_CD IN ('P', 'D', 'F', 'R')),
    PROC_TS         TIMESTAMP(6),
    PROC_USR_ID     VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC
)
PRIMARY INDEX (TXN_DT, PORT_ID, SEQ_NO)
PARTITION BY RANGE_N(TXN_DT BETWEEN DATE '2020-01-01' AND DATE '2030-12-31' EACH INTERVAL '1' MONTH);

COMMENT ON TABLE TD_TRANSACTION_LOG IS 'Transaction log - all buy/sell/transfer/fee transactions';
COMMENT ON COLUMN TD_TRANSACTION_LOG.TXN_DT IS 'Transaction date';
COMMENT ON COLUMN TD_TRANSACTION_LOG.TXN_TM IS 'Transaction time with microsecond precision';
COMMENT ON COLUMN TD_TRANSACTION_LOG.PORT_ID IS 'Foreign key to TD_PORTFOLIO_MASTER.PORT_ID';
COMMENT ON COLUMN TD_TRANSACTION_LOG.SEQ_NO IS 'Sequence number within date/portfolio - 6 digit zero-padded';
COMMENT ON COLUMN TD_TRANSACTION_LOG.TXN_TYP_CD IS 'Transaction type: BU=Buy, SL=Sell, TR=Transfer, FE=Fee';
COMMENT ON COLUMN TD_TRANSACTION_LOG.STAT_CD IS 'Status: P=Pending, D=Done, F=Failed, R=Reversed';

COLLECT STATISTICS ON TD_TRANSACTION_LOG INDEX (TXN_DT, PORT_ID, SEQ_NO);
COLLECT STATISTICS ON TD_TRANSACTION_LOG COLUMN (PORT_ID);
COLLECT STATISTICS ON TD_TRANSACTION_LOG COLUMN (TXN_TYP_CD);
COLLECT STATISTICS ON TD_TRANSACTION_LOG COLUMN (STAT_CD);


-- ---------------------------------------------------------------------------
-- AUDIT_HISTORY: Change audit trail
-- Mirrors: backend/models/history.py -> History ORM model
-- ---------------------------------------------------------------------------
CREATE MULTISET TABLE TD_AUDIT_HISTORY, NO FALLBACK,
     NO BEFORE JOURNAL,
     NO AFTER JOURNAL,
     CHECKSUM = DEFAULT,
     DEFAULT MERGEBLOCKRATIO
(
    PORT_ID         VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    AUD_DT          VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    AUD_TM          VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    SEQ_NO          VARCHAR(4) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
    REC_TYP_CD      CHAR(2) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (REC_TYP_CD IN ('PT', 'PS', 'TR')),
    ACT_CD          CHAR(1) CHARACTER SET LATIN NOT CASESPECIFIC
                     CHECK (ACT_CD IN ('A', 'C', 'D')),
    BEF_IMG_TX      CLOB(1M) CHARACTER SET LATIN,
    AFT_IMG_TX      CLOB(1M) CHARACTER SET LATIN,
    RSN_CD          VARCHAR(4) CHARACTER SET LATIN NOT CASESPECIFIC,
    PROC_TS         TIMESTAMP(6),
    PROC_USR_ID     VARCHAR(8) CHARACTER SET LATIN NOT CASESPECIFIC
)
PRIMARY INDEX (PORT_ID, AUD_DT, AUD_TM, SEQ_NO)
PARTITION BY RANGE_N(AUD_DT BETWEEN '20200101' AND '20301231' EACH 1);

COMMENT ON TABLE TD_AUDIT_HISTORY IS 'Audit history - tracks all changes to portfolio, position, and transaction records';
COMMENT ON COLUMN TD_AUDIT_HISTORY.PORT_ID IS 'Foreign key to TD_PORTFOLIO_MASTER.PORT_ID';
COMMENT ON COLUMN TD_AUDIT_HISTORY.AUD_DT IS 'Audit date in YYYYMMDD format';
COMMENT ON COLUMN TD_AUDIT_HISTORY.AUD_TM IS 'Audit time in HHMMSSFF format';
COMMENT ON COLUMN TD_AUDIT_HISTORY.REC_TYP_CD IS 'Record type: PT=Portfolio, PS=Position, TR=Transaction';
COMMENT ON COLUMN TD_AUDIT_HISTORY.ACT_CD IS 'Action code: A=Add, C=Change, D=Delete';
COMMENT ON COLUMN TD_AUDIT_HISTORY.BEF_IMG_TX IS 'JSON before-image of the changed record';
COMMENT ON COLUMN TD_AUDIT_HISTORY.AFT_IMG_TX IS 'JSON after-image of the changed record';

COLLECT STATISTICS ON TD_AUDIT_HISTORY INDEX (PORT_ID, AUD_DT, AUD_TM, SEQ_NO);
COLLECT STATISTICS ON TD_AUDIT_HISTORY COLUMN (PORT_ID);
COLLECT STATISTICS ON TD_AUDIT_HISTORY COLUMN (REC_TYP_CD);
COLLECT STATISTICS ON TD_AUDIT_HISTORY COLUMN (ACT_CD);


-- ---------------------------------------------------------------------------
-- Reporting views (used by Ab Initio downstream graphs)
-- ---------------------------------------------------------------------------
CREATE VIEW TD_VW_PORTFOLIO_SUMMARY AS
SELECT
    pm.PORT_ID,
    pm.ACCT_NO,
    pm.CLT_NM,
    pm.CLT_TYP_CD,
    pm.STAT_CD,
    pm.TOT_VAL_AM,
    pm.CSH_BAL_AM,
    COUNT(pd.INVST_ID) AS POSITION_CNT,
    SUM(pd.MKT_VAL_AM) AS TOTAL_MKT_VAL,
    SUM(pd.CST_BAS_AM) AS TOTAL_CST_BAS,
    SUM(pd.MKT_VAL_AM) - SUM(pd.CST_BAS_AM) AS TOTAL_GAIN_LOSS
FROM TD_PORTFOLIO_MASTER pm
LEFT JOIN TD_POSITION_DETAIL pd
    ON pm.PORT_ID = pd.PORT_ID
    AND pd.STAT_CD = 'A'
GROUP BY
    pm.PORT_ID, pm.ACCT_NO, pm.CLT_NM, pm.CLT_TYP_CD,
    pm.STAT_CD, pm.TOT_VAL_AM, pm.CSH_BAL_AM;
