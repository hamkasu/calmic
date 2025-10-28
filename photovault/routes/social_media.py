"""
Social Media Integration Routes
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Handles OAuth flows and photo sharing to social platforms
"""
from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify, session
from flask_login import login_required, current_user
from photovault.services.social_media_service import SocialMediaService
from photovault.extensions import db
from photovault.models import SocialMediaConnection, Photo
import secrets

social_media_bp = Blueprint('social_media', __name__, url_prefix='/social')

social_service = SocialMediaService()


@social_media_bp.route('/connect')
@login_required
def connect_accounts():
    """Display social media connection management page"""
    available_platforms = social_service.get_available_platforms()
    
    # Get user's connected accounts
    connections = SocialMediaConnection.query.filter_by(user_id=current_user.id).all()
    connected_platforms = {conn.platform: conn for conn in connections}
    
    return render_template(
        'social_media/connect.html',
        available_platforms=available_platforms,
        connected_platforms=connected_platforms
    )


@social_media_bp.route('/authorize/<platform>')
@login_required
def authorize(platform):
    """Initiate OAuth flow for a social media platform"""
    if platform not in social_service.SUPPORTED_PLATFORMS:
        flash(f'Unsupported platform: {platform}', 'error')
        return redirect(url_for('social_media.connect_accounts'))
    
    if not social_service.is_platform_configured(platform):
        flash(f'{platform.title()} is not configured. Please contact support.', 'error')
        return redirect(url_for('social_media.connect_accounts'))
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session[f'{platform}_oauth_state'] = state
    
    # Get redirect URI
    redirect_uri = url_for('social_media.callback', platform=platform, _external=True)
    
    try:
        # Generate authorization URL with PKCE
        auth_url, state, code_verifier = social_service.get_authorization_url(platform, redirect_uri, state)
        
        # Store code verifier in session for token exchange
        session[f'{platform}_code_verifier'] = code_verifier
        
        return redirect(auth_url)
    
    except Exception as e:
        flash(f'Error connecting to {platform.title()}: {str(e)}', 'error')
        return redirect(url_for('social_media.connect_accounts'))


@social_media_bp.route('/callback/<platform>')
@login_required
def callback(platform):
    """Handle OAuth callback from social media platform"""
    # Verify state parameter (CSRF protection)
    state = request.args.get('state')
    stored_state = session.get(f'{platform}_oauth_state')
    
    if not state or state != stored_state:
        flash('Invalid OAuth state. Please try again.', 'error')
        return redirect(url_for('social_media.connect_accounts'))
    
    # Get authorization code
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f'Authorization failed: {error}', 'error')
        return redirect(url_for('social_media.connect_accounts'))
    
    if not code:
        flash('No authorization code received', 'error')
        return redirect(url_for('social_media.connect_accounts'))
    
    try:
        # Get code verifier from session
        code_verifier = session.get(f'{platform}_code_verifier')
        redirect_uri = url_for('social_media.callback', platform=platform, _external=True)
        
        # Exchange code for access token
        token_data = social_service.exchange_code_for_token(platform, code, redirect_uri, code_verifier)
        
        # Store or update connection in database
        connection = SocialMediaConnection.query.filter_by(
            user_id=current_user.id,
            platform=platform
        ).first()
        
        if connection:
            connection.access_token = token_data.get('access_token')
            connection.refresh_token = token_data.get('refresh_token')
            connection.platform_user_id = token_data.get('user_id') or token_data.get('id')
            connection.is_active = True
        else:
            connection = SocialMediaConnection(
                user_id=current_user.id,
                platform=platform,
                access_token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                platform_user_id=token_data.get('user_id') or token_data.get('id'),
                is_active=True
            )
            db.session.add(connection)
        
        db.session.commit()
        
        # Clean up session
        session.pop(f'{platform}_oauth_state', None)
        session.pop(f'{platform}_code_verifier', None)
        
        flash(f'Successfully connected to {platform.title()}!', 'success')
    
    except Exception as e:
        flash(f'Error connecting to {platform.title()}: {str(e)}', 'error')
    
    return redirect(url_for('social_media.connect_accounts'))


@social_media_bp.route('/disconnect/<platform>', methods=['POST'])
@login_required
def disconnect(platform):
    """Disconnect a social media account"""
    connection = SocialMediaConnection.query.filter_by(
        user_id=current_user.id,
        platform=platform
    ).first()
    
    if connection:
        connection.is_active = False
        db.session.commit()
        flash(f'Disconnected from {platform.title()}', 'success')
    
    return redirect(url_for('social_media.connect_accounts'))


@social_media_bp.route('/share/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def share_photo(photo_id):
    """Share a photo to selected social media platforms"""
    photo = Photo.query.get_or_404(photo_id)
    
    # Verify ownership
    if photo.user_id != current_user.id:
        flash('You do not have permission to share this photo', 'error')
        return redirect(url_for('gallery.dashboard'))
    
    if request.method == 'GET':
        # Get user's active connections
        connections = SocialMediaConnection.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        return render_template(
            'social_media/share.html',
            photo=photo,
            connections=connections
        )
    
    # Handle POST - share to selected platforms
    platforms = request.form.getlist('platforms')
    caption = request.form.get('caption', '')
    
    if not platforms:
        flash('Please select at least one platform', 'warning')
        return redirect(url_for('social_media.share_photo', photo_id=photo_id))
    
    results = []
    
    for platform in platforms:
        connection = SocialMediaConnection.query.filter_by(
            user_id=current_user.id,
            platform=platform,
            is_active=True
        ).first()
        
        if not connection:
            results.append({'platform': platform, 'success': False, 'error': 'Not connected'})
            continue
        
        try:
            # Get photo URL (assuming it's stored in object storage or served via route)
            photo_url = url_for('gallery.uploaded_file', filename=photo.filename, _external=True)
            
            # Share to platform
            if platform == 'instagram':
                result = social_service.post_to_instagram(
                    connection.platform_user_id,
                    connection.access_token,
                    photo_url,
                    caption
                )
            elif platform == 'facebook':
                result = social_service.post_to_facebook(
                    connection.platform_user_id,
                    connection.access_token,
                    photo_url,
                    caption
                )
            elif platform == 'twitter':
                # For Twitter, we need the actual file path
                result = social_service.post_to_twitter(
                    connection.access_token,
                    photo.file_path,
                    caption
                )
            elif platform == 'pinterest':
                # For Pinterest, need board_id - could be stored in connection data
                board_id = connection.connection_data.get('default_board_id') if connection.connection_data else None
                if not board_id:
                    raise ValueError('No default board configured for Pinterest')
                
                result = social_service.post_to_pinterest(
                    connection.access_token,
                    board_id,
                    photo_url,
                    photo.original_name,
                    caption
                )
            
            results.append({'platform': platform, 'success': True, 'data': result})
        
        except Exception as e:
            results.append({'platform': platform, 'success': False, 'error': str(e)})
    
    # Count successes
    successes = sum(1 for r in results if r['success'])
    
    if successes == len(platforms):
        flash(f'Successfully shared to {successes} platform(s)!', 'success')
    elif successes > 0:
        flash(f'Shared to {successes} of {len(platforms)} platform(s). Some failed.', 'warning')
    else:
        flash('Failed to share to any platforms', 'error')
    
    return redirect(url_for('social_media.share_photo', photo_id=photo_id))


@social_media_bp.route('/api/status', methods=['GET'])
@login_required
def api_status():
    """API endpoint to check social media connection status"""
    connections = SocialMediaConnection.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    return jsonify({
        'connected_platforms': [conn.platform for conn in connections],
        'available_platforms': social_service.get_available_platforms()
    })
