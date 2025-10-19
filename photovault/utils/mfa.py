"""
Multi-Factor Authentication (MFA/2FA) Utilities using TOTP
"""
import pyotp
import qrcode
import io
import base64
import json
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from photovault.extensions import db
from photovault.models import MFASecret
import logging

logger = logging.getLogger(__name__)


def generate_mfa_secret(user_id, username, app_name="StoryKeep"):
    """
    Generate a new MFA secret for a user
    
    Args:
        user_id: User ID
        username: Username for QR code label
        app_name: Application name for QR code issuer
    
    Returns: (secret, qr_code_data_uri, backup_codes)
    """
    try:
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name=app_name
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert QR code to image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to data URI
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_data = base64.b64encode(buffer.getvalue()).decode()
        qr_data_uri = f"data:image/png;base64,{img_data}"
        
        # Generate backup codes (plaintext for user display)
        backup_codes_plaintext = generate_backup_codes()
        
        # Hash backup codes for secure storage
        backup_codes_hashed = [generate_password_hash(code, method='scrypt') for code in backup_codes_plaintext]
        
        # Save to database (but don't enable yet)
        existing_secret = MFASecret.query.filter_by(user_id=user_id).first()
        if existing_secret:
            # Update existing
            existing_secret.secret = secret
            existing_secret.backup_codes = json.dumps(backup_codes_hashed)  # Store hashes
            existing_secret.created_at = datetime.utcnow()
            existing_secret.is_enabled = False  # Require verification before enabling
        else:
            # Create new
            mfa_secret = MFASecret(
                user_id=user_id,
                secret=secret,
                backup_codes=json.dumps(backup_codes_hashed),  # Store hashes
                is_enabled=False,
                created_at=datetime.utcnow()
            )
            db.session.add(mfa_secret)
        
        db.session.commit()
        logger.info(f"Generated MFA secret for user {user_id}")
        
        # Return plaintext codes to user (they need to save them), hashed versions are in DB
        return secret, qr_data_uri, backup_codes_plaintext
    except Exception as e:
        logger.error(f"Failed to generate MFA secret: {str(e)}")
        db.session.rollback()
        return None, None, None


def verify_mfa_code(user_id, code):
    """
    Verify a TOTP code for a user
    
    Args:
        user_id: User ID
        code: 6-digit TOTP code
    
    Returns: (is_valid, error_message)
    """
    try:
        mfa_secret = MFASecret.query.filter_by(user_id=user_id).first()
        
        if not mfa_secret:
            return False, "MFA not set up for this user"
        
        # Clean the code (remove spaces, dashes)
        code = code.replace(' ', '').replace('-', '')
        
        # Check if it's a backup code
        if len(code) == 9 and '-' in code:  # Format: XXXX-XXXX
            is_valid, msg = verify_backup_code(user_id, code)
            if is_valid:
                return True, "Backup code accepted"
            return False, msg
        
        # Verify TOTP code
        totp = pyotp.TOTP(mfa_secret.secret)
        is_valid = totp.verify(code, valid_window=1)  # Allow 1 step (30s) time drift
        
        if is_valid:
            # Update last used timestamp
            mfa_secret.last_used_at = datetime.utcnow()
            db.session.commit()
            return True, "Code verified"
        
        return False, "Invalid code"
    except Exception as e:
        logger.error(f"Failed to verify MFA code: {str(e)}")
        return False, f"Verification error: {str(e)}"


def enable_mfa(user_id, verification_code):
    """
    Enable MFA for a user after verifying a code
    
    Args:
        user_id: User ID
        verification_code: TOTP code to verify before enabling
    
    Returns: (success, message)
    """
    try:
        is_valid, msg = verify_mfa_code(user_id, verification_code)
        
        if not is_valid:
            return False, f"Cannot enable MFA: {msg}"
        
        mfa_secret = MFASecret.query.filter_by(user_id=user_id).first()
        if not mfa_secret:
            return False, "MFA secret not found"
        
        mfa_secret.is_enabled = True
        mfa_secret.enabled_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"MFA enabled for user {user_id}")
        return True, "MFA enabled successfully"
    except Exception as e:
        logger.error(f"Failed to enable MFA: {str(e)}")
        db.session.rollback()
        return False, f"Failed to enable MFA: {str(e)}"


