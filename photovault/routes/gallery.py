"""
PhotoVault Gallery Routes
Simple gallery blueprint for photo management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, send_file, abort, current_app, Response, jsonify
from flask_login import login_required, current_user
from photovault.extensions import db, limiter
import os
import zipfile
import tempfile
import time
import io
from photovault.utils.enhanced_file_handler import get_file_content, file_exists_enhanced
from photovault.utils.jwt_auth import hybrid_auth

# Create the gallery blueprint
gallery_bp = Blueprint('gallery', __name__)

def generate_placeholder_image():
    """Generate a simple 1x1 transparent PNG as placeholder"""
    from PIL import Image
    
    # Create a 200x200 light gray placeholder
    img = Image.new('RGB', (200, 200), color=(240, 240, 240))
    
    # Save to bytes
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return img_io

@gallery_bp.route('/gallery')
@login_required
def gallery():
    """Gallery index - redirect to photos"""
    return redirect(url_for('gallery.photos'))

@gallery_bp.route('/gallery/photos')
@login_required  
def gallery_photos():
    """Redirect gallery/photos to photos for compatibility"""
    return redirect(url_for('gallery.photos'))

@gallery_bp.route('/dashboard')
@login_required
def dashboard():
    """Gallery dashboard"""
    try:
        from photovault.models import Photo, UserSubscription
        from sqlalchemy import func
        
        photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).limit(12).all()
        total_photos = Photo.query.filter_by(user_id=current_user.id).count()
        
        # Count edited photos (photos with edited_filename)
        edited_photos = Photo.query.filter_by(user_id=current_user.id).filter(Photo.edited_filename.isnot(None)).count()
        
        # Count original photos (photos without edited_filename)
        original_photos = Photo.query.filter_by(user_id=current_user.id).filter(Photo.edited_filename.is_(None)).count()
        
        # Calculate total storage used in MB
        total_storage_bytes = db.session.query(func.sum(Photo.file_size)).filter_by(user_id=current_user.id).scalar() or 0
        storage_used_mb = round(total_storage_bytes / (1024 * 1024), 2)
        
        # Get storage limit from user's active subscription
        active_subscription = UserSubscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        if active_subscription and active_subscription.plan:
            storage_limit_mb = active_subscription.plan.storage_gb * 1024
        else:
            storage_limit_mb = 100  # Default 100 MB for users without subscription
        
        storage_percent = (storage_used_mb / storage_limit_mb * 100) if storage_limit_mb > 0 else 0
        
    except Exception as e:
        photos = []
        total_photos = 0
        edited_photos = 0
        original_photos = 0
        storage_used_mb = 0
        storage_limit_mb = 100
        storage_percent = 0
        flash('Photo database not ready yet.', 'info')
    
    return render_template('gallery/dashboard.html', 
                         photos=photos, 
                         total_photos=total_photos,
                         edited_photos=edited_photos,
                         original_photos=original_photos,
                         storage_used_mb=storage_used_mb,
                         storage_limit_mb=storage_limit_mb,
                         storage_percent=storage_percent)

@gallery_bp.route('/photos')
@login_required
def photos():
    """All photos page with optional colorization filter"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        filter_type = request.args.get('filter', 'all')
        
        # Start with base query
        query = Photo.query.filter_by(user_id=current_user.id)
        
        # Apply colorization filter
        if filter_type == 'dnn':
            # Photos colorized with DNN method
            query = query.filter(Photo.enhancement_metadata['colorization']['method'].astext == 'dnn')
        elif filter_type == 'ai':
            # Photos colorized with AI method
            query = query.filter(Photo.enhancement_metadata['colorization']['method'].astext == 'ai_guided_dnn')
        elif filter_type == 'uncolorized':
            # Photos without colorization
            query = query.filter(Photo.enhancement_metadata.is_(None))
        # else: show all photos (filter_type == 'all' or any other value)
        
        photos = query.order_by(Photo.created_at.desc())\
                     .paginate(page=page, per_page=20, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready yet.', 'info')
        filter_type = 'all'
    
    return render_template('gallery/photos.html', photos=photos, current_filter=filter_type)

@gallery_bp.route('/albums')
@login_required
def albums():
    """Albums page"""
    try:
        from photovault.models import Album
        albums = Album.query.filter_by(user_id=current_user.id).order_by(Album.created_at.desc()).all()
    except Exception as e:
        albums = []
        flash('Album database not ready yet.', 'info')
    
    return render_template('gallery/albums.html', albums=albums)

@gallery_bp.route('/upload')
@login_required
def upload():
    """Upload page - redirect to main upload route"""
    return redirect(url_for('photo.upload_page'))

@gallery_bp.route('/photo/<int:photo_id>')
@login_required
def view_photo(photo_id):
    """View single photo"""
    try:
        from photovault.models import Photo
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
        return render_template('view_photo.html', photo=photo, tagged_people=[], all_people=[])
    except Exception as e:
        flash('Photo not found or database not ready.', 'error')
        return redirect(url_for('gallery.dashboard'))

@gallery_bp.route('/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Delete a photo"""
    try:
        from photovault.models import Photo
        from photovault import db
        
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
        
        # Delete file from disk
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        # Delete thumbnail if exists
        if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
            os.remove(photo.thumbnail_path)
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully.', 'success')
    except Exception as e:
        flash('Error deleting photo or database not ready.', 'error')
    
    return redirect(url_for('gallery.dashboard'))
@gallery_bp.route('/photos/originals')
@login_required
def originals():
    """Show only original photos (no edited versions)"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .filter(~Photo.filename.contains('enhanced'))\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready yet.', 'info')
    
    return render_template('gallery/originals.html', photos=photos)

@gallery_bp.route('/photos/edited')
@login_required
def edited():
    """Show only edited photos"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .filter(Photo.edited_filename.isnot(None))\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready.', 'info')
    
    return render_template('gallery/edited.html', photos=photos)

@gallery_bp.route('/photos/compare')
@login_required
def compare_photos():
    """Show photos with side-by-side comparison of original and edited versions"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .filter(Photo.edited_filename.isnot(None))\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=6, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready.', 'info')
    
    return render_template('gallery/compare.html', photos=photos)

@gallery_bp.route('/photo/<int:photo_id>/compare')
@login_required
def compare_single_photo(photo_id):
    """View single photo with side-by-side original vs edited comparison"""
    try:
        from photovault.models import Photo
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
        
        # Ensure the photo has an edited version
        if not photo.edited_filename:
            flash('This photo does not have an edited version for comparison.', 'warning')
            return redirect(url_for('gallery.view_photo', photo_id=photo_id))
        
        return render_template('gallery/compare_single.html', photo=photo)
    except Exception as e:
        flash('Photo not found or database not ready.', 'error')
        return redirect(url_for('gallery.dashboard'))

@gallery_bp.route('/debug/file-diagnostics')
@login_required
def file_diagnostics():
    """Debug page for file integrity diagnostics"""
    # Temporarily allow all users for debugging (remove after fixing the issue)
    # if not current_user.is_admin:
    #     flash('Access denied. Admin privileges required.', 'error')
    #     return redirect(url_for('gallery.dashboard'))
    
    return render_template('debug/file_diagnostics.html')

@gallery_bp.route('/uploads/<int:user_id>/<path:filename>')
@limiter.exempt  # Exempt from rate limiting - already protected by JWT/session auth
@hybrid_auth
def uploaded_file(current_user, user_id, filename):
    """Secure route for serving uploaded files with authentication checks (supports both session and JWT)"""
    # Security check: Users can access their own files, admin can access all files,
    # or if the photo is shared in a family vault where the user is a member
    access_allowed = (
        current_user.id == user_id or 
        current_user.is_admin
    )
    
    # If not the owner or admin, check if photo is shared in a family vault where user is a member
    if not access_allowed:
        try:
            from photovault.models import Photo, VaultPhoto, FamilyMember
            
            # Find the photo being requested
            original_filename = filename
            if filename.endswith('_thumb.jpg') or filename.endswith('_thumb.png') or filename.endswith('_thumb.jpeg'):
                base_name = filename.rsplit('_thumb.', 1)[0]
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    potential_original = base_name + ext
                    test_photo = Photo.query.filter_by(user_id=user_id).filter(
                        (Photo.filename == potential_original) | (Photo.edited_filename == potential_original)
                    ).first()
                    if test_photo:
                        original_filename = potential_original
                        break
            
            # Find the photo record
            photo = Photo.query.filter_by(user_id=user_id).filter(
                (Photo.filename == original_filename) | (Photo.edited_filename == original_filename)
            ).first()
            
            if photo:
                # Check if this photo is shared in any family vault where current user is a member
                shared_in_vault = db.session.query(VaultPhoto).join(FamilyMember, VaultPhoto.vault_id == FamilyMember.vault_id).filter(
                    VaultPhoto.photo_id == photo.id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.status == 'active'
                ).first()
                
                if shared_in_vault:
                    access_allowed = True
        except Exception as e:
            # If there's any error in the vault check, deny access for security
            pass
    
    if not access_allowed:
        abort(403)
    
    # Verify the file exists and belongs to the user
    try:
        from photovault.models import Photo
        
        # Handle thumbnail files by checking for original file
        original_filename = filename
        is_thumbnail_request = filename.endswith('_thumb.jpg') or filename.endswith('_thumb.png') or filename.endswith('_thumb.jpeg')
        
        if is_thumbnail_request:
            # Extract original filename by removing _thumb suffix
            base_name = filename.rsplit('_thumb.', 1)[0]
            
            # First try to find by checking App Storage paths
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                potential_original = base_name + ext
                app_storage_original = f"users/{user_id}/{potential_original}"
                if file_exists_enhanced(app_storage_original):
                    original_filename = potential_original
                    break
            else:
                # Fallback to checking local filesystem
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    if os.path.exists(os.path.join(current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads'), str(user_id), base_name + ext)):
                        original_filename = base_name + ext
                        break
                else:
                    # If original file not found for thumbnail, return placeholder
                    current_app.logger.warning(f"Thumbnail requested for missing original file: {filename}")
                    return redirect(url_for('static', filename='img/placeholder.png'))
        
        photo = Photo.query.filter_by(user_id=user_id).filter(
            (Photo.filename == original_filename) | (Photo.edited_filename == original_filename)
        ).first()
        
        # Check if this is a profile picture/avatar (not a photo)
        is_avatar = filename.startswith('avatar_')
        
        # Handle avatars separately - they're not in Photo table, they're in User table
        if is_avatar:
            from photovault.models import User
            user = User.query.get(user_id)
            # Safe check for profile_picture attribute (may not exist in older database schemas)
            user_profile_pic = getattr(user, 'profile_picture', None) if user else None
            if user and user_profile_pic == filename:
                current_app.logger.info(f"Serving avatar for user {user_id}: {filename}")
            else:
                current_app.logger.warning(f"Avatar file requested but not current profile picture: {filename} for user {user_id}")
            
            # Try to serve avatar from App Storage first
            app_storage_path = f"users/{user_id}/{filename}"
            
            if file_exists_enhanced(app_storage_path):
                success, file_content = get_file_content(app_storage_path)
                if success:
                    import mimetypes
                    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                    return Response(
                        file_content,
                        mimetype=content_type,
                        headers={
                            'Content-Disposition': f'inline; filename="{filename}"',
                            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                            'Pragma': 'no-cache',
                            'Expires': '0'
                        }
                    )
            
            # Fallback to local filesystem for avatar
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
            avatar_path = os.path.join(upload_folder, str(user_id), filename)
            
            if os.path.exists(avatar_path):
                current_app.logger.info(f"Serving avatar from local storage: {avatar_path}")
                response = send_file(avatar_path)
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            else:
                current_app.logger.error(f"Avatar file not found: {avatar_path}")
                return send_file(generate_placeholder_image(), mimetype='image/png')
        
        # For regular photos (not avatars), photo record must exist
        if not photo:
            if is_thumbnail_request:
                current_app.logger.warning(f"Photo record not found for thumbnail: {filename}")
                return send_file(generate_placeholder_image(), mimetype='image/png')
            else:
                abort(404)
        
        # Try to serve from App Storage first, then fallback to local filesystem
        
        # Check if this is likely an App Storage path (based on how we store photos)
        app_storage_path = f"users/{user_id}/{filename}"
        
        if file_exists_enhanced(app_storage_path):
            # Serve from App Storage
            success, file_content = get_file_content(app_storage_path)
            if success:
                # Determine content type
                import mimetypes
                content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                
                return Response(
                    file_content,
                    mimetype=content_type,
                    headers={
                        'Content-Disposition': f'inline; filename="{filename}"',
                        'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                )
            else:
                # App Storage exists check passed but download failed
                current_app.logger.error(f"App Storage download failed for {app_storage_path}: {file_content}")
                # If it's a thumbnail request, serve placeholder instead of 404
                if is_thumbnail_request:
                    current_app.logger.warning(f"Serving placeholder for failed thumbnail: {filename}")
                    return send_file(generate_placeholder_image(), mimetype='image/png')
                abort(404)
        
        # Fallback to local filesystem
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        
        # Handle both /data/ and /data/uploads/ configurations
        # Check if files exist in uploads subdirectory
        uploads_with_subdir = os.path.join(upload_folder, 'uploads', str(user_id))
        uploads_dir = os.path.join(upload_folder, str(user_id))
        
        # Use the one that exists, prefer the direct path
        if os.path.exists(uploads_with_subdir) and not os.path.exists(uploads_dir):
            uploads_dir = uploads_with_subdir
            current_app.logger.info(f"Using uploads subdirectory: {uploads_dir}")
        
        # IMPORTANT: Serve the exact filename requested
        # Original files should always be in the canonical location: uploads_dir/filename
        # Edited files use edited_path
        
        file_to_serve = None
        
        if photo.filename == filename:
            # User requested the original - construct canonical path
            file_to_serve = os.path.join(uploads_dir, filename)
            
            # If not found in canonical location, try fallback locations for legacy data
            # BUT reject any fallback that points to the edited file
            if not os.path.exists(file_to_serve) and photo.file_path:
                file_path = photo.file_path
                fallback_path = None
                
                if os.path.isabs(file_path):
                    # Try absolute path first
                    if os.path.exists(file_path):
                        fallback_path = file_path
                    else:
                        # Remap old absolute paths (e.g., /data/uploads/1/file.jpg) to current UPLOAD_FOLDER
                        path_parts = file_path.split('/')
                        for i, part in enumerate(path_parts):
                            if part.isdigit() and i + 1 < len(path_parts):
                                extracted_user_id = part
                                remaining_path = '/'.join(path_parts[i+1:])
                                remapped_path = os.path.join(upload_folder, extracted_user_id, remaining_path)
                                if os.path.exists(remapped_path):
                                    fallback_path = remapped_path
                                    current_app.logger.info(f"Remapped {file_path} to {remapped_path}")
                                    break
                elif file_path.startswith(upload_folder + '/'):
                    fallback_path = file_path
                elif file_path.startswith('uploads/') or file_path.startswith('users/'):
                    path_parts = file_path.split('/', 1)
                    if len(path_parts) > 1:
                        fallback_path = os.path.join(upload_folder, path_parts[1])
                elif '/' in file_path and file_path.split('/')[0].isdigit():
                    fallback_path = os.path.join(upload_folder, file_path)
                else:
                    # Relative path within user directory
                    fallback_path = os.path.join(uploads_dir, file_path)
                
                # Only use fallback if it exists AND doesn't match the edited filename
                if fallback_path and os.path.exists(fallback_path):
                    # Reject if this path points to the edited file
                    fallback_basename = os.path.basename(fallback_path)
                    if not (photo.edited_filename and fallback_basename == photo.edited_filename):
                        file_to_serve = fallback_path
                            
        elif photo.edited_filename == filename:
            # User requested the edited version
            file_to_serve = os.path.join(uploads_dir, filename)
            
            # If not found, try edited_path if available
            if not os.path.exists(file_to_serve) and hasattr(photo, 'edited_path') and photo.edited_path:
                edited_path = photo.edited_path
                if os.path.isabs(edited_path):
                    file_to_serve = edited_path
                elif edited_path.startswith('uploads/') or edited_path.startswith('users/'):
                    path_parts = edited_path.split('/', 1)
                    if len(path_parts) > 1:
                        file_to_serve = os.path.join(upload_folder, path_parts[1])
                    else:
                        file_to_serve = os.path.join(uploads_dir, edited_path)
                else:
                    file_to_serve = os.path.join(uploads_dir, edited_path)
        else:
            # Unknown filename - try uploads directory
            file_to_serve = os.path.join(uploads_dir, filename)
        
        # Check if file is in object storage first (profile pictures)
        if photo.file_path and (photo.file_path.startswith('users/') or photo.file_path.startswith('uploads/')):
            try:
                from photovault.services.app_storage_service import app_storage
                import io
                
                success, file_bytes = app_storage.download_file(photo.file_path)
                if success:
                    current_app.logger.info(f"Serving file from object storage: {photo.file_path}")
                    response = send_file(
                        io.BytesIO(file_bytes),
                        mimetype=f'image/{filename.rsplit(".", 1)[-1] if "." in filename else "jpeg"}'
                    )
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    return response
            except Exception as storage_err:
                current_app.logger.warning(f"Object storage download failed: {storage_err}")
        
        if file_to_serve and os.path.exists(file_to_serve):
            response = send_file(file_to_serve)
            # Add cache control headers to prevent stale image caching
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            # Try additional fallback locations before serving placeholder
            fallback_locations = []
            
            # Fallback 1: Try the exact file_path from database (absolute or relative)
            if photo.file_path:
                if os.path.isabs(photo.file_path):
                    # Absolute path - try it directly first
                    fallback_locations.append(photo.file_path)
                    
                    # IMPORTANT: Remap old absolute paths to current UPLOAD_FOLDER
                    # Handle paths like /data/uploads/1/file.jpg from Railway
                    # Extract the meaningful parts: user_id and filename
                    path_parts = photo.file_path.split('/')
                    if len(path_parts) >= 2:
                        # Try to find user_id and filename in the path
                        # Patterns: /data/uploads/1/file.jpg or /uploads/1/file.jpg
                        for i, part in enumerate(path_parts):
                            if part.isdigit() and i + 1 < len(path_parts):
                                # Found user_id, reconstruct path with current UPLOAD_FOLDER
                                extracted_user_id = part
                                remaining_path = '/'.join(path_parts[i+1:])
                                remapped_path = os.path.join(upload_folder, extracted_user_id, remaining_path)
                                fallback_locations.append(remapped_path)
                                current_app.logger.info(f"Remapped absolute path {photo.file_path} to {remapped_path}")
                                break
                else:
                    # Relative path - try different interpretations
                    fallback_locations.append(photo.file_path)
                    fallback_locations.append(os.path.join(upload_folder, photo.file_path))
            
            # Fallback 2: Try base upload folder without user subdirectory
            fallback_locations.append(os.path.join(upload_folder, filename))
            
            # Fallback 3: If file_path is an App Storage path, try converting it to local
            if photo.file_path and (photo.file_path.startswith('users/') or photo.file_path.startswith('uploads/')):
                path_parts = photo.file_path.split('/', 1)
                if len(path_parts) > 1:
                    fallback_locations.append(os.path.join(upload_folder, path_parts[1]))
            
            # Try each fallback location
            for fallback in fallback_locations:
                if fallback and os.path.exists(fallback):
                    current_app.logger.info(f"File found at fallback location: {fallback}")
                    response = send_file(fallback)
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    return response
            
            current_app.logger.error(f"File not found: {file_to_serve} (requested filename: {filename}). Tried fallbacks: {fallback_locations}")
            # Serve placeholder for both thumbnails and regular images instead of 404
            current_app.logger.warning(f"Serving placeholder for missing file: {file_to_serve}")
            return send_file(generate_placeholder_image(), mimetype='image/png')
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {filename} for user {user_id}: {e}")
        # Serve placeholder for any exception instead of 404
        current_app.logger.warning(f"Serving placeholder due to exception: {filename}")
        return send_file(generate_placeholder_image(), mimetype='image/png')

@gallery_bp.route('/api/photos/bulk-download', methods=['POST'])
@login_required
def bulk_download_photos():
    """Create ZIP file of selected photos and serve for download"""
    try:
        from photovault.models import Photo
        
        # Get photo IDs from form data
        photo_ids = request.form.getlist('photo_ids')
        
        if not photo_ids:
            flash('No photos selected for download.', 'warning')
            return redirect(url_for('gallery.photos'))
        
        # Server-side limits for resource protection
        MAX_PHOTOS = 50  # Limit bulk downloads to 50 photos
        MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500MB limit
        
        if len(photo_ids) > MAX_PHOTOS:
            flash(f'Too many photos selected. Maximum {MAX_PHOTOS} photos allowed per download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Validate that all photos belong to current user
        photos = Photo.query.filter(
            Photo.id.in_(photo_ids),
            Photo.user_id == current_user.id
        ).all()
        
        if not photos:
            flash('No valid photos found for download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Pre-validate file sizes to avoid resource exhaustion
        total_size = 0
        valid_photos = []
        
        for photo in photos:
            filename_to_use = photo.edited_filename if photo.edited_filename else photo.filename
            file_size = 0
            
            # Check App Storage first
            app_storage_path = f"users/{photo.user_id}/{filename_to_use}"
            if file_exists_enhanced(app_storage_path):
                valid_photos.append((photo, app_storage_path, None))
                # Estimate file size (cannot get exact size from App Storage easily)
                file_size = 5 * 1024 * 1024  # Estimate 5MB per photo for safety
            elif photo.file_path:
                # Check local filesystem
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                file_path = photo.file_path
                
                if os.path.isabs(file_path):
                    full_path = file_path
                elif file_path.startswith(upload_folder + '/'):
                    full_path = file_path
                elif file_path.startswith('uploads/') or file_path.startswith('users/'):
                    path_parts = file_path.split('/', 1)
                    if len(path_parts) > 1:
                        full_path = os.path.join(upload_folder, path_parts[1])
                    else:
                        full_path = os.path.join(upload_folder, str(photo.user_id), filename_to_use)
                else:
                    full_path = os.path.join(upload_folder, str(photo.user_id), file_path)
                
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    valid_photos.append((photo, None, full_path))
            
            total_size += file_size
            if total_size > MAX_TOTAL_SIZE:
                flash(f'Selected photos exceed maximum download size limit ({MAX_TOTAL_SIZE // (1024*1024)}MB).', 'error')
                return redirect(url_for('gallery.photos'))
        
        if not valid_photos:
            flash('No valid photo files found for download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Use TemporaryDirectory for guaranteed cleanup
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = int(time.time())
            zip_filename = f"photovault_photos_{timestamp}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                added_files = 0
                file_count = {}  # Track duplicate filenames
                
                for photo, app_storage_path, local_path in valid_photos:
                    try:
                        filename_to_use = photo.edited_filename if photo.edited_filename else photo.filename
                        original_name = photo.original_name or filename_to_use
                        
                        # Sanitize filename for ZIP (prevent path traversal)
                        original_name = os.path.basename(original_name).replace('/', '_').replace('\\', '_')
                        
                        # Handle duplicate filenames by adding counter
                        base_name, ext = os.path.splitext(original_name)
                        if original_name in file_count:
                            file_count[original_name] += 1
                            zip_filename_final = f"{base_name}_{file_count[original_name]}{ext}"
                        else:
                            file_count[original_name] = 0
                            zip_filename_final = original_name
                        
                        # Add file to ZIP with memory-efficient approach
                        if app_storage_path:
                            # App Storage: Load file content
                            success, file_content = get_file_content(app_storage_path)
                            if success and file_content:
                                zipf.writestr(zip_filename_final, file_content)
                                added_files += 1
                                current_app.logger.info(f"Added photo {photo.id} from App Storage as {zip_filename_final}")
                            else:
                                current_app.logger.warning(f"Failed to get App Storage content for photo {photo.id}")
                        elif local_path:
                            # Local filesystem: Use ZIP's built-in file reading for better memory usage
                            zipf.write(local_path, zip_filename_final)
                            added_files += 1
                            current_app.logger.info(f"Added photo {photo.id} from local storage as {zip_filename_final}")
                    except Exception as e:
                        current_app.logger.warning(f"Error adding photo {photo.id} to ZIP: {e}")
                        continue
            
            if added_files == 0:
                flash('No photo files could be found for download.', 'error')
                return redirect(url_for('gallery.photos'))
            
            current_app.logger.info(f"Serving ZIP download with {added_files} photos for user {current_user.id}")
            
            # Send the ZIP file (TemporaryDirectory will auto-cleanup)
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"PhotoVault_Photos_{added_files}_photos.zip",
                mimetype='application/zip'
            )
            # TemporaryDirectory context manager ensures cleanup
            
    except Exception as e:
        current_app.logger.error(f"Error creating bulk download: {e}")
        flash('Failed to create download. Please try again.', 'error')
        return redirect(url_for('gallery.photos'))

@gallery_bp.route('/api/photos/download-all', methods=['POST'])
@login_required
def download_all_photos():
    """Download all photos for the current user as a ZIP file"""
    try:
        from photovault.models import Photo
        
        # Get all photos for current user
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        if not photos:
            flash('You have no photos to download.', 'info')
            return redirect(url_for('gallery.photos'))
        
        # Resource limits
        MAX_PHOTOS = 200  # Allow more for download all
        MAX_TOTAL_SIZE = 1024 * 1024 * 1024  # 1GB limit
        
        if len(photos) > MAX_PHOTOS:
            flash(f'You have too many photos ({len(photos)}). Maximum {MAX_PHOTOS} photos allowed per download. Please use selective download instead.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Pre-validate file sizes
        total_size = 0
        valid_photos = []
        
        for photo in photos:
            filename_to_use = photo.edited_filename if photo.edited_filename else photo.filename
            file_size = 0
            
            # Check App Storage first
            app_storage_path = f"users/{photo.user_id}/{filename_to_use}"
            if file_exists_enhanced(app_storage_path):
                valid_photos.append((photo, app_storage_path, None))
                file_size = 5 * 1024 * 1024  # Estimate 5MB per photo
            elif photo.file_path:
                # Check local filesystem
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                file_path = photo.file_path
                
                if os.path.isabs(file_path):
                    full_path = file_path
                elif file_path.startswith(upload_folder + '/'):
                    full_path = file_path
                elif file_path.startswith('uploads/') or file_path.startswith('users/'):
                    path_parts = file_path.split('/', 1)
                    if len(path_parts) > 1:
                        full_path = os.path.join(upload_folder, path_parts[1])
                    else:
                        full_path = os.path.join(upload_folder, str(photo.user_id), filename_to_use)
                else:
                    full_path = os.path.join(upload_folder, str(photo.user_id), file_path)
                
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    valid_photos.append((photo, None, full_path))
            
            total_size += file_size
            if total_size > MAX_TOTAL_SIZE:
                flash(f'Your photo collection exceeds the maximum download size limit ({MAX_TOTAL_SIZE // (1024*1024)}MB). Please use selective download instead.', 'error')
                return redirect(url_for('gallery.photos'))
        
        if not valid_photos:
            flash('No valid photo files found for download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Create ZIP file
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = int(time.time())
            zip_filename = f"photovault_all_photos_{timestamp}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                added_files = 0
                file_count = {}
                
                for photo, app_storage_path, local_path in valid_photos:
                    try:
                        filename_to_use = photo.edited_filename if photo.edited_filename else photo.filename
                        original_name = photo.original_name or filename_to_use
                        
                        # Sanitize filename
                        original_name = os.path.basename(original_name).replace('/', '_').replace('\\', '_')
                        
                        # Handle duplicate filenames
                        base_name, ext = os.path.splitext(original_name)
                        if original_name in file_count:
                            file_count[original_name] += 1
                            zip_filename_final = f"{base_name}_{file_count[original_name]}{ext}"
                        else:
                            file_count[original_name] = 0
                            zip_filename_final = original_name
                        
                        # Add file to ZIP
                        if app_storage_path:
                            success, file_content = get_file_content(app_storage_path)
                            if success and file_content:
                                zipf.writestr(zip_filename_final, file_content)
                                added_files += 1
                        elif local_path:
                            zipf.write(local_path, zip_filename_final)
                            added_files += 1
                    except Exception as e:
                        current_app.logger.warning(f"Error adding photo {photo.id} to ZIP: {e}")
                        continue
            
            if added_files == 0:
                flash('No photo files could be found for download.', 'error')
                return redirect(url_for('gallery.photos'))
            
            current_app.logger.info(f"Serving complete photo collection ZIP with {added_files} photos for user {current_user.id}")
            
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"PhotoVault_All_Photos_{added_files}_photos.zip",
                mimetype='application/zip'
            )
            
    except Exception as e:
        current_app.logger.error(f"Error creating download all ZIP: {e}")
        flash('Failed to create download. Please try again.', 'error')
        return redirect(url_for('gallery.photos'))
