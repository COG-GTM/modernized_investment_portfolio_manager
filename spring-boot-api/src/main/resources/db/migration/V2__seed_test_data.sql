-- Seed portfolios
INSERT INTO portfolios (port_id, account_no, client_name, client_type, create_date, last_maint, status, total_value, cash_balance, last_user, last_trans)
VALUES ('PORT0001', '1000000001', 'GROWTH PORTFOLIO', 'I', DATE '2024-03-20', DATE '2024-03-20', 'A', 12345678.99, 50000.00, 'SYSTEM', 'INIT');

INSERT INTO portfolios (port_id, account_no, client_name, client_type, create_date, last_maint, status, total_value, cash_balance, last_user, last_trans)
VALUES ('PORT0002', '1000000002', 'INCOME PORTFOLIO', 'C', DATE '2024-03-20', DATE '2024-03-20', 'A', 98765432.10, 100000.00, 'SYSTEM', 'INIT');

INSERT INTO portfolios (port_id, account_no, client_name, client_type, create_date, last_maint, status, total_value, cash_balance, last_user, last_trans)
VALUES ('PORT0003', '1000000003', 'BALANCED PORTFOLIO', 'T', DATE '2024-03-20', DATE '2024-03-20', 'S', 5555555.55, 25000.00, 'SYSTEM', 'INIT');

-- Seed positions for PORT0001
INSERT INTO positions (portfolio_id, date, investment_id, quantity, cost_basis, market_value, currency, status, last_maint_date, last_maint_user)
VALUES ('PORT0001', DATE '2024-03-20', 'IBM0000001', 500.0000, 62500.00, 68750.00, 'USD', 'A', TIMESTAMP '2024-03-20 15:30:45', 'SYSTEM');

INSERT INTO positions (portfolio_id, date, investment_id, quantity, cost_basis, market_value, currency, status, last_maint_date, last_maint_user)
VALUES ('PORT0001', DATE '2024-03-20', 'AAPL000001', 200.0000, 30000.00, 34400.00, 'USD', 'A', TIMESTAMP '2024-03-20 15:31:00', 'SYSTEM');

INSERT INTO positions (portfolio_id, date, investment_id, quantity, cost_basis, market_value, currency, status, last_maint_date, last_maint_user)
VALUES ('PORT0001', DATE '2024-03-20', 'MSFT000001', 300.0000, 90000.00, 117000.00, 'USD', 'A', TIMESTAMP '2024-03-20 15:32:00', 'SYSTEM');

-- Seed positions for PORT0002
INSERT INTO positions (portfolio_id, date, investment_id, quantity, cost_basis, market_value, currency, status, last_maint_date, last_maint_user)
VALUES ('PORT0002', DATE '2024-03-20', 'MSFT000001', 1000.0000, 300000.00, 390000.00, 'USD', 'A', TIMESTAMP '2024-03-20 15:31:12', 'SYSTEM');

-- Seed transactions
INSERT INTO transactions (date, time, portfolio_id, sequence_no, investment_id, type, quantity, price, amount, currency, status, process_date, process_user)
VALUES (DATE '2024-03-20', TIME '15:30:45', 'PORT0001', '000001', 'IBM0000001', 'BU', 500.0000, 125.0000, 62500.00, 'USD', 'D', TIMESTAMP '2024-03-20 15:30:45', 'SYSTEM');

INSERT INTO transactions (date, time, portfolio_id, sequence_no, investment_id, type, quantity, price, amount, currency, status, process_date, process_user)
VALUES (DATE '2024-03-20', TIME '15:31:12', 'PORT0002', '000001', 'MSFT000001', 'SL', 50.0000, 390.0000, 19500.00, 'USD', 'D', TIMESTAMP '2024-03-20 15:31:12', 'SYSTEM');

INSERT INTO transactions (date, time, portfolio_id, sequence_no, investment_id, type, quantity, price, amount, currency, status, process_date, process_user)
VALUES (DATE '2024-03-20', TIME '15:32:01', 'PORT0001', '000002', 'AAPL000001', 'BU', 200.0000, 150.0000, 30000.00, 'USD', 'D', TIMESTAMP '2024-03-20 15:32:01', 'SYSTEM');

INSERT INTO transactions (date, time, portfolio_id, sequence_no, investment_id, type, quantity, price, amount, currency, status, process_date, process_user)
VALUES (DATE '2024-03-21', TIME '10:00:00', 'PORT0001', '000001', 'MSFT000001', 'BU', 300.0000, 300.0000, 90000.00, 'USD', 'D', TIMESTAMP '2024-03-21 10:00:00', 'SYSTEM');

INSERT INTO transactions (date, time, portfolio_id, sequence_no, investment_id, type, quantity, price, amount, currency, status, process_date, process_user)
VALUES (DATE '2024-03-22', TIME '09:15:00', 'PORT0001', '000001', 'IBM0000001', 'SL', 100.0000, 130.0000, 13000.00, 'USD', 'P', TIMESTAMP '2024-03-22 09:15:00', 'SYSTEM');

-- Seed history records
INSERT INTO history (portfolio_id, date, time, seq_no, record_type, action_code, before_image, after_image, reason_code, process_date, process_user)
VALUES ('PORT0001', '20240320', '15304500', '0001', 'TR', 'A', NULL, '{"type":"BU","investment_id":"IBM0000001","quantity":500,"amount":62500.00}', 'AUTO', TIMESTAMP '2024-03-20 15:30:45', 'SYSTEM');

INSERT INTO history (portfolio_id, date, time, seq_no, record_type, action_code, before_image, after_image, reason_code, process_date, process_user)
VALUES ('PORT0001', '20240320', '15310000', '0001', 'PS', 'A', NULL, '{"investment_id":"IBM0000001","quantity":500,"cost_basis":62500.00}', 'AUTO', TIMESTAMP '2024-03-20 15:31:00', 'SYSTEM');

INSERT INTO history (portfolio_id, date, time, seq_no, record_type, action_code, before_image, after_image, reason_code, process_date, process_user)
VALUES ('PORT0001', '20240320', '15320100', '0001', 'TR', 'A', NULL, '{"type":"BU","investment_id":"AAPL000001","quantity":200,"amount":30000.00}', 'AUTO', TIMESTAMP '2024-03-20 15:32:01', 'SYSTEM');

INSERT INTO history (portfolio_id, date, time, seq_no, record_type, action_code, before_image, after_image, reason_code, process_date, process_user)
VALUES ('PORT0002', '20240320', '15311200', '0001', 'TR', 'A', NULL, '{"type":"SL","investment_id":"MSFT000001","quantity":50,"amount":19500.00}', 'AUTO', TIMESTAMP '2024-03-20 15:31:12', 'SYSTEM');

INSERT INTO history (portfolio_id, date, time, seq_no, record_type, action_code, before_image, after_image, reason_code, process_date, process_user)
VALUES ('PORT0001', '20240322', '09150000', '0001', 'TR', 'A', NULL, '{"type":"SL","investment_id":"IBM0000001","quantity":100,"amount":13000.00}', 'AUTO', TIMESTAMP '2024-03-22 09:15:00', 'SYSTEM');