def disable_mfa(user_id):
    """
    Disable MFA for a user
    
    Args:
        user_id: User ID
    
    Returns: (success, message)
    """
    try:
        mfa_secret = MFASecret.query.filter_by(user_id=user_id).first()
        
        if not mfa_secret:
            return True, "MFA was not enabled"
        
        # Don't delete, just disable for audit trail
        mfa_secret.is_enabled = False
        db.session.commit()
        
        logger.info(f"MFA disabled for user {user_id}")
        return True, "MFA disabled successfully"
    except Exception as e:
        logger.error(f"Failed to disable MFA: {str(e)}")
        db.session.rollback()
        return False, f"Failed to disable MFA: {str(e)}"


def is_mfa_enabled(user_id):
    """
    Check if MFA is enabled for a user
    
    Args:
        user_id: User ID
    
    Returns: bool
    """
    try:
        mfa_secret = MFASecret.query.filter_by(user_id=user_id, is_enabled=True).first()
        return mfa_secret is not None
    except Exception as e:
        logger.error(f"Failed to check MFA status: {str(e)}")
        return False


def generate_backup_codes(count=10):
    """
    Generate backup codes for MFA recovery
    
    Args:
        count: Number of codes to generate
    
    Returns: List of backup codes
    """
    codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    return codes


def verify_backup_code(user_id, code):
    """
    Verify and consume a backup code (uses constant-time comparison)
    
    Args:
        user_id: User ID
        code: Backup code to verify (plaintext)
    
    Returns: (is_valid, message)
    """
    try:
        mfa_secret = MFASecret.query.filter_by(user_id=user_id).first()
        
        if not mfa_secret or not mfa_secret.backup_codes:
            return False, "No backup codes found"
        
        backup_code_hashes = json.loads(mfa_secret.backup_codes)
        
        # Check each hashed code using constant-time comparison
        matched_index = None
        for idx, code_hash in enumerate(backup_code_hashes):
            if check_password_hash(code_hash, code):
                matched_index = idx
                break
        
        if matched_index is not None:
            # Remove used code hash
            backup_code_hashes.pop(matched_index)
            mfa_secret.backup_codes = json.dumps(backup_code_hashes)
            mfa_secret.last_used_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Backup code used for user {user_id}. {len(backup_code_hashes)} codes remaining")
            return True, "Backup code accepted"
        
        return False, "Invalid backup code"
    except Exception as e:
        logger.error(f"Failed to verify backup code: {str(e)}")
        db.session.rollback()
        return False, f"Verification error: {str(e)}"


def regenerate_backup_codes(user_id):
    """
    Generate new backup codes (replacing old ones)
    
    Args:
        user_id: User ID
    
    Returns: (success, backup_codes_plaintext_list)
    """
    try:
        mfa_secret = MFASecret.query.filter_by(user_id=user_id).first()
        
        if not mfa_secret:
            return False, []
        
        # Generate new codes (plaintext for user)
        new_codes_plaintext = generate_backup_codes()
        
        # Hash for storage
        new_codes_hashed = [generate_password_hash(code, method='scrypt') for code in new_codes_plaintext]
        
        mfa_secret.backup_codes = json.dumps(new_codes_hashed)
        db.session.commit()
        
        logger.info(f"Regenerated backup codes for user {user_id}")
        # Return plaintext codes (user needs to save them)
        return True, new_codes_plaintext
    except Exception as e:
        logger.error(f"Failed to regenerate backup codes: {str(e)}")
        db.session.rollback()
        return False, []
