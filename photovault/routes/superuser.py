"""
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
"""

# photovault/routes/superuser.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import ProgrammingError
from photovault import db
from photovault.models import User
from datetime import datetime

superuser_bp = Blueprint('superuser', __name__, url_prefix='/superuser')

def superuser_required(f):
    """Decorator to require superuser access"""
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superuser:
            flash("Access denied. Superuser privileges required.", "danger")
            return redirect(url_for('main.index')) # Or redirect to login/dashboard
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@superuser_bp.route('/')
@superuser_bp.route('/dashboard')
@login_required
@superuser_required
def dashboard():
    """Superuser dashboard showing all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('superuser/dashboard.html', users=users)

@superuser_bp.route('/users/toggle_superuser/<int:user_id>', methods=['POST'])
@login_required
@superuser_required
def toggle_superuser(user_id):
    """Toggle the superuser status of a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent users from modifying their own superuser status via this route
    if user.id == current_user.id:
        flash("You cannot change your own superuser status here.", "warning")
        return redirect(url_for('superuser.dashboard'))

    user.is_superuser = not user.is_superuser
    db.session.commit()
    status = "granted" if user.is_superuser else "revoked"
    flash(f"Superuser status {status} for user {user.username}.", "success")
    return redirect(url_for('superuser.dashboard'))

@superuser_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@superuser_required
def delete_user(user_id):
    """Delete a user and their photos"""
    user = User.query.get_or_404(user_id)
    
    # Prevent users from deleting themselves
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('superuser.dashboard'))

    username = user.username
    
    # Use raw SQL to delete user to avoid ORM relationship loading issues
    # when security tables don't exist
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    
    try:
        # Delete from each security table if it exists (check each one individually)
        security_tables = ['account_lockout', 'refresh_token', 'security_log', 'mfa_secret', 'oauth_provider']
        for table_name in security_tables:
            if inspector.has_table(table_name):
                try:
                    db.session.execute(text(f'DELETE FROM {table_name} WHERE user_id = :user_id'), {'user_id': user_id})
                except ProgrammingError as e:
                    # Table might not have user_id column or other issues - skip and continue
                    db.session.rollback()
                    print(f"Note: Could not delete from {table_name}: {e}")
        
        # Delete user - this will cascade delete photos, vaults, etc. via ON DELETE CASCADE in DB
        db.session.execute(text('DELETE FROM "user" WHERE id = :user_id'), {'user_id': user_id})
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")
        return redirect(url_for('superuser.dashboard'))
    flash(f"User {username} deleted successfully.", "success")
    return redirect(url_for('superuser.dashboard'))
