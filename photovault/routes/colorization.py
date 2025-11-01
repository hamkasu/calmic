"""
Colorization Routes for PhotoVault
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

API endpoints for AI-powered and traditional colorization
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from photovault.models import Photo
from photovault.extensions import db
from photovault.services.ai_service import get_ai_service
from photovault.utils.colorization import get_colorizer
from photovault.utils.subscription_enforcement import require_ai_quota, log_ai_enhancement

logger = logging.getLogger(__name__)

colorization_bp = Blueprint('colorization', __name__, url_prefix='/api/colorization')


@colorization_bp.route('/colorize', methods=['POST'])
@login_required
@require_ai_quota()
def colorize_photo():
    """
    Colorize a photo using DNN-based colorization
    
    Request JSON:
        {
            "photo_id": int,  # Photo ID to colorize
            "method": "auto" | "dnn" | "basic"  # Optional, default "auto"
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "edited_url": str,
            "method": str,
            "message": str
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        method = data.get('method', 'auto')
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file paths
        original_path = photo.file_path
        
        if not os.path.exists(original_path):
            return jsonify({
                'success': False,
                'error': 'Original photo file not found'
            }), 404
        
        # Generate edited filename using username.date.col.randomnumber format
        from werkzeug.utils import secure_filename as sanitize_name
        from datetime import datetime
        from photovault.services.app_storage_service import app_storage
        import random
        import io
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)  # 6-digit random number
        safe_username = sanitize_name(current_user.username)
        edited_filename = f"{safe_username}.{date}.col.{random_number}.jpg"
        
        # Safety check: Ensure edited filename is different from original
        # This prevents loading the same file twice in comparison view
        attempts = 0
        while edited_filename == photo.filename and attempts < 10:
            random_number = random.randint(100000, 999999)
            edited_filename = f"{safe_username}.{date}.col.{random_number}.jpg"
            attempts += 1
        
        if edited_filename == photo.filename:
            logger.error(f"Failed to generate unique edited filename for photo {photo_id}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate unique filename for edited version'
            }), 500
        
        logger.info(f"Colorizing photo {photo_id}: original='{photo.filename}', edited='{edited_filename}'")
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_upload_folder, exist_ok=True)
        temp_edited_path = os.path.join(user_upload_folder, edited_filename)
        
        # Perform colorization (saves to temp local)
        colorizer = get_colorizer()
        result_path, method_used = colorizer.colorize_image(
            original_path,
            temp_edited_path,
            method=method
        )
        
        # Upload to App Storage for persistence
        edited_path = temp_edited_path  # Default to local
        if app_storage.is_available():
            with open(temp_edited_path, 'rb') as f:
                img_bytes = io.BytesIO(f.read())
                success, storage_path = app_storage.upload_file(img_bytes, edited_filename, str(current_user.id))
                if success:
                    edited_path = storage_path
                    logger.info(f"Colorized photo uploaded to App Storage: {storage_path}")
                    # Clean up temp file
                    try:
                        os.remove(temp_edited_path)
                    except:
                        pass
                else:
                    logger.warning(f"App Storage upload failed, keeping local: {storage_path}")
        
        # Update database with edited version
        photo.edited_filename = edited_filename
        photo.edited_path = edited_path
        photo.enhancement_metadata = {
            'colorization': {
                'method': method_used,
                'timestamp': str(datetime.now())
            }
        }
        db.session.commit()
        
        # Log AI enhancement usage for quota tracking
        log_ai_enhancement(current_user.id, 'colorization', photo.id)
        
        logger.info(f"Photo {photo_id} colorized successfully using {method_used}")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'edited_url': f'/uploads/{current_user.id}/{edited_filename}',
            'method': method_used,
            'message': f'Photo colorized successfully using {method_used} method'
        })
        
    except Exception as e:
        logger.error(f"Colorization failed: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@colorization_bp.route('/colorize-ai', methods=['POST'])
@login_required
@require_ai_quota()
def colorize_photo_ai():
    """
    Colorize a photo using AI-powered colorization
    
    Request JSON:
        {
            "photo_id": int  # Photo ID to colorize
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "edited_url": str,
            "ai_guidance": str,
            "method": str,
            "message": str
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        
        # Check if AI service is available
        ai_service = get_ai_service()
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service not available. Please configure GEMINI_API_KEY.'
            }), 503
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file paths
        original_path = photo.file_path
        
        if not os.path.exists(original_path):
            return jsonify({
                'success': False,
                'error': 'Original photo file not found'
            }), 404
        
        # Generate edited filename using username.date.col.randomnumber format
        from werkzeug.utils import secure_filename as sanitize_name
        from datetime import datetime
        from photovault.services.app_storage_service import app_storage
        import random
        import io
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)  # 6-digit random number
        safe_username = sanitize_name(current_user.username)
        edited_filename = f"{safe_username}.{date}.col.{random_number}.jpg"
        
        # Safety check: Ensure edited filename is different from original
        # This prevents loading the same file twice in comparison view
        attempts = 0
        while edited_filename == photo.filename and attempts < 10:
            random_number = random.randint(100000, 999999)
            edited_filename = f"{safe_username}.{date}.col.{random_number}.jpg"
            attempts += 1
        
        if edited_filename == photo.filename:
            logger.error(f"Failed to generate unique edited filename for photo {photo_id}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate unique filename for edited version'
            }), 500
        
        logger.info(f"Colorizing photo {photo_id}: original='{photo.filename}', edited='{edited_filename}'")
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_upload_folder, exist_ok=True)
        temp_edited_path = os.path.join(user_upload_folder, edited_filename)
        
        # Perform AI colorization (saves to temp local)
        result_path, metadata = ai_service.colorize_image_ai(
            original_path,
            temp_edited_path
        )
        
        # Upload to App Storage for persistence
        edited_path = temp_edited_path  # Default to local
        if app_storage.is_available():
            with open(temp_edited_path, 'rb') as f:
                img_bytes = io.BytesIO(f.read())
                success, storage_path = app_storage.upload_file(img_bytes, edited_filename, str(current_user.id))
                if success:
                    edited_path = storage_path
                    logger.info(f"AI colorized photo uploaded to App Storage: {storage_path}")
                    # Clean up temp file
                    try:
                        os.remove(temp_edited_path)
                    except:
                        pass
                else:
                    logger.warning(f"App Storage upload failed, keeping local: {storage_path}")
        
        # Update database with edited version
        photo.edited_filename = edited_filename
        photo.edited_path = edited_path
        photo.enhancement_metadata = {
            'colorization': {
                'method': metadata['method'],
                'ai_guidance': metadata['ai_guidance'],
                'model': metadata['model'],
                'timestamp': str(datetime.now())
            }
        }
        db.session.commit()
        
        logger.info(f"Photo {photo_id} AI-colorized successfully")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'edited_url': f'/uploads/{current_user.id}/{edited_filename}',
            'ai_guidance': metadata['ai_guidance'],
            'method': metadata['method'],
            'message': 'Photo colorized successfully using AI'
        })
        
    except Exception as e:
        logger.error(f"AI colorization failed: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@colorization_bp.route('/enhance', methods=['POST'])
@login_required
def enhance_photo():
    """
    Apply image enhancement to a photo (web endpoint)
    
    Request JSON:
        {
            "photo_id": int,  # Photo ID to enhance
            "settings": {}    # Enhancement settings
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "enhanced_url": str,
            "message": str
        }
    """
    try:
        from photovault.utils.image_enhancement import enhancer
        import random
        
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        settings = data.get('settings', {})
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file paths
        original_path = photo.file_path
        
        if not os.path.exists(original_path):
            return jsonify({
                'success': False,
                'error': 'Original photo file not found'
            }), 404
        
        # Generate enhanced filename
        from werkzeug.utils import secure_filename as sanitize_name
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)
        safe_username = sanitize_name(current_user.username)
        enhanced_filename = f"{safe_username}.{date}.enh.{random_number}.jpg"
        
        logger.info(f"Enhancing photo {photo_id}: original='{photo.filename}', enhanced='{enhanced_filename}'")
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_upload_folder, exist_ok=True)
        enhanced_filepath = os.path.join(user_upload_folder, enhanced_filename)
        
        # Apply enhancements
        output_path, applied_settings = enhancer.auto_enhance_photo(
            original_path,
            enhanced_filepath,
            settings
        )
        
        # Update database with enhanced version
        photo.edited_filename = enhanced_filename
        photo.edited_path = enhanced_filepath
        photo.enhancement_metadata = {
            'enhancement': {
                'settings': applied_settings,
                'timestamp': str(datetime.now())
            }
        }
        db.session.commit()
        
        logger.info(f"Photo {photo_id} enhanced successfully")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'enhanced_url': f'/uploads/{current_user.id}/{enhanced_filename}',
            'settings_applied': applied_settings,
            'message': 'Photo enhanced successfully'
        })
        
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@colorization_bp.route('/sharpen', methods=['POST'])
@login_required
def sharpen_photo():
    """
    Apply image sharpening to a photo (web endpoint)
    
    Request JSON:
        {
            "photo_id": int,     # Photo ID to sharpen
            "radius": float,     # Sharpening radius (optional, default: 2.0)
            "amount": float,     # Sharpening amount (optional, default: 1.5)
            "threshold": int,    # Sharpening threshold (optional, default: 3)
            "method": str        # Sharpening method (optional, default: 'unsharp')
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "enhanced_url": str,
            "message": str
        }
    """
    try:
        from photovault.utils.image_enhancement import enhancer
        import random
        
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        radius = data.get('radius', 2.0)
        amount = data.get('amount', 1.5)
        threshold = data.get('threshold', 3)
        method = data.get('method', 'unsharp')
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file paths
        original_path = photo.file_path
        
        if not os.path.exists(original_path):
            return jsonify({
                'success': False,
                'error': 'Original photo file not found'
            }), 404
        
        # Generate sharpened filename
        from werkzeug.utils import secure_filename as sanitize_name
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)
        safe_username = sanitize_name(current_user.username)
        sharpened_filename = f"{safe_username}.{date}.sharp.{random_number}.jpg"
        
        logger.info(f"Sharpening photo {photo_id}: original='{photo.filename}', sharpened='{sharpened_filename}'")
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_upload_folder, exist_ok=True)
        sharpened_filepath = os.path.join(user_upload_folder, sharpened_filename)
        
        # Apply sharpening
        output_path = enhancer.sharpen_image(
            original_path,
            sharpened_filepath,
            radius=radius,
            amount=amount,
            threshold=threshold,
            method=method
        )
        
        # Update database with sharpened version
        photo.edited_filename = sharpened_filename
        photo.edited_path = sharpened_filepath
        photo.enhancement_metadata = {
            'sharpening': {
                'radius': radius,
                'amount': amount,
                'threshold': threshold,
                'method': method,
                'timestamp': str(datetime.now())
            }
        }
        db.session.commit()
        
        logger.info(f"Photo {photo_id} sharpened successfully")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'enhanced_url': f'/uploads/{current_user.id}/{sharpened_filename}',
            'message': 'Photo sharpened successfully'
        })
        
    except Exception as e:
        logger.error(f"Sharpening failed: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@colorization_bp.route('/enhance-analyze', methods=['POST'])
@login_required
def analyze_enhancement():
    """
    Analyze a photo and provide AI-powered enhancement suggestions
    
    Request JSON:
        {
            "photo_id": int  # Photo ID to analyze
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "analysis": {
                "needs_enhancement": bool,
                "suggestions": [str],
                "priority": str,
                "issues": [str]
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        
        # Check if AI service is available
        ai_service = get_ai_service()
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service not available. Please configure GEMINI_API_KEY.'
            }), 503
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file path
        photo_path = photo.file_path
        
        if not os.path.exists(photo_path):
            return jsonify({
                'success': False,
                'error': 'Photo file not found'
            }), 404
        
        # Perform AI analysis
        analysis = ai_service.enhance_image_ai(photo_path)
        
        logger.info(f"Photo {photo_id} analyzed for enhancement")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Enhancement analysis failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@colorization_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_photo():
    """
    Analyze photo content using AI
    
    Request JSON:
        {
            "photo_id": int  # Photo ID to analyze
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "analysis": str,
            "message": str
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        
        # Check if AI service is available
        ai_service = get_ai_service()
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service not available. Please configure GEMINI_API_KEY.'
            }), 503
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file path
        photo_path = photo.file_path
        
        if not os.path.exists(photo_path):
            return jsonify({
                'success': False,
                'error': 'Photo file not found'
            }), 404
        
        # Perform AI analysis
        analysis = ai_service.analyze_image(photo_path)
        
        # Optionally update photo description
        if not photo.description or len(photo.description) < 50:
            photo.description = analysis
            db.session.commit()
        
        logger.info(f"Photo {photo_id} content analyzed")
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'analysis': analysis,
            'message': 'Photo analyzed successfully'
        })
        
    except Exception as e:
        logger.error(f"Photo analysis failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@colorization_bp.route('/check-grayscale', methods=['POST'])
@login_required
def check_grayscale():
    """
    Check if a photo is grayscale/black and white
    
    Request JSON:
        {
            "photo_id": int  # Photo ID to check
        }
    
    Returns:
        {
            "success": bool,
            "photo_id": int,
            "is_grayscale": bool
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'photo_id' not in data:
            return jsonify({
                'success': False,
                'error': 'photo_id is required'
            }), 400
        
        photo_id = data['photo_id']
        
        # Get photo from database
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        
        if not photo:
            return jsonify({
                'success': False,
                'error': 'Photo not found or unauthorized'
            }), 404
        
        # Get file path
        photo_path = photo.file_path
        
        if not os.path.exists(photo_path):
            return jsonify({
                'success': False,
                'error': 'Photo file not found'
            }), 404
        
        # Check if grayscale
        colorizer = get_colorizer()
        is_grayscale = colorizer.is_grayscale(photo_path)
        
        return jsonify({
            'success': True,
            'photo_id': photo.id,
            'is_grayscale': is_grayscale
        })
        
    except Exception as e:
        logger.error(f"Grayscale check failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


