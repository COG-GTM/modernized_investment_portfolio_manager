"""add db2 and vsam migrated tables

Revision ID: 4f940954b756
Revises: 40a256798f94
Create Date: 2026-03-12 05:21:24.556078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f940954b756'
down_revision: Union[str, Sequence[str], None] = '40a256798f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create DB2 and VSAM migrated tables.

    These tables are new additions migrated from the legacy DB2/VSAM
    definitions in COG-GTM/COBOL-Legacy-Benchmark-Suite.  The pre-existing
    legacy tables (portfolios, positions, transactions, history) are NOT
    touched by this migration -- they are managed by earlier revisions.
    """

    # --- DB2 tables -------------------------------------------------------

    # PORTFOLIO_MASTER  (src/database/db2/db2-definitions.sql)
    op.create_table('portfolio_master',
    sa.Column('portfolio_id', sa.String(length=8), nullable=False, comment='Portfolio identifier (DB2 CHAR(8))'),
    sa.Column('account_type', sa.String(length=2), nullable=False, comment='Account type code (DB2 CHAR(2))'),
    sa.Column('branch_id', sa.String(length=2), nullable=False, comment='Branch identifier (DB2 CHAR(2))'),
    sa.Column('client_id', sa.String(length=10), nullable=False, comment='Client identifier (DB2 CHAR(10))'),
    sa.Column('portfolio_name', sa.String(length=50), nullable=False, comment='Portfolio display name (DB2 VARCHAR(50))'),
    sa.Column('currency_code', sa.String(length=3), nullable=False, comment='ISO currency code (DB2 CHAR(3))'),
    sa.Column('risk_level', sa.String(length=1), nullable=False, comment='Risk level indicator (DB2 CHAR(1))'),
    sa.Column('status', sa.String(length=1), nullable=False, comment='Portfolio status: A=Active, C=Closed, S=Suspended'),
    sa.Column('open_date', sa.Date(), nullable=False, comment='Date portfolio was opened (DB2 DATE)'),
    sa.Column('close_date', sa.Date(), nullable=True, comment='Date portfolio was closed, NULL if open (DB2 DATE)'),
    sa.Column('last_maint_date', sa.DateTime(), nullable=False, comment='Last maintenance timestamp (DB2 TIMESTAMP)'),
    sa.Column('last_maint_user', sa.String(length=8), nullable=False, comment='User who last modified the record (DB2 VARCHAR(8))'),
    sa.PrimaryKeyConstraint('portfolio_id'),
    comment='Portfolio master -- migrated from DB2 PORTFOLIO_MASTER'
    )
    op.create_index('idx_port_master_client', 'portfolio_master', ['client_id', 'status'], unique=False)

    # INVESTMENT_POSITIONS  (src/database/db2/db2-definitions.sql)
    op.create_table('investment_positions',
    sa.Column('portfolio_id', sa.String(length=8), nullable=False, comment='FK to portfolio_master (DB2 CHAR(8))'),
    sa.Column('investment_id', sa.String(length=10), nullable=False, comment='Security / investment identifier (DB2 CHAR(10))'),
    sa.Column('position_date', sa.Date(), nullable=False, comment='Valuation date for this position (DB2 DATE)'),
    sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, comment='Number of units held (DB2 DECIMAL(18,4))'),
    sa.Column('cost_basis', sa.Numeric(precision=18, scale=2), nullable=False, comment='Total cost basis (DB2 DECIMAL(18,2))'),
    sa.Column('market_value', sa.Numeric(precision=18, scale=2), nullable=False, comment='Current market value (DB2 DECIMAL(18,2))'),
    sa.Column('currency_code', sa.String(length=3), nullable=False, comment='ISO currency code (DB2 CHAR(3))'),
    sa.Column('last_maint_date', sa.DateTime(), nullable=False, comment='Last maintenance timestamp (DB2 TIMESTAMP)'),
    sa.Column('last_maint_user', sa.String(length=8), nullable=False, comment='User who last modified the record (DB2 VARCHAR(8))'),
    sa.ForeignKeyConstraint(['portfolio_id'], ['portfolio_master.portfolio_id'], ),
    sa.PrimaryKeyConstraint('portfolio_id', 'investment_id', 'position_date'),
    comment='Investment positions -- migrated from DB2 INVESTMENT_POSITIONS'
    )
    op.create_index('idx_positions_date', 'investment_positions', ['position_date', 'portfolio_id'], unique=False)

    # TRANSACTION_HISTORY  (src/database/db2/db2-definitions.sql)
    op.create_table('transaction_history',
    sa.Column('transaction_id', sa.String(length=20), nullable=False, comment='Unique transaction ID: YYYYMMDDHHMMSS + seq (DB2 CHAR(20))'),
    sa.Column('portfolio_id', sa.String(length=8), nullable=False, comment='FK to portfolio_master (DB2 CHAR(8))'),
    sa.Column('transaction_date', sa.Date(), nullable=False, comment='Business date of the transaction (DB2 DATE)'),
    sa.Column('transaction_time', sa.Time(), nullable=False, comment='Time of the transaction (DB2 TIME)'),
    sa.Column('investment_id', sa.String(length=10), nullable=False, comment='Security / investment identifier (DB2 CHAR(10))'),
    sa.Column('transaction_type', sa.String(length=2), nullable=False, comment='Type: BU=Buy, SL=Sell, TR=Transfer, FE=Fee (DB2 CHAR(2))'),
    sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, comment='Transaction quantity (DB2 DECIMAL(18,4))'),
    sa.Column('price', sa.Numeric(precision=18, scale=4), nullable=False, comment='Transaction price per unit (DB2 DECIMAL(18,4))'),
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False, comment='Total transaction amount (DB2 DECIMAL(18,2))'),
    sa.Column('currency_code', sa.String(length=3), nullable=False, comment='ISO currency code (DB2 CHAR(3))'),
    sa.Column('status', sa.String(length=1), nullable=False, comment='Status: P=Processed, F=Failed, R=Reversed (DB2 CHAR(1))'),
    sa.Column('process_date', sa.DateTime(), nullable=False, comment='Processing timestamp (DB2 TIMESTAMP)'),
    sa.Column('process_user', sa.String(length=8), nullable=False, comment='User who processed the transaction (DB2 VARCHAR(8))'),
    sa.ForeignKeyConstraint(['portfolio_id'], ['portfolio_master.portfolio_id'], ),
    sa.PrimaryKeyConstraint('transaction_id'),
    comment='Transaction history -- migrated from DB2 TRANSACTION_HISTORY'
    )
    op.create_index('idx_trans_hist_port', 'transaction_history', ['portfolio_id', 'transaction_date'], unique=False)
    op.create_index('idx_trans_hist_date', 'transaction_history', ['transaction_date', 'portfolio_id'], unique=False)

    # POSHIST  (src/database/db2/POSHIST.sql)
    op.create_table('position_history',
    sa.Column('account_no', sa.String(length=8), nullable=False, comment='Account number (DB2 CHAR(8))'),
    sa.Column('portfolio_id', sa.String(length=10), nullable=False, comment='Portfolio identifier (DB2 CHAR(10))'),
    sa.Column('trans_date', sa.Date(), nullable=False, comment='Transaction date (DB2 DATE)'),
    sa.Column('trans_time', sa.Time(), nullable=False, comment='Transaction time (DB2 TIME)'),
    sa.Column('trans_type', sa.String(length=2), nullable=False, comment='Transaction type: BU=Buy, SL=Sell, TR=Transfer (DB2 CHAR(2))'),
    sa.Column('security_id', sa.String(length=12), nullable=False, comment='Security identifier (DB2 CHAR(12))'),
    sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=False, comment='Transaction quantity (DB2 DECIMAL(15,3))'),
    sa.Column('price', sa.Numeric(precision=15, scale=3), nullable=False, comment='Transaction price per unit (DB2 DECIMAL(15,3))'),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False, comment='Transaction amount (DB2 DECIMAL(15,2))'),
    sa.Column('fees', sa.Numeric(precision=15, scale=2), server_default='0', nullable=False, comment='Transaction fees (DB2 DECIMAL(15,2) DEFAULT 0)'),
    sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False, comment='Total amount including fees (DB2 DECIMAL(15,2))'),
    sa.Column('cost_basis', sa.Numeric(precision=15, scale=2), nullable=False, comment='Cost basis amount (DB2 DECIMAL(15,2))'),
    sa.Column('gain_loss', sa.Numeric(precision=15, scale=2), nullable=False, comment='Realized gain/loss amount (DB2 DECIMAL(15,2))'),
    sa.Column('process_date', sa.Date(), nullable=False, comment='Processing date (DB2 DATE)'),
    sa.Column('process_time', sa.Time(), nullable=False, comment='Processing time (DB2 TIME)'),
    sa.Column('program_id', sa.String(length=8), nullable=False, comment='Originating program ID (DB2 CHAR(8))'),
    sa.Column('user_id', sa.String(length=8), nullable=False, comment='User who processed the record (DB2 CHAR(8))'),
    sa.Column('audit_timestamp', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Audit timestamp (DB2 TIMESTAMP WITH DEFAULT)'),
    sa.PrimaryKeyConstraint('account_no', 'portfolio_id', 'trans_date', 'trans_time'),
    comment='Position history -- migrated from DB2 POSHIST'
    )
    op.create_index('poshist_ix1', 'position_history', ['security_id', 'trans_date'], unique=False)
    op.create_index('poshist_ix2', 'position_history', ['process_date', 'program_id'], unique=False)

    # ERRLOG  (src/database/db2/ERRLOG.sql)
    op.create_table('error_log',
    sa.Column('error_timestamp', sa.DateTime(), nullable=False, comment='Error timestamp (DB2 TIMESTAMP)'),
    sa.Column('program_id', sa.String(length=8), nullable=False, comment='Originating program ID (DB2 CHAR(8))'),
    sa.Column('error_type', sa.String(length=1), nullable=False, comment='Error type: S=System, A=Application, D=Data (DB2 CHAR(1))'),
    sa.Column('error_severity', sa.Integer(), nullable=False, comment='Severity: 1=Info, 2=Warning, 3=Error, 4=Severe (DB2 INTEGER)'),
    sa.Column('error_code', sa.String(length=8), nullable=False, comment='Application error code (DB2 CHAR(8))'),
    sa.Column('error_message', sa.String(length=200), nullable=False, comment='Human-readable error description (DB2 VARCHAR(200))'),
    sa.Column('process_date', sa.Date(), nullable=False, comment='Processing date (DB2 DATE)'),
    sa.Column('process_time', sa.Time(), nullable=False, comment='Processing time (DB2 TIME)'),
    sa.Column('user_id', sa.String(length=8), nullable=False, comment='User associated with the error (DB2 CHAR(8))'),
    sa.Column('additional_info', sa.String(length=500), nullable=True, comment='Optional additional context (DB2 VARCHAR(500))'),
    sa.PrimaryKeyConstraint('error_timestamp', 'program_id'),
    comment='Error log -- migrated from DB2 ERRLOG'
    )
    op.create_index('errlog_ix1', 'error_log', ['process_date', sa.text('error_severity DESC')], unique=False)

    # RTNCODES  (src/database/db2/RTNCODES.sql)
    op.create_table('return_codes',
    sa.Column('timestamp', sa.DateTime(), nullable=False, comment='Execution timestamp (DB2 TIMESTAMP)'),
    sa.Column('program_id', sa.String(length=8), nullable=False, comment='Program identifier (DB2 CHAR(8))'),
    sa.Column('return_code', sa.Integer(), nullable=False, comment='Program return code (DB2 INTEGER)'),
    sa.Column('highest_code', sa.Integer(), nullable=False, comment='Highest return code in batch run (DB2 INTEGER)'),
    sa.Column('status_code', sa.String(length=1), nullable=False, comment='Execution status code (DB2 CHAR(1))'),
    sa.Column('message_text', sa.String(length=80), nullable=True, comment='Optional status/error message (DB2 VARCHAR(80))'),
    sa.PrimaryKeyConstraint('timestamp', 'program_id'),
    comment='Return codes -- migrated from DB2 RTNCODES'
    )
    op.create_index('rtncodes_prg_idx', 'return_codes', ['program_id', 'timestamp'], unique=False)
    op.create_index('rtncodes_sts_idx', 'return_codes', ['status_code', 'timestamp'], unique=False)

    # --- VSAM replacement tables ------------------------------------------

    # PORTMSTR / POSHIST KSDS  (src/database/vsam/vsam-definitions.txt)
    op.create_table('position_master',
    sa.Column('portfolio_id', sa.String(length=8), nullable=False, comment='Portfolio identifier - first 8 bytes of VSAM key'),
    sa.Column('security_id', sa.String(length=12), nullable=False, comment='Security identifier - maps to VSAM POSHIST key'),
    sa.Column('account_type', sa.String(length=2), nullable=False, comment='Account type - bytes 9-10 of PORTMSTR VSAM key'),
    sa.Column('branch_id', sa.String(length=2), nullable=False, comment='Branch identifier - bytes 11-12 of PORTMSTR VSAM key'),
    sa.Column('position_date', sa.Date(), nullable=False, comment='Position valuation date (YYYYMMDD in VSAM)'),
    sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, comment='Number of units held'),
    sa.Column('cost_basis', sa.Numeric(precision=18, scale=2), nullable=False, comment='Total cost basis'),
    sa.Column('market_value', sa.Numeric(precision=18, scale=2), nullable=False, comment='Current market value'),
    sa.Column('currency_code', sa.String(length=3), nullable=False, comment='ISO currency code'),
    sa.Column('status', sa.String(length=1), nullable=False, comment='Position status: A=Active, C=Closed'),
    sa.Column('last_maint_date', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Last maintenance timestamp'),
    sa.Column('last_maint_user', sa.String(length=8), nullable=False, comment='User who last modified the record'),
    sa.PrimaryKeyConstraint('portfolio_id', 'security_id'),
    comment='Position master -- VSAM KSDS replacement (PORTMSTR/POSHIST)'
    )
    op.create_index('idx_pos_master_date', 'position_master', ['position_date', 'portfolio_id'], unique=False)
    op.create_index('idx_pos_master_security', 'position_master', ['security_id', 'position_date'], unique=False)

    # TRANHIST KSDS  (src/database/vsam/vsam-definitions.txt)
    op.create_table('transaction_file',
    sa.Column('transaction_date', sa.Date(), nullable=False, comment='Transaction date - bytes 1-8 of VSAM key (YYYYMMDD)'),
    sa.Column('transaction_time', sa.Time(), nullable=False, comment='Transaction time - bytes 9-14 of VSAM key (HHMMSS)'),
    sa.Column('portfolio_id', sa.String(length=8), nullable=False, comment='Portfolio identifier - bytes 15-22 of VSAM key'),
    sa.Column('sequence_no', sa.String(length=6), nullable=False, comment='Sequence number - bytes 23-28 of VSAM key'),
    sa.Column('investment_id', sa.String(length=10), nullable=False, comment='Security / investment identifier'),
    sa.Column('transaction_type', sa.String(length=2), nullable=False, comment='Type: BU=Buy, SL=Sell, TR=Transfer, FE=Fee'),
    sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False, comment='Transaction quantity'),
    sa.Column('price', sa.Numeric(precision=18, scale=4), nullable=False, comment='Price per unit'),
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False, comment='Transaction amount (quantity * price)'),
    sa.Column('currency_code', sa.String(length=3), nullable=False, comment='ISO currency code'),
    sa.Column('status', sa.String(length=1), nullable=False, comment='Status: P=Processed, F=Failed, R=Reversed'),
    sa.Column('process_timestamp', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='Processing timestamp'),
    sa.Column('process_user', sa.String(length=8), nullable=False, comment='User who processed the transaction'),
    sa.PrimaryKeyConstraint('transaction_date', 'transaction_time', 'portfolio_id', 'sequence_no'),
    comment='Transaction file -- VSAM KSDS replacement (TRANHIST)'
    )
    op.create_index('idx_txn_file_portfolio', 'transaction_file', ['portfolio_id', 'transaction_date'], unique=False)
    op.create_index('idx_txn_file_date', 'transaction_file', ['transaction_date', 'portfolio_id'], unique=False)


