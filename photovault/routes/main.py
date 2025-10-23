"""
PhotoVault Main Routes Blueprint
This should only contain routes, not a Flask app
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import current_user, login_required

# Create the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Get actual stats from database
    try:
        from photovault.models import Photo, User
        total_photos = Photo.query.count()
        total_users = User.query.count()
        
        stats = {
            'total_photos': total_photos,
            'total_users': total_users
        }
    except Exception as e:
        print(f"Stats error: {str(e)}")
        stats = {'total_photos': 0, 'total_users': 0}
    
    return render_template('index.html', stats=stats)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with pagination - Rebuilt for reliability"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Initialize default values
    stats = {
        'total_photos': 0,
        'edited_photos': 0,
        'original_photos': 0,
        'total_size_mb': 0.0,
        'storage_limit_mb': 100,
        'storage_usage_percent': 0.0
    }
    pagination = {
        'page': 1,
        'per_page': 25,
        'total_photos': 0,
        'total_pages': 0,
        'has_prev': False,
        'has_next': False,
        'prev_num': None,
        'next_num': None
    }
    photos_with_memos = []
    
    try:
        # Get page number from query parameter (default to 1)
        page = request.args.get('page', 1, type=int)
        per_page = 25
        
        logger.info(f"Loading dashboard for user {current_user.username} (ID: {current_user.id}), page {page}")
        
        # Import models
        from photovault.models import Photo, VoiceMemo, UserSubscription
        from photovault.extensions import db
        from sqlalchemy import func
        
        # Calculate photo statistics
        total_photos = Photo.query.filter_by(user_id=current_user.id).count()
        logger.info(f"Total photos: {total_photos}")
        
        # Count edited photos
        edited_photos = Photo.query.filter_by(user_id=current_user.id)\
                              .filter(Photo.edited_filename.isnot(None))\
                              .count()
        original_photos = total_photos - edited_photos
        logger.info(f"Edited photos: {edited_photos}, Original: {original_photos}")
        
        # Calculate storage
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        total_size_bytes = sum(photo.file_size or 0 for photo in photos)
        total_size_mb = round(total_size_bytes / 1024 / 1024, 2) if total_size_bytes > 0 else 0.0
        logger.info(f"Storage used: {total_size_mb} MB")
        
        # Get subscription info
        user_subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
        if user_subscription and user_subscription.plan:
            storage_limit_mb = user_subscription.plan.storage_gb * 1024
            logger.info(f"Subscription: {user_subscription.plan.name}, Limit: {storage_limit_mb} MB")
        else:
            storage_limit_mb = 100
            logger.info("No subscription - using default 100 MB limit")
        
        # Calculate percentage
        storage_usage_percent = round((total_size_mb / storage_limit_mb * 100), 2) if storage_limit_mb > 0 else 0.0
        
        # Update stats dictionary
        stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos,
            'original_photos': original_photos,
            'total_size_mb': total_size_mb,
            'storage_limit_mb': storage_limit_mb,
            'storage_usage_percent': storage_usage_percent
        }
        logger.info(f"Stats calculated: {stats}")
        
        # Get paginated photos with voice memo counts
        offset = (page - 1) * per_page
        
        photos_query = db.session.query(
            Photo,
            func.count(VoiceMemo.id).label('voice_memo_count')
        ).outerjoin(VoiceMemo).filter(
            Photo.user_id == current_user.id
        ).group_by(Photo.id).order_by(Photo.created_at.desc())
        
        paginated_photos = photos_query.limit(per_page).offset(offset).all()
        
        # Attach voice memo counts
        photos_with_memos = []
        for photo, memo_count in paginated_photos:
            photo.voice_memo_count = memo_count
            photos_with_memos.append(photo)
        
        # Calculate pagination
        total_pages = (total_photos + per_page - 1) // per_page if total_photos > 0 else 0
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_photos': total_photos,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None
        }
        
        logger.info(f"Rendering dashboard with {len(photos_with_memos)} photos")
        
    except Exception as e:
        logger.error(f"Dashboard error for user {current_user.id}: {str(e)}", exc_info=True)
        # Keep default values - already set at top
    
    return render_template('dashboard.html', stats=stats, photos=photos_with_memos, pagination=pagination)

@main_bp.route('/upload')
@login_required
def upload():
    """Upload page"""
    return render_template('upload.html', user=current_user)

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Initialize with defaults
    stats = {
        'total_photos': 0,
        'edited_photos': 0,
        'total_size': 0,
        'member_since': 'Unknown'
    }
    
    try:
        # Calculate user statistics
        from photovault.models import Photo
        from datetime import datetime
        import os
        
        # Get all photos for current user
        user_photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        # Calculate statistics - update file sizes if they're missing
        total_photos = len(user_photos)
        edited_photos = sum(1 for photo in user_photos if photo.edited_filename and photo.edited_filename.strip())
        
        # Calculate total size, and update database if file_size is missing
        total_size = 0
        for photo in user_photos:
            if photo.file_size and photo.file_size > 0:
                total_size += photo.file_size
            else:
                # Try to get file size from disk and update database
                try:
                    if os.path.exists(photo.file_path):
                        file_size = os.path.getsize(photo.file_path)
                        photo.file_size = file_size
                        total_size += file_size
                        # Don't commit yet - batch update
                except:
                    pass
        
        # Commit any file size updates
        try:
            from photovault.extensions import db
            db.session.commit()
        except:
            pass
        
        # Format member since date
        if current_user.created_at:
            member_since = current_user.created_at.strftime('%B %Y')
        else:
            member_since = 'Unknown'
        
        # Calculate storage in MB (float for accurate display)
        total_size_mb = round(total_size / 1024 / 1024, 2) if total_size > 0 else 0
        storage_limit_mb = 500  # 500MB limit per user
        storage_usage_percent = min(100, round(total_size_mb / storage_limit_mb * 100, 1)) if storage_limit_mb > 0 else 0
            
        stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos, 
            'total_size': total_size,
            'total_size_mb': total_size_mb,
            'storage_usage_percent': storage_usage_percent,
            'storage_limit_mb': storage_limit_mb,
            'member_since': member_since
        }
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        # stats already initialized with defaults above
        
    return render_template('profile.html', user=current_user, stats=stats)

@main_bp.route('/gallery')
@login_required
def gallery():
    """Gallery page"""
    try:
        from photovault.models import Photo
        
        # Get all photos for the current user with voice memo counts
        from photovault.models import VoiceMemo
        from photovault.extensions import db
        from sqlalchemy import func
        
        photos_with_counts = db.session.query(
            Photo,
            func.count(VoiceMemo.id).label('voice_memo_count')
        ).outerjoin(VoiceMemo).filter(
            Photo.user_id == current_user.id
        ).group_by(Photo.id).order_by(Photo.created_at.desc()).all()
        
        # Convert to a format the template expects
        photos_with_memos = []
        for photo, memo_count in photos_with_counts:
            photo.voice_memo_count = memo_count
            photos_with_memos.append(photo)
        
        return render_template('gallery/dashboard.html', photos=photos_with_memos, total_photos=len(photos_with_memos))
    except Exception as e:
        print(f"Gallery error: {str(e)}")
        return render_template('gallery/dashboard.html', photos=[], total_photos=0)

@main_bp.route('/photos/<int:photo_id>/edit')
@login_required
def edit_photo(photo_id):
    """Photo editor page"""
    try:
        from photovault.models import Photo
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return redirect(url_for('main.dashboard'))
            
        return render_template('editor.html', photo=photo)
    except Exception as e:
        print(f"Edit photo error: {str(e)}")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/advanced-enhancement')
@login_required
def advanced_enhancement():
    """Advanced Image Enhancement page"""
    try:
        from photovault.models import Photo
        from photovault.utils.image_enhancement import OPENCV_AVAILABLE
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 50  # Show 50 photos per page
        
        # Get user's photos with pagination
        photos_pagination = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('advanced_enhancement.html', 
                             photos=photos_pagination.items,
                             pagination=photos_pagination,
                             opencv_available=OPENCV_AVAILABLE)
    except Exception as e:
        print(f"Advanced enhancement error: {str(e)}")
        flash('Error accessing advanced enhancement features.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/photos/<int:photo_id>/enhance')
@login_required
def enhance_photo(photo_id):
    """Advanced Image Enhancement page for specific photo"""
    try:
        from photovault.models import Photo
        from photovault.utils.image_enhancement import OPENCV_AVAILABLE
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return redirect(url_for('main.dashboard'))
            
        return render_template('advanced_enhancement.html', 
                             photo=photo,
                             opencv_available=OPENCV_AVAILABLE)
    except Exception as e:
        print(f"Enhanced photo error: {str(e)}")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/people')
@login_required
def people():
    """People management page"""
    try:
        from photovault.models import Person
        from photovault.extensions import db
        from sqlalchemy import select
        
        # Get all people for the current user with pagination (SQLAlchemy 2.0 compatible)
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        # Build the query using SQLAlchemy 2.0 select() syntax with where() clause
        stmt = select(Person).where(Person.user_id == current_user.id).order_by(Person.name.asc())
        
        # Use db.paginate() instead of Query.paginate() for SQLAlchemy 2.0
        people = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
        
        return render_template('people.html', people=people)
    except Exception as e:
        print(f"People page error: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('people.html', people=None)

@main_bp.route('/montage')
@login_required
def montage():
    """Photo montage creation page"""
    try:
        from photovault.models import Photo
        # Get user's photos for montage creation
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        return render_template('montage.html', photos=photos)
    except Exception as e:
        flash('Error loading montage page.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/sharpening')
@login_required
def sharpening():
    """Photo sharpening page"""
    try:
        from photovault.models import Photo
        # Get user's photos for sharpening
        photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).limit(20).all()
        return render_template('sharpening.html', photos=photos)
    except Exception as e:
        print(f"Sharpening page error: {str(e)}")
        flash('Error loading sharpening page.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/damage-repair')
@login_required
def damage_repair():
    """Photo damage repair page"""
    try:
        from photovault.models import Photo
        # Get user's photos for damage repair
        photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).limit(20).all()
        return render_template('damage_repair.html', photos=photos)
    except Exception as e:
        print(f"Damage repair page error: {str(e)}")
        flash('Error loading damage repair page.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/people/add', methods=['POST'])
@login_required
def add_person():
    """Add a new person - Robust implementation"""
    from photovault.models import Person
    from photovault.extensions import db
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        nickname = request.form.get('nickname', '').strip()
        relationship = request.form.get('relationship', '').strip()
        birth_year_str = request.form.get('birth_year', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Validate name (required)
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('main.people'))
        
        # Validate birth year (optional)
        birth_year_value = None
        if birth_year_str:
            try:
                birth_year_value = int(birth_year_str)
                if birth_year_value < 1900 or birth_year_value > 2025:
                    flash('Birth year must be between 1900 and 2025.', 'error')
                    return redirect(url_for('main.people'))
            except ValueError:
                flash('Birth year must be a valid number.', 'error')
                return redirect(url_for('main.people'))
        
        # Create new person using property assignment (SQLAlchemy 2.0)
        person = Person()
        person.user_id = current_user.id
        person.name = name
        person.nickname = nickname if nickname else None
        person.relationship = relationship if relationship else None
        person.birth_year = birth_year_value
        person.notes = notes if notes else None
        
        # Save to database
        db.session.add(person)
        db.session.commit()
        
        logger.info(f"✅ Added person: {name} (ID: {person.id}) for user {current_user.id}")
        flash(f'{name} has been added successfully!', 'success')
        return redirect(url_for('main.people'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Add person error: {str(e)}", exc_info=True)
        flash('Error adding person. Please try again.', 'error')
        return redirect(url_for('main.people'))

@main_bp.route('/people/<int:person_id>/edit', methods=['POST'])
@login_required
def edit_person(person_id):
    """Edit an existing person - Robust implementation"""
    from photovault.models import Person
    from photovault.extensions import db
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get person and verify ownership
        person = Person.query.get_or_404(person_id)
        
        if person.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('main.people'))
        
        # Get form data
        name = request.form.get('name', '').strip()
        nickname = request.form.get('nickname', '').strip()
        relationship = request.form.get('relationship', '').strip()
        birth_year_str = request.form.get('birth_year', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Validate name (required)
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('main.people'))
        
        # Validate birth year (optional)
        birth_year_value = None
        if birth_year_str:
            try:
                birth_year_value = int(birth_year_str)
                if birth_year_value < 1900 or birth_year_value > 2025:
                    flash('Birth year must be between 1900 and 2025.', 'error')
                    return redirect(url_for('main.people'))
            except ValueError:
                flash('Birth year must be a valid number.', 'error')
                return redirect(url_for('main.people'))
        
        # Update person properties
        person.name = name
        person.nickname = nickname if nickname else None
        person.relationship = relationship if relationship else None
        person.birth_year = birth_year_value
        person.notes = notes if notes else None
        
        # Save changes
        db.session.commit()
        
        logger.info(f"✅ Updated person: {name} (ID: {person.id}) for user {current_user.id}")
        flash(f'{name} has been updated successfully!', 'success')
        return redirect(url_for('main.people'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Edit person error: {str(e)}", exc_info=True)
        flash('Error updating person. Please try again.', 'error')
        return redirect(url_for('main.people'))

@main_bp.route('/api', methods=['GET', 'HEAD'])
def api_health():
    """API health check endpoint - no database required"""
    return jsonify({'status': 'ok', 'service': 'PhotoVault'}), 200

@main_bp.route('/api/health/db', methods=['GET'])
def db_health():
    """Database health check endpoint"""
    from photovault.extensions import db
    import logging
    
    try:
        # Try a simple database query
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ok', 'database': 'connected'}), 200
    except Exception as e:
        # Log full error details for debugging but don't expose them publicly
        logging.error(f"Database health check failed: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'database': 'disconnected'}), 500

@main_bp.route('/health', methods=['GET', 'HEAD'])
def health_check():
    """Simple health check for Railway/production monitoring"""
    return 'OK', 200

@main_bp.route('/api/debug/plans', methods=['GET'])
def debug_plans():
    """Debug endpoint to check subscription plans in database"""
    try:
        from photovault.models import SubscriptionPlan
        from photovault.extensions import db
        
        plans = SubscriptionPlan.query.all()
        plans_data = [{
            'id': p.id,
            'name': p.name,
            'display_name': p.display_name,
            'price_myr': float(p.price_myr),
            'total_price_myr': p.total_price_myr,
            'sst_amount': p.sst_amount,
            'is_active': p.is_active
        } for p in plans]
        
        return jsonify({
            'status': 'ok',
            'count': len(plans),
            'plans': plans_data
        }), 200
    except Exception as e:
        import logging
        logging.error(f"Debug plans error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'type': type(e).__name__
        }), 500

@main_bp.route('/api/person/delete/<int:person_id>', methods=['DELETE'])
@login_required
def delete_person(person_id):
    """Delete a person - Robust implementation"""
    from photovault.models import Person
    from photovault.extensions import db
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get person and verify ownership
        person = Person.query.get_or_404(person_id)
        
        if person.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Delete person (cascade will handle related records)
        name = person.name
        db.session.delete(person)
        db.session.commit()
        
        logger.info(f"✅ Deleted person: {name} (ID: {person_id}) for user {current_user.id}")
        return jsonify({'success': True, 'message': f'{name} deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Delete person error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error deleting person'}), 500

@main_bp.route('/test-recording')
@login_required
def test_recording():
    """Voice memo recording test page"""
    try:
        from photovault.models import Photo
        
        # Get user's first photo for testing, or create a test photo
        photo = Photo.query.filter_by(user_id=current_user.id).first()
        
        if not photo:
            # No photos - show message
            return render_template('test_recording.html', photo=None)
        
        return render_template('test_recording.html', photo=photo)
    except Exception as e:
        print(f"Test recording error: {str(e)}")
        flash('Error loading test recording page.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/test-recording/<int:photo_id>/upload', methods=['POST'])
@login_required
def test_recording_upload(photo_id):
    """Upload test voice memo"""
    try:
        from photovault.models import Photo, VoiceMemo
        from photovault.extensions import db
        from werkzeug.utils import secure_filename
        import os
        from datetime import datetime
        
        # Verify photo ownership
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo:
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # Get audio file
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        # Get duration from form
        duration = request.form.get('duration', 0)
        try:
            duration = int(float(duration))
        except:
            duration = 0
        
        # Save the file
        filename = secure_filename(f"voice_memo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m4a")
        upload_folder = os.path.join('photovault', 'static', 'uploads', str(current_user.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        audio_file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create voice memo record
        voice_memo = VoiceMemo()
        voice_memo.photo_id = photo.id
        voice_memo.filename = filename
        voice_memo.duration = duration
        voice_memo.file_size = file_size
        voice_memo.created_at = datetime.utcnow()
        
        db.session.add(voice_memo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Voice memo uploaded successfully!',
            'voice_memo': {
                'id': voice_memo.id,
                'filename': voice_memo.filename,
                'duration': voice_memo.duration,
                'file_size_mb': round(file_size / 1024 / 1024, 2)
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/download-all')
@login_required
def download_all():
    """Download all user photos as a ZIP file"""
    import os
    import zipfile
    import tempfile
    from datetime import datetime
    from photovault.models import Photo
    from photovault.services.app_storage_service import app_storage
    from flask import current_app
    
    try:
        # Get all photos for the current user
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        if not photos:
            flash('No photos to download', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Create a temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for photo in photos:
                # Process original photo
                if photo.filename:
                    file_added = False
                    
                    # Check if file is in object storage (starts with users/ or uploads/)
                    if photo.filename.startswith('users/') or photo.filename.startswith('uploads/'):
                        # Download from object storage
                        success, file_bytes = app_storage.download_file(photo.filename)
                        if success:
                            archive_name = f"original/{photo.original_name or os.path.basename(photo.filename)}"
                            zipf.writestr(archive_name, file_bytes)
                            file_added = True
                    else:
                        # Try local file system
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                        original_path = os.path.join(upload_folder, str(photo.user_id), photo.filename)
                        if os.path.exists(original_path):
                            archive_name = f"original/{photo.original_name or photo.filename}"
                            zipf.write(original_path, archive_name)
                            file_added = True
                
                # Process edited photo if exists
                if photo.edited_filename:
                    file_added = False
                    
                    # Check if file is in object storage
                    if photo.edited_filename.startswith('users/') or photo.edited_filename.startswith('uploads/'):
                        # Download from object storage
                        success, file_bytes = app_storage.download_file(photo.edited_filename)
                        if success:
                            archive_name = f"edited/{photo.original_name or os.path.basename(photo.edited_filename)}"
                            zipf.writestr(archive_name, file_bytes)
                            file_added = True
                    else:
                        # Try local file system
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                        edited_path = os.path.join(upload_folder, str(photo.user_id), photo.edited_filename)
                        if os.path.exists(edited_path):
                            archive_name = f"edited/{photo.original_name or photo.edited_filename}"
                            zipf.write(edited_path, archive_name)
                            file_added = True
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_filename = f"StoryKeep_Photos_{current_user.username}_{timestamp}.zip"
        
        # Send the file
        return send_file(
            temp_zip.name,
            mimetype='application/zip',
            as_attachment=True,
            download_name=download_filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error creating download: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))