"""
PhotoVault Enhanced Upload Route
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Handles file uploads from both traditional file selection and camera capture
"""
import os
import uuid
import mimetypes
import random
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from flask import Blueprint, request, jsonify, current_app, session, url_for
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, CSRFError
from photovault.extensions import csrf
from PIL import Image
import logging

# Import your models
from photovault.models import Photo, Album, User, Person, PhotoPerson
from photovault.extensions import db

# Import face detection utilities
from photovault.utils.face_detection import detect_faces_in_photo
from photovault.utils.face_recognition import face_recognizer

# Import file handling utilities
from photovault.utils.file_handler import create_thumbnail

# Import photo detection utilities
from photovault.utils.photo_detection import detect_photos_in_image, extract_detected_photos

# Import JWT authentication utilities
from photovault.utils.jwt_auth import hybrid_auth

# Create blueprint
photo_bp = Blueprint('photo', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_IMAGE_DIMENSION = 4096  # Maximum width/height
THUMBNAIL_SIZE = (300, 300)

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_content(file_stream):
    """Validate that the file is actually a valid image"""
    try:
        with Image.open(file_stream) as img:
            img.verify()  # Verify image integrity
            return True
    except Exception as e:
        logger.warning(f"Image validation failed: {str(e)}")
        return False

def get_image_info(file_path):
    """Extract image metadata"""
    try:
        with Image.open(file_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': os.path.getsize(file_path)
            }
    except Exception as e:
        logger.error(f"Failed to get image info: {str(e)}")
        return None

def create_thumbnail_local(original_path, thumbnail_path):
    """Create thumbnail for uploaded image with specified path"""
    try:
        with Image.open(original_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Created thumbnail: {thumbnail_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}")
        return False

def process_uploaded_file(file, upload_source='file'):
    """Process and save uploaded file"""
    try:
        # Generate unique filename in new format: username.date.random6digits.ext
        import random
        from flask_login import current_user
        
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)  # 6-digit random number
        safe_username = secure_filename(current_user.username)
        
        safe_filename = f"{safe_username}.{date}.{random_number}.{file_extension}"
        original_name = safe_filename  # Use the new format for display
        
        # Create upload directories if they don't exist
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        thumbnails_dir = os.path.join(upload_dir, 'thumbnails')
        
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # File paths
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Save original file
        file.save(file_path)
        logger.info(f"Saved file: {file_path}")
        
        # Get image information
        image_info = get_image_info(file_path)
        if not image_info:
            raise ValueError("Invalid image file")
        
        # Check image dimensions
        if image_info['width'] > MAX_IMAGE_DIMENSION or image_info['height'] > MAX_IMAGE_DIMENSION:
            raise ValueError(f"Image dimensions too large. Max: {MAX_IMAGE_DIMENSION}px")
        
        # Save to database first to get photo.id (use flush to get ID without committing)
        from photovault.models import Photo
        photo = Photo()
        photo.user_id = current_user.id if current_user.is_authenticated else None
        photo.filename = safe_filename
        photo.original_name = original_name
        photo.file_path = file_path
        photo.file_size = image_info['size_bytes']
        photo.width = image_info['width']
        photo.height = image_info['height']
        photo.mime_type = mimetypes.guess_type(file_path)[0]
        photo.upload_source = upload_source
        db.session.add(photo)
        db.session.flush()  # Flush to get photo.id without committing transaction
        
        # Set unique_id after flush so we have the photo.id
        unique_id = str(photo.id)
        
        # Create thumbnail with ID-based naming (must be after flush to have photo.id)
        thumbnail_filename = f"thumb_{photo.id}_{safe_filename}"
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
        thumbnail_created = create_thumbnail_local(file_path, thumbnail_path)
        
        # Update photo with thumbnail path
        if thumbnail_created:
            photo.thumbnail_path = thumbnail_path
        
        # Generate blurhash and grid thumbnail for fast gallery loading
        from photovault.utils.image_optimization import process_image_for_gallery
        optimization_result = process_image_for_gallery(file_path, current_user.id, safe_filename)
        photo.blurhash = optimization_result.get('blurhash')
        photo.grid_thumbnail_path = optimization_result.get('grid_thumbnail_path')
        
        # Prepare file metadata (must be after commit to have photo.id)
        file_metadata = {
            'id': unique_id,
            'original_name': original_name,
            'filename': safe_filename,
            'thumbnail_filename': thumbnail_filename if thumbnail_created else None,
            'file_path': file_path,
            'thumbnail_path': thumbnail_path if thumbnail_created else None,
            'upload_source': upload_source,  # 'file' or 'camera'
            'upload_time': datetime.now(),
            'file_size': image_info['size_bytes'],
            'image_width': image_info['width'],
            'image_height': image_info['height'],
            'image_format': image_info['format'],
            'mime_type': mimetypes.guess_type(file_path)[0]
        }
        
        face_processing_result = {}
        try:
            from photovault.services.face_detection_service import face_detection_service
            
            face_processing_result = face_detection_service.process_and_tag_photo(photo, auto_tag=True)
            
            if face_processing_result.get('faces_detected', 0) > 0:
                logger.info(f"Face processing completed for {original_name}: "
                           f"{face_processing_result['faces_detected']} faces detected, "
                           f"{face_processing_result['tags_created']} auto-tagged")
        
        except Exception as face_detection_error:
            logger.warning(f"Face processing failed for {original_name}: {face_detection_error}")
            face_processing_result = {'error': str(face_detection_error)}
        
        file_metadata['faces_detected'] = face_processing_result.get('faces_detected', 0)
        file_metadata['tags_created'] = face_processing_result.get('tags_created', 0)
        
        # Commit the transaction only after all processing succeeds
        db.session.commit()
        
        logger.info(f"Successfully processed {upload_source} upload: {original_name}")
        return file_metadata
        
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {str(e)}")
        # Rollback database session
        db.session.rollback()
        # Clean up partial files
        file_path = locals().get('file_path')
        thumbnail_path = locals().get('thumbnail_path')
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except:
            pass
        raise

@photo_bp.route('/api/web/upload', methods=['POST'])
@login_required
def upload_photo():
    """
    Handle photo upload from web browser (file selection or camera capture)
    Supports both single and multiple file uploads with CSRF protection
    Note: Mobile uploads use /api/upload with JWT authentication
    """
    # CSRF protection is enabled for this route to prevent CSRF attacks
    
    try:
        logger.info(f"Upload request from user: {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        # Check if files were provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        files = request.files.getlist('file')
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        # Determine upload source from request or headers
        upload_source = request.form.get('source', 'file')
        user_agent = request.headers.get('User-Agent', '').lower()
        if 'mobile' in user_agent or upload_source == 'camera':
            upload_source = 'camera'
        
        logger.info(f"Processing {len(files)} file(s) from {upload_source}")
        
        # Process each file
        uploaded_files = []
        errors = []
        
        for file in files:
            if not file or file.filename == '':
                continue
                
            try:
                # Validate file extension
                if not allowed_file(file.filename):
                    errors.append(f"Invalid file type for {file.filename}")
                    continue
                
                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > MAX_FILE_SIZE:
                    size_mb = file_size / (1024 * 1024)
                    max_mb = MAX_FILE_SIZE / (1024 * 1024)
                    errors.append(f"File {file.filename} too large ({size_mb:.1f}MB, max: {max_mb}MB)")
                    continue
                
                # Validate image content
                if not validate_image_content(file):
                    errors.append(f"Invalid image content in {file.filename}")
                    continue
                
                # Reset file pointer after validation
                file.seek(0)
                
                # Process the file
                file_metadata = process_uploaded_file(file, upload_source)
                uploaded_files.append(file_metadata)
                
            except ValueError as e:
                errors.append(f"Error processing {file.filename}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
                errors.append(f"Failed to process {file.filename}")
                continue
        
        # Prepare response
        if uploaded_files:
            response_data = {
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'uploaded_files': len(uploaded_files),
                'files': [
                    {
                        'id': f['id'],
                        'filename': f['filename'],
                        'original_name': f['original_name'],
                        'file_size': f['file_size'],
                        'dimensions': f"{f['image_width']}x{f['image_height']}",
                        'upload_source': f['upload_source'],
                        'thumbnail_url': f"/api/thumbnail/{f['id']}" if f.get('thumbnail_filename') else None
                    }
                    for f in uploaded_files
                ]
            }
            
            if errors:
                response_data['warnings'] = errors
                response_data['message'] += f" ({len(errors)} files had errors)"
            
            logger.info(f"Upload successful: {len(uploaded_files)} files processed")
            return jsonify(response_data), 200
        
        else:
            # All files failed
            return jsonify({
                'success': False,
                'error': 'All files failed to upload',
                'details': errors
            }), 400
            
    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
        }), 413
        
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred'
        }), 500

