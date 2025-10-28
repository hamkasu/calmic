"""
Multi-Factor Authentication (MFA/2FA) Routes
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Handles MFA setup, verification, and management
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from photovault.utils.mfa import (
    generate_mfa_secret, 
    verify_mfa_code, 
    enable_mfa, 
    disable_mfa, 
    is_mfa_enabled,
    regenerate_backup_codes
)
from photovault.utils.security import log_security_event
from photovault.extensions import csrf
import logging

logger = logging.getLogger(__name__)

mfa_bp = Blueprint('mfa', __name__, url_prefix='/mfa')


@mfa_bp.route('/setup', methods=['GET'])
@login_required
def setup():
    """Show MFA setup page"""
    if is_mfa_enabled(current_user.id):
        flash('MFA is already enabled for your account', 'info')
        return redirect(url_for('mfa.manage'))
    
    return render_template('mfa/setup.html')


@mfa_bp.route('/generate-secret', methods=['POST'])
@login_required
def generate_secret():
    """Generate new MFA secret and QR code"""
    try:
        secret, qr_code, backup_codes = generate_mfa_secret(
            current_user.id, 
            current_user.username
        )
        
        if not secret:
            return jsonify({
                'success': False, 
                'error': 'Failed to generate MFA secret'
            }), 500
        
        return jsonify({
            'success': True,
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes
        }), 200
        
    except Exception as e:
        logger.error(f"MFA secret generation error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'An error occurred while generating MFA secret'
        }), 500


@mfa_bp.route('/enable', methods=['POST'])
@login_required
def enable():
    """Enable MFA after verifying a code"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({
                'success': False, 
                'error': 'Verification code is required'
            }), 400
        
        success, message = enable_mfa(current_user.id, code)
        
        if success:
            log_security_event(
                user_id=current_user.id,
                event_type='mfa_enabled',
                severity='info',
                description='User enabled MFA/2FA'
            )
            
            return jsonify({
                'success': True, 
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False, 
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"MFA enable error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'An error occurred while enabling MFA'
        }), 500


@mfa_bp.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable MFA for current user"""
    try:
        success, message = disable_mfa(current_user.id)
        
        if success:
            log_security_event(
                user_id=current_user.id,
                event_type='mfa_disabled',
                severity='warning',
                description='User disabled MFA/2FA'
            )
            
            flash('MFA has been disabled for your account', 'success')
            return jsonify({
                'success': True, 
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False, 
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"MFA disable error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'An error occurred while disabling MFA'
        }), 500


@mfa_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify MFA code during login"""
    # Check if user is in MFA verification state
    if 'mfa_user_id' not in session:
        flash('Invalid MFA verification session', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user_id = session.get('mfa_user_id')
        
        if not code:
            flash('Please enter your verification code', 'error')
            return render_template('mfa/verify.html')
        
        is_valid, message = verify_mfa_code(user_id, code)
        
        if is_valid:
            # Import here to avoid circular import
            from photovault.models import User
            from flask_login import login_user
            
            user = User.query.get(user_id)
            if user:
                # Complete login
                login_user(user, remember=session.get('mfa_remember_me', False))
                
                # Clear MFA session data
                session.pop('mfa_user_id', None)
                session.pop('mfa_remember_me', None)
                
                log_security_event(
                    user_id=user.id,
                    event_type='mfa_login_success',
                    severity='info',
                    description='User successfully logged in with MFA'
                )
                
                flash('Login successful!', 'success')
                return redirect(url_for('main.dashboard'))
        else:
            flash(f'Invalid code: {message}', 'error')
            log_security_event(
                user_id=user_id,
                event_type='mfa_login_failed',
                severity='warning',
                description=f'Failed MFA verification: {message}'
            )
    
    return render_template('mfa/verify.html')


@mfa_bp.route('/manage', methods=['GET'])
@login_required
def manage():
    """MFA management page"""
    mfa_enabled = is_mfa_enabled(current_user.id)
    return render_template('mfa/manage.html', mfa_enabled=mfa_enabled)


@mfa_bp.route('/regenerate-backup-codes', methods=['POST'])
@login_required
def regenerate_backup():
    """Regenerate backup codes"""
    try:
        if not is_mfa_enabled(current_user.id):
            return jsonify({
                'success': False, 
                'error': 'MFA is not enabled'
            }), 400
        
        success, backup_codes = regenerate_backup_codes(current_user.id)
        
        if success:
            log_security_event(
                user_id=current_user.id,
                event_type='mfa_backup_codes_regenerated',
                severity='info',
                description='User regenerated MFA backup codes'
            )
            
            return jsonify({
                'success': True,
                'backup_codes': backup_codes
            }), 200
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to regenerate backup codes'
            }), 500
            
    except Exception as e:
        logger.error(f"Backup code regeneration error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'An error occurred while regenerating backup codes'
        }), 500


# Mobile API endpoints
@mfa_bp.route('/api/enable', methods=['POST'])
@csrf.exempt
def mobile_enable():
    """Mobile API: Enable MFA after verifying a code"""
    from photovault.utils.jwt_auth import token_required
    
    @token_required
    def _enable(current_user):
        try:
            data = request.get_json()
            code = data.get('code', '').strip()
            
            if not code:
                return jsonify({
                    'success': False, 
                    'error': 'Verification code is required'
                }), 400
            
            success, message = enable_mfa(current_user.id, code)
            
            if success:
                log_security_event(
                    user_id=current_user.id,
                    event_type='mfa_enabled',
                    severity='info',
                    description='User enabled MFA/2FA via mobile'
                )
                
                return jsonify({
                    'success': True, 
                    'message': message
                }), 200
            else:
                return jsonify({
                    'success': False, 
                    'error': message
                }), 400
                
        except Exception as e:
            logger.error(f"Mobile MFA enable error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'An error occurred while enabling MFA'
            }), 500
    
    return _enable()


@mfa_bp.route('/api/verify', methods=['POST'])
@csrf.exempt
def mobile_verify():
    """Mobile API: Verify MFA code during login"""
    try:
        from photovault.models import User
        import jwt
        from datetime import timedelta
        from flask import current_app
        from datetime import datetime
        
        data = request.get_json()
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        temp_token = data.get('temp_token', '').strip()
        
        if not all([email, code, temp_token]):
            return jsonify({
                'success': False, 
                'error': 'Email, code, and temp_token are required'
            }), 400
        
        # Verify temp token
        try:
            payload = jwt.decode(temp_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('type') != 'mfa_temp':
                return jsonify({'success': False, 'error': 'Invalid token type'}), 401
            user_id = payload.get('user_id')
        except:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Verify MFA code
        is_valid, message = verify_mfa_code(user_id, code)
        
        if is_valid:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Generate full JWT token (check for remember_me in request)
            remember_me = data.get('remember_me', True)
            token_expiry_days = 30 if remember_me else 7
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(days=token_expiry_days)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            log_security_event(
                user_id=user.id,
                event_type='mfa_login_success',
                severity='info',
                description='User successfully logged in with MFA via mobile'
            )
            
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
        else:
            log_security_event(
                user_id=user_id,
                event_type='mfa_login_failed',
                severity='warning',
                description=f'Failed MFA verification via mobile: {message}'
            )
            return jsonify({
                'success': False, 
                'error': message
            }), 401
            
    except Exception as e:
        logger.error(f"Mobile MFA verification error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'An error occurred during MFA verification'
        }), 500
