"""
Image Enhancement Utilities for PhotoVault
Advanced image enhancement with OpenCV
"""

import numpy as np
from PIL import Image, ImageEnhance, ExifTags
import json
import logging
from typing import Dict, Tuple, Optional, Union
import os
import cv2

logger = logging.getLogger(__name__)

# OpenCV functionality enabled
OPENCV_AVAILABLE = True
logger.info("Image enhancement with OpenCV - advanced features enabled")

class ImageEnhancer:
    """Advanced image enhancement using OpenCV and PIL"""
    
    def __init__(self):
        self.default_settings = {
            'brightness': 1.0,
            'contrast': 1.0,
            'sharpness': 1.0,
            'color': 1.0,
            'denoise': False,
            'clahe_enabled': False,
            'auto_levels': False,
            'unsharp_radius': 1.5,
            'unsharp_amount': 1.5,
            'denoise_strength': 10
        }
    
    def apply_unsharp_mask(self, image: np.ndarray, radius: float = 1.5, 
                           amount: float = 1.5) -> np.ndarray:
        """
        Apply unsharp mask sharpening using OpenCV
        
        Args:
            image: Input image as numpy array (BGR format)
            radius: Gaussian blur radius (kernel size)
            amount: Sharpening strength (1.0 = no change, >1.0 = sharpen)
            
        Returns:
            Sharpened image as numpy array
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available, skipping unsharp mask")
            return image
        
        # Calculate kernel size from radius (must be odd)
        kernel_size = int(radius * 2) * 2 + 1
        
        # Create Gaussian blurred version
        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        
        # Apply unsharp mask formula: sharp = original + amount * (original - blurred)
        sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
        
        return sharpened
    
    def apply_denoise(self, image: np.ndarray, h: int = 10, 
                      templateWindowSize: int = 7, 
                      searchWindowSize: int = 21) -> np.ndarray:
        """
        Apply Non-Local Means denoising using OpenCV
        
        Args:
            image: Input image as numpy array (BGR format)
            h: Filter strength (higher = more denoising, 10 is typical)
            templateWindowSize: Size of template patch (should be odd, 7 is typical)
            searchWindowSize: Size of search area (should be odd, 21 is typical)
            
        Returns:
            Denoised image as numpy array
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available, skipping denoise")
            return image
        
        # Apply Non-Local Means denoising for colored images
        denoised = cv2.fastNlMeansDenoisingColored(
            image, 
            None, 
            h=h, 
            hColor=h,
            templateWindowSize=templateWindowSize, 
            searchWindowSize=searchWindowSize
        )
        
        return denoised
    
    def auto_enhance_photo(self, image_path: str, output_path: str = None, 
                          settings: Dict = None) -> Tuple[str, Dict]:
        """
        Advanced photo enhancement using OpenCV and PIL
        
        Args:
            image_path: Path to input image
            output_path: Path for enhanced output (if None, overwrites original)
            settings: Custom enhancement settings
            
        Returns:
            Tuple of (output_path, applied_settings)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Starting advanced enhancement for: {image_path}")
        
        # Merge default with custom settings
        enhancement_settings = self.default_settings.copy()
        if settings:
            enhancement_settings.update(settings)
        
        try:
            # Load image with PIL
            pil_img = Image.open(image_path)
            
            # Convert to RGB if needed
            if pil_img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', pil_img.size, (255, 255, 255))
                if pil_img.mode == 'RGBA':
                    background.paste(pil_img, mask=pil_img.split()[-1])
                else:
                    background.paste(pil_img, mask=pil_img.split()[-1])
                pil_img = background
            elif pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            
            # Convert to OpenCV format for advanced processing
            cv_img = None
            if OPENCV_AVAILABLE:
                cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
                # Apply denoising first if enabled
                if enhancement_settings.get('denoise', False):
                    denoise_strength = enhancement_settings.get('denoise_strength', 10)
                    logger.info(f"Applying Non-Local Means denoising with strength {denoise_strength}")
                    cv_img = self.apply_denoise(cv_img, h=denoise_strength)
                
                # Apply unsharp mask sharpening if sharpness > 1.0
                if enhancement_settings.get('sharpness', 1.0) > 1.0:
                    unsharp_radius = enhancement_settings.get('unsharp_radius', 1.5)
                    unsharp_amount = enhancement_settings.get('unsharp_amount', 1.5)
                    logger.info(f"Applying unsharp mask with radius {unsharp_radius}, amount {unsharp_amount}")
                    cv_img = self.apply_unsharp_mask(cv_img, radius=unsharp_radius, amount=unsharp_amount)
                
                # Convert back to PIL
                pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            
            # Apply PIL enhancements for brightness/contrast/color
            if enhancement_settings.get('brightness', 1.0) != 1.0:
                enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = enhancer.enhance(enhancement_settings['brightness'])
            
            if enhancement_settings.get('contrast', 1.0) != 1.0:
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(enhancement_settings['contrast'])
            
            # Note: Skip PIL sharpness if we already applied unsharp mask
            if not OPENCV_AVAILABLE or enhancement_settings.get('sharpness', 1.0) <= 1.0:
                if enhancement_settings.get('sharpness', 1.0) != 1.0:
                    enhancer = ImageEnhance.Sharpness(pil_img)
                    pil_img = enhancer.enhance(enhancement_settings['sharpness'])
            
            if enhancement_settings.get('color', 1.0) != 1.0:
                enhancer = ImageEnhance.Color(pil_img)
                pil_img = enhancer.enhance(enhancement_settings['color'])
            
            # Determine output path
            if output_path is None:
                output_path = image_path
            
            # Save enhanced image
            quality = 95
            pil_img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            logger.info(f"Advanced enhancement completed: {output_path}")
            
            return output_path, enhancement_settings
            
        except Exception as e:
            logger.error(f"Enhancement failed for {image_path}: {e}")
            raise
    
    def get_enhancement_suggestions(self, image_path: str) -> Dict:
        """Get basic enhancement suggestions - advanced analysis disabled"""
        logger.info("Advanced enhancement analysis disabled - providing basic suggestions")
        return {
            'brightness_adjustment': 0.0,
            'contrast_adjustment': 0.0,
            'suggested_settings': self.default_settings,
            'analysis_method': 'basic_pil_only'
        }

# Global instance
enhancer = ImageEnhancer()

def auto_enhance_photo(image_path: str, output_path: str = None, 
                      settings: Dict = None) -> Tuple[str, Dict]:
    """Convenience function for auto-enhancing photos - basic PIL only"""
    return enhancer.auto_enhance_photo(image_path, output_path, settings)