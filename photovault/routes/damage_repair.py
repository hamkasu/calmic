"""
Damage Repair Routes
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Handles photo damage repair and restoration features
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from photovault.models import Photo, db
from photovault.utils.damage_repair import damage_repair
from photovault.services.ai_service import get_ai_service
from photovault.utils.file_handler import get_image_info, create_thumbnail
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

damage_repair_bp = Blueprint('damage_repair', __name__)


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/scratches', methods=['POST'])
@login_required
def repair_scratches(photo_id):
    """Remove scratches and dust from a photo"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get parameters
        data = request.get_json() or {}
        sensitivity = int(data.get('sensitivity', 5))
        inpaint_radius = int(data.get('inpaint_radius', 3))
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_scratch_repaired_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Repair scratches
        result_path, stats = damage_repair.remove_scratches_and_dust(
            photo.file_path, output_path, sensitivity, inpaint_radius
        )
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"scratch_repaired_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='damage_repair',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='scratch_repair'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Scratches repaired for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': f'Scratches removed successfully ({stats["damage_percentage"]:.2f}% damage repaired)',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'repaired_filename': new_photo.filename,
            'user_id': current_user.id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error repairing scratches for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/stains', methods=['POST'])
@login_required
def repair_stains(photo_id):
    """Remove stains and discoloration from a photo"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get parameters
        data = request.get_json() or {}
        strength = float(data.get('strength', 1.5))
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_stain_removed_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Remove stains
        result_path, stats = damage_repair.remove_stains(
            photo.file_path, output_path, strength
        )
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"stain_removed_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='damage_repair',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='stain_removal'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Stains removed for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': 'Stains removed successfully',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'repaired_filename': new_photo.filename,
            'user_id': current_user.id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error removing stains for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/cracks', methods=['POST'])
@login_required
def repair_cracks(photo_id):
    """Repair cracks in a photo"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get parameters
        data = request.get_json() or {}
        sensitivity = int(data.get('sensitivity', 5))
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_crack_repaired_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Repair cracks
        result_path, stats = damage_repair.repair_cracks(
            photo.file_path, output_path, sensitivity
        )
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"crack_repaired_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='damage_repair',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='crack_repair'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Cracks repaired for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': f'Cracks repaired successfully ({stats["crack_percentage"]:.2f}% cracks repaired)',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'repaired_filename': new_photo.filename,
            'user_id': current_user.id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error repairing cracks for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/severe-cracks', methods=['POST'])
@login_required
def repair_severe_cracks(photo_id):
    """Repair severe cracks in a heavily damaged photo"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get parameters
        data = request.get_json() or {}
        intensity = data.get('intensity', 'high')  # 'medium', 'high', 'maximum'
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_severe_crack_repaired_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Repair severe cracks
        logger.info(f"Starting severe crack repair for photo {photo_id} with {intensity} intensity")
        result_path, stats = damage_repair.repair_severe_cracks(
            photo.file_path, output_path, intensity
        )
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"severe_crack_repaired_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='severe_damage_repair',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='severe_crack_repair'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Severe cracks repaired for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': f'Severe cracks repaired successfully ({stats["crack_percentage"]:.2f}% damage repaired with {stats["inpaint_passes"]} passes)',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'repaired_filename': new_photo.filename,
            'user_id': current_user.id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error repairing severe cracks for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/comprehensive', methods=['POST'])
@login_required
def comprehensive_repair(photo_id):
    """Apply comprehensive damage repair (all methods)"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get parameters
        data = request.get_json() or {}
        scratch_sensitivity = int(data.get('scratch_sensitivity', 5))
        crack_sensitivity = int(data.get('crack_sensitivity', 5))
        stain_strength = float(data.get('stain_strength', 1.5))
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_fully_repaired_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Apply comprehensive repair
        result_path, stats = damage_repair.comprehensive_repair(
            photo.file_path, output_path,
            scratch_sensitivity, crack_sensitivity, stain_strength
        )
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"fully_repaired_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='damage_repair',
            user_id=current_user.id,
            album_id=photo.album_id,
            original_photo_id=photo_id,
            is_enhanced_version=True,
            enhancement_type='comprehensive_repair'
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"Comprehensive repair completed for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': 'Comprehensive damage repair completed successfully',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'repaired_filename': new_photo.filename,
            'user_id': current_user.id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in comprehensive repair for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/detect-damage', methods=['GET'])
