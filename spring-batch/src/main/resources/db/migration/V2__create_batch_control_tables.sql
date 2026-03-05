-- Batch Control Schema (migrated from COBOL BCHCTL00/PRCSEQ00)

CREATE TABLE IF NOT EXISTS batch_job_control (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(64) NOT NULL,
    process_date DATE NOT NULL,
    sequence_no INT NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'READY',
    return_code INT DEFAULT 0,
    records_read BIGINT DEFAULT 0,
    records_written BIGINT DEFAULT 0,
    error_count BIGINT DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    restart_count INT DEFAULT 0,
    max_restarts INT DEFAULT 3,
    error_desc VARCHAR(255),
    checkpoint_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bjc_job_name ON batch_job_control(job_name);
CREATE INDEX IF NOT EXISTS idx_bjc_process_date ON batch_job_control(process_date);
CREATE INDEX IF NOT EXISTS idx_bjc_status ON batch_job_control(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bjc_job_date_seq ON batch_job_control(job_name, process_date, sequence_no);

CREATE TABLE IF NOT EXISTS batch_process_sequence (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    process_date DATE NOT NULL,
    sequence_type VARCHAR(8) NOT NULL DEFAULT 'DAILY',
    process_id VARCHAR(64) NOT NULL,
    sequence_order INT NOT NULL,
    dependency_ids VARCHAR(512),
    max_return_code INT DEFAULT 4,
    restartable BOOLEAN DEFAULT TRUE,
    status VARCHAR(16) NOT NULL DEFAULT 'READY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bps_process_date ON batch_process_sequence(process_date);
CREATE INDEX IF NOT EXISTS idx_bps_sequence_type ON batch_process_sequence(sequence_type);
