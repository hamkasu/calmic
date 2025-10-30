"""
Image Optimization Utilities
Generates blurhash and optimized thumbnails for fast gallery loading
"""
import os
from PIL import Image
import blurhash

def generate_blurhash(image_path, components_x=4, components_y=3):
    """
    Generate blurhash string from image
    
    Args:
        image_path: Path to the image file
        components_x: Horizontal components (4-9, default 4)
        components_y: Vertical components (3-9, default 3)
    
    Returns:
        Blurhash string or None if failed
    """
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            
            hash_string = blurhash.encode(img, components_x, components_y)
            return hash_string
    except Exception as e:
        print(f"Error generating blurhash: {e}")
        return None


def generate_grid_thumbnail(image_path, output_path, size=200):
    """
    Generate small optimized thumbnail for gallery grid
    
    Args:
        image_path: Path to the source image
        output_path: Path where thumbnail will be saved
        size: Thumbnail size (default 200x200)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"Error generating grid thumbnail: {e}")
        return False


def process_image_for_gallery(image_path, user_id, filename):
    """
    Complete image processing for gallery optimization
    Generates both blurhash and grid thumbnail
    
    Args:
        image_path: Path to the original image
        user_id: User ID for organizing thumbnails
        filename: Original filename
    
    Returns:
        dict with 'blurhash' and 'grid_thumbnail_path' or None values
    """
    result = {
        'blurhash': None,
        'grid_thumbnail_path': None
    }
    
    result['blurhash'] = generate_blurhash(image_path)
    
    uploads_dir = os.path.join('uploads', str(user_id))
    os.makedirs(uploads_dir, exist_ok=True)
    
    name_without_ext = os.path.splitext(filename)[0]
    grid_thumb_filename = f"{name_without_ext}_grid.jpg"
    grid_thumb_path = os.path.join(uploads_dir, grid_thumb_filename)
    
    if generate_grid_thumbnail(image_path, grid_thumb_path, size=200):
        result['grid_thumbnail_path'] = grid_thumb_path
    
    return result