@login_required
def detect_damage(photo_id):
    """Detect and analyze damage in a photo using AI"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get AI service
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({
                'success': False,
                'error': 'AI service not available. Please configure GEMINI_API_KEY'
            }), 503
        
        # Detect damage
        damage_info = ai_service.detect_damage(photo.file_path)
        
        logger.info(f"Damage detection completed for photo {photo_id}")
        
        return jsonify({
            'success': True,
            'photo_id': photo_id,
            'damage_info': damage_info
        })
        
    except Exception as e:
        logger.error(f"Error detecting damage for photo {photo_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/ai', methods=['POST'])
@login_required
def ai_restoration(photo_id):
    """Use AI to restore damaged photos with GFPGAN or CodeFormer"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Import AI restoration service
        from photovault.utils.ai_restoration import ai_restoration as ai_service
        
        if not ai_service.enabled:
            return jsonify({
                'success': False,
                'error': 'AI restoration not available. Please configure REPLICATE_API_TOKEN'
            }), 503
        
        # Get parameters
        data = request.get_json() or {}
        model = data.get('model', 'codeformer')  # 'gfpgan' or 'codeformer'
        quality = data.get('quality', 'balanced')  # 'fast', 'balanced', 'quality', 'maximum'
        fidelity = float(data.get('fidelity', 0.5))  # CodeFormer only
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_ai_{model}_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Perform AI restoration
        logger.info(f"Starting AI restoration for photo {photo_id} with model={model}, quality={quality}")
        
        if model == 'gfpgan':
            # Map quality presets to GFPGAN parameters
            scale_map = {'fast': 1, 'balanced': 2, 'quality': 2, 'maximum': 4}
            version_map = {'fast': 'v1.3', 'balanced': 'v1.4', 'quality': 'v1.4', 'maximum': 'v1.4'}
            
            result_path, stats = ai_service.restore_with_gfpgan(
                photo.file_path,
                output_path,
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
            
            result_path, stats = ai_service.restore_with_codeformer(
                photo.file_path,
                output_path,
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
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"ai_{model}_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='ai_restoration',
            user_id=current_user.id,
            album_id=photo.album_id
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"AI restoration completed for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': f'AI restoration completed successfully using {model.upper()}',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'repaired_filename': new_photo.filename,
            'user_id': current_user.id,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in AI restoration for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@damage_repair_bp.route('/api/photos/<int:photo_id>/repair/ai-inpaint', methods=['POST'])
@login_required
def ai_inpaint(photo_id):
    """Use AI to inpaint damaged areas in a photo"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        
        # Verify ownership
        if photo.user_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access to this photo'
            }), 403
        
        # Get parameters
        data = request.get_json() or {}
        prompt = data.get('prompt')
        
        # Get AI service
        ai_service = get_ai_service()
        
        if not ai_service.openai_client:
            return jsonify({
                'success': False,
                'error': 'OpenAI not available. Please configure OPENAI_API_KEY for AI inpainting'
            }), 503
        
        # Create output path
        output_dir = os.path.dirname(photo.file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{current_user.username}_ai_inpainted_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Perform AI inpainting
        result_path, metadata = ai_service.inpaint_damage_ai(
            photo.file_path, output_path, prompt=prompt
        )
        
        # Create thumbnail
        thumbnail_path = create_thumbnail(result_path, current_user.id)
        
        # Get image info
        image_info = get_image_info(result_path)
        
        # Create new photo record
        new_photo = Photo(
            filename=output_filename,
            original_name=f"ai_inpainted_{photo.original_name}",
            file_path=result_path,
            thumbnail_path=thumbnail_path,
            file_size=image_info.get('size_bytes') if image_info else None,
            width=image_info.get('width') if image_info else None,
            height=image_info.get('height') if image_info else None,
            mime_type=f"image/{image_info.get('format', 'jpeg').lower()}" if image_info else 'image/jpeg',
            upload_source='ai_damage_repair',
            user_id=current_user.id,
            album_id=photo.album_id
        )
        
        db.session.add(new_photo)
        db.session.commit()
        
        logger.info(f"AI inpainting completed for photo {photo_id}, new photo {new_photo.id}")
        
        return jsonify({
            'success': True,
            'message': 'AI inpainting completed successfully',
            'original_photo_id': photo_id,
            'repaired_photo_id': new_photo.id,
            'metadata': metadata
        })
        
    except Exception as e:
        logger.error(f"Error in AI inpainting for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
