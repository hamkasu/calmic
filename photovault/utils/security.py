"""
Security Utilities for PhotoVault/StoryKeep
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Includes password validation, rate limiting, MFA, and security logging
"""
import re
import secrets
import json
from datetime import datetime, timedelta
from flask import request, current_app
from photovault.extensions import db
from photovault.models import LoginAttempt, AccountLockout, SecurityLog, RefreshToken
import logging

logger = logging.getLogger(__name__)

# Password Policy Constants (Simplified for better UX)
MIN_PASSWORD_LENGTH = 8
PASSWORD_MUST_HAVE = {
    'uppercase': True,
    'lowercase': True,
    'digit': True,
    'special': False
}
SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

# Rate Limiting Constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
ATTEMPT_WINDOW_MINUTES = 15

def validate_password_strength(password):
    """
    Validate password against security policy
    Returns: (is_valid, message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if PASSWORD_MUST_HAVE['uppercase'] and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if PASSWORD_MUST_HAVE['lowercase'] and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if PASSWORD_MUST_HAVE['digit'] and not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if PASSWORD_MUST_HAVE['special'] and not re.search(f'[{re.escape(SPECIAL_CHARACTERS)}]', password):
        return False, f"Password must contain at least one special character ({SPECIAL_CHARACTERS})"
    
    # Check for common patterns
    if password.lower() in ['password123!', 'qwerty123!', 'admin123!', 'welcome123!']:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, "Password is strong"


def log_login_attempt(username_or_email, success=False, failure_reason=None):
    """
    Log a login attempt to the database
    Returns: LoginAttempt object
    """
    try:
        attempt = LoginAttempt(
            username_or_email=username_or_email,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
            success=success,
            failure_reason=failure_reason,
            attempted_at=datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt
    except Exception as e:
        logger.error(f"Failed to log login attempt: {str(e)}")
        db.session.rollback()
        return None


def check_account_lockout(user_id):
    """
    Check if account is currently locked out
    Returns: (is_locked, unlock_time, active_lockout)
    """
    try:
        active_lockout = AccountLockout.query.filter_by(
            user_id=user_id,
            is_active=True
        ).filter(
            AccountLockout.unlock_at > datetime.utcnow()
        ).first()
        
        if active_lockout:
            return True, active_lockout.unlock_at, active_lockout
        
        return False, None, None
    except Exception as e:
        logger.error(f"Failed to check account lockout: {str(e)}")
        return False, None, None


def check_and_lockout_account(username_or_email, user_id=None):
    """
    Check recent failed login attempts and lock account if threshold exceeded
    Returns: (should_lockout, unlock_time, attempts_count)
    """
    try:
        # Check if already locked
        if user_id:
            is_locked, unlock_time, _ = check_account_lockout(user_id)
            if is_locked:
                return True, unlock_time, MAX_LOGIN_ATTEMPTS
        
        # Count failed attempts in the window
        window_start = datetime.utcnow() - timedelta(minutes=ATTEMPT_WINDOW_MINUTES)
        failed_attempts = LoginAttempt.query.filter(
            LoginAttempt.username_or_email == username_or_email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= window_start
        ).count()
        
        # If threshold exceeded, create lockout
        if failed_attempts >= MAX_LOGIN_ATTEMPTS and user_id:
            unlock_time = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            lockout = AccountLockout(
                user_id=user_id,
                locked_at=datetime.utcnow(),
                unlock_at=unlock_time,
                reason=f"Too many failed login attempts ({failed_attempts} attempts)",
                is_active=True
            )
            db.session.add(lockout)
            db.session.commit()
            
            # Log security event
            log_security_event(
                user_id=user_id,
                event_type='account_locked',
                severity='warning',
                description=f'Account locked due to {failed_attempts} failed login attempts'
            )
            
            return True, unlock_time, failed_attempts
        
        return False, None, failed_attempts
    except Exception as e:
        logger.error(f"Failed to check/lockout account: {str(e)}")
        db.session.rollback()
        return False, None, 0


def log_security_event(user_id, event_type, severity='info', description=None, metadata=None):
    """
    Log a security event
    
    Args:
        user_id: User ID (can be None for pre-auth events)
        event_type: Type of event (e.g., 'login_success', 'mfa_enabled', 'password_changed')
        severity: 'info', 'warning', or 'critical'
        description: Human-readable description
        metadata: Dict of additional data
    
    Returns: SecurityLog object
    """
    try:
        log_entry = SecurityLog(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:500] if request else None,
            event_metadata=event_metadata,
            created_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Also log to application logger for critical events
        if severity == 'critical':
            logger.warning(f"SECURITY: {event_type} - {description} - User: {user_id}")
        
        return log_entry
    except Exception as e:
        logger.error(f"Failed to log security event: {str(e)}")
        db.session.rollback()
        return None


def get_client_ip():
    """
    Get client IP address, handling proxies
    """
    if request:
        # Check for proxy headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    return None


def generate_backup_codes(count=10):
    """
    Generate backup codes for MFA recovery
    
    Args:
        count: Number of backup codes to generate (default: 10)
    
    Returns: List of backup codes
    """
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = secrets.token_hex(4).upper()  # 8 hex characters
        formatted_code = f"{code[:4]}-{code[4:]}"  # Format as XXXX-XXXX
        codes.append(formatted_code)
    return codes


# ============================================================================
# Refresh Token Management (Secure)
# ============================================================================

def create_refresh_token(user_id, device_info=None, expires_days=30):
    """
    Create a new refresh token for a user (token is hashed before storage)
    
    Args:
        user_id: User ID
        device_info: Optional device information
        expires_days: Token expiration in days (default: 30)
    
    Returns: (token_string, RefreshToken object) or (None, None) on failure
    """
    try:
        from werkzeug.security import generate_password_hash
        
        # Generate random token
        token_string = secrets.token_urlsafe(64)
        
        # Hash the token for storage
        token_hash = generate_password_hash(token_string, method='scrypt')
        
        # Create database record
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_hash,  # Store hashed version
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            created_at=datetime.utcnow(),
            device_info=device_info[:500] if device_info else None,
            ip_address=get_client_ip()
        )
        
        db.session.add(refresh_token)
        db.session.commit()
        
        logger.info(f"Created refresh token for user {user_id}")
        
        # Return the plaintext token (user needs this) and the DB object
        return token_string, refresh_token
    except Exception as e:
        logger.error(f"Failed to create refresh token: {str(e)}")
        db.session.rollback()
        return None, None


def verify_refresh_token(token_string):
    """
    Verify a refresh token and return the user_id if valid
    Uses constant-time comparison to prevent timing attacks
    
    Args:
        token_string: The plaintext token to verify
    
    Returns: (user_id, RefreshToken object) or (None, None) if invalid
    """
    try:
        from werkzeug.security import check_password_hash
        
        # Get all non-revoked, non-expired tokens
        # We need to check each one since we can't query by hashed value
        now = datetime.utcnow()
        active_tokens = RefreshToken.query.filter(
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now
        ).all()
        
        # Check each token using constant-time comparison
        for token_obj in active_tokens:
            if check_password_hash(token_obj.token, token_string):
                # Token is valid
                return token_obj.user_id, token_obj
        
        # No matching token found
        return None, None
    except Exception as e:
        logger.error(f"Failed to verify refresh token: {str(e)}")
        return None, None


def revoke_refresh_token(token_id=None, token_string=None):
    """
    Revoke a refresh token (by ID or by token string)
    
    Args:
        token_id: RefreshToken ID (faster)
        token_string: Plaintext token (slower, requires verification)
    
    Returns: bool (success)
    """
    try:
        if token_id:
            token_obj = RefreshToken.query.get(token_id)
        elif token_string:
            _, token_obj = verify_refresh_token(token_string)
        else:
            return False
        
        if not token_obj:
            return False
        
        token_obj.revoked_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Revoked refresh token {token_obj.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to revoke refresh token: {str(e)}")
        db.session.rollback()
        return False


def revoke_all_user_tokens(user_id):
    """
    Revoke all refresh tokens for a user (useful for logout all devices)
    
    Args:
        user_id: User ID
    
    Returns: int (number of tokens revoked)
    """
    try:
        count = RefreshToken.query.filter_by(
            user_id=user_id,
            revoked_at=None
        ).update({'revoked_at': datetime.utcnow()})
        
        db.session.commit()
        logger.info(f"Revoked {count} refresh tokens for user {user_id}")
        return count
    except Exception as e:
        logger.error(f"Failed to revoke all user tokens: {str(e)}")
        db.session.rollback()
        return 0


def cleanup_expired_tokens():
    """
    Clean up expired and revoked refresh tokens (should be run periodically)
    
    Returns: int (number of tokens deleted)
    """
    try:
        # Delete tokens that expired more than 7 days ago or were revoked more than 30 days ago
        cutoff_expired = datetime.utcnow() - timedelta(days=7)
        cutoff_revoked = datetime.utcnow() - timedelta(days=30)
        
        count = RefreshToken.query.filter(
            db.or_(
                RefreshToken.expires_at < cutoff_expired,
                db.and_(
                    RefreshToken.revoked_at.isnot(None),
                    RefreshToken.revoked_at < cutoff_revoked
                )
            )
        ).delete()
        
        db.session.commit()
        logger.info(f"Cleaned up {count} expired/revoked refresh tokens")
        return count
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {str(e)}")
        db.session.rollback()
        return 0
