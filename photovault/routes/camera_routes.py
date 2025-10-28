"""
PhotoVault Camera Routes
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Enhanced camera functionality with full screen + landscape support
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from PIL import Image
import io

# Create camera blueprint with URL prefix to avoid conflicts
camera_bp = Blueprint('camera', __name__, url_prefix='/camera')

@camera_bp.route('/')
@login_required
def camera():
    """Render the enhanced camera page with full screen support"""
    return render_template('camera.html', 
                         title='Camera',
                         user=current_user)

@camera_bp.route('/upload', methods=['POST'])
@login_required  
def upload_image():
    """Handle image uploads from camera capture"""
    try:
        # Check if image was sent
        if 'image' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No image data received'
            }), 400

        file = request.files['image']
        
        # Validate file
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': 'Invalid file type'
            }), 400

        # Get capture mode information
        quadrant = request.form.get('quadrant', '')
        sequence_number = request.form.get('sequence_number', '')
        
        # Generate secure filename in format: <username>.<date>.<random number>.<ext>
        import random
        from werkzeug.utils import secure_filename as sanitize_name
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)  # 6-digit random number
        file_extension = get_file_extension(file.filename)
        safe_username = sanitize_name(current_user.username)
        
        # Use standard naming format for all camera uploads
        filename = f"{safe_username}.{date}.{random_number}{file_extension}"
        
        # Ensure upload directory exists
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(upload_path, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(upload_path, filename)
        
        # Process and save image
        success, message = process_and_save_image(file, file_path)
        
        if success:
            # Save to database (adjust based on your models structure)
            try:
                # Import your models - adjust path as needed
                from photovault.models import Photo, db
                
                # Use the new filename format for display
                photo = Photo()
                photo.filename = filename
                photo.original_name = filename  # Use the new format for display
                photo.user_id = current_user.id
                photo.file_path = file_path
                photo.created_at = datetime.utcnow()
                photo.updated_at = datetime.utcnow()
                photo.file_size = os.path.getsize(file_path)
                photo.upload_source = 'camera'  # Mark as camera capture
                # Note: quadrant info is preserved in filename and original_name
                
                db.session.add(photo)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Photo captured and saved successfully!',
                    'filename': filename,
                    'photo_id': photo.id
                })
                
            except Exception as db_error:
                current_app.logger.error(f"Database error: {str(db_error)}")
                # File was saved but DB failed
                return jsonify({
                    'success': True,
                    'message': 'Photo saved but database error occurred',
                    'filename': filename,
                    'warning': 'Database sync issue'
                })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error during upload'
        }), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get file extension with dot"""
    if '.' in filename:
        return '.' + filename.rsplit('.', 1)[1].lower()
    return '.jpg'  # Default to jpg

def process_and_save_image(file, file_path):
    """Process and save image with optimization"""
    try:
        # Read image data
        image_data = file.read()
        file.seek(0)  # Reset file pointer
        
        # Open with PIL for processing
        image = Image.open(io.BytesIO(image_data))
        
        # Auto-rotate based on EXIF data
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(274, 1)  # Orientation tag
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Optimize file size while maintaining quality
        max_size = (2048, 2048)  # Max dimensions
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Determine format from file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        image_format = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.gif': 'GIF',
            '.bmp': 'BMP',
            '.webp': 'WEBP'
        }.get(file_ext, 'JPEG')
        
        # Save optimized image with correct format
        save_kwargs = {
            'format': image_format,
            'optimize': True
        }
        
        # Add quality parameter for JPEG format
        if image_format == 'JPEG':
            save_kwargs['quality'] = 85
        
        image.save(file_path, **save_kwargs)
        
        current_app.logger.info(f"Image saved: {file_path}")
        return True, "Image processed and saved successfully"
        
    except Exception as e:
        current_app.logger.error(f"Image processing error: {str(e)}")
        return False, f"Image processing failed: {str(e)}"

@camera_bp.route('/camera/settings')
@login_required
def camera_settings():
    """Camera settings and preferences"""
    return render_template('camera_settings.html',
                         title='Camera Settings',
                         user=current_user)

@camera_bp.route('/api/camera/check-support')
def check_camera_support():
    """API endpoint to check camera capabilities"""
    return jsonify({
        'server_support': True,
        'upload_max_size': current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024),
        'allowed_formats': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        'features': {
            'fullscreen': True,
            'orientation_lock': True,
            'high_resolution': True,
            'auto_upload': True
        }
    })