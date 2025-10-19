"""
Security Utilities for PhotoVault/StoryKeep
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

# Password Policy Constants
MIN_PASSWORD_LENGTH = 12
PASSWORD_MUST_HAVE = {
    'uppercase': True,
    'lowercase': True,
    'digit': True,
    'special': True
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
            metadata=metadata,
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


def generate_refresh_token(user_id, device_info=None, expiry_days=90):
    """
    Generate a secure refresh token for token refresh mechanism
    
    Args:
        user_id: User ID
        device_info: Device fingerprint/info
        expiry_days: Days until token expires (default: 90)
    
    Returns: (token_string, RefreshToken object)
    """
    try:
        # Generate secure random token
        token_string = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_string,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=request.remote_addr if request else None,
            created_at=datetime.utcnow()
        )
        db.session.add(refresh_token)
        db.session.commit()
        
        logger.info(f"Generated refresh token for user {user_id}")
        return token_string, refresh_token
    except Exception as e:
        logger.error(f"Failed to generate refresh token: {str(e)}")
        db.session.rollback()
        return None, None


def validate_refresh_token(token_string):
    """
    Validate a refresh token
    
    Args:
        token_string: The refresh token to validate
    
    Returns: (is_valid, user_id, refresh_token_object, error_message)
    """
    try:
        refresh_token = RefreshToken.query.filter_by(token=token_string).first()
        
        if not refresh_token:
            return False, None, None, "Invalid refresh token"
        
        if refresh_token.revoked_at:
            return False, None, refresh_token, "Refresh token has been revoked"
        
        if datetime.utcnow() >= refresh_token.expires_at:
            return False, None, refresh_token, "Refresh token has expired"
        
        return True, refresh_token.user_id, refresh_token, None
    except Exception as e:
        logger.error(f"Failed to validate refresh token: {str(e)}")
        return False, None, None, f"Token validation error: {str(e)}"


def revoke_all_refresh_tokens(user_id):
    """
    Revoke all refresh tokens for a user (useful for logout all devices, password change, etc.)
    
    Args:
        user_id: User ID
    
    Returns: Number of tokens revoked
    """
    try:
        tokens = RefreshToken.query.filter_by(
            user_id=user_id
        ).filter(
            RefreshToken.revoked_at.is_(None)
        ).all()
        
        count = 0
        for token in tokens:
            token.revoke()
            count += 1
        
        db.session.commit()
        logger.info(f"Revoked {count} refresh tokens for user {user_id}")
        return count
    except Exception as e:
        logger.error(f"Failed to revoke refresh tokens: {str(e)}")
        db.session.rollback()
        return 0


def cleanup_expired_tokens():
    """
    Cleanup expired refresh tokens and old login attempts
    Should be run periodically (e.g., daily cron job)
    
    Returns: (tokens_deleted, attempts_deleted, lockouts_deleted)
    """
    try:
        # Delete expired refresh tokens (older than 30 days after expiration)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        expired_tokens = RefreshToken.query.filter(
            RefreshToken.expires_at < cutoff_date
        ).delete()
        
        # Delete old login attempts (older than 90 days)
        old_attempts_cutoff = datetime.utcnow() - timedelta(days=90)
        old_attempts = LoginAttempt.query.filter(
            LoginAttempt.attempted_at < old_attempts_cutoff
        ).delete()
        
        # Deactivate old lockouts (older than 30 days)
        old_lockouts_cutoff = datetime.utcnow() - timedelta(days=30)
        old_lockouts = AccountLockout.query.filter(
            AccountLockout.unlock_at < old_lockouts_cutoff,
            AccountLockout.is_active == True
        ).update({'is_active': False})
        
        db.session.commit()
        logger.info(f"Cleanup: {expired_tokens} tokens, {old_attempts} attempts, {old_lockouts} lockouts")
        return expired_tokens, old_attempts, old_lockouts
    except Exception as e:
        logger.error(f"Failed to cleanup expired data: {str(e)}")
        db.session.rollback()
        return 0, 0, 0


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
