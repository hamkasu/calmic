"""
OAuth Social Login Routes (Google, Apple)
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""
from flask import Blueprint, redirect, url_for, session, flash, request
from flask_login import login_user, current_user
from photovault.utils.oauth import oauth, get_or_create_oauth_user
from photovault.utils.security import log_security_event
import logging

logger = logging.getLogger(__name__)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')


@oauth_bp.route('/login/<provider>')
def login(provider):
    """Initiate OAuth login with provider (google or apple)"""
    if current_user.is_authenticated:
        return redirect(url_for('gallery.dashboard'))
    
    if provider not in ['google', 'apple']:
        flash('Invalid OAuth provider', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Store return URL in session
        session['oauth_return_to'] = request.args.get('next') or url_for('gallery.dashboard')
        
        # Generate callback URL
        redirect_uri = url_for('oauth.callback', provider=provider, _external=True)
        
        # Start OAuth flow
        return oauth.create_client(provider).authorize_redirect(redirect_uri)
    except Exception as e:
        logger.error(f"OAuth login initiation error for {provider}: {str(e)}")
        flash(f'Failed to initiate {provider.title()} login', 'error')
        return redirect(url_for('auth.login'))


@oauth_bp.route('/callback/<provider>')
def callback(provider):
    """Handle OAuth callback from provider"""
    if provider not in ['google', 'apple']:
        flash('Invalid OAuth provider', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Get OAuth client
        client = oauth.create_client(provider)
        
        # Exchange code for token
        token = client.authorize_access_token()
        
        # Get user info
        if provider == 'google':
            resp = client.get('https://www.googleapis.com/oauth2/v3/userinfo')
            user_info = resp.json()
            provider_user_id = user_info.get('sub')
            email = user_info.get('email')
            display_name = user_info.get('name')
            profile_picture = user_info.get('picture')
        elif provider == 'apple':
            user_info = token.get('userinfo', {})
            provider_user_id = user_info.get('sub')
            email = user_info.get('email')
            # Apple may not always provide name
            display_name = user_info.get('name', email.split('@')[0] if email else None)
            profile_picture = None
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        if not provider_user_id or not email:
            flash(f'Failed to get user information from {provider.title()}', 'error')
            return redirect(url_for('auth.login'))
        
        # Get or create user
        user, is_new_user, oauth_conn = get_or_create_oauth_user(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            display_name=display_name,
            profile_picture=profile_picture
        )
        
        if not user:
            flash(f'Failed to create/link {provider.title()} account', 'error')
            return redirect(url_for('auth.login'))
        
        # Log user in
        login_user(user, remember=True)
        
        # Log security event
        log_security_event(
            user_id=user.id,
            event_type=f'oauth_login_{provider}',
            severity='info',
            description=f'User logged in via {provider.title()} OAuth' + (' (new account)' if is_new_user else '')
        )
        
        # Show success message
        if is_new_user:
            flash(f'Welcome! Your account has been created using {provider.title()}.', 'success')
        else:
            flash(f'Welcome back! Logged in with {provider.title()}.', 'success')
        
        # Redirect to original destination or dashboard
        return_to = session.pop('oauth_return_to', url_for('gallery.dashboard'))
        return redirect(return_to)
        
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {str(e)}")
        flash(f'Failed to complete {provider.title()} login. Please try again.', 'error')
        return redirect(url_for('auth.login'))


@oauth_bp.route('/disconnect/<provider>', methods=['POST'])
def disconnect(provider):
    """Disconnect OAuth provider from current user"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if provider not in ['google', 'apple']:
        flash('Invalid OAuth provider', 'error')
        return redirect(url_for('main.settings'))
    
    try:
        from photovault.utils.oauth import disconnect_oauth_provider
        success, message = disconnect_oauth_provider(current_user.id, provider)
        
        if success:
            log_security_event(
                user_id=current_user.id,
                event_type=f'oauth_disconnected_{provider}',
                severity='info',
                description=f'User disconnected {provider.title()} OAuth'
            )
            flash(message, 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        logger.error(f"OAuth disconnect error for {provider}: {str(e)}")
        flash(f'Failed to disconnect {provider.title()}', 'error')
    
    return redirect(url_for('main.settings'))