def downgrade() -> None:
    """Drop all DB2/VSAM migrated tables (reverse order of creation)."""

    # --- VSAM replacement tables ------------------------------------------
    op.drop_index('idx_txn_file_date', table_name='transaction_file')
    op.drop_index('idx_txn_file_portfolio', table_name='transaction_file')
    op.drop_table('transaction_file')

    op.drop_index('idx_pos_master_security', table_name='position_master')
    op.drop_index('idx_pos_master_date', table_name='position_master')
    op.drop_table('position_master')

    # --- DB2 tables (children before parents) -----------------------------
    op.drop_index('rtncodes_sts_idx', table_name='return_codes')
    op.drop_index('rtncodes_prg_idx', table_name='return_codes')
    op.drop_table('return_codes')

    op.drop_index('errlog_ix1', table_name='error_log')
    op.drop_table('error_log')

    op.drop_index('poshist_ix2', table_name='position_history')
    op.drop_index('poshist_ix1', table_name='position_history')
    op.drop_table('position_history')

    op.drop_index('idx_trans_hist_date', table_name='transaction_history')
    op.drop_index('idx_trans_hist_port', table_name='transaction_history')
    op.drop_table('transaction_history')

    op.drop_index('idx_positions_date', table_name='investment_positions')
    op.drop_table('investment_positions')

    op.drop_index('idx_port_master_client', table_name='portfolio_master')
    op.drop_table('portfolio_master')
