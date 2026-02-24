-- Flyway Migration V1: Create security tables
-- Replaces COBOL SECMGR AUTHFILE table and user management from RACF
-- These tables support JWT-based authentication and role-based access control

-- Roles table - replaces RACF resource control levels
-- Maps to SECMGR access types: READ (inquiry), UPDATE, ADMIN (maintenance)
CREATE TABLE roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200)
);

-- Users table - replaces CICS user credential storage
-- Stores user credentials for JWT authentication replacing SECMGR P100-VALIDATE-USER
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    account_non_locked BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Role join table - replaces AUTHFILE from SECMGR P200-CHECK-AUTH
-- Maps users to roles for authorization checks
CREATE TABLE user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Seed default roles matching COBOL security levels
-- READ -> USER role (inquiry access like INQONLN)
-- UPDATE -> USER role (position updates)
-- ADMIN -> ADMIN role (maintenance like UTLMNT00)
INSERT INTO roles (name, description) VALUES ('USER', 'Standard user with read access to portfolio data');
INSERT INTO roles (name, description) VALUES ('ADMIN', 'Administrator with full system access including audit logs');
