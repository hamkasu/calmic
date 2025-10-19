"""
OAuth 2.0 Social Login Utilities (Google, Apple)
"""
from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for, session
from photovault.models import User, OAuthProvider
from photovault.extensions import db
from werkzeug.security import generate_password_hash
import secrets
import logging

logger = logging.getLogger(__name__)

# Initialize OAuth object (will be configured in __init__.py)
oauth = OAuth()


def init_oauth(app):
    """
    Initialize OAuth with app configuration
    
    Args:
        app: Flask application instance
    """
    oauth.init_app(app)
    
    # Register Google OAuth
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logger.info("Google OAuth configured")
    
    # Register Apple OAuth
    if app.config.get('APPLE_CLIENT_ID') and app.config.get('APPLE_CLIENT_SECRET'):
        oauth.register(
            name='apple',
            client_id=app.config.get('APPLE_CLIENT_ID'),
            client_secret=app.config.get('APPLE_CLIENT_SECRET'),
            server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email name'
            }
        )
        logger.info("Apple OAuth configured")


def get_or_create_oauth_user(provider, provider_user_id, email, display_name=None, profile_picture=None):
    """
    Get or create a user from OAuth provider data
    
    Args:
        provider: OAuth provider name ('google', 'apple')
        provider_user_id: Provider's unique user ID
        email: User's email
        display_name: User's display name
        profile_picture: Profile picture URL
    
    Returns: (User object, is_new_user, OAuthProvider object)
    """
    try:
        # Check if OAuth connection exists
        oauth_conn = OAuthProvider.query.filter_by(
            provider=provider,
            provider_user_id=provider_user_id
        ).first()
        
        if oauth_conn:
            # Existing OAuth user
            user = User.query.get(oauth_conn.user_id)
            if user:
                # Update last login
                oauth_conn.last_login_at = db.func.now()
                db.session.commit()
                return user, False, oauth_conn
        
        # Check if user exists with this email
        user = User.query.filter_by(email=email).first()
        
        is_new_user = False
        if not user:
            # Create new user
            # Generate username from email
            username_base = email.split('@')[0]
            username = username_base
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{username_base}{counter}"
                counter += 1
            
            # Create user with random password (they'll use OAuth to log in)
            user = User()
            user.username = username
            user.email = email
            user.password_hash = generate_password_hash(secrets.token_urlsafe(32))
            user.is_active = True
            
            db.session.add(user)
            db.session.flush()  # Get user.id
            is_new_user = True
            logger.info(f"Created new user from {provider} OAuth: {email}")
        
        # Create or update OAuth connection
        if not oauth_conn:
            oauth_conn = OAuthProvider(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                email=email,
                display_name=display_name,
                profile_picture_url=profile_picture,
                last_login_at=db.func.now()
            )
            db.session.add(oauth_conn)
        else:
            # Update existing connection
            oauth_conn.email = email
            oauth_conn.display_name = display_name
            oauth_conn.profile_picture_url = profile_picture
            oauth_conn.last_login_at = db.func.now()
        
        db.session.commit()
        return user, is_new_user, oauth_conn
    except Exception as e:
        logger.error(f"Failed to get/create OAuth user: {str(e)}")
        db.session.rollback()
        return None, False, None


def update_oauth_tokens(oauth_provider_id, access_token, refresh_token=None, expires_at=None):
    """
    Update OAuth access and refresh tokens
    
    Args:
        oauth_provider_id: OAuthProvider ID
        access_token: OAuth access token
        refresh_token: OAuth refresh token (optional)
        expires_at: Token expiration datetime (optional)
    
    Returns: bool (success)
    """
    try:
        oauth_conn = OAuthProvider.query.get(oauth_provider_id)
        if not oauth_conn:
            return False
        
        oauth_conn.access_token = access_token
        if refresh_token:
            oauth_conn.refresh_token = refresh_token
        if expires_at:
            oauth_conn.token_expires_at = expires_at
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to update OAuth tokens: {str(e)}")
        db.session.rollback()
        return False


def disconnect_oauth_provider(user_id, provider):
    """
    Disconnect an OAuth provider from a user
    
    Args:
        user_id: User ID
        provider: Provider name ('google', 'apple')
    
    Returns: (success, message)
    """
    try:
        oauth_conn = OAuthProvider.query.filter_by(
            user_id=user_id,
            provider=provider
        ).first()
        
        if not oauth_conn:
            return False, "OAuth connection not found"
        
        # Check if user has a password set (or other OAuth providers)
        user = User.query.get(user_id)
        other_providers = OAuthProvider.query.filter(
            OAuthProvider.user_id == user_id,
            OAuthProvider.provider != provider
        ).count()
        
        # Don't allow disconnecting if it's the only login method and no password
        if not other_providers and not user.password_hash:
            return False, "Cannot disconnect: this is your only login method. Please set a password first."
        
        db.session.delete(oauth_conn)
        db.session.commit()
        
        logger.info(f"Disconnected {provider} OAuth for user {user_id}")
        return True, "OAuth provider disconnected successfully"
    except Exception as e:
        logger.error(f"Failed to disconnect OAuth provider: {str(e)}")
        db.session.rollback()
        return False, f"Failed to disconnect: {str(e)}"