@photo_bp.route('/api/thumbnail/<file_id>')
def get_thumbnail(file_id):
    """Serve thumbnail images"""
    try:
        # You would typically look up the file in your database here
        # For now, we'll construct the path directly
        thumbnails_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'thumbnails')
        
        # Find thumbnail file by ID
        for filename in os.listdir(thumbnails_dir):
            if filename.startswith(f"thumb_{file_id}"):
                thumbnail_path = os.path.join(thumbnails_dir, filename)
                if os.path.exists(thumbnail_path):
                    from flask import send_file
                    return send_file(thumbnail_path, mimetype='image/jpeg')
        
        return jsonify({'error': 'Thumbnail not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving thumbnail {file_id}: {str(e)}")
        return jsonify({'error': 'Failed to serve thumbnail'}), 500

@photo_bp.route('/api/photos/<int:photo_id>/annotate', methods=['POST'])
@login_required
@csrf.exempt
def annotate_photo(photo_id):
    """Save annotated version of a photo"""
    try:
        import base64
        import io
        from photovault.services.app_storage_service import app_storage
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get the annotated image data from request
        data = request.get_json()
        if not data or 'imageData' not in data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Decode base64 image data
        image_data = data['imageData']
        if image_data.startswith('data:image'):
            # Remove data:image/png;base64, prefix
            image_data = image_data.split(',')[1]
        
        # Decode and process the image
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Generate filename for edited version
        from werkzeug.utils import secure_filename as sanitize_name
        date = datetime.now().strftime('%Y%m%d')
        random_number = random.randint(100000, 999999)  # 6-digit random number
        safe_username = sanitize_name(current_user.username)
        edited_filename = f"{safe_username}.enhanced.{date}.{random_number}.jpg"
        
        # Convert image to bytes for storage
        img_io = io.BytesIO()
        img.convert('RGB').save(img_io, 'JPEG', quality=90)
        img_io.seek(0)
        
        # Save to App Storage (persistent) or fallback to local
        if app_storage.is_available():
            success, storage_path = app_storage.upload_file(img_io, edited_filename, str(current_user.id))
            if success:
                edited_filepath = storage_path
                logger.info(f"Annotated photo saved to App Storage: {storage_path}")
            else:
                logger.warning(f"App Storage failed, using local storage: {storage_path}")
                # Fallback to local storage
                user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
                os.makedirs(user_upload_dir, exist_ok=True)
                edited_filepath = os.path.join(user_upload_dir, edited_filename)
                img_io.seek(0)
                with open(edited_filepath, 'wb') as f:
                    f.write(img_io.read())
        else:
            # Fallback to local storage
            user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
            os.makedirs(user_upload_dir, exist_ok=True)
            edited_filepath = os.path.join(user_upload_dir, edited_filename)
            img_io.seek(0)
            with open(edited_filepath, 'wb') as f:
                f.write(img_io.read())
        
        # Create thumbnail
        thumbnail_filename = f"{safe_username}.enhanced.{date}.{random_number}_thumb.jpg"
        if app_storage.is_available() and edited_filepath.startswith('users/'):
            # Create thumbnail in App Storage
            success, thumbnail_path = app_storage.create_thumbnail(edited_filepath)
            if not success:
                logger.error(f"Failed to create thumbnail in App Storage: {thumbnail_path}")
                thumbnail_path = None
        else:
            # Create thumbnail locally
            success, result = create_thumbnail(edited_filepath)
            if not success:
                logger.error(f"Failed to create thumbnail: {result}")
                thumbnail_path = None
            else:
                thumbnail_path = result
        
        # Get edited image info
        from photovault.utils.enhanced_file_handler import get_image_info_enhanced
        edited_image_info = get_image_info_enhanced(edited_filepath)
        
        # Get file size with fallback
        file_size = None
        if edited_image_info:
            file_size = edited_image_info.get('size_bytes')
        if not file_size:
            try:
                if os.path.exists(edited_filepath):
                    file_size = os.path.getsize(edited_filepath)
                else:
                    file_size = getattr(photo, 'file_size', 0)
            except:
                file_size = getattr(photo, 'file_size', 0)
        
        # Create a NEW photo record for the edited/annotated image
        edited_photo = Photo()
        edited_photo.user_id = current_user.id
        edited_photo.filename = edited_filename
        edited_photo.original_name = f"Edited - {photo.original_name}"
        edited_photo.file_path = edited_filepath
        edited_photo.thumbnail_path = thumbnail_path
        edited_photo.file_size = file_size
        edited_photo.width = edited_image_info.get('width') if edited_image_info else getattr(photo, 'width', None)
        edited_photo.height = edited_image_info.get('height') if edited_image_info else getattr(photo, 'height', None)
        edited_photo.mime_type = edited_image_info.get('mime_type', 'image/jpeg') if edited_image_info else 'image/jpeg'
        edited_photo.upload_source = getattr(photo, 'upload_source', 'file')
        
        # Copy ALL metadata from original photo (with safe attribute access)
        edited_photo.date_taken = getattr(photo, 'date_taken', None)
        edited_photo.camera_make = getattr(photo, 'camera_make', None)
        edited_photo.camera_model = getattr(photo, 'camera_model', None)
        edited_photo.iso = getattr(photo, 'iso', None)
        edited_photo.aperture = getattr(photo, 'aperture', None)
        edited_photo.shutter_speed = getattr(photo, 'shutter_speed', None)
        edited_photo.focal_length = getattr(photo, 'focal_length', None)
        edited_photo.flash_used = getattr(photo, 'flash_used', None)
        edited_photo.gps_latitude = getattr(photo, 'gps_latitude', None)
        edited_photo.gps_longitude = getattr(photo, 'gps_longitude', None)
        edited_photo.gps_altitude = getattr(photo, 'gps_altitude', None)
        edited_photo.location_name = getattr(photo, 'location_name', None)
        edited_photo.orientation = getattr(photo, 'orientation', None)
        edited_photo.color_space = getattr(photo, 'color_space', None)
        edited_photo.description = getattr(photo, 'description', None)
        edited_photo.tags = getattr(photo, 'tags', None)
        edited_photo.event_name = getattr(photo, 'event_name', None)
        edited_photo.estimated_year = getattr(photo, 'estimated_year', None)
        edited_photo.ai_metadata = getattr(photo, 'ai_metadata', None)
        
        # Also update original photo with edited version info for backward compatibility
        photo.edited_filename = edited_filename
        photo.edited_path = edited_filepath
        photo.updated_at = datetime.utcnow()
        
        # Ensure database transaction is committed properly
        try:
            db.session.add(edited_photo)
            db.session.commit()
            # Verify the insert was successful by refreshing from database
            db.session.refresh(edited_photo)
            logger.info(f"Annotated photo created as new record: {edited_photo.id}, filename: {edited_photo.filename}")
        except Exception as commit_error:
            logger.error(f"Database commit failed for annotated photo {photo_id}: {commit_error}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Failed to save annotation to database'
            }), 500
        
        logger.info(f"Successfully saved annotated photo for user {current_user.id}, photo {photo_id}, new photo ID: {edited_photo.id}")
        
        return jsonify({
            'success': True,
            'message': 'Annotated photo saved successfully',
            'photo_id': edited_photo.id,
            'edited_filename': edited_filename,
            'thumbnail_url': url_for('gallery.uploaded_file', user_id=current_user.id, filename=thumbnail_filename) if thumbnail_path else None,
            'edited_url': url_for('gallery.uploaded_file', user_id=current_user.id, filename=edited_filename)
        })
        
    except Exception as e:
        logger.error(f"Error saving annotated photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save annotated photo'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/delete', methods=['DELETE'])
@login_required
def delete_photo(photo_id):
    """Delete a photo and its files with selective deletion options"""
    try:
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get deletion type from request body or default to 'both'
        data = request.get_json() or {}
        deletion_type = data.get('deletion_type', 'both')  # 'original', 'edited', 'both'
        
        # Validate deletion type
        if deletion_type not in ['original', 'edited', 'both']:
            return jsonify({'success': False, 'error': 'Invalid deletion type'}), 400
        
        # Check if photo has edited version for validation
        has_edited = bool(photo.edited_filename)
        
        if deletion_type == 'edited' and not has_edited:
            return jsonify({'success': False, 'error': 'No edited version to delete'}), 400
        
        if deletion_type == 'original' and not has_edited:
            return jsonify({'success': False, 'error': 'Cannot delete original when no edited version exists'}), 400
        
        files_deleted = []
        
        # Handle selective file deletion
        if deletion_type in ['original', 'both']:
            # Delete original file
            if photo.file_path and os.path.exists(photo.file_path):
                os.remove(photo.file_path)
                files_deleted.append('original')
            
            # Delete thumbnail (always tied to original)
            if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
                os.remove(photo.thumbnail_path)
        
        if deletion_type in ['edited', 'both']:
            # Delete edited version if it exists
            if photo.edited_filename:
                edited_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(photo.user_id), photo.edited_filename)
                if os.path.exists(edited_path):
                    os.remove(edited_path)
                    files_deleted.append('edited')
        
        # Handle database updates and associations based on deletion type
        from photovault.models import VoiceMemo, VaultPhoto, PhotoPerson, StoryPhoto
        
        if deletion_type == 'both':
            # Delete entire photo record and all associations
            
            # Delete associated voice memos
            voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).all()
            for memo in voice_memos:
                if memo.file_path and os.path.exists(memo.file_path):
                    os.remove(memo.file_path)
                db.session.delete(memo)
            
            # Delete associated vault photo shares
            vault_photos = VaultPhoto.query.filter_by(photo_id=photo.id).all()
            for vault_photo in vault_photos:
                db.session.delete(vault_photo)
            
            # Delete associated photo-person tags
            photo_people = PhotoPerson.query.filter_by(photo_id=photo.id).all()
            for photo_person in photo_people:
                db.session.delete(photo_person)
            
            # Delete associated story photo attachments
            story_photos = StoryPhoto.query.filter_by(photo_id=photo.id).all()
            for story_photo in story_photos:
                db.session.delete(story_photo)
            
            # Delete the photo record
            db.session.delete(photo)
            
        elif deletion_type == 'edited':
            # Keep original, remove edited version info from database
            photo.edited_filename = None
            photo.edited_path = None
            # Reset thumbnail_path to ensure it points to original thumbnail
            if photo.thumbnail_path:
                # Check if thumbnail exists, if not regenerate from original
                if not os.path.exists(photo.thumbnail_path):
                    try:
                        # Regenerate thumbnail from original
                        from PIL import Image
                        original_image = Image.open(photo.file_path)
                        original_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                        
                        # Save thumbnail
                        thumbnail_filename = f"{os.path.splitext(photo.filename)[0]}_thumb.jpg"
                        thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(photo.user_id), thumbnail_filename)
                        original_image.save(thumbnail_path, 'JPEG', quality=85)
                        photo.thumbnail_path = thumbnail_path
                    except Exception as e:
                        logger.warning(f"Failed to regenerate thumbnail for photo {photo.id}: {str(e)}")
                        photo.thumbnail_path = None
            photo.updated_at = datetime.utcnow()
            
        elif deletion_type == 'original':
            # Promote edited version to be the new original
            if photo.edited_filename and photo.edited_path:
                # Log this action for troubleshooting gallery issues
                logger.info(f"Promoting edited version to original for photo {photo.id}: {photo.edited_filename} -> {photo.filename}")
                
                # Delete the original file first
                try:
                    if os.path.exists(photo.file_path):
                        os.remove(photo.file_path)
                        logger.info(f"Deleted original file: {photo.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete original file {photo.file_path}: {str(e)}")
                
                # Update database to use edited version as the main photo
                photo.filename = photo.edited_filename
                photo.file_path = photo.edited_path
                
                # Generate new thumbnail from the edited version
                try:
                    from PIL import Image
                    edited_image = Image.open(photo.edited_path)
                    edited_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                    
                    # Save new thumbnail
                    thumbnail_filename = f"{os.path.splitext(photo.edited_filename)[0]}_thumb.jpg"
                    new_thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(photo.user_id), thumbnail_filename)
                    edited_image.save(new_thumbnail_path, 'JPEG', quality=85)
                    photo.thumbnail_path = new_thumbnail_path
                except Exception as e:
                    logger.warning(f"Failed to generate thumbnail from edited version for photo {photo.id}: {str(e)}")
                    photo.thumbnail_path = None
                
                # Clear edited fields since it's now the original
                # NOTE: This will move the photo from edited gallery back to originals gallery
                photo.edited_filename = None
                photo.edited_path = None
                photo.updated_at = datetime.utcnow()
                
                logger.info(f"Photo {photo.id} promoted: edited version is now the original, will appear in originals gallery")
        
        db.session.commit()
        
        logger.info(f"Successfully deleted {deletion_type} version(s) of photo {photo_id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deletion_type} version(s)',
            'files_deleted': files_deleted,
            'deletion_type': deletion_type
        })
        
    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete photo'
        }), 500

