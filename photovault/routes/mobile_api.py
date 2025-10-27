"""
Mobile API Routes for StoryKeep iOS/Android App
"""
from flask import Blueprint, jsonify, request, current_app, url_for
from photovault.models import Photo, UserSubscription, FamilyVault, FamilyMember, User, VaultPhoto, VaultInvitation, PhotoComment
from photovault.extensions import db, csrf
from photovault.utils.jwt_auth import token_required
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
import uuid
from datetime import datetime, timedelta
from PIL import Image
import logging
import jwt
import re
import traceback

logger = logging.getLogger(__name__)
mobile_api_bp = Blueprint('mobile_api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@mobile_api_bp.route('/auth/login', methods=['POST'])
@csrf.exempt
def mobile_login():
    """Mobile app login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Support both email and username for login
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', True)  # Default to True for convenience
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email or username
        user = User.query.filter(
            (User.email == email) | (User.username == email)
        ).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed login attempt for: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if MFA is enabled for this user
        from photovault.utils.mfa import is_mfa_enabled
        mfa_enabled = is_mfa_enabled(user.id)
        
        if mfa_enabled:
            # Generate temporary token for MFA verification (short expiry)
            temp_token = jwt.encode({
                'user_id': user.id,
                'type': 'mfa_temp',
                'exp': datetime.utcnow() + timedelta(minutes=5)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            logger.info(f"MFA required for mobile login: {user.username}")
            
            return jsonify({
                'success': True,
                'mfa_required': True,
                'temp_token': temp_token,
                'email': user.email,
                'message': 'Please enter your MFA code'
            }), 200
        
        # No MFA - generate normal JWT token
        # Token expiration: 30 days if remember_me, 7 days otherwise
        token_expiry_days = 30 if remember_me else 7
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(days=token_expiry_days)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        logger.info(f"Successful mobile login for user: {user.username}")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Mobile login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500

@mobile_api_bp.route('/auth/register', methods=['POST'])
@csrf.exempt
def mobile_register():
    """Mobile app registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        terms_accepted = data.get('terms_accepted', False)
        
        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength using centralized security function
        from photovault.utils.security import validate_password_strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate terms acceptance - must be explicitly True (boolean)
        if terms_accepted is not True:
            return jsonify({'error': 'You must accept the Terms and Conditions to register'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already exists'}), 400
            else:
                return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        new_user = User()
        new_user.username = username
        new_user.email = email
        new_user.password_hash = generate_password_hash(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT token (default to remember_me=True for new registrations)
        remember_me = data.get('remember_me', True)
        token_expiry_days = 30 if remember_me else 7
        token = jwt.encode({
            'user_id': new_user.id,
            'username': new_user.username,
            'exp': datetime.utcnow() + timedelta(days=token_expiry_days)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        logger.info(f"New mobile user registered: {username}")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Mobile registration error: {str(e)}")
        return jsonify({'error': 'An error occurred during registration'}), 500

@mobile_api_bp.route('/dashboard', methods=['GET'])
@csrf.exempt
@token_required
def get_dashboard(current_user):
    """Get dashboard statistics for mobile app"""
    try:
        from photovault.models import VoiceMemo, PhotoComment
        from sqlalchemy import func
        
        # Calculate photo statistics
        total_photos = Photo.query.filter_by(user_id=current_user.id).count()
        
        # Count enhanced photos (photos with edited_filename)
        enhanced_photos = Photo.query.filter_by(user_id=current_user.id).filter(
            Photo.edited_filename.isnot(None)
        ).count()
        
        # Calculate total storage
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        total_size_bytes = sum(photo.file_size or 0 for photo in photos)
        total_size_mb = round(total_size_bytes / 1024 / 1024, 2) if total_size_bytes > 0 else 0
        
        # Count family vaults (where user is creator or member) - avoid double counting
        from photovault.models import FamilyVault, FamilyMember
        
        # Get distinct vault IDs where user is creator
        created_vault_ids = set([v.id for v in FamilyVault.query.filter_by(created_by=current_user.id).all()])
        
        # Get distinct vault IDs where user is a member
        member_vault_ids = set([m.vault_id for m in FamilyMember.query.filter_by(user_id=current_user.id, status='active').all()])
        
        # Union of both sets gives unique vault count
        total_vaults = len(created_vault_ids | member_vault_ids)
        
        # Get subscription info and storage limits
        user_subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
        subscription_plan = user_subscription.plan.name if user_subscription and user_subscription.plan else 'Free'
        
        # Calculate storage limit based on subscription plan
        if user_subscription and user_subscription.plan and user_subscription.plan.storage_gb:
            storage_limit_gb = user_subscription.plan.storage_gb
            # Handle unlimited storage (usually represented as -1 or very large number)
            if storage_limit_gb < 0 or storage_limit_gb >= 999:
                storage_limit_mb = -1  # -1 indicates unlimited
                storage_usage_percent = 0  # No percentage for unlimited
            else:
                storage_limit_mb = storage_limit_gb * 1024
                storage_usage_percent = round((total_size_mb / storage_limit_mb * 100), 1) if storage_limit_mb > 0 else 0
        else:
            # Free plan defaults - 100MB
            storage_limit_mb = 100
            storage_usage_percent = round((total_size_mb / storage_limit_mb * 100), 1) if storage_limit_mb > 0 else 0
        
        # Get voice memo counts for all photos efficiently (single query)
        voice_memo_dict = {}
        comment_dict = {}
        if photos:  # Only query if user has photos
            photo_ids = [p.id for p in photos]
            
            # Voice memo counts
            voice_memo_counts = db.session.query(
                VoiceMemo.photo_id,
                func.count(VoiceMemo.id).label('count')
            ).filter(
                VoiceMemo.photo_id.in_(photo_ids)
            ).group_by(VoiceMemo.photo_id).all()
            
            # Create a dictionary for quick lookup
            voice_memo_dict = {photo_id: count for photo_id, count in voice_memo_counts}
            
            # Comment/annotation counts
            comment_counts = db.session.query(
                PhotoComment.photo_id,
                func.count(PhotoComment.id).label('count')
            ).filter(
                PhotoComment.photo_id.in_(photo_ids)
            ).group_by(PhotoComment.photo_id).all()
            
            # Create a dictionary for quick lookup
            comment_dict = {photo_id: count for photo_id, count in comment_counts}
        
        # Sort photos by creation date (newest first)
        sorted_photos = sorted(photos, key=lambda p: p.created_at if p.created_at else datetime.min, reverse=True)
        
        # Get one recent photo for diagnostic
        recent_photo = None
        if sorted_photos:
            photo = sorted_photos[0]
            recent_photo = {
                'id': photo.id,
                'filename': photo.filename,
                'original_url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
                'edited_url': f'/uploads/{current_user.id}/{photo.edited_filename}' if photo.edited_filename else None,
                'created_at': photo.created_at.isoformat() if photo.created_at else None
            }
        
        # Return ALL photos using same pattern for Gallery to use
        all_photos = []
        for photo in sorted_photos:
            all_photos.append({
                'id': photo.id,
                'filename': photo.filename,
                'url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
                'original_url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
                'edited_url': f'/uploads/{current_user.id}/{photo.edited_filename}' if photo.edited_filename else None,
                'created_at': photo.created_at.isoformat() if photo.created_at else None,
                'file_size': photo.file_size,
                'has_edited': photo.edited_filename is not None,
                'voice_memo_count': voice_memo_dict.get(photo.id, 0),
                'comment_count': comment_dict.get(photo.id, 0),
                # Annotation data for iOS app display - use getattr for fields that may not exist
                'enhancement_metadata': getattr(photo, 'enhancement_metadata', None),
                'processing_notes': getattr(photo, 'processing_notes', None),
                'back_text': getattr(photo, 'back_text', None),
                'date_text': getattr(photo, 'date_text', None),
                'location_text': getattr(photo, 'location_text', None),
                'occasion': getattr(photo, 'occasion', None),
                'photo_date': getattr(photo, 'photo_date', None).isoformat() if getattr(photo, 'photo_date', None) else None,
                'condition': getattr(photo, 'condition', None),
                'photo_source': getattr(photo, 'photo_source', None),
                'needs_restoration': getattr(photo, 'needs_restoration', None),
                'auto_enhanced': getattr(photo, 'auto_enhanced', False)
            })
        
        return jsonify({
            'total_photos': total_photos,
            'enhanced_photos': enhanced_photos,
            'albums': 0,
            'vaults': total_vaults,
            'storage_used': total_size_mb,
            'storage_limit_mb': storage_limit_mb,  # -1 for unlimited
            'storage_usage_percent': storage_usage_percent,
            'subscription_plan': subscription_plan,
            'recent_photo': recent_photo,
            'all_photos': all_photos,  # ALL photos for gallery
            'debug_photos_count': len(photos)
        })
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@mobile_api_bp.route('/auth/profile', methods=['GET'])
@csrf.exempt
@token_required
def get_profile(current_user):
    """Get user profile for mobile app"""
    try:
        user_subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
        
        # Query database directly for profile_picture (bypass SQLAlchemy model)
        # This works even if the column isn't in the model definition
        result = db.session.execute(
            db.text("SELECT profile_picture FROM \"user\" WHERE id = :user_id"),
            {"user_id": current_user.id}
        ).fetchone()
        
        profile_picture = result[0] if result and result[0] else None
        
        logger.info(f"📸 Profile picture from database for user {current_user.username}: {profile_picture}")
        
        # Build profile picture URL if exists - handle both object storage and local paths
        profile_picture_url = None
        if profile_picture:
            # Check if it's an object storage path
            if profile_picture.startswith('uploads/'):
                # Already has uploads/ prefix - just add leading slash
                profile_picture_url = f'/{profile_picture}'
            elif profile_picture.startswith('users/'):
                # Object storage with users/ prefix - add /uploads/ prefix
                profile_picture_url = f'/uploads/{profile_picture}'
            else:
                # Local filesystem - just filename, use user_id subdirectory
                profile_picture_url = f'/uploads/{current_user.id}/{profile_picture}'
            
            logger.info(f"✅ Built profile picture URL: {profile_picture_url}")
        else:
            logger.warning(f"⚠️ No profile picture in database for user {current_user.username}")
        
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'subscription_plan': user_subscription.plan.name if user_subscription and user_subscription.plan else 'Free',
            'profile_picture': profile_picture_url,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None
        })
    except Exception as e:
        logger.error(f"❌ Profile error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@mobile_api_bp.route('/profile/avatar', methods=['POST'])
@csrf.exempt
@token_required
def update_avatar(current_user):
    """Profile picture upload with object storage support for Railway persistence"""
    try:
        # Get the uploaded file
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if not image_file or image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Validate file type - accept HEIC for iOS devices
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp', 'heic', 'heif'}
        original_ext = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else ''
        if original_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Use: {", ".join(allowed_extensions)}'}), 400
        
        # Determine if we need to convert HEIC
        is_heic = original_ext in ('heic', 'heif')
        target_ext = 'jpg' if is_heic else original_ext
        
        # Generate simple filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        avatar_filename = f'avatar_{timestamp}.{target_ext}'
        
        # Process image in memory (resize, convert, etc.)
        try:
            # Register HEIC decoder if available
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
            except:
                pass
            
            from PIL import Image
            import io
            
            # Open image from upload stream
            img = Image.open(image_file.stream)
            
            # Convert to RGB if needed (for HEIC/PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 300x300 thumbnail
            img.thumbnail((300, 300))
            
            # Save to BytesIO buffer
            buffer = io.BytesIO()
            save_format = 'JPEG' if target_ext == 'jpg' else target_ext.upper()
            img.save(buffer, format=save_format, quality=85)
            buffer.seek(0)
            
            # Create a file-like object for enhanced file handler
            from werkzeug.datastructures import FileStorage
            processed_file = FileStorage(
                stream=buffer,
                filename=avatar_filename,
                content_type=f'image/{target_ext}'
            )
            
        except Exception as process_err:
            logger.error(f"Image processing failed: {str(process_err)}")
            return jsonify({'error': 'Failed to process image. Please try a different image format.'}), 500
        
        # Save using enhanced file handler (supports object storage + Railway volumes)
        from photovault.utils.enhanced_file_handler import save_uploaded_file_enhanced
        
        success, file_path = save_uploaded_file_enhanced(
            file=processed_file,
            filename=avatar_filename,
            user_id=current_user.id
        )
        
        if not success:
            logger.error(f"Failed to save avatar: {file_path}")
            return jsonify({'error': 'Failed to save profile picture'}), 500
        
        # Determine the stored path format (object storage vs local)
        # Object storage paths: users/1/avatar.jpg or uploads/1/avatar.jpg
        # Local paths: /path/to/uploads/1/avatar.jpg
        if file_path.startswith('users/') or file_path.startswith('uploads/'):
            # Object storage path - store as-is
            stored_path = file_path
        else:
            # Local filesystem path - store just the filename
            stored_path = avatar_filename
        
        # Update database - use SQL update to avoid model issues
        try:
            db.session.execute(
                db.text("UPDATE \"user\" SET profile_picture = :filename WHERE id = :user_id"),
                {'filename': stored_path, 'user_id': current_user.id}
            )
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            logger.error(f"Database update failed: {str(db_err)}")
            return jsonify({'error': 'Database error'}), 500
        
        # Build avatar URL based on storage type
        if stored_path.startswith('users/') or stored_path.startswith('uploads/'):
            # Object storage - use direct path
            avatar_url = f'/uploads/{stored_path}'
        else:
            # Local storage - use user_id path
            avatar_url = f'/uploads/{current_user.id}/{stored_path}'
        
        logger.info(f"✅ Profile picture updated for user {current_user.id}: {avatar_url}")
        
        return jsonify({
            'success': True,
            'avatar_url': avatar_url,
            'message': 'Profile picture updated'
        }), 200
        
    except Exception as e:
        logger.error(f"Avatar upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@mobile_api_bp.route('/photos', methods=['GET'])
@csrf.exempt
@token_required
def get_photos(current_user):
    """
    Gallery Endpoint with Server-Side Pagination for iOS/Android app
    Returns paginated photos with metadata for efficient loading
    """
    try:
        # Get pagination parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 30))))  # Default 30, max 100
        filter_type = request.args.get('filter', 'all').lower()
        
        logger.info(f"📸 Gallery request from user {current_user.id} - page {page}, per_page {per_page}, filter: {filter_type}")
        
        # Build base query with proper ordering for index usage
        base_query = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc())
        
        # Apply filtering if requested
        if filter_type == 'enhanced':
            base_query = base_query.filter(Photo.edited_filename.isnot(None))
        elif filter_type == 'originals':
            base_query = base_query.filter(Photo.edited_filename.is_(None))
        # 'all' or any other value returns all photos
        
        # Get total count for pagination metadata
        total_count = base_query.count()
        
        # Calculate pagination metadata
        total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
        has_more = page < total_pages
        
        # Execute paginated query using LIMIT and OFFSET
        offset = (page - 1) * per_page
        photos = base_query.limit(per_page).offset(offset).all()
        
        logger.info(f"📊 Found {len(photos)} photos for page {page} (total: {total_count})")
        
        # Build photo list with all required metadata
        photos_list = []
        for photo in photos:
            photo_dict = {
                'id': photo.id,
                'filename': photo.filename,
                'url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
                'thumbnail_url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
                'created_at': photo.created_at.isoformat() if photo.created_at else None,
                'file_size': photo.file_size or 0,
                'has_edited': bool(photo.edited_filename),
                'enhancement_metadata': photo.enhancement_metadata,
                'voice_memo_count': getattr(photo, 'voice_memo_count', 0),
                'comment_count': getattr(photo, 'comment_count', 0)
            }
            
            # Add edited URL if it exists
            if photo.edited_filename:
                photo_dict['edited_url'] = f'/uploads/{current_user.id}/{photo.edited_filename}'
            
            photos_list.append(photo_dict)
        
        # Return paginated response with metadata
        response = {
            'success': True,
            'photos': photos_list,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_more': has_more
            },
            'filter': filter_type
        }
        
        logger.info(f"✅ Returning page {page}/{total_pages} ({len(photos_list)} photos) to mobile app")
        return jsonify(response), 200
        
    except ValueError as ve:
        logger.error(f"❌ Invalid pagination parameters: {str(ve)}")
        return jsonify({
            'success': False,
            'error': 'Invalid page or per_page parameter',
            'photos': []
        }), 400
    except Exception as e:
        logger.error(f"❌ Gallery error: {str(e)}")
        logger.error(f"❌ Error details: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'photos': []
        }), 500

@mobile_api_bp.route('/photos/<int:photo_id>', methods=['GET'])
@csrf.exempt
@token_required
def get_photo_detail(current_user, photo_id):
    """Get single photo details for mobile app"""
    try:
        # Fetch the photo
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({'error': 'Photo not found'}), 404
        
        # Build photo data - same format as get_photos
        photo_data = {
            'id': photo.id,
            'filename': photo.filename,
            'original_url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
            'url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
            'thumbnail_url': f'/uploads/{current_user.id}/{photo.filename}' if photo.filename else None,
            'created_at': photo.created_at.isoformat() if photo.created_at else None,
            'file_size': photo.file_size,
            'has_edited': photo.edited_filename is not None,
            # Annotation data
            'enhancement_metadata': photo.enhancement_metadata,
            'processing_notes': photo.processing_notes,
            'back_text': photo.back_text,
            'date_text': photo.date_text,
            'location_text': photo.location_text,
            'occasion': photo.occasion,
            'photo_date': photo.photo_date.isoformat() if photo.photo_date else None,
            'condition': photo.condition,
            'photo_source': photo.photo_source,
            'needs_restoration': photo.needs_restoration,
            'auto_enhanced': photo.auto_enhanced
        }
        
        if photo.edited_filename:
            photo_data['edited_url'] = f'/uploads/{current_user.id}/{photo.edited_filename}'
        
        logger.info(f"📸 Photo detail fetched: {photo.id} for user {current_user.username}")
        
        return jsonify(photo_data), 200
        
    except Exception as e:
        logger.error(f"Photo detail error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@mobile_api_bp.route('/upload', methods=['POST'])
@csrf.exempt
@token_required
def upload_photo(current_user):
    """Upload photo from mobile app with photo detection support"""
    try:
        logger.info(f"Mobile upload from user: {current_user.id}")
        
        # Check if file was provided (accept both 'photo' and 'image' field names)
        file = None
        if 'photo' in request.files:
            file = request.files['photo']
        elif 'image' in request.files:
            file = request.files['image']
        else:
            return jsonify({'error': 'No photo provided'}), 400
        
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Check file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large (max 50MB)'}), 400
        
        # Generate unique filename
        if not file.filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        
        # Save file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        filepath = os.path.join(user_folder, unique_filename)
        file.save(filepath)
        
        # Create thumbnail
        thumbnail_filename = f"thumb_{unique_filename}"
        thumbnail_path = os.path.join(user_folder, thumbnail_filename)
        try:
            img = Image.open(filepath)
            img.thumbnail((300, 300))
            img.save(thumbnail_path)
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            thumbnail_path = filepath
        
        # Create photo record
        photo = Photo()
        photo.user_id = current_user.id
        photo.filename = unique_filename
        photo.original_name = file.filename
        photo.file_path = filepath
        photo.thumbnail_path = thumbnail_path
        photo.file_size = file_size
        photo.upload_source = 'mobile_camera'
        
        # Add metadata from request form (for enhanced photos)
        if 'title' in request.form:
            photo.occasion = request.form.get('title')
        if 'description' in request.form:
            photo.processing_notes = request.form.get('description')
        if 'enhancement_type' in request.form:
            enhancement_type = request.form.get('enhancement_type')
            photo.enhancement_metadata = {'type': enhancement_type, 'source': 'mobile_app'}
            photo.auto_enhanced = True
        if 'original_photo_id' in request.form:
            original_id = request.form.get('original_photo_id')
            logger.info(f"Enhanced photo uploaded from original photo {original_id}")
        
        db.session.add(photo)
        db.session.commit()
        
        logger.info(f"Photo uploaded successfully: {photo.id}")
        
        face_processing_result = {}
        try:
            from photovault.services.face_detection_service import face_detection_service
            
            face_processing_result = face_detection_service.process_and_tag_photo(photo, auto_tag=True)
            
            if face_processing_result.get('faces_detected', 0) > 0:
                logger.info(f"Face processing completed: "
                           f"{face_processing_result['faces_detected']} faces detected, "
                           f"{face_processing_result['tags_created']} auto-tagged")
        
        except Exception as face_detection_error:
            logger.warning(f"Face processing failed: {face_detection_error}")
            face_processing_result = {'error': str(face_detection_error)}
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'photo': {
                'id': photo.id,
                'filename': photo.filename,
                'url': url_for('gallery.uploaded_file',
                             user_id=current_user.id,
                             filename=photo.filename,
                             _external=True),
                'thumbnail_url': url_for('gallery.uploaded_file',
                                       user_id=current_user.id,
                                       filename=os.path.basename(thumbnail_path),
                                       _external=True),
                'faces_detected': face_processing_result.get('faces_detected', 0),
                'tags_created': face_processing_result.get('tags_created', 0)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Upload failed'}), 500

@mobile_api_bp.route('/photos/<int:photo_id>/upload-enhanced', methods=['POST'])
@csrf.exempt
@token_required
def upload_enhanced_photo(current_user, photo_id):
    """Upload pre-processed enhanced photo from mobile app"""
    try:
        logger.info(f"📤 Enhanced photo upload for photo {photo_id} from user: {current_user.id}")
        
        # Verify photo ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file was provided
        if 'file' not in request.files:
            logger.error("❌ No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            logger.error("❌ Empty file")
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get enhancement metadata from form data
        enhancement_type = request.form.get('enhancement_type', 'sharpen')
        settings = request.form.get('settings', '{}')
        
        logger.info(f"🎨 Enhancement type: {enhancement_type}, settings: {settings}")
        
        # Generate unique filename for edited version
        if not file.filename:
            return jsonify({'error': 'Invalid filename'}), 400
        ext = file.filename.rsplit('.', 1)[1].lower()
        edited_filename = f"{photo.id}_edited_{enhancement_type}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Save enhanced file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        edited_filepath = os.path.join(user_folder, edited_filename)
        file.save(edited_filepath)
        
        logger.info(f"💾 Saved enhanced photo to: {edited_filepath}")
        
        # Update photo record with edited version
        photo.edited_filename = edited_filename
        photo.updated_at = datetime.utcnow()
        
        # Update enhancement metadata if provided
        if settings != '{}':
            photo.enhancement_metadata = settings
        
        db.session.commit()
        
        logger.info(f"✅ Photo {photo_id} updated with enhanced version")
        
        return jsonify({
            'success': True,
            'message': 'Enhanced photo uploaded successfully',
            'photo': {
                'id': photo.id,
                'filename': photo.filename,
                'edited_filename': edited_filename,
                'edited_url': f'/uploads/{current_user.id}/{edited_filename}',
                'enhancement_type': enhancement_type
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Enhanced upload error: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@mobile_api_bp.route('/detect-and-extract', methods=['POST'])
@csrf.exempt
@token_required
def detect_and_extract_photos(current_user):
    """Detect and extract photos from uploaded image (digitizer functionality)"""
    try:
        from photovault.utils.photo_detection import PhotoDetector
        from photovault.utils.file_handler import validate_image_file, generate_unique_filename
        
        logger.info(f"🎯 Photo detection request from user: {current_user.id}")
        
        # Check if file was uploaded
        if 'image' not in request.files:
            logger.error("❌ No image file in request")
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if not file or not file.filename:
            logger.error("❌ Empty file")
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"📁 Processing uploaded file: {file.filename}")
        
        # Validate file
        is_valid, validation_msg = validate_image_file(file)
        if not is_valid:
            logger.error(f"❌ Invalid file: {validation_msg}")
            return jsonify({'error': f'Invalid file: {validation_msg}'}), 400
        
        # Generate unique filename
        unique_filename = generate_unique_filename(
            file.filename,
            prefix='digitizer',
            username=current_user.username
        )
        
        # Save uploaded file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        source_path = os.path.join(user_folder, unique_filename)
        file.save(source_path)
        
        logger.info(f"💾 Saved source image to: {source_path}")
        
        # Initialize detector
        detector = PhotoDetector()
        
        # Detect photos in the image
        detected = detector.detect_photos(source_path)
        
        if not detected or len(detected) == 0:
            logger.info("ℹ️ No photos detected in image")
            # Still save the original image
            file_size = os.path.getsize(source_path)
            
            # Create thumbnail
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_path = os.path.join(user_folder, thumbnail_filename)
            try:
                img = Image.open(source_path)
                img.thumbnail((300, 300))
                img.save(thumbnail_path)
            except Exception as e:
                logger.error(f"Thumbnail creation failed: {e}")
                thumbnail_path = source_path
            
            # Save as regular photo
            photo = Photo()
            photo.user_id = current_user.id
            photo.filename = unique_filename
            photo.original_name = file.filename
            photo.file_path = source_path
            photo.thumbnail_path = thumbnail_path
            photo.file_size = file_size
            photo.upload_source = 'digitizer'
            
            db.session.add(photo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'No photos detected - saved as single image',
                'photos_extracted': 0,
                'photo': {
                    'id': photo.id,
                    'filename': photo.filename
                }
            }), 200
        
        logger.info(f"✅ Detected {len(detected)} photos in image")
        
        # Extract detected photos with username for new naming format
        extracted_files = detector.extract_photos(source_path, user_folder, detected, username=current_user.username)
        
        extracted_photos = []
        
        for i, extracted_file in enumerate(extracted_files):
            try:
                extracted_path = extracted_file['path']
                
                # Create thumbnail
                thumbnail_filename = f"thumb_{os.path.basename(extracted_path)}"
                thumbnail_path = os.path.join(user_folder, thumbnail_filename)
                try:
                    img = Image.open(extracted_path)
                    img.thumbnail((300, 300))
                    img.save(thumbnail_path)
                except Exception as e:
                    logger.error(f"Thumbnail creation failed: {e}")
                    thumbnail_path = extracted_path
                
                # Get file size
                extracted_size = os.path.getsize(extracted_path)
                
                # Create new photo record
                extracted_photo = Photo()
                extracted_photo.user_id = current_user.id
                extracted_photo.filename = os.path.basename(extracted_path)
                # Use detected photo filename as original_name (format: <username>.detected.<date>.<random>.jpg)
                extracted_photo.original_name = os.path.basename(extracted_path)
                extracted_photo.file_path = extracted_path
                extracted_photo.thumbnail_path = thumbnail_path
                extracted_photo.file_size = extracted_size
                extracted_photo.upload_source = 'digitizer'
                
                db.session.add(extracted_photo)
                db.session.commit()
                
                extracted_photos.append({
                    'id': extracted_photo.id,
                    'filename': extracted_photo.filename,
                    'confidence': extracted_file.get('confidence', 0)
                })
                
                logger.info(f"✅ Extracted photo {i+1}: {extracted_photo.filename}")
                
            except Exception as extract_error:
                logger.error(f"❌ Error processing extracted photo {i}: {extract_error}")
                continue
        
        # Clean up source file after successful extraction
        try:
            if os.path.exists(source_path):
                os.remove(source_path)
                logger.info(f"🗑️ Cleaned up source file: {source_path}")
        except Exception as e:
            logger.error(f"Failed to clean up source file: {e}")
        
        logger.info(f"🎉 Successfully extracted {len(extracted_photos)} photos")
        
        return jsonify({
            'success': True,
            'message': f'Successfully extracted {len(extracted_photos)} photos',
            'photos_extracted': len(extracted_photos),
            'total_detected': len(detected),
            'extracted_photos': extracted_photos
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Photo detection error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Photo detection failed: {str(e)}'}), 500

@mobile_api_bp.route('/preview-detection', methods=['POST'])
@csrf.exempt
@token_required
def preview_detection(current_user):
    """Preview photo detection without saving - for real-time camera overlay"""
    try:
        from photovault.utils.photo_detection import PhotoDetector
        from photovault.utils.file_handler import validate_image_file
        import tempfile
        
        logger.info(f"📸 Preview detection request from user: {current_user.id}")
        
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        is_valid, validation_msg = validate_image_file(file)
        if not is_valid:
            return jsonify({'error': f'Invalid file: {validation_msg}'}), 400
        
        # Save to temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)
        
        try:
            # Initialize detector
            detector = PhotoDetector()
            
            # Detect photos
            detected = detector.detect_photos(temp_path)
            
            # Return detection results with corner points for overlay
            detection_results = []
            for det in detected:
                detection_results.append({
                    'x': det['x'],
                    'y': det['y'],
                    'width': det['width'],
                    'height': det['height'],
                    'confidence': det['confidence'],
                    'corners': det.get('corners', [])  # Corner points for drawing overlay
                })
            
            return jsonify({
                'success': True,
                'detected_count': len(detected),
                'detections': detection_results,
                'message': f'Detected {len(detected)} photo(s)' if detected else 'No photos detected'
            }), 200
            
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to clean up temp file: {e}")
        
    except Exception as e:
        logger.error(f"❌ Preview detection error: {str(e)}")
        return jsonify({'error': 'Preview detection failed'}), 500

@mobile_api_bp.route('/family/vaults', methods=['GET', 'POST'])
@csrf.exempt
@token_required
def family_vaults(current_user):
    """Get user's family vaults or create new vault for mobile app"""
    if request.method == 'GET':
        try:
            # Get vaults created by user
            created_vaults = FamilyVault.query.filter_by(created_by=current_user.id).all()
            
            # Get vaults user is a member of
            member_vaults = db.session.query(FamilyVault).join(FamilyMember).filter(
                FamilyMember.user_id == current_user.id,
                FamilyMember.status == 'active'
            ).all()
            
            # Combine and deduplicate
            all_vaults = list({v.id: v for v in created_vaults + member_vaults}.values())
            
            # Build response
            vaults_list = []
            for vault in all_vaults:
                vault_data = {
                    'id': vault.id,
                    'name': vault.name,
                    'description': vault.description,
                    'vault_code': vault.vault_code,
                    'is_public': vault.is_public,
                    'created_at': vault.created_at.isoformat() if vault.created_at else None,
                    'is_creator': vault.created_by == current_user.id,
                    'member_role': vault.get_member_role(current_user.id) if hasattr(vault, 'get_member_role') else 'member'
                }
                vaults_list.append(vault_data)
            
            return jsonify({
                'success': True,
                'vaults': vaults_list
            })
            
        except Exception as e:
            logger.error(f"Error fetching family vaults: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            from photovault.routes.family import validate_vault_name, validate_vault_description, generate_vault_code
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            is_public = data.get('is_public', False)
            
            # Validate inputs
            valid_name, name_msg = validate_vault_name(name)
            valid_desc, desc_msg = validate_vault_description(description)
            
            if not valid_name:
                return jsonify({'error': name_msg}), 400
            
            if not valid_desc:
                return jsonify({'error': desc_msg}), 400
            
            # Generate unique vault code
            vault_code = generate_vault_code()
            while FamilyVault.query.filter_by(vault_code=vault_code).first():
                vault_code = generate_vault_code()
            
            # Create vault
            vault = FamilyVault()
            vault.name = name
            vault.description = description
            vault.created_by = current_user.id
            vault.vault_code = vault_code
            vault.is_public = is_public
            
            db.session.add(vault)
            db.session.flush()
            
            # Add creator as admin member
            creator_member = FamilyMember()
            creator_member.vault_id = vault.id
            creator_member.user_id = current_user.id
            creator_member.role = 'admin'
            creator_member.status = 'active'
            db.session.add(creator_member)
            
            db.session.commit()
            
            logger.info(f"✅ Vault created successfully: {vault.id} by user {current_user.username}")
            
            return jsonify({
                'success': True,
                'vault': {
                    'id': vault.id,
                    'name': vault.name,
                    'description': vault.description,
                    'vault_code': vault_code,
                    'is_public': vault.is_public,
                    'created_at': vault.created_at.isoformat() if vault.created_at else None
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating vault: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Failed to create vault'}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>', methods=['GET'])
@csrf.exempt
@token_required
def get_vault_detail(current_user, vault_id):
    """Get vault details for mobile app - REWRITTEN for better error handling"""
    try:
        logger.info(f"🔍 VAULT DETAIL REQUEST: vault_id={vault_id}, user_id={current_user.id}, username={current_user.username}")
        
        # Step 1: Get vault with null check
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            logger.error(f"❌ VAULT NOT FOUND: vault_id={vault_id}")
            return jsonify({
                'success': False,
                'error': 'Vault not found',
                'vault_id': vault_id
            }), 404
        
        logger.info(f"✅ VAULT FOUND: id={vault.id}, name={vault.name}, created_by={vault.created_by}")
        
        # Step 2: Check access permissions
        is_creator = (vault.created_by == current_user.id)
        
        # Check membership
        membership = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        is_member = membership is not None
        
        has_access = is_creator or is_member
        
        logger.info(f"🔐 ACCESS CHECK: is_creator={is_creator}, is_member={is_member}, has_access={has_access}")
        
        if not has_access:
            logger.error(f"❌ ACCESS DENIED: user_id={current_user.id} has no access to vault_id={vault_id}")
            return jsonify({
                'success': False,
                'error': 'You do not have permission to view this vault',
                'vault_id': vault_id
            }), 403
        
        # Step 3: Get vault photos with safe handling
        photos_list = []
        try:
            # Try to use VaultPhoto model
            vault_photos = VaultPhoto.query.filter_by(vault_id=vault_id).order_by(VaultPhoto.shared_at.desc()).all()
            logger.info(f"📸 FOUND {len(vault_photos)} vault photos using VaultPhoto model")
            
            for vp in vault_photos:
                try:
                    photo = Photo.query.get(vp.photo_id)
                    if photo:
                        photo_url = f"/uploads/{photo.user_id}/{photo.filename}" if photo.filename else None
                        thumbnail_url = f"/uploads/{photo.user_id}/{photo.filename}" if photo.filename else None
                        
                        # Get voice memos for this photo
                        voice_memos_list = []
                        try:
                            from photovault.models import VoiceMemo
                            voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).order_by(VoiceMemo.created_at.desc()).all()
                            for vm in voice_memos:
                                voice_memos_list.append({
                                    'id': vm.id,
                                    'filename': vm.filename,
                                    'url': f"/uploads/{vm.user_id}/voice_memos/{vm.filename}",
                                    'duration': vm.duration,
                                    'title': vm.title,
                                    'transcript': vm.transcript,
                                    'created_at': vm.created_at.isoformat() if vm.created_at else None,
                                    'user_id': vm.user_id
                                })
                        except Exception as vm_error:
                            logger.warning(f"⚠️ Error loading voice memos for photo {photo.id}: {str(vm_error)}")
                        
                        # Get comments/annotations for this photo
                        comments_list = []
                        try:
                            from photovault.models import PhotoComment
                            comments = PhotoComment.query.filter_by(photo_id=photo.id).order_by(PhotoComment.created_at.asc()).all()
                            for comment in comments:
                                user = User.query.get(comment.user_id)
                                comments_list.append({
                                    'id': comment.id,
                                    'comment_text': comment.comment_text,
                                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                                    'user_id': comment.user_id,
                                    'username': user.username if user else 'Unknown'
                                })
                        except Exception as comment_error:
                            logger.warning(f"⚠️ Error loading comments for photo {photo.id}: {str(comment_error)}")
                        
                        # Get the user who shared this photo
                        shared_by_user = User.query.get(vp.shared_by) if hasattr(vp, 'shared_by') and vp.shared_by else None
                        shared_by_username = shared_by_user.username if shared_by_user else 'Unknown'
                        
                        photos_list.append({
                            'id': photo.id,
                            'filename': photo.filename,
                            'url': photo_url,
                            'original_url': photo_url,
                            'thumbnail_url': thumbnail_url,
                            'caption': vp.caption if hasattr(vp, 'caption') else None,
                            'created_at': photo.created_at.isoformat() if photo.created_at else None,
                            'shared_at': vp.shared_at.isoformat() if vp.shared_at else None,
                            'shared_by_user_id': vp.shared_by if hasattr(vp, 'shared_by') else None,
                            'shared_by_username': shared_by_username,
                            'user_id': photo.user_id,
                            'voice_memos': voice_memos_list,
                            'comments': comments_list
                        })
                except Exception as photo_error:
                    logger.warning(f"⚠️ Error processing vault photo {vp.id}: {str(photo_error)}")
                    continue
                    
        except Exception as vault_photo_error:
            logger.error(f"❌ VaultPhoto query failed: {str(vault_photo_error)}")
            logger.info("📋 Using fallback: returning empty photos list")
            photos_list = []
        
        # Step 4: Get vault members with safe handling
        members_list = []
        try:
            members = FamilyMember.query.filter_by(vault_id=vault_id, status='active').all()
            logger.info(f"👥 FOUND {len(members)} vault members")
            
            for member in members:
                try:
                    user = User.query.get(member.user_id)
                    if user:
                        members_list.append({
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'role': member.role if hasattr(member, 'role') else 'member',
                            'is_creator': user.id == vault.created_by,
                            'joined_at': member.joined_at.isoformat() if member.joined_at else None
                        })
                except Exception as member_error:
                    logger.warning(f"⚠️ Error processing member {member.id}: {str(member_error)}")
                    continue
                    
        except Exception as members_error:
            logger.error(f"❌ Members query failed: {str(members_error)}")
            members_list = []
        
        # Step 5: Determine member role safely
        member_role = 'viewer'
        if is_creator:
            member_role = 'owner'
        elif membership and hasattr(membership, 'role'):
            member_role = membership.role
        
        # Step 6: Build success response
        response_data = {
            'success': True,
            'vault': {
                'id': vault.id,
                'name': vault.name,
                'description': vault.description if hasattr(vault, 'description') else '',
                'vault_code': vault.vault_code if hasattr(vault, 'vault_code') else None,
                'is_public': vault.is_public if hasattr(vault, 'is_public') else False,
                'created_at': vault.created_at.isoformat() if vault.created_at else None,
                'is_creator': is_creator,
                'member_role': member_role,
                'photo_count': len(photos_list),
                'member_count': len(members_list)
            },
            'photos': photos_list,
            'members': members_list
        }
        
        logger.info(f"✅ VAULT DETAIL SUCCESS: {len(photos_list)} photos, {len(members_list)} members")
        return jsonify(response_data), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"💥 VAULT DETAIL FATAL ERROR: {str(e)}")
        logger.error(f"📋 TRACEBACK:\n{error_trace}")
        
        return jsonify({
            'success': False,
            'error': f'Failed to load vault details: {str(e)}',
            'vault_id': vault_id,
            'error_type': type(e).__name__
        }), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/add-photo', methods=['POST'])
@csrf.exempt
@token_required
def add_photo_to_vault(current_user, vault_id):
    """Add photo to vault - FRESH IMPLEMENTATION using working gallery pattern"""
    logger.info(f"🎯 ADD PHOTO: vault={vault_id}, user={current_user.id}")
    
    try:
        # Get photo_id from request
        data = request.get_json()
        photo_id = data.get('photo_id') if data else None
        caption = data.get('caption', '') if data else ''
        
        logger.info(f"📥 Request data: photo_id={photo_id}, caption={caption}")
        
        if not photo_id:
            logger.error("❌ No photo_id provided")
            return jsonify({'success': False, 'error': 'photo_id required'}), 400
        
        # Get vault - simple query
        vault = FamilyVault.query.filter_by(id=vault_id).first()
        if not vault:
            logger.error(f"❌ Vault {vault_id} not found")
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check vault access - creator OR member
        is_creator = (vault.created_by == current_user.id)
        member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        
        if not is_creator and not member:
            logger.error(f"❌ No access to vault {vault_id}")
            return jsonify({'success': False, 'error': 'No vault access'}), 403
        
        # Get photo - use same pattern as gallery
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.error(f"❌ Photo {photo_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        logger.info(f"✅ Photo found: {photo.filename}")
        
        # Check if already added
        existing = VaultPhoto.query.filter_by(vault_id=vault_id, photo_id=photo_id).first()
        if existing:
            logger.info(f"⚠️ Already added, returning success")
            return jsonify({
                'success': True,
                'message': 'Photo already in vault',
                'photo': {
                    'id': photo.id,
                    'original_url': f'/uploads/{current_user.id}/{photo.filename}',
                    'caption': existing.caption
                }
            }), 200
        
        # Add to vault - fresh simple code
        vault_photo = VaultPhoto()
        vault_photo.vault_id = vault_id
        vault_photo.photo_id = photo_id
        vault_photo.shared_by = current_user.id
        vault_photo.shared_at = datetime.utcnow()
        vault_photo.caption = caption
        
        db.session.add(vault_photo)
        db.session.commit()
        
        logger.info(f"✅ SUCCESS! Added photo {photo_id} to vault {vault_id}")
        
        # Return photo info using same URL pattern as gallery
        return jsonify({
            'success': True,
            'message': 'Photo added to vault',
            'photo': {
                'id': photo.id,
                'original_url': f'/uploads/{current_user.id}/{photo.filename}',
                'edited_url': f'/uploads/{current_user.id}/{photo.edited_filename}' if photo.edited_filename else None,
                'caption': caption
            }
        }), 201
        
    except Exception as e:
        logger.error(f"💥 ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/add-photos-bulk', methods=['POST'])
@csrf.exempt
@token_required
def add_photos_to_vault_bulk(current_user, vault_id):
    """Bulk add multiple photos to vault"""
    try:
        data = request.get_json()
        if not data or 'photo_ids' not in data:
            return jsonify({'success': False, 'error': 'photo_ids required'}), 400
        
        photo_ids = data.get('photo_ids', [])
        caption = data.get('caption', '')
        
        if not isinstance(photo_ids, list) or len(photo_ids) == 0:
            return jsonify({'success': False, 'error': 'photo_ids must be a non-empty array'}), 400
        
        logger.info(f"📤 BULK SHARE REQUEST: vault={vault_id}, {len(photo_ids)} photos, user={current_user.username}")
        
        # Get vault and verify access
        vault = FamilyVault.query.filter_by(id=vault_id).first()
        if not vault:
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check vault access - creator OR member
        is_creator = (vault.created_by == current_user.id)
        member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        
        if not is_creator and not member:
            return jsonify({'success': False, 'error': 'No vault access'}), 403
        
        success_count = 0
        failed_count = 0
        failed_photo_ids = []
        errors = []
        
        for photo_id in photo_ids:
            try:
                # Get photo
                photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
                if not photo:
                    logger.warning(f"❌ Photo {photo_id} not found")
                    failed_count += 1
                    failed_photo_ids.append(photo_id)
                    errors.append(f"Photo {photo_id} not found")
                    continue
                
                # Check if already added
                existing = VaultPhoto.query.filter_by(vault_id=vault_id, photo_id=photo_id).first()
                if existing:
                    logger.info(f"⚠️ Photo {photo_id} already in vault")
                    success_count += 1
                    continue
                
                # Add to vault
                vault_photo = VaultPhoto()
                vault_photo.vault_id = vault_id
                vault_photo.photo_id = photo_id
                vault_photo.shared_by = current_user.id
                vault_photo.shared_at = datetime.utcnow()
                vault_photo.caption = caption
                
                db.session.add(vault_photo)
                success_count += 1
                logger.info(f"✅ Photo {photo_id} added to vault")
                
            except Exception as e:
                logger.error(f"❌ Error adding photo {photo_id}: {str(e)}")
                failed_count += 1
                failed_photo_ids.append(photo_id)
                errors.append(f"Photo {photo_id}: {str(e)}")
                continue
        
        # Commit all additions
        db.session.commit()
        
        logger.info(f"🎯 BULK SHARE COMPLETE: success={success_count}, failed={failed_count}")
        
        return jsonify({
            'success': True,
            'message': f'Added {success_count} photos to vault',
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_photo_ids': failed_photo_ids,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"💥 BULK SHARE ERROR: {str(e)}")
        logger.error(f"📋 TRACEBACK:\n{error_trace}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Bulk share failed: {str(e)}'}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/photos/<int:photo_id>', methods=['DELETE'])
@csrf.exempt
@token_required
def remove_photo_from_vault(current_user, vault_id, photo_id):
    """Remove photo from vault - Mobile API"""
    try:
        logger.info(f"🗑️ REMOVE PHOTO FROM VAULT: vault_id={vault_id}, photo_id={photo_id}, user_id={current_user.id}")
        
        # Verify vault exists
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            logger.error(f"❌ Vault not found: {vault_id}")
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check if user is a member of the vault
        member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        
        if not member:
            logger.error(f"❌ User {current_user.id} is not a member of vault {vault_id}")
            return jsonify({'success': False, 'error': 'You are not a member of this vault'}), 403
        
        # Find the vault photo
        vault_photo = VaultPhoto.query.filter_by(
            vault_id=vault_id,
            photo_id=photo_id
        ).first()
        
        if not vault_photo:
            logger.error(f"❌ Photo {photo_id} not found in vault {vault_id}")
            return jsonify({'success': False, 'error': 'Photo not found in vault'}), 404
        
        # Check permission: can delete if user is admin, creator, or the one who shared it
        is_creator = vault.created_by == current_user.id
        is_admin = member.role == 'admin'
        is_sharer = vault_photo.shared_by == current_user.id
        
        if not (is_creator or is_admin or is_sharer):
            logger.error(f"❌ User {current_user.id} does not have permission to remove photo {photo_id}")
            return jsonify({'success': False, 'error': 'You do not have permission to remove this photo'}), 403
        
        # Delete the vault photo association
        db.session.delete(vault_photo)
        db.session.commit()
        
        logger.info(f"✅ Successfully removed photo {photo_id} from vault {vault_id}")
        
        return jsonify({
            'success': True,
            'message': 'Photo removed from vault'
        }), 200
        
    except Exception as e:
        logger.error(f"💥 ERROR removing photo from vault: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/photos/delete-bulk', methods=['POST'])
@csrf.exempt
@token_required
def remove_photos_bulk_from_vault(current_user, vault_id):
    """Remove multiple photos from vault - owner can delete their own, admin can delete any"""
    try:
        data = request.get_json()
        if not data or 'photo_ids' not in data:
            return jsonify({'success': False, 'error': 'photo_ids required'}), 400
        
        photo_ids = data.get('photo_ids', [])
        if not photo_ids or not isinstance(photo_ids, list):
            return jsonify({'success': False, 'error': 'photo_ids must be a non-empty array'}), 400
        
        logger.info(f"🗑️ BULK DELETE FROM VAULT: vault_id={vault_id}, user_id={current_user.id}, count={len(photo_ids)}")
        
        # Verify vault exists
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check if user is a member
        member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        
        if not member:
            return jsonify({'success': False, 'error': 'You are not a member of this vault'}), 403
        
        # Check if user has admin privileges
        is_creator = vault.created_by == current_user.id
        is_admin = member.role == 'admin'
        can_delete_any = is_creator or is_admin
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for photo_id in photo_ids:
            try:
                # Find the vault photo
                vault_photo = VaultPhoto.query.filter_by(
                    vault_id=vault_id,
                    photo_id=photo_id
                ).first()
                
                if not vault_photo:
                    errors.append(f"Photo {photo_id} not found in vault")
                    failed_count += 1
                    continue
                
                # Check permission: admin/creator can delete any, regular members can only delete their own
                is_owner = vault_photo.shared_by == current_user.id
                
                if not (can_delete_any or is_owner):
                    errors.append(f"Photo {photo_id}: No permission (not your photo)")
                    failed_count += 1
                    continue
                
                # Delete the vault photo association
                db.session.delete(vault_photo)
                success_count += 1
                logger.info(f"✅ Removed photo {photo_id} from vault")
                
            except Exception as e:
                logger.error(f"❌ Error removing photo {photo_id}: {str(e)}")
                errors.append(f"Photo {photo_id}: {str(e)}")
                failed_count += 1
                continue
        
        # Commit all deletions
        db.session.commit()
        
        logger.info(f"✅ BULK DELETE COMPLETE: success={success_count}, failed={failed_count}")
        
        return jsonify({
            'success': True,
            'message': f'Removed {success_count} photo(s) from vault',
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        logger.error(f"💥 BULK DELETE ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/invite', methods=['POST'])
@csrf.exempt
@token_required
def invite_member_to_vault(current_user, vault_id):
    """Invite a member to family vault - Mobile API"""
    try:
        from photovault.forms import (
            validate_email_for_invitation, validate_invitation_role,
            generate_invitation_token, get_invitation_expiry
        )
        
        logger.info(f"👥 INVITE MEMBER REQUEST: vault_id={vault_id}, user_id={current_user.id}")
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'member')
        
        logger.info(f"📋 Data: email={email}, role={role}")
        
        # Step 1: Verify vault exists
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            logger.error(f"❌ VAULT NOT FOUND: vault_id={vault_id}")
            return jsonify({
                'success': False,
                'error': 'Vault not found'
            }), 404
        
        # Step 2: Check if user can manage vault (admin or creator)
        user_role = vault.get_member_role(current_user.id)
        is_creator = vault.created_by == current_user.id
        
        if user_role not in ['admin'] and not is_creator:
            logger.error(f"❌ PERMISSION DENIED: user {current_user.id} cannot invite to vault {vault_id}")
            return jsonify({
                'success': False,
                'error': 'You do not have permission to invite members'
            }), 403
        
        logger.info(f"✅ PERMISSION GRANTED: is_creator={is_creator}, user_role={user_role}")
        
        # Step 3: Validate inputs
        valid_email, email_msg = validate_email_for_invitation(email)
        valid_role, role_msg = validate_invitation_role(role)
        
        if not valid_email:
            logger.error(f"❌ INVALID EMAIL: {email_msg}")
            return jsonify({
                'success': False,
                'error': email_msg
            }), 400
        
        if not valid_role:
            logger.error(f"❌ INVALID ROLE: {role_msg}")
            return jsonify({
                'success': False,
                'error': role_msg
            }), 400
        
        # Step 4: Check if user is already a member
        existing_member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            status='active'
        ).join(User, FamilyMember.user_id == User.id).filter(
            User.email == email
        ).first()
        
        if existing_member:
            logger.warning(f"⚠️ USER ALREADY MEMBER: email={email}, vault_id={vault_id}")
            return jsonify({
                'success': False,
                'error': 'This user is already a member of the vault'
            }), 400
        
        # Step 5: Check if invitation already exists
        existing_invitation = VaultInvitation.query.filter_by(
            vault_id=vault_id,
            email=email,
            status='pending'
        ).first()
        
        if existing_invitation:
            logger.warning(f"⚠️ INVITATION ALREADY EXISTS: email={email}, vault_id={vault_id}")
            return jsonify({
                'success': False,
                'error': 'An invitation has already been sent to this email'
            }), 400
        
        # Step 6: Create invitation
        invitation = VaultInvitation()
        invitation.vault_id = vault_id
        invitation.email = email
        invitation.invited_by = current_user.id
        invitation.role = role
        invitation.invitation_token = generate_invitation_token()
        invitation.expires_at = get_invitation_expiry()
        
        db.session.add(invitation)
        db.session.commit()
        
        logger.info(f"✅ INVITATION CREATED: invitation_id={invitation.id}")
        
        # Step 7: Send invitation email
        try:
            from photovault.services.sendgrid_service import send_family_invitation_email
            
            email_sent = send_family_invitation_email(
                email=email,
                invitation_token=invitation.invitation_token,
                vault_name=vault.name,
                inviter_name=current_user.username
            )
            
            if email_sent:
                invitation.mark_as_sent()
                db.session.commit()
                logger.info(f"📧 INVITATION EMAIL SENT: email={email}")
            else:
                logger.warning(f"⚠️ EMAIL FAILED: email={email}")
                
        except Exception as e:
            logger.error(f"❌ EMAIL ERROR: {str(e)}")
        
        # Return success even if email fails (invitation is created)
        invitation_url = url_for('family.accept_invitation', token=invitation.invitation_token, _external=True)
        
        return jsonify({
            'success': True,
            'message': f'Invitation sent to {email}',
            'invitation': {
                'id': invitation.id,
                'email': email,
                'role': role,
                'invitation_url': invitation_url,
                'expires_at': invitation.expires_at.isoformat() if invitation.expires_at else None
            }
        }), 201
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"💥 INVITE MEMBER ERROR: {str(e)}")
        logger.error(f"📋 TRACEBACK:\n{error_trace}")
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'error': f'Failed to send invitation: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>', methods=['PATCH'])
@csrf.exempt
@token_required
def edit_vault(current_user, vault_id):
    """Edit vault name and description - Admin/Creator only"""
    try:
        logger.info(f"✏️ EDIT VAULT REQUEST: vault_id={vault_id}, user_id={current_user.id}")
        
        # Get vault
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check if user is creator or admin
        is_creator = vault.created_by == current_user.id
        membership = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        is_admin = membership and membership.role == 'admin'
        
        if not (is_creator or is_admin):
            logger.error(f"❌ User {current_user.id} does not have permission to edit vault {vault_id}")
            return jsonify({'success': False, 'error': 'Only admins can edit vault'}), 403
        
        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update vault
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({'success': False, 'error': 'Vault name cannot be empty'}), 400
            vault.name = name
        
        if 'description' in data:
            vault.description = data['description'].strip()
        
        db.session.commit()
        
        logger.info(f"✅ Vault {vault_id} updated successfully")
        
        return jsonify({
            'success': True,
            'message': 'Vault updated successfully',
            'vault': {
                'id': vault.id,
                'name': vault.name,
                'description': vault.description
            }
        }), 200
        
    except Exception as e:
        logger.error(f"💥 EDIT VAULT ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>', methods=['DELETE'])
@csrf.exempt
@token_required
def delete_vault(current_user, vault_id):
    """Delete vault - Creator only"""
    try:
        logger.info(f"🗑️ DELETE VAULT REQUEST: vault_id={vault_id}, user_id={current_user.id}")
        
        # Get vault
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Only creator can delete vault
        if vault.created_by != current_user.id:
            logger.error(f"❌ User {current_user.id} is not the creator of vault {vault_id}")
            return jsonify({'success': False, 'error': 'Only vault creator can delete vault'}), 403
        
        # Delete all related data
        # Delete vault photos
        VaultPhoto.query.filter_by(vault_id=vault_id).delete()
        
        # Delete vault members
        FamilyMember.query.filter_by(vault_id=vault_id).delete()
        
        # Delete pending invitations
        VaultInvitation.query.filter_by(vault_id=vault_id).delete()
        
        # Delete vault
        db.session.delete(vault)
        db.session.commit()
        
        logger.info(f"✅ Vault {vault_id} deleted successfully")
        
        return jsonify({
            'success': True,
            'message': 'Vault deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"💥 DELETE VAULT ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/member/<int:user_id>', methods=['DELETE'])
@csrf.exempt
@token_required
def remove_vault_member(current_user, vault_id, user_id):
    """Remove member from vault - Admin/Creator only"""
    try:
        logger.info(f"👤❌ REMOVE MEMBER REQUEST: vault_id={vault_id}, user_id={user_id}, requester={current_user.id}")
        
        # Get vault
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check if requester is creator or admin
        is_creator = vault.created_by == current_user.id
        requester_membership = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        is_admin = requester_membership and requester_membership.role == 'admin'
        
        if not (is_creator or is_admin):
            logger.error(f"❌ User {current_user.id} does not have permission to remove members")
            return jsonify({'success': False, 'error': 'Only admins can remove members'}), 403
        
        # Cannot remove the creator
        if user_id == vault.created_by:
            return jsonify({'success': False, 'error': 'Cannot remove vault creator'}), 400
        
        # Cannot remove yourself
        if user_id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot remove yourself. Leave vault instead.'}), 400
        
        # Get member to remove
        member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not member:
            return jsonify({'success': False, 'error': 'Member not found in vault'}), 404
        
        # Remove member
        member.status = 'removed'
        db.session.commit()
        
        logger.info(f"✅ Member {user_id} removed from vault {vault_id}")
        
        return jsonify({
            'success': True,
            'message': 'Member removed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"💥 REMOVE MEMBER ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/family/vault/<int:vault_id>/member/<int:user_id>/role', methods=['PATCH'])
@csrf.exempt
@token_required
def change_member_role(current_user, vault_id, user_id):
    """Change member role between admin and member - Admin/Creator only"""
    try:
        logger.info(f"👤🔄 CHANGE ROLE REQUEST: vault_id={vault_id}, user_id={user_id}, requester={current_user.id}")
        
        # Get vault
        vault = FamilyVault.query.get(vault_id)
        if not vault:
            return jsonify({'success': False, 'error': 'Vault not found'}), 404
        
        # Check if requester is creator or admin
        is_creator = vault.created_by == current_user.id
        requester_membership = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=current_user.id,
            status='active'
        ).first()
        is_admin = requester_membership and requester_membership.role == 'admin'
        
        if not (is_creator or is_admin):
            logger.error(f"❌ User {current_user.id} does not have permission to change roles")
            return jsonify({'success': False, 'error': 'Only admins can change member roles'}), 403
        
        # Cannot downgrade creator
        if user_id == vault.created_by:
            return jsonify({'success': False, 'error': 'Cannot downgrade creator'}), 400
        
        # Get new role from request
        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({'success': False, 'error': 'Role not provided'}), 400
        
        new_role = data['role']
        if new_role not in ['admin', 'member']:
            return jsonify({'success': False, 'error': 'Invalid role. Use "admin" or "member"'}), 400
        
        # Get member to update
        member = FamilyMember.query.filter_by(
            vault_id=vault_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not member:
            return jsonify({'success': False, 'error': 'Member not found in vault'}), 404
        
        # Update role
        old_role = member.role
        member.role = new_role
        db.session.commit()
        
        logger.info(f"✅ Member {user_id} role changed from {old_role} to {new_role} in vault {vault_id}")
        
        # Get updated user info
        user = User.query.get(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Member role updated to {new_role}',
            'member': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': new_role
            }
        }), 200
        
    except Exception as e:
        logger.error(f"💥 CHANGE ROLE ERROR: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@mobile_api_bp.route('/photos/<int:photo_id>/enhance', methods=['POST'])
@csrf.exempt
@token_required
def enhance_photo_mobile(current_user, photo_id):
    """
    Mobile API endpoint to apply image enhancement with JWT authentication
    """
    try:
        logger.info(f"✨ ENHANCE REQUEST: photo_id={photo_id}, user={current_user.username}")
        
        from photovault.utils.image_enhancement import enhancer
        import random
        from datetime import datetime
        
        # Get the photo and verify ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.warning(f"❌ Photo {photo_id} not found or access denied for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found or access denied'}), 404
        
        logger.info(f"📸 Found photo: filename={photo.filename}, file_path={photo.file_path}")
        
        # Construct full file path
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        if os.path.isabs(photo.file_path):
            full_file_path = photo.file_path
        else:
            full_file_path = os.path.join(user_upload_dir, photo.file_path)
        
        logger.info(f"📂 Full file path: {full_file_path}")
        
        # Check if file exists
        if not os.path.exists(full_file_path):
            logger.error(f"❌ File not found on disk: {full_file_path}")
            return jsonify({'success': False, 'error': 'Photo file not found'}), 404
        
        # Check image size
        file_size = os.path.getsize(full_file_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"📏 File size: {file_size_mb:.2f}MB")
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            logger.warning(f"⚠️ File too large: {file_size_mb:.2f}MB > 10MB limit")
            return jsonify({
                'success': False, 
                'error': 'Image too large for enhancement. Please use smaller images (under 10MB).'
            }), 400
        
        # Get enhancement settings from request
        data = request.get_json() or {}
        enhancement_settings = data.get('settings', {})
        logger.info(f"⚙️ Enhancement settings: {enhancement_settings}")
        
        # Generate filename for enhanced version
        from werkzeug.utils import secure_filename as sanitize_name
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)
        safe_username = sanitize_name(current_user.username)
        enhanced_filename = f"{safe_username}.enhanced.{date}.{random_number}.jpg"
        
        logger.info(f"🎯 Enhanced filename: {enhanced_filename}")
        
        # Create user upload directory
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Enhanced image path
        enhanced_filepath = os.path.join(user_upload_dir, enhanced_filename)
        
        # Apply enhancements
        logger.info(f"🔧 Applying enhancements...")
        output_path, applied_settings = enhancer.auto_enhance_photo(
            full_file_path, 
            enhanced_filepath, 
            enhancement_settings
        )
        
        logger.info(f"✅ Enhancement complete: {output_path}, settings: {applied_settings}")
        
        # Update photo record with enhanced version
        photo.edited_filename = enhanced_filename
        photo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"💾 Database updated: photo {photo_id} enhanced successfully")
        
        return jsonify({
            'success': True,
            'message': 'Photo enhanced successfully',
            'photo': {
                'id': photo.id,
                'filename': photo.filename,
                'enhanced_filename': enhanced_filename,
                'enhanced_url': f'/uploads/{current_user.id}/{enhanced_filename}',
                'settings_applied': applied_settings
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"💥 ENHANCE ERROR for photo {photo_id}: {str(e)}")
        logger.error(f"📋 TRACEBACK:\n{error_trace}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Enhancement failed: {str(e)}'}), 500

@mobile_api_bp.route('/photos/<int:photo_id>/colorize', methods=['POST'])
@csrf.exempt
@token_required
def colorize_photo_mobile(current_user, photo_id):
    """
    Mobile API endpoint to colorize a black and white photo with JWT authentication
    """
    try:
        from photovault.utils.colorization import get_colorizer
        
        # Get the photo and verify ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            return jsonify({'success': False, 'error': 'Photo not found or access denied'}), 404
        
        # Get colorization method from request
        data = request.get_json() or {}
        method = data.get('method', 'auto')
        
        if method not in ['auto', 'dnn', 'basic']:
            return jsonify({
                'success': False,
                'error': 'Invalid colorization method. Use auto, dnn, or basic'
            }), 400
        
        # Initialize colorizer
        colorizer = get_colorizer()
        
        # Check if file exists
        if not os.path.exists(photo.file_path):
            return jsonify({'success': False, 'error': 'Photo file not found'}), 404
        
        # Check if photo is grayscale
        try:
            is_grayscale = colorizer.is_grayscale(photo.file_path)
        except Exception as e:
            logger.error(f"Error checking grayscale: {str(e)}")
            return jsonify({'success': False, 'error': 'Error processing photo'}), 500
        
        if not is_grayscale:
            return jsonify({
                'success': False,
                'error': 'Photo is already in color',
                'is_grayscale': False
            }), 400
        
        # Generate unique filename for colorized version
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        colorized_filename = f"{current_user.id}_{unique_id}_colorized_{timestamp}{file_extension}"
        
        # Create user folder
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        colorized_path = os.path.join(user_folder, colorized_filename)
        
        logger.info(f"Colorizing photo {photo_id} for user {current_user.id} using method: {method}")
        
        # Perform colorization
        try:
            colorized_path, actual_method = colorizer.colorize_image(photo.file_path, colorized_path, method=method)
        except RuntimeError as e:
            if 'DNN model not available' in str(e):
                return jsonify({
                    'success': False,
                    'error': 'DNN colorization model not available. Using basic method instead.'
                }), 400
            else:
                raise
        
        # Update photo record with colorized version
        photo.edited_filename = colorized_filename
        photo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Photo {photo_id} colorized successfully using {actual_method}")
        
        return jsonify({
            'success': True,
            'message': 'Photo colorized successfully',
            'photo': {
                'id': photo.id,
                'filename': photo.filename,
                'colorized_filename': colorized_filename,
                'colorized_url': f'/uploads/{current_user.id}/{colorized_filename}',
                'method_used': actual_method
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Mobile colorize error for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Colorization failed'}), 500


@mobile_api_bp.route('/photos/<int:photo_id>/colorize-ai', methods=['POST'])
@csrf.exempt
@token_required
def colorize_photo_ai_mobile(current_user, photo_id):
    """
    Mobile API endpoint to colorize a black and white photo using AI with JWT authentication
    """
    try:
        from photovault.services.ai_service import get_ai_service
        from photovault.services.app_storage_service import app_storage
        from photovault.utils.quota_manager import check_ai_quota, increment_ai_usage
        import io
        
        # Check AI quota before processing
        has_quota, quota_info, error_message = check_ai_quota(current_user)
        if not has_quota:
            return jsonify({
                'success': False,
                'error': error_message,
                'quota_info': {
                    'quota_limit': quota_info['quota_limit'],
                    'quota_used': quota_info['quota_used'],
                    'quota_remaining': quota_info['quota_remaining'],
                    'reset_date': quota_info['reset_date'].isoformat() if quota_info['reset_date'] else None,
                    'plan_name': quota_info['plan_name']
                }
            }), 429  # 429 Too Many Requests
        
        # Check if AI service is available
        ai_service = get_ai_service()
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service not available. Please configure GEMINI_API_KEY.'
            }), 503
        
        # Get the photo and verify ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            return jsonify({'success': False, 'error': 'Photo not found or access denied'}), 404
        
        # Check if file exists
        if not os.path.exists(photo.file_path):
            return jsonify({'success': False, 'error': 'Photo file not found'}), 404
        
        # Generate unique filename for colorized version
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        colorized_filename = f"{current_user.id}_{unique_id}_colorized_ai_{timestamp}{file_extension}"
        
        # Create user folder
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        colorized_path = os.path.join(user_folder, colorized_filename)
        
        logger.info(f"🎨 AI Colorizing photo {photo_id} for user {current_user.id}")
        
        # Perform AI colorization
        try:
            result_path, metadata = ai_service.colorize_image_ai(photo.file_path, colorized_path)
        except Exception as e:
            logger.error(f"AI colorization failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'AI colorization failed: {str(e)}'
            }), 500
        
        # Upload to App Storage if available
        edited_path = colorized_path
        if app_storage.is_available():
            try:
                with open(colorized_path, 'rb') as f:
                    img_bytes = io.BytesIO(f.read())
                    success, storage_path = app_storage.upload_file(img_bytes, colorized_filename, str(current_user.id))
                    if success:
                        edited_path = storage_path
                        logger.info(f"AI colorized photo uploaded to App Storage: {storage_path}")
                        # Clean up temp file
                        try:
                            os.remove(colorized_path)
                        except:
                            pass
            except Exception as e:
                logger.warning(f"App Storage upload failed, keeping local: {str(e)}")
        
        # Update photo record with colorized version
        photo.edited_filename = colorized_filename
        photo.edited_path = edited_path
        photo.enhancement_metadata = {
            'colorization': {
                'method': metadata['method'],
                'ai_guidance': metadata.get('ai_guidance', ''),
                'model': metadata.get('model', 'gemini-2.0-flash-exp'),
                'timestamp': str(datetime.now())
            }
        }
        photo.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Increment AI quota usage (atomic operation)
        success, new_usage, usage_error = increment_ai_usage(current_user)
        if not success:
            logger.error(f"Quota increment failed after colorization: {usage_error}")
        else:
            logger.info(f"✅ Photo {photo_id} AI-colorized successfully using {metadata['method']} (quota: {new_usage}/{quota_info['quota_limit']})")
        
        return jsonify({
            'success': True,
            'message': 'Photo colorized successfully using AI',
            'photo': {
                'id': photo.id,
                'filename': photo.filename,
                'colorized_filename': colorized_filename,
                'colorized_url': f'/uploads/{current_user.id}/{colorized_filename}',
                'method_used': metadata['method'],
                'ai_guidance': metadata.get('ai_guidance', '')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Mobile AI colorize error for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'AI Colorization failed'}), 500


@mobile_api_bp.route('/quota', methods=['GET'])
@csrf.exempt
@token_required
def get_quota_info(current_user):
    """
    Get AI enhancement quota information for the current user
    Returns quota limit, usage, and remaining count
    """
    try:
        from photovault.utils.quota_manager import get_ai_quota_info
        
        quota_info = get_ai_quota_info(current_user)
        
        return jsonify({
            'success': True,
            'quota': {
                'limit': quota_info['quota_limit'],
                'used': quota_info['quota_used'],
                'remaining': quota_info['quota_remaining'],
                'reset_date': quota_info['reset_date'].isoformat() if quota_info['reset_date'] else None,
                'unlimited': quota_info['unlimited'],
                'plan_name': quota_info['plan_name']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get quota info for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve quota information'
        }), 500


@mobile_api_bp.route('/photos/<int:photo_id>/check-grayscale', methods=['GET'])
@csrf.exempt
@token_required
def check_grayscale_mobile(current_user, photo_id):
    """
    Mobile API endpoint to check if a photo is black and white (grayscale)
    Returns True if photo is grayscale, False if it's already in color
    """
    try:
        from photovault.utils.colorization import get_colorizer
        
        # Get the photo and verify ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or access denied'
            }), 404
        
        # Check if file exists
        if not os.path.exists(photo.file_path):
            return jsonify({
                'success': False,
                'error': 'Photo file not found'
            }), 404
        
        # Check if photo is grayscale using OpenCV
        colorizer = get_colorizer()
        is_grayscale = colorizer.is_grayscale(photo.file_path)
        
        logger.info(f"🔍 Grayscale check for photo {photo_id}: {is_grayscale}")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'is_grayscale': is_grayscale
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Grayscale check error for photo {photo_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check photo color mode'
        }), 500


@mobile_api_bp.route('/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt
@token_required
def sharpen_photo_mobile(current_user, photo_id):
    """
    Apply image sharpening to a photo and save as NEW photo in gallery
    
    Request JSON:
        {
            "intensity": float,   # iOS sends intensity (mapped to amount)
            "radius": float,      # Sharpening radius (optional, default: 2.0)
            "threshold": int,     # Sharpening threshold (optional, default: 3)
            "method": str         # Sharpening method (optional, default: 'unsharp')
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,        # NEW photo ID
            "original_photo_id": int,  # Original photo ID
            "photo_url": str,
            "thumbnail_url": str,
            "message": str
        }
    """
    try:
        from photovault.utils.image_enhancement import enhancer
        from photovault.services.app_storage_service import app_storage
        from werkzeug.utils import secure_filename as sanitize_name
        import random
        from datetime import datetime
        import io
        
        # Get original photo
        original_photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not original_photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file paths
        original_path = original_photo.file_path
        
        if not os.path.exists(original_path):
            return jsonify({
                'success': False,
                'error': 'Original photo file not found'
            }), 404
        
        # Parameters - accept both JSON and form data
        # iOS sends form data, web sends JSON
        if request.is_json:
            data = request.get_json() or {}
            amount = data.get('amount', data.get('intensity', 1.5))
            radius = data.get('radius', 2.0)
            threshold = data.get('threshold', 3)
            method = data.get('method', 'unsharp')
        else:
            # Form data from iOS - safe parsing with defaults
            def safe_float(value, default):
                try:
                    return float(value) if value else default
                except (ValueError, TypeError):
                    return default
            
            def safe_int(value, default):
                try:
                    return int(value) if value else default
                except (ValueError, TypeError):
                    return default
            
            # iOS sends 'intensity', web sends 'amount'
            amount_str = request.form.get('amount') or request.form.get('intensity')
            amount = safe_float(amount_str, 1.5)
            radius = safe_float(request.form.get('radius'), 2.0)
            threshold = safe_int(request.form.get('threshold'), 3)
            method = request.form.get('method', 'unsharp')
        
        # Generate sharpened filename: <username>.sharpened.<date>.<random>.jpg
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)
        safe_username = sanitize_name(current_user.username)
        sharpened_filename = f"{safe_username}.sharpened.{date}.{random_number}.jpg"
        
        logger.info(f"🔧 Sharpening photo {photo_id}: '{original_photo.filename}' -> '{sharpened_filename}'")
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_upload_folder, exist_ok=True)
        sharpened_filepath = os.path.join(user_upload_folder, sharpened_filename)
        
        # Apply sharpening using PIL UnsharpMask
        output_path = enhancer.sharpen_image(
            original_path,
            sharpened_filepath,
            radius=radius,
            amount=amount,
            threshold=threshold,
            method=method
        )
        
        # Create thumbnail (300x300) - matching detect-and-extract pattern
        thumbnail_filename = f"thumb_{sharpened_filename}"
        thumbnail_path = os.path.join(user_upload_folder, thumbnail_filename)
        try:
            img = Image.open(sharpened_filepath)
            img.thumbnail((300, 300))
            img.save(thumbnail_path)
            logger.info(f"📸 Created thumbnail: {thumbnail_filename}")
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            thumbnail_path = sharpened_filepath
        
        # Get file size
        sharpened_size = os.path.getsize(sharpened_filepath)
        
        # Upload to app storage if available (Railway persistence)
        if app_storage.is_available():
            # Upload sharpened image
            with open(sharpened_filepath, 'rb') as f:
                img_bytes = io.BytesIO(f.read())
                success, storage_path = app_storage.upload_file(img_bytes, sharpened_filename, str(current_user.id))
                if success:
                    old_path = sharpened_filepath
                    sharpened_filepath = storage_path
                    try:
                        os.remove(old_path)
                    except:
                        pass
            
            # Upload thumbnail
            with open(thumbnail_path, 'rb') as f:
                thumb_bytes = io.BytesIO(f.read())
                success, thumb_storage_path = app_storage.upload_file(thumb_bytes, thumbnail_filename, str(current_user.id))
                if success:
                    old_thumb = thumbnail_path
                    thumbnail_path = thumb_storage_path
                    try:
                        os.remove(old_thumb)
                    except:
                        pass
        
        # Create NEW photo record in database (like detect-and-extract does)
        new_photo = Photo()
        new_photo.user_id = current_user.id
        new_photo.filename = sharpened_filename
        new_photo.original_name = f"{original_photo.original_name or original_photo.filename} (Sharpened)"
        new_photo.file_path = sharpened_filepath
        new_photo.thumbnail_path = thumbnail_path
        new_photo.file_size = sharpened_size
        new_photo.upload_source = 'sharpened'  # Mark as sharpened photo
        new_photo.enhancement_metadata = {
            'sharpening': {
                'radius': radius,
                'amount': amount,
                'threshold': threshold,
                'method': method,
                'timestamp': str(datetime.now()),
                'original_photo_id': photo_id
            }
        }
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"✅ Created new sharpened photo: ID={new_photo.id}, filename='{sharpened_filename}'")
        
        return jsonify({
            'success': True,
            'photo_id': new_photo.id,  # New photo ID
            'original_photo_id': photo_id,  # Original photo ID
            'photo_url': f'/uploads/{current_user.id}/{sharpened_filename}',
            'thumbnail_url': f'/uploads/{current_user.id}/{thumbnail_filename}',
            'message': 'Photo sharpened and saved to gallery'
        })
        
    except Exception as e:
        logger.error(f"❌ Sharpening failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# VOICE MEMO API - Rewritten for Mobile App with Duration Support
# ============================================================================

@mobile_api_bp.route('/photos/<int:photo_id>/voice-memos', methods=['GET'])
@csrf.exempt
@token_required
def get_voice_memos(current_user, photo_id):
    """Get all voice memos for a photo"""
    from photovault.models import VoiceMemo
    
    try:
        logger.info(f"📝 GET voice memos for photo {photo_id} by user {current_user.id}")
        
        # Verify photo ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.warning(f"❌ Photo {photo_id} not found or access denied for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # Get voice memos
        voice_memos = VoiceMemo.query.filter_by(photo_id=photo_id).order_by(VoiceMemo.created_at.desc()).all()
        
        memos_data = [{
            'id': memo.id,
            'filename': memo.filename,
            'duration': memo.duration or 0,
            'duration_formatted': memo.duration_formatted,
            'file_size_mb': memo.file_size_mb,
            'created_at': memo.created_at.isoformat() if memo.created_at else None,
        } for memo in voice_memos]
        
        logger.info(f"✅ Found {len(memos_data)} voice memos for photo {photo_id}")
        return jsonify({
            'success': True,
            'voice_memos': memos_data,
            'total': len(memos_data)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting voice memos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/photos/<int:photo_id>/voice-memos', methods=['POST'])
@csrf.exempt
@token_required
def upload_voice_memo(current_user, photo_id):
    """Upload a new voice memo with duration"""
    from photovault.models import VoiceMemo
    
    try:
        logger.info(f"🎤 === VOICE MEMO UPLOAD START ===")
        logger.info(f"📱 User ID: {current_user.id}, Photo ID: {photo_id}")
        logger.info(f"📦 Request files: {list(request.files.keys())}")
        logger.info(f"📦 Request form: {dict(request.form)}")
        logger.info(f"📦 Request headers: {dict(request.headers)}")
        logger.info(f"📦 Content-Length: {request.content_length}")
        logger.info(f"📦 Content-Type: {request.content_type}")
        
        # Check file size limit
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        logger.info(f"⚙️ Max upload size: {max_size / 1024 / 1024:.2f} MB")
        
        # Verify photo ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.warning(f"❌ Photo {photo_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # Validate audio file
        if 'audio' not in request.files:
            logger.error(f"❌ No audio file in request. Available keys: {list(request.files.keys())}")
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if not audio_file or not audio_file.filename:
            logger.error(f"❌ Empty audio file")
            return jsonify({'success': False, 'error': 'Empty audio file'}), 400
        
        # Log file details before saving
        logger.info(f"📄 Audio file: {audio_file.filename}")
        logger.info(f"📄 Content-Type: {audio_file.content_type}")
        
        # Get duration from form data (sent by iOS app)
        duration_str = request.form.get('duration', '0')
        try:
            duration = float(duration_str)
            logger.info(f"⏱️ Recording duration: {duration} seconds")
        except (ValueError, TypeError):
            duration = 0
            logger.warning(f"⚠️ Invalid duration value: {duration_str}, using 0")
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_ext = os.path.splitext(audio_file.filename)[1] or '.m4a'
        filename = f"voice_{current_user.id}_{timestamp}_{unique_id}{file_ext}"
        
        # Create directory and save file
        voice_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'voice_memos', str(current_user.id))
        os.makedirs(voice_folder, exist_ok=True)
        logger.info(f"📁 Save directory: {voice_folder}")
        
        filepath = os.path.join(voice_folder, filename)
        logger.info(f"💾 Saving to: {filepath}")
        audio_file.save(filepath)
        
        file_size = os.path.getsize(filepath)
        logger.info(f"💾 Saved successfully: {filename} ({file_size} bytes / {file_size/1024/1024:.2f} MB, duration: {duration}s)")
        
        # Create database record
        memo = VoiceMemo()
        memo.photo_id = photo_id
        memo.user_id = current_user.id
        memo.filename = filename
        memo.original_name = audio_file.filename
        memo.file_path = filepath
        memo.file_size = file_size
        memo.duration = duration
        memo.mime_type = audio_file.content_type or 'audio/m4a'
        
        db.session.add(memo)
        db.session.commit()
        
        logger.info(f"✅ Voice memo {memo.id} uploaded successfully")
        logger.info(f"🎤 === VOICE MEMO UPLOAD COMPLETE ===")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo uploaded',
            'voice_memo': {
                'id': memo.id,
                'filename': memo.filename,
                'duration': memo.duration,
                'duration_formatted': memo.duration_formatted,
                'created_at': memo.created_at.isoformat(),
                'file_size_mb': round(file_size / 1024 / 1024, 2)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"❌ === VOICE MEMO UPLOAD FAILED ===")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error message: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e), 'error_type': type(e).__name__}), 500


@mobile_api_bp.route('/voice-memo-test', methods=['GET'])
@csrf.exempt
@token_required
def voice_memo_test(current_user):
    """Diagnostic endpoint to test voice memo configuration"""
    try:
        logger.info(f"🔧 Voice memo diagnostic test for user {current_user.id}")
        
        # Get configuration
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # Check directory permissions
        voice_folder = os.path.join(upload_folder, 'voice_memos', str(current_user.id))
        can_create_dir = False
        try:
            os.makedirs(voice_folder, exist_ok=True)
            can_create_dir = True
        except Exception as e:
            logger.error(f"Cannot create directory: {e}")
        
        # Get first photo for testing
        photo = Photo.query.filter_by(user_id=current_user.id).first()
        
        return jsonify({
            'success': True,
            'config': {
                'max_upload_size_mb': round(max_size / 1024 / 1024, 2),
                'upload_folder': upload_folder,
                'voice_folder': voice_folder,
                'can_create_directory': can_create_dir,
                'has_photos': photo is not None,
                'first_photo_id': photo.id if photo else None
            },
            'user': {
                'id': current_user.id,
                'username': current_user.username
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Diagnostic test error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/voice-memos/<int:memo_id>/audio', methods=['GET'])
@csrf.exempt
@token_required
def download_voice_memo(current_user, memo_id):
    """Download voice memo audio file"""
    from photovault.models import VoiceMemo
    from flask import send_file
    
    try:
        logger.info(f"🔊 Downloading voice memo {memo_id} for user {current_user.id}")
        
        # Verify ownership
        memo = VoiceMemo.query.filter_by(id=memo_id, user_id=current_user.id).first()
        if not memo:
            logger.warning(f"❌ Voice memo {memo_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Voice memo not found'}), 404
        
        # Check file exists
        if not os.path.exists(memo.file_path):
            logger.error(f"❌ Audio file not found: {memo.file_path}")
            return jsonify({'success': False, 'error': 'Audio file not found'}), 404
        
        # Determine MIME type
        mimetype_map = {
            '.m4a': 'audio/m4a',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.aac': 'audio/aac'
        }
        file_ext = os.path.splitext(memo.filename)[1].lower()
        mimetype = mimetype_map.get(file_ext, 'audio/mpeg')
        
        logger.info(f"✅ Sending audio file: {memo.filename} ({mimetype})")
        
        return send_file(
            memo.file_path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=memo.original_name
        )
        
    except Exception as e:
        logger.error(f"❌ Download error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/voice-memos/<int:memo_id>', methods=['DELETE'])
@csrf.exempt
@token_required
def delete_voice_memo(current_user, memo_id):
    """Delete a voice memo"""
    from photovault.models import VoiceMemo
    
    try:
        logger.info(f"🗑️ Deleting voice memo {memo_id} for user {current_user.id}")
        
        # Verify ownership
        memo = VoiceMemo.query.filter_by(id=memo_id, user_id=current_user.id).first()
        if not memo:
            logger.warning(f"❌ Voice memo {memo_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Voice memo not found'}), 404
        
        # Delete audio file
        if os.path.exists(memo.file_path):
            try:
                os.remove(memo.file_path)
                logger.info(f"🗑️ Deleted file: {memo.file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Could not delete file: {str(e)}")
        
        # Delete database record
        db.session.delete(memo)
        db.session.commit()
        
        logger.info(f"✅ Voice memo {memo_id} deleted")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo deleted'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Delete error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PHOTO COMMENTS API ENDPOINTS
# ============================================================================

@mobile_api_bp.route('/photos/<int:photo_id>/comments', methods=['GET'])
@csrf.exempt
@token_required
def get_photo_comments(current_user, photo_id):
    """Get all comments for a photo"""
    try:
        logger.info(f"💬 Getting comments for photo {photo_id}")
        
        # Verify photo exists and user has access
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.warning(f"❌ Photo {photo_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # Get all comments for this photo
        comments = PhotoComment.query.filter_by(photo_id=photo_id).order_by(PhotoComment.created_at.desc()).all()
        
        comments_data = [{
            'id': comment.id,
            'comment_text': comment.comment_text,
            'user_id': comment.user_id,
            'username': comment.user.username,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat()
        } for comment in comments]
        
        logger.info(f"✅ Retrieved {len(comments_data)} comments for photo {photo_id}")
        
        return jsonify({
            'success': True,
            'photo_id': photo_id,
            'comments': comments_data,
            'total': len(comments_data)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting comments: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/photos/<int:photo_id>/comments', methods=['POST'])
@csrf.exempt
@token_required
def add_photo_comment(current_user, photo_id):
    """Add a new comment to a photo"""
    try:
        logger.info(f"💬 Adding comment to photo {photo_id}")
        
        # Verify photo exists and user has access
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.warning(f"❌ Photo {photo_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # Get comment text from request
        data = request.get_json()
        comment_text = data.get('comment_text', '').strip()
        
        if not comment_text:
            return jsonify({'success': False, 'error': 'Comment text is required'}), 400
        
        # Create new comment
        new_comment = PhotoComment()
        new_comment.photo_id = photo_id
        new_comment.user_id = current_user.id
        new_comment.comment_text = comment_text
        
        db.session.add(new_comment)
        db.session.commit()
        
        logger.info(f"✅ Comment {new_comment.id} added to photo {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': new_comment.id,
                'comment_text': new_comment.comment_text,
                'user_id': new_comment.user_id,
                'username': current_user.username,
                'created_at': new_comment.created_at.isoformat(),
                'updated_at': new_comment.updated_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error adding comment: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@csrf.exempt
@token_required
def delete_photo_comment(current_user, comment_id):
    """Delete a comment"""
    try:
        logger.info(f"🗑️ Deleting comment {comment_id} for user {current_user.id}")
        
        # Verify ownership
        comment = PhotoComment.query.filter_by(id=comment_id, user_id=current_user.id).first()
        if not comment:
            logger.warning(f"❌ Comment {comment_id} not found for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Comment not found'}), 404
        
        # Delete database record
        db.session.delete(comment)
        db.session.commit()
        
        logger.info(f"✅ Comment {comment_id} deleted")
        
        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Delete error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/photos/<int:photo_id>', methods=['DELETE'])
@csrf.exempt
@token_required
def delete_photo(current_user, photo_id):
    """Delete a photo for mobile app"""
    try:
        logger.info(f"🗑️ DELETE REQUEST: photo_id={photo_id}, user={current_user.username}")
        
        # Get the photo and verify ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            logger.warning(f"❌ Photo {photo_id} not found or access denied for user {current_user.id}")
            return jsonify({'success': False, 'error': 'Photo not found or access denied'}), 404
        
        logger.info(f"📸 Found photo: filename={photo.filename}, file_path={photo.file_path}")
        
        # Delete associated files
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        files_deleted = []
        
        # Delete original file
        if photo.file_path:
            if os.path.isabs(photo.file_path):
                full_path = photo.file_path
            else:
                full_path = os.path.join(user_upload_dir, photo.file_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                files_deleted.append('original')
                logger.info(f"🗑️ Deleted original file: {full_path}")
        
        # Delete thumbnail
        if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
            os.remove(photo.thumbnail_path)
            files_deleted.append('thumbnail')
            logger.info(f"🗑️ Deleted thumbnail: {photo.thumbnail_path}")
        
        # Delete edited version if exists
        if photo.edited_filename:
            edited_path = os.path.join(user_upload_dir, photo.edited_filename)
            if os.path.exists(edited_path):
                os.remove(edited_path)
                files_deleted.append('edited')
                logger.info(f"🗑️ Deleted edited file: {edited_path}")
        
        # Delete associated data
        from photovault.models import VoiceMemo, VaultPhoto, PhotoPerson, PhotoComment
        
        # Delete voice memos
        voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).all()
        for memo in voice_memos:
            if memo.file_path and os.path.exists(memo.file_path):
                os.remove(memo.file_path)
            db.session.delete(memo)
        
        # Delete vault photo associations
        vault_photos = VaultPhoto.query.filter_by(photo_id=photo.id).all()
        for vault_photo in vault_photos:
            db.session.delete(vault_photo)
        
        # Delete photo-person tags
        photo_people = PhotoPerson.query.filter_by(photo_id=photo.id).all()
        for photo_person in photo_people:
            db.session.delete(photo_person)
        
        # Delete comments
        comments = PhotoComment.query.filter_by(photo_id=photo.id).all()
        for comment in comments:
            db.session.delete(comment)
        
        # Delete photo record
        db.session.delete(photo)
        db.session.commit()
        
        logger.info(f"✅ Photo {photo_id} deleted successfully (files: {files_deleted})")
        
        return jsonify({
            'success': True,
            'message': 'Photo deleted successfully',
            'files_deleted': files_deleted
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"💥 DELETE ERROR for photo {photo_id}: {str(e)}")
        logger.error(f"📋 TRACEBACK:\n{error_trace}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Delete failed: {str(e)}'}), 500


@mobile_api_bp.route('/photos/bulk-delete-mobile', methods=['POST'])
@csrf.exempt
@token_required
def bulk_delete_photos_mobile(current_user):
    """Bulk delete multiple photos for mobile app"""
    try:
        data = request.get_json()
        if not data or 'photo_ids' not in data:
            return jsonify({'success': False, 'error': 'photo_ids required'}), 400
        
        photo_ids = data.get('photo_ids', [])
        
        if not isinstance(photo_ids, list) or len(photo_ids) == 0:
            return jsonify({'success': False, 'error': 'photo_ids must be a non-empty array'}), 400
        
        logger.info(f"🗑️ BULK DELETE REQUEST: {len(photo_ids)} photos, user={current_user.username}")
        logger.info(f"📋 Photo IDs: {photo_ids}")
        
        deleted_count = 0
        failed_count = 0
        errors = []
        
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        
        for photo_id in photo_ids:
            try:
                # Get the photo and verify ownership
                photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
                if not photo:
                    logger.warning(f"❌ Photo {photo_id} not found or access denied")
                    failed_count += 1
                    errors.append(f"Photo {photo_id} not found")
                    continue
                
                # Delete associated files
                files_to_delete = []
                
                # Delete original file
                if photo.file_path:
                    if os.path.isabs(photo.file_path):
                        full_path = photo.file_path
                    else:
                        full_path = os.path.join(user_upload_dir, photo.file_path)
                    
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        files_to_delete.append('original')
                
                # Delete thumbnail
                if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
                    os.remove(photo.thumbnail_path)
                    files_to_delete.append('thumbnail')
                
                # Delete edited version if exists
                if photo.edited_filename:
                    edited_path = os.path.join(user_upload_dir, photo.edited_filename)
                    if os.path.exists(edited_path):
                        os.remove(edited_path)
                        files_to_delete.append('edited')
                
                # Delete associated data
                from photovault.models import VoiceMemo, VaultPhoto, PhotoPerson, PhotoComment
                
                # Delete voice memos
                voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).all()
                for memo in voice_memos:
                    if memo.file_path and os.path.exists(memo.file_path):
                        os.remove(memo.file_path)
                    db.session.delete(memo)
                
                # Delete vault photo associations
                vault_photos = VaultPhoto.query.filter_by(photo_id=photo.id).all()
                for vault_photo in vault_photos:
                    db.session.delete(vault_photo)
                
                # Delete photo-person tags
                photo_people = PhotoPerson.query.filter_by(photo_id=photo.id).all()
                for photo_person in photo_people:
                    db.session.delete(photo_person)
                
                # Delete comments
                comments = PhotoComment.query.filter_by(photo_id=photo.id).all()
                for comment in comments:
                    db.session.delete(comment)
                
                # Delete photo record
                db.session.delete(photo)
                deleted_count += 1
                
                logger.info(f"✅ Photo {photo_id} deleted (files: {files_to_delete})")
                
            except Exception as e:
                logger.error(f"❌ Error deleting photo {photo_id}: {str(e)}")
                failed_count += 1
                errors.append(f"Photo {photo_id}: {str(e)}")
                continue
        
        # Commit all deletions
        db.session.commit()
        
        logger.info(f"🎯 BULK DELETE COMPLETE: deleted={deleted_count}, failed={failed_count}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} photos',
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"💥 BULK DELETE ERROR: {str(e)}")
        logger.error(f"📋 TRACEBACK:\n{error_trace}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Bulk delete failed: {str(e)}'}), 500

# Damage Repair Endpoints for Mobile
@mobile_api_bp.route('/photos/<int:photo_id>/detect-damage', methods=['GET'])
@csrf.exempt
@token_required
def detect_damage_mobile(current_user, photo_id):
    """Detect damage in photo using AI (mobile endpoint)"""
    try:
        photo = Photo.query.get(photo_id)
        if not photo or photo.user_id != current_user.id:
            return jsonify({'error': 'Photo not found'}), 404
        
        from photovault.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service not available'
            }), 503
        
        # Get storage path
        from photovault.utils.app_storage import app_storage
        if app_storage.is_available() and photo.file_path.startswith('uploads/'):
            photo_path = app_storage.download_to_temp(photo.file_path)
        else:
            photo_path = photo.file_path
        
        # Detect damage
        damage_info = ai_service.detect_damage(photo_path)
        
        return jsonify({
            'success': True,
            'photo_id': photo_id,
            'has_damage': damage_info.get('has_damage', False),
            'damage_types': damage_info.get('damage_types', []),
            'severity': damage_info.get('severity', 'unknown'),
            'repair_recommendations': damage_info.get('repair_recommendations', [])
        })
        
    except Exception as e:
        logger.error(f"Damage detection failed for photo {photo_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mobile_api_bp.route('/photos/<int:photo_id>/repair', methods=['POST'])
@csrf.exempt
@token_required
def repair_damage_mobile(current_user, photo_id):
    """Apply damage repair to photo (mobile endpoint)"""
    try:
        photo = Photo.query.get(photo_id)
        if not photo or photo.user_id != current_user.id:
            return jsonify({'error': 'Photo not found'}), 404
        
        # Get repair type
        data = request.get_json() or {}
        repair_type = data.get('type', 'comprehensive')  # 'scratches', 'stains', 'cracks', 'comprehensive', or 'ai'
        sensitivity = int(data.get('sensitivity', 5))
        
        # Handle AI restoration
        if repair_type == 'ai':
            from photovault.utils.ai_restoration import ai_restoration as ai_service
            from photovault.utils.quota_manager import check_ai_quota, increment_ai_usage
            
            # Check AI quota before processing
            has_quota, quota_info, error_message = check_ai_quota(current_user)
            if not has_quota:
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'quota_info': {
                        'quota_limit': quota_info['quota_limit'],
                        'quota_used': quota_info['quota_used'],
                        'quota_remaining': quota_info['quota_remaining'],
                        'reset_date': quota_info['reset_date'].isoformat() if quota_info['reset_date'] else None,
                        'plan_name': quota_info['plan_name']
                    }
                }), 429  # 429 Too Many Requests
            
            if not ai_service.enabled:
                return jsonify({
                    'success': False,
                    'error': 'AI restoration not available. Please configure REPLICATE_API_TOKEN'
                }), 503
            
            # Get AI parameters
            model = data.get('model', 'codeformer')  # 'gfpgan' or 'codeformer'
            quality = data.get('quality', 'balanced')  # 'fast', 'balanced', 'quality', 'maximum'
            fidelity = float(data.get('fidelity', 0.5))  # CodeFormer only
            
            from photovault.utils.app_storage import app_storage
            from datetime import datetime
            import random
            
            # Get original file path
            if app_storage.is_available() and photo.file_path.startswith('uploads/'):
                original_path = app_storage.download_to_temp(photo.file_path)
            else:
                original_path = photo.file_path
            
            # Generate filename for AI restored version
            from werkzeug.utils import secure_filename as sanitize_name
            date = datetime.now().strftime('%Y%m%d')
            random_number = random.randint(100000, 999999)
            safe_username = sanitize_name(current_user.username)
            ai_filename = f"{safe_username}.{date}.ai_{model}.{random_number}.jpg"
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
            user_upload_folder = os.path.join(upload_folder, str(current_user.id))
            os.makedirs(user_upload_folder, exist_ok=True)
            temp_ai_filepath = os.path.join(user_upload_folder, ai_filename)
            
            # Perform AI restoration
            logger.info(f"Starting AI restoration for mobile photo {photo_id} with model={model}, quality={quality}")
            
            if model == 'gfpgan':
                # Map quality presets to GFPGAN parameters
                scale_map = {'fast': 1, 'balanced': 2, 'quality': 2, 'maximum': 4}
                version_map = {'fast': 'v1.3', 'balanced': 'v1.4', 'quality': 'v1.4', 'maximum': 'v1.4'}
                
                output_path, stats = ai_service.restore_with_gfpgan(
                    original_path,
                    temp_ai_filepath,
                    scale=scale_map.get(quality, 2),
                    version=version_map.get(quality, 'v1.4')
                )
            elif model == 'codeformer':
                # Map quality presets to CodeFormer parameters
                if quality == 'fast':
                    upscale, bg_enhance, face_up = 1, False, False
                elif quality == 'balanced':
                    upscale, bg_enhance, face_up = 2, False, True
                elif quality == 'quality':
                    upscale, bg_enhance, face_up = 2, True, True
                else:  # maximum
                    upscale, bg_enhance, face_up = 4, True, True
                
                output_path, stats = ai_service.restore_with_codeformer(
                    original_path,
                    temp_ai_filepath,
                    fidelity=fidelity,
                    upscale=upscale,
                    background_enhance=bg_enhance,
                    face_upsample=face_up
                )
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unknown AI model: {model}. Use "gfpgan" or "codeformer"'
                }), 400
            
            # Upload to storage if available
            ai_filepath = temp_ai_filepath
            if app_storage.is_available():
                import io
                with open(temp_ai_filepath, 'rb') as f:
                    img_bytes = io.BytesIO(f.read())
                    success, storage_path = app_storage.upload_file(
                        img_bytes, ai_filename, str(current_user.id)
                    )
                    if success:
                        ai_filepath = storage_path
                        try:
                            os.remove(temp_ai_filepath)
                        except:
                            pass
            
            # Update photo with AI restored version
            photo.edited_filename = ai_filename
            photo.edited_path = ai_filepath
            photo.enhancement_metadata = {
                'ai_restoration': {
                    'model': model,
                    'quality': quality,
                    'fidelity': fidelity,
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats
                }
            }
            db.session.commit()
            
            # Increment AI quota usage (atomic operation)
            success, new_usage, usage_error = increment_ai_usage(current_user)
            if not success:
                logger.error(f"Quota increment failed after restoration: {usage_error}")
            else:
                logger.info(f"Photo {photo_id} AI restoration completed successfully (model: {model}, quota: {new_usage}/{quota_info['quota_limit']})")
            
            return jsonify({
                'success': True,
                'photo_id': photo.id,
                'repaired_url': f'/uploads/{current_user.id}/{ai_filename}',
                'repair_type': 'ai',
                'model': model,
                'quality': quality,
                'stats': stats,
                'message': f'AI restoration completed successfully using {model.upper()}'
            })
        
        # Original OpenCV repair types below
        sensitivity = int(data.get('sensitivity', 5))
        
        from photovault.utils.damage_repair import damage_repair
        from photovault.utils.app_storage import app_storage
        from datetime import datetime
        import random
        
        # Get original file path
        if app_storage.is_available() and photo.file_path.startswith('uploads/'):
            original_path = app_storage.download_to_temp(photo.file_path)
        else:
            original_path = photo.file_path
        
        # Generate filename for repaired version
        from werkzeug.utils import secure_filename as sanitize_name
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)
        safe_username = sanitize_name(current_user.username)
        repaired_filename = f"{safe_username}.{date}.repaired.{random_number}.jpg"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_upload_folder, exist_ok=True)
        temp_repaired_filepath = os.path.join(user_upload_folder, repaired_filename)
        
        # Apply repair based on type
        if repair_type == 'scratches':
            output_path, stats = damage_repair.remove_scratches_and_dust(
                original_path, temp_repaired_filepath, sensitivity
            )
        elif repair_type == 'stains':
            output_path, stats = damage_repair.remove_stains(
                original_path, temp_repaired_filepath, float(data.get('strength', 1.5))
            )
        elif repair_type == 'cracks':
            output_path, stats = damage_repair.repair_cracks(
                original_path, temp_repaired_filepath, sensitivity
            )
        else:  # comprehensive
            output_path, stats = damage_repair.comprehensive_repair(
                original_path, temp_repaired_filepath, sensitivity, sensitivity, 1.5
            )
        
        # Upload to storage if available
        repaired_filepath = temp_repaired_filepath
        if app_storage.is_available():
            import io
            with open(temp_repaired_filepath, 'rb') as f:
                img_bytes = io.BytesIO(f.read())
                success, storage_path = app_storage.upload_file(
                    img_bytes, repaired_filename, str(current_user.id)
                )
                if success:
                    repaired_filepath = storage_path
                    try:
                        os.remove(temp_repaired_filepath)
                    except:
                        pass
        
        # Update photo with repaired version
        photo.edited_filename = repaired_filename
        photo.edited_path = repaired_filepath
        photo.enhancement_metadata = {
            'damage_repair': {
                'type': repair_type,
                'sensitivity': sensitivity,
                'timestamp': datetime.now().isoformat(),
                'stats': stats
            }
        }
        db.session.commit()
        
        logger.info(f"Photo {photo_id} damage repaired successfully (type: {repair_type})")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'repaired_url': f'/uploads/{current_user.id}/{repaired_filename}',
            'repair_type': repair_type,
            'stats': stats,
            'message': f'{repair_type.capitalize()} repair completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Damage repair failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
