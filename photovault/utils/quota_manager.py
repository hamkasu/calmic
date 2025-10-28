"""
AI Enhancement Quota Management
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Tracks and enforces monthly limits for AI-powered photo enhancements (colorization and restoration)
"""
from datetime import datetime, timedelta
from photovault.extensions import db
from photovault.models import User, UserSubscription, SubscriptionPlan
import logging

logger = logging.getLogger(__name__)


def get_user_subscription(user_id):
    """
    Get the active subscription for a user
    
    Args:
        user_id: User ID
        
    Returns:
        UserSubscription object or None
    """
    return UserSubscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).first()


def get_user_plan(user):
    """
    Get the subscription plan for a user (active subscription or default to Free)
    
    Args:
        user: User object
        
    Returns:
        SubscriptionPlan object
    """
    # Get active subscription
    subscription = get_user_subscription(user.id)
    
    if subscription and subscription.plan:
        return subscription.plan
    
    # Default to Free plan
    free_plan = SubscriptionPlan.query.filter_by(name='free', is_active=True).first()
    return free_plan


def get_ai_quota_info(user):
    """
    Get quota information for a user
    
    Args:
        user: User object
        
    Returns:
        dict with quota information:
        {
            'quota_limit': int,  # Monthly limit
            'quota_used': int,   # Used this month
            'quota_remaining': int,  # Remaining
            'reset_date': datetime,  # When quota resets
            'unlimited': bool  # Whether user has unlimited quota
        }
    """
    plan = get_user_plan(user)
    subscription = get_user_subscription(user.id)
    
    # Get quota limit from plan
    quota_limit = plan.ai_enhancement_quota if plan else 0
    unlimited = quota_limit >= 9999  # Treat very large quotas as unlimited
    
    # Get current usage
    quota_used = 0
    reset_date = None
    
    if subscription:
        quota_used = subscription.ai_enhancements_used or 0
        reset_date = subscription.ai_enhancements_reset_date
        
        # Initialize reset date if not set
        if not reset_date:
            reset_date = get_next_reset_date()
            subscription.ai_enhancements_reset_date = reset_date
            db.session.commit()
    else:
        # For users without subscription, reset monthly
        reset_date = get_next_reset_date()
    
    quota_remaining = max(0, quota_limit - quota_used) if not unlimited else 9999
    
    return {
        'quota_limit': quota_limit,
        'quota_used': quota_used,
        'quota_remaining': quota_remaining,
        'reset_date': reset_date,
        'unlimited': unlimited,
        'plan_name': plan.display_name if plan else 'Free Plan'
    }


def check_ai_quota(user):
    """
    Check if user has AI enhancement quota remaining
    
    Args:
        user: User object
        
    Returns:
        tuple: (has_quota: bool, quota_info: dict, error_message: str)
    """
    # NOTE: This is a READ-ONLY check. Actual quota consumption is atomic via increment_ai_usage_atomic()
    quota_info = get_ai_quota_info(user)
    
    # Check if quota reset is needed
    subscription = get_user_subscription(user.id)
    if subscription and subscription.ai_enhancements_reset_date:
        if datetime.utcnow() >= subscription.ai_enhancements_reset_date:
            # Reset quota
            subscription.ai_enhancements_used = 0
            subscription.ai_enhancements_reset_date = get_next_reset_date()
            db.session.commit()
            
            # Refresh quota info after reset
            quota_info = get_ai_quota_info(user)
    
    # Check if user has quota
    if quota_info['unlimited']:
        return True, quota_info, None
    
    if quota_info['quota_remaining'] <= 0:
        reset_date_str = quota_info['reset_date'].strftime('%Y-%m-%d') if quota_info['reset_date'] else 'next month'
        error_message = (
            f"You've reached your monthly AI enhancement limit ({quota_info['quota_limit']} enhancements). "
            f"Your quota will reset on {reset_date_str}. "
            f"Upgrade your plan for more AI enhancements!"
        )
        return False, quota_info, error_message
    
    return True, quota_info, None


def increment_ai_usage(user):
    """
    ATOMIC increment of AI enhancement usage counter with quota enforcement
    
    Uses database-level row locking (SELECT FOR UPDATE) to prevent race conditions
    where concurrent requests could both bypass the quota limit.
    
    Args:
        user: User object
        
    Returns:
        tuple: (success: bool, new_usage: int, error_message: str or None)
    """
    from sqlalchemy import text
    
    subscription = get_user_subscription(user.id)
    
    if not subscription:
        # Create a basic subscription record for Free users to track usage
        free_plan = SubscriptionPlan.query.filter_by(name='free', is_active=True).first()
        if not free_plan:
            logger.error("Free plan not found in database")
            return False, 0, "System error: Free plan not configured"
        
        subscription = UserSubscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status='active',
            ai_enhancements_used=1,
            ai_enhancements_reset_date=get_next_reset_date()
        )
        db.session.add(subscription)
        db.session.commit()
        return True, 1, None
    
    # Lock the subscription row to prevent concurrent modifications
    locked_subscription = db.session.query(UserSubscription).filter_by(
        id=subscription.id
    ).with_for_update().first()
    
    if not locked_subscription:
        db.session.rollback()
        return False, 0, "Failed to lock subscription record"
    
    # Get quota limit
    plan = get_user_plan(user)
    quota_limit = plan.ai_enhancement_quota if plan else 0
    current_usage = locked_subscription.ai_enhancements_used or 0
    
    # Check if quota allows this increment (double-check within transaction)
    if quota_limit < 9999 and current_usage >= quota_limit:
        db.session.rollback()
        return False, current_usage, f"Quota exceeded: {current_usage}/{quota_limit}"
    
    # Atomically increment
    locked_subscription.ai_enhancements_used = current_usage + 1
    
    # Ensure reset date is set
    if not locked_subscription.ai_enhancements_reset_date:
        locked_subscription.ai_enhancements_reset_date = get_next_reset_date()
    
    db.session.commit()
    
    new_usage = locked_subscription.ai_enhancements_used
    logger.info(f"AI quota atomically incremented for user {user.id}: {new_usage}/{quota_limit}")
    
    return True, new_usage, None


def get_next_reset_date():
    """
    Calculate the next monthly reset date (1st of next month)
    
    Returns:
        datetime: Next reset date
    """
    now = datetime.utcnow()
    
    # Get first day of next month
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    
    return next_month


def reset_all_quotas():
    """
    Reset all user quotas (called by monthly cron job)
    
    Also handles legacy subscriptions with NULL reset dates
    
    Returns:
        int: Number of quotas reset
    """
    try:
        now = datetime.utcnow()
        
        # Find all subscriptions that need reset (including NULL reset dates for legacy accounts)
        subscriptions = UserSubscription.query.filter(
            db.or_(
                UserSubscription.ai_enhancements_reset_date.is_(None),
                UserSubscription.ai_enhancements_reset_date <= now
            )
        ).all()
        
        count = 0
        for subscription in subscriptions:
            subscription.ai_enhancements_used = 0
            subscription.ai_enhancements_reset_date = get_next_reset_date()
            count += 1
        
        db.session.commit()
        logger.info(f"Reset AI enhancement quotas for {count} users (including legacy subscriptions)")
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to reset quotas: {str(e)}")
        db.session.rollback()
        return 0