@photo_bp.route('/api/photos/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_photos():
    """Delete multiple photos in bulk"""
    try:
        data = request.get_json()
        if not data or 'photo_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'No photo IDs provided'
            }), 400
        
        photo_ids = data['photo_ids']
        if not photo_ids or not isinstance(photo_ids, list):
            return jsonify({
                'success': False,
                'error': 'Invalid photo IDs format'
            }), 400
        
        # Convert to integers and filter out invalid values
        try:
            photo_ids = [int(pid) for pid in photo_ids if str(pid).isdigit()]
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid photo ID format'
            }), 400
        
        if not photo_ids:
            return jsonify({
                'success': False,
                'error': 'No valid photo IDs provided'
            }), 400
        
        # Get photos that belong to current user
        photos_to_delete = Photo.query.filter(
            Photo.id.in_(photo_ids),
            Photo.user_id == current_user.id
        ).all()
        
        if not photos_to_delete:
            return jsonify({
                'success': False,
                'error': 'No photos found or access denied'
            }), 404
        
        deleted_count = 0
        errors = []
        
        # Get upload folder for security validation
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_dir = os.path.realpath(os.path.join(upload_folder, str(current_user.id)))
        
        def is_safe_path(filepath, base_dir):
            """Validate that filepath is within base_dir to prevent path traversal"""
            try:
                real_path = os.path.realpath(filepath)
                return real_path.startswith(base_dir + os.sep) or real_path == base_dir
            except (OSError, ValueError):
                return False
        
        for photo in photos_to_delete:
            try:
                # Validate and delete physical files with path security
                if photo.file_path and os.path.exists(photo.file_path):
                    if is_safe_path(photo.file_path, user_upload_dir):
                        os.remove(photo.file_path)
                
                if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
                    if is_safe_path(photo.thumbnail_path, user_upload_dir):
                        os.remove(photo.thumbnail_path)
                    
                # Delete edited version if it exists
                if photo.edited_filename:
                    edited_path = os.path.join(user_upload_dir, photo.edited_filename)
                    if os.path.exists(edited_path):
                        os.remove(edited_path)
                
                # Delete all associated records that reference this photo
                from photovault.models import VoiceMemo, VaultPhoto, PhotoPerson, StoryPhoto
                
                # Delete associated voice memos
                voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).all()
                for memo in voice_memos:
                    if memo.file_path and os.path.exists(memo.file_path):
                        if is_safe_path(memo.file_path, user_upload_dir):
                            os.remove(memo.file_path)
                    db.session.delete(memo)
                
                # Delete associated vault photo shares
                vault_photos = VaultPhoto.query.filter_by(photo_id=photo.id).all()
                for vault_photo in vault_photos:
                    db.session.delete(vault_photo)
                
                # Delete associated photo-person tags
                photo_people = PhotoPerson.query.filter_by(photo_id=photo.id).all()
                for photo_person in photo_people:
                    db.session.delete(photo_person)
                
                # Delete associated story photo attachments
                story_photos = StoryPhoto.query.filter_by(photo_id=photo.id).all()
                for story_photo in story_photos:
                    db.session.delete(story_photo)
                
                # Delete the photo record
                db.session.delete(photo)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting photo {photo.id}: {str(e)}")
                errors.append(f"Photo {photo.id}: {str(e)}")
                continue
        
        # Commit all deletions
        db.session.commit()
        
        logger.info(f"Successfully bulk deleted {deleted_count} photos for user {current_user.id}")
        
        response_data = {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} photo{"s" if deleted_count != 1 else ""}'
        }
        
        if errors:
            response_data['warnings'] = errors
            response_data['message'] += f' ({len(errors)} photos had errors)'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in bulk delete photos: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete photos'
        }), 500

# Voice Memo API Endpoints

@photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['POST'])
@csrf.exempt
@hybrid_auth
def upload_voice_memo(current_user, photo_id):
    """Upload a voice memo for a photo"""
    try:
        from photovault.models import VoiceMemo
        import uuid
        import os
        from werkzeug.utils import secure_filename
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if audio file was provided
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if not audio_file.filename:
            return jsonify({'success': False, 'error': 'No audio file selected'}), 400
        
        # Validate audio file type (handle codec variations)
        content_type = audio_file.content_type.lower()
        base_type = content_type.split(';')[0].strip()  # Remove codec specifications
        
        allowed_audio_types = {'audio/webm', 'audio/wav', 'audio/mp3', 'audio/ogg', 'audio/mp4', 'audio/mpeg', 'audio/m4a', 'audio/x-m4a'}
        if base_type not in allowed_audio_types:
            return jsonify({'success': False, 'error': f'Invalid audio file type: {content_type}'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_extension = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else 'webm'
        filename = f"voice_memo_{photo_id}_{timestamp}_{unique_id}.{file_extension}"
        
        # Create voice memos directory
        voice_memo_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), 'voice_memos')
        os.makedirs(voice_memo_dir, exist_ok=True)
        
        # Save audio file
        file_path = os.path.join(voice_memo_dir, filename)
        audio_file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Get optional metadata from request
        title = request.form.get('title', '').strip()
        transcript = request.form.get('transcript', '').strip()
        duration = request.form.get('duration')  # Duration in seconds from frontend
        
        # Convert duration to float if provided
        try:
            duration = float(duration) if duration else None
        except (ValueError, TypeError):
            duration = None
        
        # Auto-generate descriptive title if not provided
        if not title:
            if transcript and len(transcript.strip()) > 0:
                # Use first few words of transcript
                words = transcript.strip().split()[:4]
                title = f"Memo: {' '.join(words)}..."
            else:
                # Use photo name and timestamp
                photo_name = photo.original_name.split('.')[0] if photo.original_name else 'Photo'
                time_str = datetime.now().strftime('%H:%M')
                title = f"Voice memo for {photo_name[:20]} at {time_str}"
        
        # Create voice memo record
        voice_memo = VoiceMemo()
        voice_memo.photo_id = photo_id
        voice_memo.user_id = current_user.id
        voice_memo.filename = filename
        voice_memo.original_name = secure_filename(audio_file.filename)
        voice_memo.file_path = file_path
        voice_memo.file_size = file_size
        voice_memo.mime_type = audio_file.content_type
        voice_memo.duration = duration
        voice_memo.title = title if title else None
        voice_memo.transcript = transcript if transcript else None
        
        db.session.add(voice_memo)
        db.session.commit()
        
        logger.info(f"Voice memo uploaded for photo {photo_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo uploaded successfully',
            'voice_memo': {
                'id': voice_memo.id,
                'filename': voice_memo.filename,
                'duration': voice_memo.duration,
                'duration_formatted': voice_memo.duration_formatted,
                'file_size_mb': voice_memo.file_size_mb,
                'title': voice_memo.title,
                'transcript': voice_memo.transcript,
                'created_at': voice_memo.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error uploading voice memo for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to upload voice memo'}), 500

@photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['GET'])
@hybrid_auth
def get_voice_memos(current_user, photo_id):
    """Get all voice memos for a photo"""
    try:
        from photovault.models import VoiceMemo
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get voice memos for this photo
        voice_memos = VoiceMemo.query.filter_by(photo_id=photo_id).order_by(VoiceMemo.created_at.desc()).all()
        
        memos_data = []
        for memo in voice_memos:
            memos_data.append({
                'id': memo.id,
                'filename': memo.filename,
                'original_name': memo.original_name,
                'duration': memo.duration,
                'duration_formatted': memo.duration_formatted,
                'file_size_mb': memo.file_size_mb,
                'title': memo.title,
                'transcript': memo.transcript,
                'created_at': memo.created_at.isoformat(),
                'updated_at': memo.updated_at.isoformat() if memo.updated_at != memo.created_at else None
            })
        
        return jsonify({
            'success': True,
            'voice_memos': memos_data,
            'total': len(memos_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting voice memos for photo {photo_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get voice memos'}), 500

@photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['GET'])
@hybrid_auth
def serve_voice_memo(current_user, memo_id):
    """Serve/download a voice memo file"""
    try:
        from photovault.models import VoiceMemo
        from flask import send_file
        
        # Get the voice memo and verify ownership
        voice_memo = VoiceMemo.query.get_or_404(memo_id)
        if voice_memo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if file exists
        if not os.path.exists(voice_memo.file_path):
            return jsonify({'success': False, 'error': 'Voice memo file not found'}), 404
        
        # Serve the file
        return send_file(
            voice_memo.file_path,
            mimetype=voice_memo.mime_type,
            as_attachment=False,
            download_name=voice_memo.original_name
        )
        
    except Exception as e:
        logger.error(f"Error serving voice memo {memo_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to serve voice memo'}), 500

@photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['PUT'])
@hybrid_auth
def update_voice_memo(current_user, memo_id):
    """Update voice memo metadata (title, transcript)"""
    try:
        from photovault.models import VoiceMemo
        
        # Get the voice memo and verify ownership
        voice_memo = VoiceMemo.query.get_or_404(memo_id)
        if voice_memo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update title if provided
        if 'title' in data:
            voice_memo.title = data['title'].strip() if data['title'] else None
        
        # Update transcript if provided
        if 'transcript' in data:
            voice_memo.transcript = data['transcript'].strip() if data['transcript'] else None
        
        voice_memo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Voice memo {memo_id} updated by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo updated successfully',
            'voice_memo': {
                'id': voice_memo.id,
                'title': voice_memo.title,
                'transcript': voice_memo.transcript,
                'updated_at': voice_memo.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating voice memo {memo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update voice memo'}), 500

@photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['DELETE'])
@hybrid_auth
def delete_voice_memo(current_user, memo_id):
    """Delete a voice memo"""
    try:
        from photovault.models import VoiceMemo
        
        # Get the voice memo and verify ownership
        voice_memo = VoiceMemo.query.get_or_404(memo_id)
        if voice_memo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Delete physical file
        if voice_memo.file_path and os.path.exists(voice_memo.file_path):
            os.remove(voice_memo.file_path)
        
        # Delete from database
        db.session.delete(voice_memo)
        db.session.commit()
        
        logger.info(f"Voice memo {memo_id} deleted by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting voice memo {memo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete voice memo'}), 500

# Error handlers for the blueprint
@photo_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413

@photo_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

@photo_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# Face Detection API Endpoints

@photo_bp.route('/api/photos/<int:photo_id>/detect-faces', methods=['POST'])
@login_required
def detect_faces_in_photo_api(photo_id):
    """
    API endpoint to detect faces in a specific photo
    """
    try:
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Detect faces in the photo
        faces = detect_faces_in_photo(photo.file_path)
        
        if not faces:
            return jsonify({
                'success': True,
                'message': 'No faces detected in this photo',
                'faces': []
            })
        
        # Store detected faces in database
        stored_faces = []
        for face in faces:
            try:
                # Try to recognize the face
                recognition_result = face_recognizer.recognize_face(photo.file_path, face)
                
                if recognition_result:
                    # Face recognized - link to existing person
                    person_id = recognition_result['person_id']
                    confidence = recognition_result['confidence']
                    manually_tagged = False
                else:
                    # Face not recognized - create unassigned detection
                    person_id = None
                    confidence = face['confidence']
                    manually_tagged = False
                
                # Check if this face detection already exists
                existing_detection = PhotoPerson.query.filter_by(
                    photo_id=photo_id,
                    face_box_x=face['x'],
                    face_box_y=face['y'],
                    face_box_width=face['width'],
                    face_box_height=face['height']
                ).first()
                
                if not existing_detection:
                    # Create new PhotoPerson record
                    photo_person = PhotoPerson(
                        photo_id=photo_id,
                        person_id=person_id,
                        confidence=confidence,
                        face_box_x=face['x'],
                        face_box_y=face['y'],
                        face_box_width=face['width'],
                        face_box_height=face['height'],
                        manually_tagged=manually_tagged,
                        verified=False
                    )
                    
                    db.session.add(photo_person)
                    
                    stored_faces.append({
                        'x': face['x'],
                        'y': face['y'],
                        'width': face['width'],
                        'height': face['height'],
                        'confidence': confidence,
                        'person_id': person_id,
                        'person_name': recognition_result['person_name'] if recognition_result else None,
                        'method': face['method']
                    })
            
            except Exception as e:
                logger.error(f"Error storing face detection: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Detected and stored {len(stored_faces)} faces',
            'faces': stored_faces
        })
        
    except Exception as e:
        logger.error(f"Error detecting faces in photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to detect faces'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/faces', methods=['GET'])
@login_required
def get_photo_faces(photo_id):
    """
    Get all detected faces for a photo
    """
    try:
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get all face detections for this photo
        photo_people = PhotoPerson.query.filter_by(photo_id=photo_id).all()
        
        faces = []
        for pp in photo_people:
            face_data = {
                'id': pp.id,
                'x': pp.face_box_x,
                'y': pp.face_box_y,
                'width': pp.face_box_width,
                'height': pp.face_box_height,
                'confidence': pp.confidence,
                'manually_tagged': pp.manually_tagged,
                'verified': pp.verified,
                'person_id': pp.person_id,
                'person_name': pp.person.name if pp.person else None,
                'notes': pp.notes
            }
            faces.append(face_data)
        
        return jsonify({
            'success': True,
            'faces': faces
        })
        
    except Exception as e:
        logger.error(f"Error getting faces for photo {photo_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get photo faces'
        }), 500

@photo_bp.route('/api/faces/<int:face_id>/assign', methods=['POST'])
@login_required
def assign_face_to_person(face_id):
    """
    Assign a detected face to a specific person
    """
    try:
        data = request.get_json()
        person_id = data.get('person_id')
        
        if not person_id:
            return jsonify({'success': False, 'error': 'Person ID is required'}), 400
        
        # Get the face detection record
        photo_person = PhotoPerson.query.get_or_404(face_id)
        
        # Verify ownership through photo
        photo = Photo.query.get_or_404(photo_person.photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Verify person belongs to user
        person = Person.query.get_or_404(person_id)
        if person.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        # Update the assignment
        photo_person.person_id = person_id
        photo_person.manually_tagged = True
        photo_person.verified = True
        
        # Add this face to the recognition system
        face_box = {
            'x': photo_person.face_box_x,
            'y': photo_person.face_box_y,
            'width': photo_person.face_box_width,
            'height': photo_person.face_box_height
        }
        face_recognizer.add_person_encoding(person_id, person.name, photo.file_path, face_box)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Face assigned to {person.name}',
            'person_name': person.name
        })
        
    except Exception as e:
        logger.error(f"Error assigning face {face_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to assign face'
        }), 500


@photo_bp.route('/api/photos/batch-detect-faces', methods=['POST'])
@login_required
def batch_detect_faces():
    """
    Run face detection on multiple photos (background processing)
    """
    try:
        data = request.get_json()
        photo_ids = data.get('photo_ids', [])
        
        if not photo_ids:
            # If no specific photos, detect faces in all user's photos without face detection
            photos = Photo.query.filter_by(user_id=current_user.id).all()
            photos_to_process = []
            
            for photo in photos:
                # Check if photo already has face detections
                existing_detections = PhotoPerson.query.filter_by(photo_id=photo.id).count()
                if existing_detections == 0:
                    photos_to_process.append(photo)
        else:
            # Process specific photos
            photos_to_process = Photo.query.filter(
                Photo.id.in_(photo_ids),
                Photo.user_id == current_user.id
            ).all()
        
        results = {
            'processed': 0,
            'faces_found': 0,
            'errors': []
        }
        
        for photo in photos_to_process:
            try:
                # Detect faces
                faces = detect_faces_in_photo(photo.file_path)
                
                faces_stored = 0
                for face in faces:
                    try:
                        # Try to recognize the face
                        recognition_result = face_recognizer.recognize_face(photo.file_path, face)
                        
                        # Store detection
                        photo_person = PhotoPerson(
                            photo_id=photo.id,
                            person_id=recognition_result['person_id'] if recognition_result else None,
                            confidence=recognition_result['confidence'] if recognition_result else face['confidence'],
                            face_box_x=face['x'],
                            face_box_y=face['y'],
                            face_box_width=face['width'],
                            face_box_height=face['height'],
                            manually_tagged=False,
                            verified=bool(recognition_result)
                        )
                        
                        db.session.add(photo_person)
                        faces_stored += 1
                        
                    except Exception as e:
                        logger.error(f"Error storing face for photo {photo.id}: {e}")
                        continue
                
                results['processed'] += 1
                results['faces_found'] += faces_stored
                
                # Commit after each photo to avoid losing progress
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing photo {photo.id}: {e}")
                results['errors'].append(f"Photo {photo.id}: {str(e)}")
                db.session.rollback()
                continue
        
        return jsonify({
            'success': True,
            'message': f'Processed {results["processed"]} photos, found {results["faces_found"]} faces',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in batch face detection: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to process batch face detection'
        }), 500

# AI-Enhanced Features API Endpoints

@photo_bp.route('/api/photos/<int:photo_id>/ai-tags', methods=['POST'])
@login_required
def save_ai_tags(photo_id):
    """
    Save AI-generated object tags from TensorFlow.js COCO-SSD detection
    """
    try:
        import json
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data or 'detectedObjects' not in data:
            return jsonify({'success': False, 'error': 'No detected objects provided'}), 400
        
        detected_objects = data['detectedObjects']
        
        # Store AI tags in photo metadata for now (can be moved to separate table later)
        ai_tags = []
        for obj in detected_objects:
            if obj.get('score', 0) > 0.6:  # Only save high-confidence detections
                ai_tags.append({
                    'tag_name': obj['class'],
                    'confidence': obj['score'],
                    'bbox': obj.get('bbox', []),
                    'model': 'COCO-SSD',
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Update photo with AI tags
        ai_metadata = json.loads(photo.ai_metadata) if photo.ai_metadata else {}
        ai_metadata['ai_tags'] = ai_tags
        ai_metadata['last_ai_processing'] = datetime.utcnow().isoformat()
        photo.ai_metadata = json.dumps(ai_metadata)
        
        db.session.commit()
        
        logger.info(f"Saved {len(ai_tags)} AI tags for photo {photo_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Saved {len(ai_tags)} AI-generated tags',
            'tags': [{'name': tag['tag_name'], 'confidence': tag['confidence']} for tag in ai_tags]
        })
        
    except Exception as e:
        logger.error(f"Error saving AI tags for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save AI tags'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/ai-faces', methods=['POST'])
@login_required
def save_ai_faces(photo_id):
    """
    Save AI-generated face detection results from TensorFlow.js BlazeFace
    """
    try:
        import json
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data or 'detectedFaces' not in data:
            return jsonify({'success': False, 'error': 'No detected faces provided'}), 400
        
        detected_faces = data['detectedFaces']
        
        # Save face detections using existing PhotoPerson model
        saved_faces = []
        for face in detected_faces:
            bbox = face.get('bbox', [])
            if len(bbox) >= 4:
                x, y, width, height = bbox[:4]
                
                # Check if this face detection already exists
                existing_detection = PhotoPerson.query.filter_by(
                    photo_id=photo_id,
                    face_box_x=int(x),
                    face_box_y=int(y),
                    face_box_width=int(width),
                    face_box_height=int(height)
                ).first()
                
                if not existing_detection:
                    photo_person = PhotoPerson(
                        photo_id=photo_id,
                        person_id=None,  # No person assigned yet
                        confidence=face.get('probability', 0.9),
                        face_box_x=int(x),
                        face_box_y=int(y),
                        face_box_width=int(width),
                        face_box_height=int(height),
                        manually_tagged=False,
                        verified=False
                    )
                    
                    # Store landmarks data if available
                    if 'landmarks' in face:
                        # Create AI metadata for landmarks
                        ai_metadata = json.loads(photo.ai_metadata) if photo.ai_metadata else {}
                        if 'ai_face_landmarks' not in ai_metadata:
                            ai_metadata['ai_face_landmarks'] = []
                        ai_metadata['ai_face_landmarks'].append({
                            'bbox': bbox,
                            'landmarks': face['landmarks'],
                            'model': 'BlazeFace',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        photo.ai_metadata = json.dumps(ai_metadata)
                    
                    db.session.add(photo_person)
                    saved_faces.append({
                        'bbox': bbox,
                        'confidence': face.get('probability', 0.9),
                        'landmarks_count': len(face.get('landmarks', []))
                    })
        
        db.session.commit()
        
        logger.info(f"Saved {len(saved_faces)} AI face detections for photo {photo_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Saved {len(saved_faces)} AI-detected faces',
            'faces': saved_faces
        })
        
    except Exception as e:
        logger.error(f"Error saving AI faces for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save AI face detections'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/ai-poses', methods=['POST'])

@login_required
def save_ai_poses(photo_id):
    """
    Save AI-generated pose detection and activity recognition data
    """
    try:
        import json
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No pose data provided'}), 400
        
        poses = data.get('poses', [])
        activity = data.get('activity', {})
        
        # Store pose data in photo metadata
        ai_metadata = json.loads(photo.ai_metadata) if photo.ai_metadata else {}
        ai_metadata['ai_poses'] = {
            'poses': poses,
            'activity': activity,
            'pose_count': len(poses),
            'detected_activity': activity.get('activity', 'unknown'),
            'activity_confidence': activity.get('confidence', 0),
            'model': 'PoseNet',
            'timestamp': datetime.utcnow().isoformat()
        }
        photo.ai_metadata = json.dumps(ai_metadata)
        
        db.session.commit()
        
        logger.info(f"Saved AI pose data for photo {photo_id}: {len(poses)} poses, activity: {activity.get('activity', 'unknown')}")
        
        return jsonify({
            'success': True,
            'message': f'Saved pose data: {len(poses)} poses detected',
            'poses_count': len(poses),
            'activity': activity.get('activity', 'unknown'),
            'activity_confidence': activity.get('confidence', 0)
        })
        
    except Exception as e:
        logger.error(f"Error saving AI pose data for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save AI pose data'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/ai-composition', methods=['POST'])
@login_required
def save_ai_composition(photo_id):
    """
    Save AI-generated composition analysis and suggestions
    """
    try:
        import json
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data or 'composition' not in data:
            return jsonify({'success': False, 'error': 'No composition data provided'}), 400
        
        composition_data = data['composition']
        
        # Store composition analysis in photo metadata
        ai_metadata = json.loads(photo.ai_metadata) if photo.ai_metadata else {}
        ai_metadata['ai_composition'] = {
            'score': composition_data.get('composition', {}).get('score', 0),
            'feedback': composition_data.get('composition', {}).get('feedback', ''),
            'suggestions': composition_data.get('suggestions', []),
            'subjects_count': len(composition_data.get('mainSubjects', [])),
            'faces_count': composition_data.get('faces', 0),
            'poses_count': composition_data.get('poses', 0),
            'timestamp': datetime.utcnow().isoformat()
        }
        photo.ai_metadata = json.dumps(ai_metadata)
        
        db.session.commit()
        
        score = ai_metadata['ai_composition']['score']
        suggestions_count = len(ai_metadata['ai_composition']['suggestions'])
        
        logger.info(f"Saved AI composition analysis for photo {photo_id}: score {score}")
        
        return jsonify({
            'success': True,
            'message': 'Saved composition analysis',
            'composition_score': score,
            'suggestions_count': suggestions_count
        })
        
    except Exception as e:
        logger.error(f"Error saving AI composition data for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save composition analysis'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/ai-metadata', methods=['GET'])
@login_required
def get_ai_metadata(photo_id):
    """
    Retrieve all AI-generated metadata for a photo
    """
    try:
        import json
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        ai_data = {
            'photo_id': photo_id,
            'has_ai_data': False,
            'ai_tags': [],
            'ai_faces': [],
            'ai_poses': {},
            'ai_composition': {},
            'ai_face_landmarks': [],
            'generated_at': None
        }
        
        # Get AI metadata from photo
        if photo.ai_metadata:
            try:
                metadata = json.loads(photo.ai_metadata)
                ai_data.update({
                    'ai_tags': metadata.get('ai_tags', []),
                    'ai_poses': metadata.get('ai_poses', {}),
                    'ai_composition': metadata.get('ai_composition', {}),
                    'ai_face_landmarks': metadata.get('ai_face_landmarks', []),
                    'has_ai_data': True,
                    'generated_at': metadata.get('last_ai_processing', photo.created_at.isoformat())
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in ai_metadata for photo {photo_id}")
        
        # Get AI face detections from PhotoPerson
        ai_faces = PhotoPerson.query.filter_by(
            photo_id=photo_id,
            manually_tagged=False
        ).all()
        
        ai_data['ai_faces'] = [{
            'bbox': [face.face_box_x, face.face_box_y, face.face_box_width, face.face_box_height],
            'confidence': face.confidence,
            'person_assigned': face.person_id is not None,
            'verified': face.verified
        } for face in ai_faces]
        
        if ai_faces:
            ai_data['has_ai_data'] = True
        
        return jsonify({
            'success': True,
            'ai_data': ai_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving AI metadata for photo {photo_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve AI metadata'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/auto-detect', methods=['POST'])
@login_required
def auto_detect_photos(photo_id):
    """Automatically detect and extract photos from a larger image"""
    try:
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get the original photo file path
        if not photo.file_path or not os.path.exists(photo.file_path):
            return jsonify({'success': False, 'error': 'Original photo file not found'}), 404
        
        logger.info(f"Starting auto-detection for photo {photo_id} by user {current_user.id}")
        
        # Detect photos in the image
        detected_photos = detect_photos_in_image(photo.file_path)
        
        if not detected_photos:
            return jsonify({
                'success': True,
                'message': 'No photos detected in the image',
                'detected_count': 0,
                'detected_photos': []
            })
        
        # Create output directory for extracted photos
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        extract_dir = os.path.join(user_upload_dir, 'auto_extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract detected photos
        extracted_photos = extract_detected_photos(photo.file_path, extract_dir, detected_photos)
        
        # Save extracted photos to database
        saved_photos = []
        
        for extracted in extracted_photos:
            try:
                # Generate secure filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                base_name = f"{current_user.username}_auto_extract_{timestamp}_{unique_id}"
                final_filename = f"{base_name}.jpg"
                
                # Move file to main upload directory
                final_path = os.path.join(user_upload_dir, final_filename)
                os.rename(extracted['file_path'], final_path)
                
                # Get image dimensions
                with Image.open(final_path) as img:
                    width, height = img.size
                
                # Create thumbnail using the imported utility function
                from photovault.utils.file_handler import create_thumbnail as create_thumb_util
                success, thumbnail_result = create_thumb_util(final_path)
                thumbnail_path = thumbnail_result if success else None
                
                # Create Photo record
                new_photo = Photo(
                    filename=final_filename,
                    file_path=final_path,
                    thumbnail_path=thumbnail_path,
                    user_id=current_user.id,
                    width=width,
                    height=height,
                    file_size=os.path.getsize(final_path),
                    upload_source='auto_extract'
                )
                
                db.session.add(new_photo)
                db.session.flush()  # Get the ID
                
                saved_photos.append({
                    'id': new_photo.id,
                    'filename': final_filename,
                    'confidence': extracted['confidence'],
                    'width': width,
                    'height': height,
                    'thumbnail_url': url_for('gallery.uploaded_file', user_id=current_user.id, filename=os.path.basename(thumbnail_path)) if thumbnail_path else None,
                    'photo_url': url_for('gallery.uploaded_file', user_id=current_user.id, filename=final_filename)
                })
                
            except Exception as e:
                logger.error(f"Failed to save extracted photo: {e}")
                continue
        
        db.session.commit()
        
        # Clean up temporary extraction directory
        try:
            import shutil
            shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup extraction directory: {e}")
        
        logger.info(f"Auto-detection completed: {len(saved_photos)} photos extracted from photo {photo_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully detected and extracted {len(saved_photos)} photos',
            'detected_count': len(detected_photos),
            'extracted_count': len(saved_photos),
            'detected_photos': [{
                'x': p['x'], 'y': p['y'], 
                'width': p['width'], 'height': p['height'],
                'confidence': p['confidence']
            } for p in detected_photos],
            'extracted_photos': saved_photos
        })
        
    except Exception as e:
        logger.error(f"Auto-detection failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to auto-detect photos'
        }), 500

@photo_bp.route('/api/photos/debug/gallery-state', methods=['GET'])
@login_required  
def debug_gallery_state():
    """Debug endpoint to check photo database state for gallery troubleshooting"""
    try:
        from photovault.models import Photo
        
        # Get all user photos with counts
        all_photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        # Categorize photos
        originals = [p for p in all_photos if not p.edited_filename]
        edited = [p for p in all_photos if p.edited_filename]
        
        # Build debug info
        debug_info = {
            'user_id': current_user.id,
            'total_photos': len(all_photos),
            'original_count': len(originals),
            'edited_count': len(edited),
            'photos': []
        }
        
        # Add detailed photo info
        for photo in all_photos:
            debug_info['photos'].append({
                'id': photo.id,
                'filename': photo.filename,
                'edited_filename': photo.edited_filename,
                'has_edited': bool(photo.edited_filename),
                'created_at': photo.created_at.isoformat() if photo.created_at else None,
                'updated_at': photo.updated_at.isoformat() if photo.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        logger.error(f"Debug gallery state failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get debug info'
        }), 500

def analyze_image_content(file_path):
    """
    Analyze image content to detect corruption, dark images, or other issues
    
    Returns:
        dict: Analysis results with status, luminance, and any issues found
    """
    try:
        from photovault.utils.enhanced_file_handler import get_file_content
        from PIL import Image, ImageStat
        import tempfile
        
        # Download file content for analysis
        success, file_data = get_file_content(file_path)
        if not success:
            return {'status': 'corrupted', 'error': 'Cannot read file from storage'}
        
        # Create temporary file for analysis
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(file_data)
            temp_file.flush()
            
            try:
                # Try to open and analyze the image
                with Image.open(temp_file.name) as img:
                    # Basic validity check
                    width, height = img.size
                    if width <= 0 or height <= 0:
                        return {'status': 'corrupted', 'error': 'Invalid image dimensions'}
                    
                    # Convert to RGB for analysis
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Calculate image statistics
                    stat = ImageStat.Stat(img)
                    
                    # Calculate mean luminance (brightness)
                    # Use standard luminance formula: 0.299*R + 0.587*G + 0.114*B
                    mean_r, mean_g, mean_b = stat.mean
                    luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b
                    
                    # Calculate standard deviation to detect uniformity
                    std_r, std_g, std_b = stat.stddev
                    avg_std = (std_r + std_g + std_b) / 3
                    
                    # Check for various corruption patterns
                    if luminance < 10:  # Very dark image
                        return {'status': 'dark', 'luminance': luminance, 'std_dev': avg_std}
                    elif avg_std < 5:  # Very uniform (potentially corrupted)
                        return {'status': 'suspicious', 'warning': f'Very uniform image (std dev: {avg_std:.2f})', 'luminance': luminance}
                    elif luminance > 250:  # Very bright (overexposed/corrupted)
                        return {'status': 'suspicious', 'warning': f'Very bright image (luminance: {luminance:.2f})', 'luminance': luminance}
                    else:
                        return {'status': 'healthy', 'luminance': luminance, 'std_dev': avg_std, 'dimensions': f'{width}x{height}'}
                        
            except Exception as img_error:
                return {'status': 'corrupted', 'error': f'Cannot decode image: {str(img_error)}'}
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                    
    except Exception as e:
        return {'status': 'corrupted', 'error': f'Analysis failed: {str(e)}'}

@photo_bp.route('/api/photos/debug/file-integrity', methods=['GET'])
@login_required  
def debug_file_integrity():
    """Debug endpoint to check file integrity and identify corrupted images"""
    try:
        from photovault.models import Photo
        from photovault.utils.enhanced_file_handler import file_exists_enhanced, get_file_size_enhanced
        
        # Get all user photos
        all_photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        results = {
            'user_id': current_user.id,
            'total_photos': len(all_photos),
            'issues_found': [],
            'healthy_files': 0,
            'corrupted_files': 0,
            'missing_files': 0
        }
        
        for photo in all_photos:
            file_status = {
                'photo_id': photo.id,
                'filename': photo.filename,
                'file_path': photo.file_path,
                'upload_source': getattr(photo, 'upload_source', 'unknown'),
                'issues': []
            }
            
            # Check if main file exists
            if photo.file_path:
                if file_exists_enhanced(photo.file_path):
                    # Check file size
                    file_size = get_file_size_enhanced(photo.file_path)
                    if file_size == 0:
                        file_status['issues'].append('File exists but is empty (0 bytes)')
                        results['corrupted_files'] += 1
                    elif file_size < 1000:  # Suspiciously small image
                        file_status['issues'].append(f'File suspiciously small ({file_size} bytes)')
                        results['corrupted_files'] += 1
                    else:
                        # Deep image analysis - check if image data is corrupted
                        image_analysis = analyze_image_content(photo.file_path)
                        if image_analysis['status'] == 'corrupted':
                            file_status['issues'].append(f"Image corrupted: {image_analysis['error']}")
                            results['corrupted_files'] += 1
                        elif image_analysis['status'] == 'dark':
                            file_status['issues'].append(f"Image appears dark/black (luminance: {image_analysis['luminance']:.2f})")
                            results['corrupted_files'] += 1
                        elif image_analysis['status'] == 'suspicious':
                            file_status['issues'].append(f"Image suspicious: {image_analysis['warning']}")
                            results['corrupted_files'] += 1
                        else:
                            results['healthy_files'] += 1
                            file_status['luminance'] = image_analysis.get('luminance', 'unknown')
                else:
                    file_status['issues'].append('Main file missing from storage')
                    results['missing_files'] += 1
            else:
                file_status['issues'].append('No file path recorded in database')
                results['missing_files'] += 1
            
            # Check thumbnail
            if photo.thumbnail_path:
                if not file_exists_enhanced(photo.thumbnail_path):
                    file_status['issues'].append('Thumbnail missing')
            
            # Check edited version if exists
            if photo.edited_filename and photo.edited_path:
                if not file_exists_enhanced(photo.edited_path):
                    file_status['issues'].append('Edited version missing')
            
            # Add to results if there are issues
            if file_status['issues']:
                results['issues_found'].append(file_status)
        
        return jsonify({
            'success': True,
            'integrity_report': results
        })
        
    except Exception as e:
        logger.error(f"File integrity check failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check file integrity'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/recover', methods=['POST'])
@login_required
def recover_corrupted_photo(photo_id):
    """Attempt to recover a corrupted photo by regenerating thumbnail and validating file"""
    try:
        from photovault.models import Photo
        from photovault.utils.enhanced_file_handler import file_exists_enhanced, get_file_size_enhanced
        from PIL import Image
        import tempfile
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        recovery_actions = []
        
        # Check if file exists and is readable
        if not photo.file_path or not file_exists_enhanced(photo.file_path):
            return jsonify({
                'success': False,
                'error': 'Cannot recover: original file is missing from storage'
            }), 404
        
        # Check file size
        file_size = get_file_size_enhanced(photo.file_path)
        if file_size == 0:
            return jsonify({
                'success': False,
                'error': 'Cannot recover: file exists but is empty (0 bytes)'
            }), 400
        
        # Try to validate image by opening it
        try:
            # For App Storage files, we need to download temporarily to validate
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                # Download file content for validation
                from photovault.utils.enhanced_file_handler import get_file_content
                success, file_data = get_file_content(photo.file_path)
                
                if not success:
                    return jsonify({
                        'success': False,
                        'error': 'Cannot read file from storage'
                    }), 400
                
                temp_file.write(file_data)
                temp_file.flush()
                
                # Try to open with PIL to validate
                with Image.open(temp_file.name) as img:
                    width, height = img.size
                    
                    # Update database with actual dimensions if they're wrong
                    if photo.width != width or photo.height != height:
                        photo.width = width
                        photo.height = height
                        recovery_actions.append(f'Updated dimensions to {width}x{height}')
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
        except Exception as img_error:
            return jsonify({
                'success': False,
                'error': f'Image file is corrupted and cannot be opened: {str(img_error)}'
            }), 400
        
        # Regenerate thumbnail if missing or corrupted
        if not photo.thumbnail_path or not file_exists_enhanced(photo.thumbnail_path):
            try:
                from photovault.utils.file_handler import create_thumbnail
                success, thumbnail_result = create_thumbnail(photo.file_path)
                if success:
                    photo.thumbnail_path = thumbnail_result
                    recovery_actions.append('Regenerated thumbnail')
                else:
                    recovery_actions.append(f'Failed to regenerate thumbnail: {thumbnail_result}')
            except Exception as thumb_error:
                recovery_actions.append(f'Thumbnail regeneration failed: {str(thumb_error)}')
        
        # Update database
        photo.updated_at = datetime.utcnow()
        db.session.commit()
        
        recovery_actions.append('Database record updated')
        
        logger.info(f"Photo {photo_id} recovery completed: {', '.join(recovery_actions)}")
        
        return jsonify({
            'success': True,
            'message': 'Photo recovery completed',
            'actions_taken': recovery_actions,
            'file_size': file_size,
            'dimensions': f"{photo.width}x{photo.height}"
        })
        
    except Exception as e:
        logger.error(f"Photo recovery failed for {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Recovery failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photo/<int:photo_id>/colorize', methods=['POST'])
@login_required
def colorize_photo_route(photo_id):
    """
    Colorize a black and white photo
    
    Args:
        photo_id: ID of the photo to colorize
        
    Request JSON:
        method: 'auto', 'dnn', or 'basic' (optional, default: 'auto')
        
    Returns:
        JSON with success status and colorized photo information
    """
    try:
        from photovault.utils.colorization import get_colorizer
        from photovault.services.app_storage_service import app_storage
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        method = data.get('method', 'auto')
        
        if method not in ['auto', 'dnn', 'basic']:
            return jsonify({
                'success': False,
                'error': 'Invalid colorization method. Use auto, dnn, or basic'
            }), 400
        
        colorizer = get_colorizer()
        
        try:
            is_grayscale = colorizer.is_grayscale(photo.file_path)
        except FileNotFoundError as e:
            logger.error(f"Photo file not found: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Photo file not found or has been deleted'
            }), 404
        except RuntimeError as e:
            logger.error(f"Photo file corrupted: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Photo file is corrupted or invalid'
            }), 500
        
        if not is_grayscale:
            return jsonify({
                'success': False,
                'error': 'Photo is already in color',
                'is_grayscale': False
            }), 400
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        colorized_filename = f"{current_user.id}_{unique_id}_colorized_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        colorized_path = os.path.join(user_folder, colorized_filename)
        
        logger.info(f"Colorizing photo {photo_id} using method: {method}")
        
        try:
            colorized_path, actual_method = colorizer.colorize_image(photo.file_path, colorized_path, method=method)
        except RuntimeError as e:
            if 'DNN model not available' in str(e) or 'not initialized' in str(e):
                if method == 'dnn':
                    return jsonify({
                        'success': False,
                        'error': 'DNN colorization model not available. Use method="basic" or method="auto" instead.'
                    }), 400
                else:
                    raise
            else:
                raise
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_colorized_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(colorized_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(colorized_path)
        
        new_photo = Photo(
            filename=colorized_filename,
            original_name=f"colorized_{photo.original_name}",
            file_path=colorized_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='colorization',
            user_id=current_user.id,
            album_id=photo.album_id,
            description=f"Colorized version of {photo.original_name}",
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='colorized'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created colorized photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Photo colorized successfully',
            'original_photo_id': photo_id,
            'colorized_photo_id': new_photo.id,
            'method_used': actual_method,
            'colorized_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=colorized_filename)
            }
        })
        
    except RuntimeError as e:
        logger.error(f"Colorization model error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Colorization failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Colorization failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photo/<int:photo_id>/check-grayscale', methods=['GET'])
@login_required
def check_grayscale_route(photo_id):
    """
    Check if a photo is grayscale (black and white)
    
    Args:
        photo_id: ID of the photo to check
        
    Returns:
        JSON with is_grayscale boolean
    """
    try:
        from photovault.utils.colorization import get_colorizer
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        colorizer = get_colorizer()
        
        try:
            is_grayscale = colorizer.is_grayscale(photo.file_path)
        except FileNotFoundError as e:
            logger.error(f"Photo file not found: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Photo file not found or has been deleted'
            }), 404
        except RuntimeError as e:
            logger.error(f"Photo file corrupted: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Photo file is corrupted or invalid'
            }), 500
        
        return jsonify({
            'success': True,
            'photo_id': photo_id,
            'is_grayscale': is_grayscale,
            'can_colorize': is_grayscale
        })
        
    except Exception as e:
        logger.error(f"Grayscale check failed for photo {photo_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check photo color mode'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@csrf.exempt
@hybrid_auth
def sketch_photo_route(current_user, photo_id):
    """
    Convert photo to sketch/drawing effect
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Request JSON:
        style: 'pencil' or 'pen' (optional, default: 'pencil')
        intensity: Blur intensity (0.1-1.0, optional, default: 0.5)
                  Lower values = more detail, Higher values = softer sketch
        
    Returns:
        JSON with success status and sketch photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        style = data.get('style', 'pencil')
        intensity = data.get('intensity', 0.5)
        
        if style not in ['pencil', 'pen']:
            return jsonify({
                'success': False,
                'error': 'Invalid style. Use pencil or pen'
            }), 400
        
        try:
            intensity = float(intensity)
            if intensity < 0.1 or intensity > 1.0:
                return jsonify({
                    'success': False,
                    'error': 'Invalid intensity. Must be between 0.1 and 1.0'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'Invalid intensity. Must be a number between 0.1 and 1.0'
            }), 400
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        sketch_filename = f"{current_user.id}_{unique_id}_sketch_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        sketch_path = os.path.join(user_folder, sketch_filename)
        
        logger.info(f"Creating sketch for photo {photo_id} using style: {style}, intensity: {intensity}")
        
        artistic_effects.create_sketch(photo.file_path, sketch_path, style=style, intensity=intensity)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_sketch_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(sketch_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(sketch_path)
        
        new_photo = Photo(
            filename=sketch_filename,
            original_name=f"sketch_{photo.original_name}",
            file_path=sketch_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='sketch'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created sketch photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sketch created successfully',
            'original_photo_id': photo_id,
            'sketch_photo_id': new_photo.id,
            'style_used': style,
            'intensity_used': intensity,
            'sketch_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=sketch_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Sketch creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Sketch creation failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/cartoon', methods=['POST'])
@csrf.exempt
@hybrid_auth
def cartoon_photo_route(current_user, photo_id):
    """
    Convert photo to cartoon/comic effect
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Request JSON:
        quality: 'fast', 'balanced', or 'high' (optional, default: 'balanced')
        edge_thickness: Edge detection block size (1-10, optional, default: 5)
                       Lower values = thinner edges, Higher values = thicker edges
        
    Returns:
        JSON with success status and cartoon photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        quality = data.get('quality', 'balanced')
        edge_thickness = data.get('edge_thickness', 5)
        
        if quality not in ['fast', 'balanced', 'high']:
            return jsonify({
                'success': False,
                'error': 'Invalid quality. Use fast, balanced, or high'
            }), 400
        
        try:
            edge_thickness = int(edge_thickness)
            if edge_thickness < 1 or edge_thickness > 10:
                return jsonify({
                    'success': False,
                    'error': 'Invalid edge_thickness. Must be integer between 1 and 10'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'Invalid edge_thickness. Must be an integer between 1 and 10'
            }), 400
        
        quality_params = {
            'fast': {'num_down': 1, 'num_bilateral': 5},
            'balanced': {'num_down': 2, 'num_bilateral': 7},
            'high': {'num_down': 2, 'num_bilateral': 10}
        }
        
        params = quality_params[quality]
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        cartoon_filename = f"{current_user.id}_{unique_id}_cartoon_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        cartoon_path = os.path.join(user_folder, cartoon_filename)
        
        logger.info(f"Creating cartoon for photo {photo_id} using quality: {quality}, edge_thickness: {edge_thickness}")
        
        artistic_effects.create_cartoon(
            photo.file_path, 
            cartoon_path, 
            num_down=params['num_down'],
            num_bilateral=params['num_bilateral'],
            edge_thickness=edge_thickness
        )
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_cartoon_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(cartoon_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(cartoon_path)
        
        new_photo = Photo(
            filename=cartoon_filename,
            original_name=f"cartoon_{photo.original_name}",
            file_path=cartoon_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='cartoon'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created cartoon photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Cartoon created successfully',
            'original_photo_id': photo_id,
            'cartoon_photo_id': new_photo.id,
            'quality_used': quality,
            'edge_thickness_used': edge_thickness,
            'cartoon_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=cartoon_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Cartoon creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Cartoon creation failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/oil-painting', methods=['POST'])
@csrf.exempt
@hybrid_auth
def oil_painting_photo_route(current_user, photo_id):
    """
    Convert photo to oil painting effect
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Request JSON:
        brush_size: Brush stroke size (1-15, optional, default: 7)
                   Lower values = fine detail, Higher values = broad strokes
        detail_level: Level of detail preservation (1-5, optional, default: 3)
                     Lower values = more smoothing, Higher values = more detail
        
    Returns:
        JSON with success status and oil painting photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        brush_size = data.get('brush_size', 7)
        detail_level = data.get('detail_level', 3)
        
        try:
            brush_size = int(brush_size)
            if brush_size < 1 or brush_size > 15:
                return jsonify({
                    'success': False,
                    'error': 'Invalid brush_size. Must be integer between 1 and 15'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'Invalid brush_size. Must be an integer between 1 and 15'
            }), 400
        
        try:
            detail_level = int(detail_level)
            if detail_level < 1 or detail_level > 5:
                return jsonify({
                    'success': False,
                    'error': 'Invalid detail_level. Must be integer between 1 and 5'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'Invalid detail_level. Must be an integer between 1 and 5'
            }), 400
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        oil_filename = f"{current_user.id}_{unique_id}_oil_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        oil_path = os.path.join(user_folder, oil_filename)
        
        logger.info(f"Creating oil painting for photo {photo_id} with brush_size: {brush_size}, detail_level: {detail_level}")
        
        artistic_effects.create_oil_painting(photo.file_path, oil_path, brush_size=brush_size, detail_level=detail_level)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_oil_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(oil_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(oil_path)
        
        new_photo = Photo(
            filename=oil_filename,
            original_name=f"oil_{photo.original_name}",
            file_path=oil_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='oil_painting'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created oil painting photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Oil painting created successfully',
            'original_photo_id': photo_id,
            'oil_photo_id': new_photo.id,
            'brush_size_used': brush_size,
            'detail_level_used': detail_level,
            'oil_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=oil_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Oil painting creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Oil painting creation failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/watercolor', methods=['POST'])
@csrf.exempt
@hybrid_auth
def watercolor_photo_route(current_user, photo_id):
    """
    Convert photo to watercolor painting effect
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Returns:
        JSON with success status and watercolor photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        watercolor_filename = f"{current_user.id}_{unique_id}_watercolor_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        watercolor_path = os.path.join(user_folder, watercolor_filename)
        
        logger.info(f"Creating watercolor for photo {photo_id}")
        
        artistic_effects.create_watercolor(photo.file_path, watercolor_path)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_watercolor_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(watercolor_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(watercolor_path)
        
        new_photo = Photo(
            filename=watercolor_filename,
            original_name=f"watercolor_{photo.original_name}",
            file_path=watercolor_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='watercolor'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created watercolor photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Watercolor created successfully',
            'original_photo_id': photo_id,
            'watercolor_photo_id': new_photo.id,
            'watercolor_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=watercolor_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Watercolor creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Watercolor creation failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/vintage', methods=['POST'])
@csrf.exempt
@hybrid_auth
def vintage_photo_route(current_user, photo_id):
    """
    Convert photo to vintage/sepia effect
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Request JSON:
        style: 'sepia', '1950s', '1970s', or 'polaroid' (optional, default: 'sepia')
        intensity: Intensity of sepia and vignette effect (0.1-1.0, optional, default: 0.7)
                  Lower values = subtle effect, Higher values = strong vintage look
        
    Returns:
        JSON with success status and vintage photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        style = data.get('style', 'sepia')
        intensity = data.get('intensity', 0.7)
        
        if style not in ['sepia', '1950s', '1970s', 'polaroid']:
            return jsonify({
                'success': False,
                'error': 'Invalid style. Use sepia, 1950s, 1970s, or polaroid'
            }), 400
        
        try:
            intensity = float(intensity)
            if intensity < 0.1 or intensity > 1.0:
                return jsonify({
                    'success': False,
                    'error': 'Invalid intensity. Must be between 0.1 and 1.0'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'Invalid intensity. Must be a number between 0.1 and 1.0'
            }), 400
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        vintage_filename = f"{current_user.id}_{unique_id}_vintage_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        vintage_path = os.path.join(user_folder, vintage_filename)
        
        logger.info(f"Creating vintage {style} for photo {photo_id} with intensity: {intensity}")
        
        artistic_effects.create_vintage_sepia(photo.file_path, vintage_path, style=style, intensity=intensity)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_vintage_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(vintage_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(vintage_path)
        
        new_photo = Photo(
            filename=vintage_filename,
            original_name=f"vintage_{photo.original_name}",
            file_path=vintage_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='vintage'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created vintage photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Vintage effect created successfully',
            'original_photo_id': photo_id,
            'vintage_photo_id': new_photo.id,
            'style_used': style,
            'intensity_used': intensity,
            'vintage_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=vintage_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Vintage creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Vintage creation failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/pop-art', methods=['POST'])
@csrf.exempt
@hybrid_auth
def pop_art_photo_route(current_user, photo_id):
    """
    Convert photo to pop art (Warhol style) effect
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Request JSON:
        colors: Number of colors 4-12 (optional, default: 8)
        
    Returns:
        JSON with success status and pop art photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        colors = data.get('colors', 8)
        
        if not isinstance(colors, int) or colors < 4 or colors > 12:
            return jsonify({
                'success': False,
                'error': 'Invalid colors. Must be integer between 4 and 12'
            }), 400
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        popart_filename = f"{current_user.id}_{unique_id}_popart_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        popart_path = os.path.join(user_folder, popart_filename)
        
        logger.info(f"Creating pop art for photo {photo_id} with {colors} colors")
        
        artistic_effects.create_pop_art(photo.file_path, popart_path, colors=colors)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_popart_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(popart_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(popart_path)
        
        new_photo = Photo(
            filename=popart_filename,
            original_name=f"popart_{photo.original_name}",
            file_path=popart_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='pop_art'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created pop art photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Pop art created successfully',
            'original_photo_id': photo_id,
            'popart_photo_id': new_photo.id,
            'colors_used': colors,
            'popart_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=popart_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Pop art creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Pop art creation failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/hdr', methods=['POST'])
@csrf.exempt
@hybrid_auth
def hdr_photo_route(current_user, photo_id):
    """
    Apply HDR tone mapping for dramatic, high-contrast images
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Returns:
        JSON with success status and HDR photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        hdr_filename = f"{current_user.id}_{unique_id}_hdr_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        hdr_path = os.path.join(user_folder, hdr_filename)
        
        logger.info(f"Creating HDR enhancement for photo {photo_id}")
        
        artistic_effects.create_hdr_enhancement(photo.file_path, hdr_path)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_hdr_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(hdr_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(hdr_path)
        
        new_photo = Photo(
            filename=hdr_filename,
            original_name=f"hdr_{photo.original_name}",
            file_path=hdr_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='hdr'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created HDR photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'HDR enhancement created successfully',
            'original_photo_id': photo_id,
            'hdr_photo_id': new_photo.id,
            'hdr_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=hdr_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"HDR enhancement failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'HDR enhancement failed due to unexpected error'
        }), 500


@photo_bp.route('/api/photos/<int:photo_id>/black-white', methods=['POST'])
@csrf.exempt
@hybrid_auth
def black_white_photo_route(current_user, photo_id):
    """
    Convert to high-quality black & white with professional toning
    
    Args:
        current_user: Authenticated user (from hybrid_auth decorator)
        photo_id: ID of the photo to convert
        
    Request JSON:
        style: 'classic', 'high_contrast', 'soft', 'film_noir', or 'selenium' (optional, default: 'classic')
        contrast: Additional contrast adjustment (-50 to +50, optional, default: 0)
                 Negative values = reduce contrast, Positive values = increase contrast
        
    Returns:
        JSON with success status and B&W photo information
    """
    try:
        from photovault.utils.artistic_effects import get_artistic_effects
        
        photo = Photo.query.get_or_404(photo_id)
        
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        data = request.get_json() or {}
        style = data.get('style', 'classic')
        contrast = data.get('contrast', 0)
        
        if style not in ['classic', 'high_contrast', 'soft', 'film_noir', 'selenium']:
            return jsonify({
                'success': False,
                'error': 'Invalid style. Use classic, high_contrast, soft, film_noir, or selenium'
            }), 400
        
        try:
            contrast = int(contrast)
            if contrast < -50 or contrast > 50:
                return jsonify({
                    'success': False,
                    'error': 'Invalid contrast. Must be integer between -50 and 50'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'error': 'Invalid contrast. Must be an integer between -50 and 50'
            }), 400
        
        artistic_effects = get_artistic_effects()
        
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = os.path.splitext(photo.filename)[1] or '.jpg'
        
        bw_filename = f"{current_user.id}_{unique_id}_bw_{timestamp}{file_extension}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        bw_path = os.path.join(user_folder, bw_filename)
        
        logger.info(f"Creating professional B&W ({style}, contrast: {contrast}) for photo {photo_id}")
        
        artistic_effects.create_professional_bw(photo.file_path, bw_path, style=style, contrast=contrast)
        
        thumbnail_path = None
        thumbnail_filename = f"{current_user.id}_{unique_id}_bw_thumb_{timestamp}.jpg"
        thumbnail_full_path = os.path.join(user_folder, thumbnail_filename)
        
        if create_thumbnail_local(bw_path, thumbnail_full_path):
            thumbnail_path = thumbnail_full_path
        
        image_info = get_image_info(bw_path)
        
        new_photo = Photo(
            filename=bw_filename,
            original_name=f"bw_{photo.original_name}",
            file_path=bw_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='artistic_effect',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='black_white'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Created B&W photo {new_photo.id} from original {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Black & white created successfully',
            'original_photo_id': photo_id,
            'bw_photo_id': new_photo.id,
            'style_used': style,
            'contrast_used': contrast,
            'bw_photo': {
                'id': new_photo.id,
                'filename': new_photo.filename,
                'original_name': new_photo.original_name,
                'width': new_photo.width,
                'height': new_photo.height,
                'file_size': new_photo.file_size,
                'created_at': new_photo.created_at.isoformat() if new_photo.created_at else None,
                'thumbnail_url': url_for('gallery.uploaded_file', 
                                        user_id=current_user.id, 
                                        filename=thumbnail_filename) if thumbnail_path else None,
                'image_url': url_for('gallery.uploaded_file', 
                                    user_id=current_user.id, 
                                    filename=bw_filename)
            }
        })
        
    except Exception as e:
        logger.error(f"Black & white creation failed for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Black & white creation failed due to unexpected error'
        }), 500
