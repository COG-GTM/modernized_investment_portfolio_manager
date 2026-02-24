-- Portfolio Management Schema (matches existing Python/Alembic schema)

CREATE TABLE IF NOT EXISTS portfolios (
    port_id VARCHAR(8) NOT NULL,
    account_no VARCHAR(10) NOT NULL,
    client_name VARCHAR(30),
    client_type VARCHAR(1),
    create_date DATE,
    last_maint DATE,
    status VARCHAR(1),
    total_value DECIMAL(15, 2),
    cash_balance DECIMAL(15, 2),
    last_user VARCHAR(8),
    last_trans VARCHAR(8),
    PRIMARY KEY (port_id, account_no)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_client_type ON portfolios(client_type);
CREATE INDEX IF NOT EXISTS idx_portfolio_status ON portfolios(status);

CREATE TABLE IF NOT EXISTS positions (
    portfolio_id VARCHAR(8) NOT NULL,
    date DATE NOT NULL,
    investment_id VARCHAR(10) NOT NULL,
    quantity DECIMAL(15, 4),
    cost_basis DECIMAL(15, 2),
    market_value DECIMAL(15, 2),
    currency VARCHAR(3),
    status VARCHAR(1),
    last_maint_date TIMESTAMP,
    last_maint_user VARCHAR(8),
    PRIMARY KEY (portfolio_id, date, investment_id)
);

CREATE INDEX IF NOT EXISTS idx_position_portfolio_id ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_position_date ON positions(date);
CREATE INDEX IF NOT EXISTS idx_position_investment_id ON positions(investment_id);
CREATE INDEX IF NOT EXISTS idx_position_status ON positions(status);

CREATE TABLE IF NOT EXISTS transactions (
    date DATE NOT NULL,
    time TIME NOT NULL,
    portfolio_id VARCHAR(8) NOT NULL,
    sequence_no VARCHAR(6) NOT NULL,
    investment_id VARCHAR(10),
    type VARCHAR(2),
    quantity DECIMAL(15, 4),
    price DECIMAL(15, 4),
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    status VARCHAR(1),
    process_date TIMESTAMP,
    process_user VARCHAR(8),
    PRIMARY KEY (date, time, portfolio_id, sequence_no)
);

CREATE INDEX IF NOT EXISTS idx_transaction_portfolio_id ON transactions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_transaction_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transaction_investment_id ON transactions(investment_id);
CREATE INDEX IF NOT EXISTS idx_transaction_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transaction_status ON transactions(status);

CREATE TABLE IF NOT EXISTS history (
    portfolio_id VARCHAR(8) NOT NULL,
    date VARCHAR(8) NOT NULL,
    time VARCHAR(8) NOT NULL,
    seq_no VARCHAR(4) NOT NULL,
    record_type VARCHAR(2),
    action_code VARCHAR(1),
    before_image TEXT,
    after_image TEXT,
    reason_code VARCHAR(4),
    process_date TIMESTAMP,
    process_user VARCHAR(8),
    PRIMARY KEY (portfolio_id, date, time, seq_no)
);

CREATE INDEX IF NOT EXISTS idx_history_portfolio_id ON history(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_history_date ON history(date);
CREATE INDEX IF NOT EXISTS idx_history_record_type ON history(record_type);
CREATE INDEX IF NOT EXISTS idx_history_action_code ON history(action_code);
