"""
PhotoVault - Subscription Enforcement Utilities
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Decorators and utilities to enforce subscription plan limits across the application
"""

from functools import wraps
from flask import jsonify, request, flash, redirect, url_for
from flask_login import current_user
from photovault.models import UserSubscription, Photo, FamilyVault, db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


def get_user_subscription(user_id):
    """Get active subscription for a user"""
    return UserSubscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()


def get_storage_usage(user_id):
    """Calculate total storage used by user in bytes"""
    result = db.session.query(func.sum(Photo.file_size)).filter_by(user_id=user_id).scalar()
    return result or 0


def get_ai_enhancement_usage(user_id):
    """Get current month's AI enhancement usage"""
    from datetime import datetime
    from photovault.models import AIEnhancementLog
    
    # Get first day of current month
    today = datetime.utcnow()
    month_start = datetime(today.year, today.month, 1)
    
    # Count AI enhancements this month
    count = AIEnhancementLog.query.filter(
        AIEnhancementLog.user_id == user_id,
        AIEnhancementLog.created_at >= month_start
    ).count()
    
    return count


def get_family_vault_count(user_id):
    """Get number of family vaults owned by user"""
    return FamilyVault.query.filter_by(owner_id=user_id).count()


def check_storage_limit(user_id, additional_size=0):
    """
    Check if user has enough storage available
    Returns: (success: bool, message: str, current_gb: float, limit_gb: float)
    """
    subscription = get_user_subscription(user_id)
    
    if not subscription or not subscription.plan:
        return False, "No active subscription plan found", 0, 0
    
    current_usage = get_storage_usage(user_id)
    new_usage = current_usage + additional_size
    
    # Storage limits in bytes (from plan)
    storage_limit_gb = subscription.plan.storage_limit_gb
    storage_limit_bytes = storage_limit_gb * 1024 * 1024 * 1024
    
    # Convert to GB for display
    current_gb = current_usage / (1024 * 1024 * 1024)
    new_gb = new_usage / (1024 * 1024 * 1024)
    
    if new_usage > storage_limit_bytes:
        return False, f"Storage limit exceeded. You are using {new_gb:.2f}GB of your {storage_limit_gb}GB limit.", current_gb, storage_limit_gb
    
    return True, "Storage available", current_gb, storage_limit_gb


def check_ai_quota(user_id):
    """
    Check if user has AI enhancements remaining this month
    Returns: (success: bool, message: str, used: int, limit: int)
    """
    subscription = get_user_subscription(user_id)
    
    if not subscription or not subscription.plan:
        return False, "No active subscription plan found", 0, 0
    
    monthly_limit = subscription.plan.ai_enhancements_per_month
    current_usage = get_ai_enhancement_usage(user_id)
    
    if current_usage >= monthly_limit:
        return False, f"Monthly AI enhancement limit reached. You have used {current_usage} of {monthly_limit} enhancements this month.", current_usage, monthly_limit
    
    return True, "AI enhancements available", current_usage, monthly_limit


def check_vault_limit(user_id):
    """
    Check if user can create more family vaults
    Returns: (success: bool, message: str, current: int, limit: int)
    """
    subscription = get_user_subscription(user_id)
    
    if not subscription or not subscription.plan:
        return False, "No active subscription plan found", 0, 0
    
    vault_limit = subscription.plan.family_vaults_limit
    current_vaults = get_family_vault_count(user_id)
    
    if current_vaults >= vault_limit:
        return False, f"Family vault limit reached. You have {current_vaults} of {vault_limit} vaults.", current_vaults, vault_limit
    
    return True, "Can create more vaults", current_vaults, vault_limit


def require_storage(additional_size=0):
    """
    Decorator to check storage limits before executing a route
    Usage: @require_storage(additional_size=file_size)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Skip check for admin/superuser
            if current_user.is_admin or current_user.is_superuser:
                return f(*args, **kwargs)
            
            success, message, current_gb, limit_gb = check_storage_limit(current_user.id, additional_size)
            
            if not success:
                # Check if request is JSON (API) or web
                if request.is_json or request.endpoint and request.endpoint.startswith('mobile_api'):
                    return jsonify({
                        'error': message,
                        'error_type': 'storage_limit_exceeded',
                        'current_storage_gb': round(current_gb, 2),
                        'storage_limit_gb': limit_gb,
                        'upgrade_required': True
                    }), 403
                else:
                    flash(f'{message} Please upgrade your plan for more storage.', 'warning')
                    return redirect(url_for('billing.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_ai_quota():
    """
    Decorator to check AI enhancement quota before executing a route
    Usage: @require_ai_quota()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Skip check for admin/superuser
            if current_user.is_admin or current_user.is_superuser:
                return f(*args, **kwargs)
            
            success, message, used, limit = check_ai_quota(current_user.id)
            
            if not success:
                # Check if request is JSON (API) or web
                if request.is_json or request.endpoint and request.endpoint.startswith('mobile_api'):
                    return jsonify({
                        'error': message,
                        'error_type': 'ai_quota_exceeded',
                        'ai_used': used,
                        'ai_limit': limit,
                        'upgrade_required': True
                    }), 403
                else:
                    flash(f'{message} Please upgrade your plan for more AI enhancements.', 'warning')
                    return redirect(url_for('billing.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_vault_capacity():
    """
    Decorator to check family vault limit before creating new vaults
    Usage: @require_vault_capacity()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Skip check for admin/superuser
            if current_user.is_admin or current_user.is_superuser:
                return f(*args, **kwargs)
            
            success, message, current, limit = check_vault_limit(current_user.id)
            
            if not success:
                # Check if request is JSON (API) or web
                if request.is_json or request.endpoint and request.endpoint.startswith('mobile_api'):
                    return jsonify({
                        'error': message,
                        'error_type': 'vault_limit_exceeded',
                        'vaults_current': current,
                        'vaults_limit': limit,
                        'upgrade_required': True
                    }), 403
                else:
                    flash(f'{message} Please upgrade your plan for more family vaults.', 'warning')
                    return redirect(url_for('billing.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_ai_enhancement(user_id, enhancement_type, photo_id=None):
    """Log an AI enhancement usage for quota tracking"""
    from photovault.models import AIEnhancementLog
    from datetime import datetime
    
    try:
        log_entry = AIEnhancementLog(
            user_id=user_id,
            enhancement_type=enhancement_type,
            photo_id=photo_id,
            created_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        logger.info(f"Logged AI enhancement: user={user_id}, type={enhancement_type}")
        return True
    except Exception as e:
        logger.error(f"Failed to log AI enhancement: {str(e)}")
        db.session.rollback()
        return False
