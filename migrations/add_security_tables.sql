-- Security Enhancement Migration
-- Adds tables for MFA, OAuth, rate limiting, and security logging
-- Run this on both development and production databases

-- Login Attempts Table (for rate limiting and audit)
CREATE TABLE IF NOT EXISTS login_attempt (
    id SERIAL PRIMARY KEY,
    username_or_email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    success BOOLEAN NOT NULL DEFAULT FALSE,
    failure_reason VARCHAR(255),
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_login_attempt_username ON login_attempt(username_or_email);
CREATE INDEX IF NOT EXISTS idx_login_attempt_time ON login_attempt(attempted_at);

-- Account Lockout Table
CREATE TABLE IF NOT EXISTS account_lockout (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    locked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    unlock_at TIMESTAMP NOT NULL,
    reason VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    unlocked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_account_lockout_user ON account_lockout(user_id);
CREATE INDEX IF NOT EXISTS idx_account_lockout_unlock ON account_lockout(unlock_at);

-- Refresh Token Table
CREATE TABLE IF NOT EXISTS refresh_token (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    device_info VARCHAR(500),
    ip_address VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_refresh_token_user ON refresh_token(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_token_token ON refresh_token(token);
CREATE INDEX IF NOT EXISTS idx_refresh_token_expires ON refresh_token(expires_at);

-- MFA Secret Table
CREATE TABLE IF NOT EXISTS mfa_secret (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    secret VARCHAR(32) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    backup_codes TEXT,
    enabled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mfa_secret_user ON mfa_secret(user_id);

-- OAuth Provider Table
CREATE TABLE IF NOT EXISTS oauth_provider (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    profile_picture_url VARCHAR(500),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    CONSTRAINT _user_oauth_provider_uc UNIQUE (user_id, provider),
    CONSTRAINT _provider_user_id_uc UNIQUE (provider, provider_user_id)
);

CREATE INDEX IF NOT EXISTS idx_provider_user_id ON oauth_provider(provider, provider_user_id);

-- Security Log Table
CREATE TABLE IF NOT EXISTS security_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_log_user ON security_log(user_id);
CREATE INDEX IF NOT EXISTS idx_security_log_event_type ON security_log(event_type);
CREATE INDEX IF NOT EXISTS idx_security_log_severity ON security_log(severity);
CREATE INDEX IF NOT EXISTS idx_security_log_created ON security_log(created_at);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_database_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_database_user;
