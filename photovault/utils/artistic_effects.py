"""
Artistic Effects Utilities
Provides sketch and cartoonify effects for photos using OpenCV
"""

import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ArtisticEffects:
    """
    Provides artistic transformation effects for photos
    """
    
    def __init__(self):
        """Initialize artistic effects processor"""
        self.initialized = True
        logger.info("Artistic effects processor initialized")
    
    def create_sketch(self, image_path, output_path=None, style='pencil'):
        """
        Convert photo to sketch/drawing effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save sketch (optional)
            style: 'pencil' for pencil sketch or 'pen' for pen sketch
            
        Returns:
            Path to sketch image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Invert grayscale image
            inverted = 255 - gray
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
            
            # Invert blurred image
            inverted_blur = 255 - blurred
            
            # Create pencil sketch by dividing grayscale by inverted blur
            sketch = cv2.divide(gray, inverted_blur, scale=256.0)
            
            if style == 'pen':
                # For pen sketch, make it darker and more contrasted
                sketch = cv2.adaptiveThreshold(
                    gray, 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 
                    11, 2
                )
            
            # Convert grayscale sketch to BGR for consistency
            sketch_bgr = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
            
            if output_path:
                cv2.imwrite(output_path, sketch_bgr)
                logger.info(f"Sketch created and saved to {output_path} (style: {style})")
                return output_path
            else:
                sketch_rgb = cv2.cvtColor(sketch_bgr, cv2.COLOR_BGR2RGB)
                return Image.fromarray(sketch_rgb)
                
        except Exception as e:
            logger.error(f"Sketch creation failed: {e}")
            raise
    
    def create_cartoon(self, image_path, output_path=None, num_down=2, num_bilateral=7):
        """
        Convert photo to cartoon/comic effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save cartoon (optional)
            num_down: Number of downsampling steps (default: 2)
            num_bilateral: Number of bilateral filter iterations (default: 7)
            
        Returns:
            Path to cartoon image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Downsample image using Gaussian pyramid
            img_color = img
            for _ in range(num_down):
                img_color = cv2.pyrDown(img_color)
            
            # Apply bilateral filter to reduce noise while keeping edges sharp
            for _ in range(num_bilateral):
                img_color = cv2.bilateralFilter(img_color, d=9, sigmaColor=9, sigmaSpace=7)
            
            # Upsample image to original size
            for _ in range(num_down):
                img_color = cv2.pyrUp(img_color)
            
            # Ensure the upsampled image matches the original size
            img_color = cv2.resize(img_color, (img.shape[1], img.shape[0]))
            
            # Convert to grayscale and apply median blur
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_blur = cv2.medianBlur(img_gray, 7)
            
            # Detect edges using adaptive threshold
            img_edge = cv2.adaptiveThreshold(
                img_blur, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                blockSize=9,
                C=2
            )
            
            # Convert edge image to BGR
            img_edge = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2BGR)
            
            # Combine color and edges using bitwise AND
            cartoon = cv2.bitwise_and(img_color, img_edge)
            
            if output_path:
                cv2.imwrite(output_path, cartoon)
                logger.info(f"Cartoon created and saved to {output_path}")
                return output_path
            else:
                cartoon_rgb = cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)
                return Image.fromarray(cartoon_rgb)
                
        except Exception as e:
            logger.error(f"Cartoon creation failed: {e}")
            raise
    
    def create_colored_sketch(self, image_path, output_path=None):
        """
        Convert photo to colored pencil sketch effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save colored sketch (optional)
            
        Returns:
            Path to colored sketch image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Use OpenCV's built-in pencilSketch function
            # This creates a colored pencil sketch effect
            _, sketch_color = cv2.pencilSketch(
                img, 
                sigma_s=60, 
                sigma_r=0.07, 
                shade_factor=0.05
            )
            
            if output_path:
                cv2.imwrite(output_path, sketch_color)
                logger.info(f"Colored sketch created and saved to {output_path}")
                return output_path
            else:
                sketch_rgb = cv2.cvtColor(sketch_color, cv2.COLOR_BGR2RGB)
                return Image.fromarray(sketch_rgb)
                
        except Exception as e:
            logger.error(f"Colored sketch creation failed: {e}")
            raise


# Global instance
_artistic_effects = None

def get_artistic_effects():
    """Get or create the global artistic effects instance"""
    global _artistic_effects
    if _artistic_effects is None:
        _artistic_effects = ArtisticEffects()
    return _artistic_effects
