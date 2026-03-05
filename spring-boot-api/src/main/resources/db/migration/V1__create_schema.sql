-- Portfolio table (mirrors Python Portfolio model)
CREATE TABLE portfolios (
    port_id     VARCHAR(8)      NOT NULL,
    account_no  VARCHAR(10)     NOT NULL,
    client_name VARCHAR(30),
    client_type VARCHAR(1)      CHECK (client_type IN ('I', 'C', 'T')),
    create_date DATE,
    last_maint  DATE,
    status      VARCHAR(1)      CHECK (status IN ('A', 'C', 'S')),
    total_value DECIMAL(15, 2),
    cash_balance DECIMAL(15, 2),
    last_user   VARCHAR(8),
    last_trans  VARCHAR(8),
    PRIMARY KEY (port_id, account_no)
);

CREATE INDEX idx_portfolio_status ON portfolios (status);
CREATE INDEX idx_portfolio_client_type ON portfolios (client_type);

-- Position table (mirrors Python Position model)
CREATE TABLE positions (
    portfolio_id    VARCHAR(8)      NOT NULL,
    date            DATE            NOT NULL,
    investment_id   VARCHAR(10)     NOT NULL,
    quantity        DECIMAL(15, 4),
    cost_basis      DECIMAL(15, 2),
    market_value    DECIMAL(15, 2),
    currency        VARCHAR(3),
    status          VARCHAR(1)      CHECK (status IN ('A', 'C', 'P')),
    last_maint_date TIMESTAMP,
    last_maint_user VARCHAR(8),
    PRIMARY KEY (portfolio_id, date, investment_id)
);

CREATE INDEX idx_position_portfolio_id ON positions (portfolio_id);
CREATE INDEX idx_position_date ON positions (date);
CREATE INDEX idx_position_investment_id ON positions (investment_id);
CREATE INDEX idx_position_status ON positions (status);

-- Transaction table (mirrors Python Transaction model)
CREATE TABLE transactions (
    date            DATE            NOT NULL,
    time            TIME            NOT NULL,
    portfolio_id    VARCHAR(8)      NOT NULL,
    sequence_no     VARCHAR(6)      NOT NULL,
    investment_id   VARCHAR(10),
    type            VARCHAR(2)      CHECK (type IN ('BU', 'SL', 'TR', 'FE')),
    quantity        DECIMAL(15, 4),
    price           DECIMAL(15, 4),
    amount          DECIMAL(15, 2),
    currency        VARCHAR(3),
    status          VARCHAR(1)      CHECK (status IN ('P', 'D', 'F', 'R')),
    process_date    TIMESTAMP,
    process_user    VARCHAR(8),
    PRIMARY KEY (date, time, portfolio_id, sequence_no)
);

CREATE INDEX idx_transaction_portfolio_id ON transactions (portfolio_id);
CREATE INDEX idx_transaction_date ON transactions (date);
CREATE INDEX idx_transaction_investment_id ON transactions (investment_id);
CREATE INDEX idx_transaction_type ON transactions (type);
CREATE INDEX idx_transaction_status ON transactions (status);

-- History table (mirrors Python History model / COBOL TRANHIST)
CREATE TABLE history (
    portfolio_id    VARCHAR(8)      NOT NULL,
    date            VARCHAR(8)      NOT NULL,
    time            VARCHAR(8)      NOT NULL,
    seq_no          VARCHAR(4)      NOT NULL,
    record_type     VARCHAR(2)      CHECK (record_type IN ('PT', 'PS', 'TR')),
    action_code     VARCHAR(1)      CHECK (action_code IN ('A', 'C', 'D')),
    before_image    CLOB,
    after_image     CLOB,
    reason_code     VARCHAR(4),
    process_date    TIMESTAMP,
    process_user    VARCHAR(8),
    PRIMARY KEY (portfolio_id, date, time, seq_no)
);

CREATE INDEX idx_history_portfolio_id ON history (portfolio_id);
CREATE INDEX idx_history_date ON history (date);
CREATE INDEX idx_history_record_type ON history (record_type);
CREATE INDEX idx_history_action_code ON history (action_code);
