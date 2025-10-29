"""
Artistic Effects Utilities
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

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
    
    def create_sketch(self, image_path, output_path=None, style='pencil', intensity=0.5):
        """
        Convert photo to sketch/drawing effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save sketch (optional)
            style: 'pencil' for pencil sketch or 'pen' for pen sketch
            intensity: Blur intensity for sketch effect (0.1-1.0, default: 0.5)
                      Lower values = more detail, Higher values = softer sketch
            
        Returns:
            Path to sketch image if output_path provided, else PIL Image
        """
        try:
            # Validate intensity parameter
            intensity = max(0.1, min(1.0, float(intensity)))
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Invert grayscale image
            inverted = 255 - gray
            
            # Apply Gaussian blur with intensity-controlled kernel size
            # Map intensity (0.1-1.0) to kernel size (5-41)
            kernel_size = int(5 + (intensity * 36))
            if kernel_size % 2 == 0:
                kernel_size += 1
            blurred = cv2.GaussianBlur(inverted, (kernel_size, kernel_size), 0)
            
            # Invert blurred image
            inverted_blur = 255 - blurred
            
            # Create pencil sketch by dividing grayscale by inverted blur
            sketch = cv2.divide(gray, inverted_blur, scale=256.0)
            
            if style == 'pen':
                # For pen sketch, make it darker and more contrasted
                # Adjust block size based on intensity
                block_size = int(7 + (intensity * 8))
                if block_size % 2 == 0:
                    block_size += 1
                sketch = cv2.adaptiveThreshold(
                    gray, 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 
                    block_size, 2
                )
            
            # Convert grayscale sketch to BGR for consistency
            sketch_bgr = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
            
            if output_path:
                cv2.imwrite(output_path, sketch_bgr)
                logger.info(f"Sketch created and saved to {output_path} (style: {style}, intensity: {intensity})")
                return output_path
            else:
                sketch_rgb = cv2.cvtColor(sketch_bgr, cv2.COLOR_BGR2RGB)
                return Image.fromarray(sketch_rgb)
                
        except Exception as e:
            logger.error(f"Sketch creation failed: {e}")
            raise
    
    def create_cartoon(self, image_path, output_path=None, num_down=2, num_bilateral=7, edge_thickness=5):
        """
        Convert photo to cartoon/comic effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save cartoon (optional)
            num_down: Number of downsampling steps (default: 2)
            num_bilateral: Number of bilateral filter iterations (default: 7)
            edge_thickness: Edge detection block size (1-10, default: 5)
                          Lower values = thinner edges, Higher values = thicker edges
            
        Returns:
            Path to cartoon image if output_path provided, else PIL Image
        """
        try:
            # Validate edge_thickness parameter
            edge_thickness = max(1, min(10, int(edge_thickness)))
            
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
            
            # Detect edges using adaptive threshold with configurable block size
            # Map edge_thickness (1-10) to blockSize (5-23)
            block_size = 5 + (edge_thickness - 1) * 2
            if block_size % 2 == 0:
                block_size += 1
            
            img_edge = cv2.adaptiveThreshold(
                img_blur, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                blockSize=block_size,
                C=2
            )
            
            # Convert edge image to BGR
            img_edge = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2BGR)
            
            # Combine color and edges using bitwise AND
            cartoon = cv2.bitwise_and(img_color, img_edge)
            
            if output_path:
                cv2.imwrite(output_path, cartoon)
                logger.info(f"Cartoon created and saved to {output_path} (edge_thickness: {edge_thickness})")
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
    
    def create_oil_painting(self, image_path, output_path=None, size=7, dynRatio=1, brush_size=7, detail_level=3):
        """
        Convert photo to oil painting effect using bilateral filtering
        
        Args:
            image_path: Path to input image
            output_path: Path to save oil painting (optional)
            size: Size of the filter (default: 7, range: 1-10) - DEPRECATED, use brush_size
            dynRatio: Image dynamic ratio (not used, kept for API compatibility)
            brush_size: Brush stroke size (1-15, default: 7)
                       Lower values = fine detail, Higher values = broad strokes
            detail_level: Level of detail preservation (1-5, default: 3)
                         Lower values = more smoothing, Higher values = more detail
            
        Returns:
            Path to oil painting image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Validate parameters
            brush_size = max(1, min(15, int(brush_size)))
            detail_level = max(1, min(5, int(detail_level)))
            
            # Map brush_size (1-15) to bilateral filter diameter (9-37)
            diameter = 9 + (brush_size - 1) * 2
            
            # Map detail_level (1-5) to number of filtering passes (1-3)
            # Lower detail = more passes = more smoothing
            num_passes = 4 - ((detail_level - 1) // 2)
            
            # Apply multiple passes of bilateral filtering for painterly effect
            result = img.copy()
            for _ in range(num_passes):
                result = cv2.bilateralFilter(result, diameter, 90, 90)
            
            # Apply edge-preserving smoothing for brush stroke effect
            # Adjust sigma_s based on brush size and sigma_r based on detail level
            sigma_s = 40 + (brush_size * 2)
            sigma_r = 0.2 + (detail_level * 0.1)
            result = cv2.edgePreservingFilter(result, flags=1, sigma_s=sigma_s, sigma_r=sigma_r)
            
            # Convert to HSV and boost saturation for vibrant oil painting look
            # Adjust saturation boost based on detail level
            saturation_boost = 1.1 + (detail_level * 0.05)
            hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 255)
            result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            if output_path:
                cv2.imwrite(output_path, result)
                logger.info(f"Oil painting created and saved to {output_path} (brush_size: {brush_size}, detail_level: {detail_level})")
                return output_path
            else:
                oil_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                return Image.fromarray(oil_rgb)
                
        except Exception as e:
            logger.error(f"Oil painting creation failed: {e}")
            raise
    
    def create_watercolor(self, image_path, output_path=None):
        """
        Convert photo to watercolor painting effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save watercolor (optional)
            
        Returns:
            Path to watercolor image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Apply bilateral filter for smooth color regions
            smooth = img
            for _ in range(3):
                smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=12, sigmaSpace=12)
            
            # Detect edges
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            edges = cv2.bitwise_not(edges)
            
            # Combine smooth color with soft edges
            watercolor = cv2.bitwise_and(smooth, edges)
            
            # Slightly reduce saturation for watercolor look
            watercolor_hsv = cv2.cvtColor(watercolor, cv2.COLOR_BGR2HSV).astype(np.float32)
            watercolor_hsv[:, :, 1] = watercolor_hsv[:, :, 1] * 0.8  # Reduce saturation
            watercolor_hsv = np.clip(watercolor_hsv, 0, 255).astype(np.uint8)
            watercolor = cv2.cvtColor(watercolor_hsv, cv2.COLOR_HSV2BGR)
            
            if output_path:
                cv2.imwrite(output_path, watercolor)
                logger.info(f"Watercolor created and saved to {output_path}")
                return output_path
            else:
                watercolor_rgb = cv2.cvtColor(watercolor, cv2.COLOR_BGR2RGB)
                return Image.fromarray(watercolor_rgb)
                
        except Exception as e:
            logger.error(f"Watercolor creation failed: {e}")
            raise
    
    def create_vintage_sepia(self, image_path, output_path=None, style='sepia', intensity=0.7):
        """
        Convert photo to vintage/sepia effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save vintage photo (optional)
            style: 'sepia', '1950s', '1970s', or 'polaroid'
            intensity: Intensity of sepia and vignette effect (0.1-1.0, default: 0.7)
                      Lower values = subtle effect, Higher values = strong vintage look
            
        Returns:
            Path to vintage image if output_path provided, else PIL Image
        """
        try:
            # Validate intensity parameter
            intensity = max(0.1, min(1.0, float(intensity)))
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Convert to float for processing
            img_float = img.astype(np.float32) / 255.0
            
            # Apply sepia tone matrix with intensity control
            if style in ['sepia', '1950s']:
                sepia_kernel = np.array([
                    [0.272, 0.534, 0.131],
                    [0.349, 0.686, 0.168],
                    [0.393, 0.769, 0.189]
                ])
                sepia = cv2.transform(img_float, sepia_kernel)
                # Blend with original based on intensity
                sepia = img_float * (1 - intensity) + sepia * intensity
            else:
                sepia = img_float
            
            # Add vintage effects based on style (scaled by intensity)
            if style == '1970s':
                # Warmer tones, slightly faded
                fade_amount = intensity * 0.1
                sepia[:, :, 0] *= (1 - fade_amount)  # Reduce blue
                sepia[:, :, 2] *= (1 + fade_amount)  # Increase red
                sepia = sepia * (1 - fade_amount * 0.5) + fade_amount * 0.5  # Slight fade
            elif style == 'polaroid':
                # High contrast, vignette
                contrast_power = 1.0 - (intensity * 0.2)
                sepia = np.power(sepia, contrast_power)  # Increase contrast
            
            # Add vignette effect with intensity control
            rows, cols = img.shape[:2]
            # Adjust kernel sigma based on intensity (stronger vignette with higher intensity)
            sigma_factor = 2.0 + (1.0 - intensity) * 2.0
            X_resultant_kernel = cv2.getGaussianKernel(cols, cols / sigma_factor)
            Y_resultant_kernel = cv2.getGaussianKernel(rows, rows / sigma_factor)
            resultant_kernel = Y_resultant_kernel * X_resultant_kernel.T
            mask = resultant_kernel / resultant_kernel.max()
            
            # Apply vignette with intensity control
            vignette_strength = 0.3 + (intensity * 0.4)
            for i in range(3):
                sepia[:, :, i] = sepia[:, :, i] * mask + sepia[:, :, i] * (1 - mask) * (1 - vignette_strength)
            
            # Add subtle film grain (scaled by intensity)
            noise_amount = 0.005 + (intensity * 0.015)
            noise = np.random.normal(0, noise_amount, img.shape).astype(np.float32)
            sepia = sepia + noise
            
            # Clip and convert back to uint8
            sepia = np.clip(sepia * 255, 0, 255).astype(np.uint8)
            
            if output_path:
                cv2.imwrite(output_path, sepia)
                logger.info(f"Vintage {style} created and saved to {output_path} (intensity: {intensity})")
                return output_path
            else:
                sepia_rgb = cv2.cvtColor(sepia, cv2.COLOR_BGR2RGB)
                return Image.fromarray(sepia_rgb)
                
        except Exception as e:
            logger.error(f"Vintage sepia creation failed: {e}")
            raise
    
    def create_pop_art(self, image_path, output_path=None, colors=8):
        """
        Convert photo to pop art (Warhol style) effect
        
        Args:
            image_path: Path to input image
            output_path: Path to save pop art (optional)
            colors: Number of colors for posterization (default: 8)
            
        Returns:
            Path to pop art image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Increase contrast
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            # Color quantization (posterization)
            Z = enhanced.reshape((-1, 3)).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(Z, colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
            centers = np.uint8(centers)
            posterized = centers[labels.flatten()]
            pop_art = posterized.reshape(enhanced.shape)
            
            # Boost saturation for vibrant pop art look
            pop_art_hsv = cv2.cvtColor(pop_art, cv2.COLOR_BGR2HSV).astype(np.float32)
            pop_art_hsv[:, :, 1] = np.clip(pop_art_hsv[:, :, 1] * 1.5, 0, 255)
            pop_art = cv2.cvtColor(pop_art_hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            if output_path:
                cv2.imwrite(output_path, pop_art)
                logger.info(f"Pop art created and saved to {output_path}")
                return output_path
            else:
                pop_art_rgb = cv2.cvtColor(pop_art, cv2.COLOR_BGR2RGB)
                return Image.fromarray(pop_art_rgb)
                
        except Exception as e:
            logger.error(f"Pop art creation failed: {e}")
            raise
    
    def create_hdr_enhancement(self, image_path, output_path=None):
        """
        Apply HDR tone mapping for dramatic, high-contrast images
        
        Args:
            image_path: Path to input image
            output_path: Path to save HDR enhanced image (optional)
            
        Returns:
            Path to HDR image if output_path provided, else PIL Image
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Convert to float32 for HDR processing
            img_float = img.astype(np.float32) / 255.0
            
            # Create tone mapper
            tonemap = cv2.createTonemapDrago(gamma=1.0, saturation=1.2, bias=0.85)
            hdr = tonemap.process(img_float)
            
            # Clip and convert back
            hdr = np.clip(hdr * 255, 0, 255).astype(np.uint8)
            
            # Apply detail enhancement
            detail_enhanced = cv2.detailEnhance(hdr, sigma_s=10, sigma_r=0.15)
            
            if output_path:
                cv2.imwrite(output_path, detail_enhanced)
                logger.info(f"HDR enhancement created and saved to {output_path}")
                return output_path
            else:
                hdr_rgb = cv2.cvtColor(detail_enhanced, cv2.COLOR_BGR2RGB)
                return Image.fromarray(hdr_rgb)
                
        except Exception as e:
            logger.error(f"HDR enhancement failed: {e}")
            raise
    
    def create_professional_bw(self, image_path, output_path=None, style='classic', contrast=0):
        """
        Convert to high-quality black & white with professional toning
        
        Args:
            image_path: Path to input image
            output_path: Path to save B&W image (optional)
            style: 'classic', 'high_contrast', 'soft', 'film_noir', or 'selenium'
            contrast: Additional contrast adjustment (-50 to +50, default: 0)
                     Negative values = reduce contrast, Positive values = increase contrast
            
        Returns:
            Path to B&W image if output_path provided, else PIL Image
        """
        try:
            # Validate contrast parameter
            contrast = max(-50, min(50, int(contrast)))
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Use luminosity method (better than simple grayscale)
            b, g, r = cv2.split(img)
            gray = 0.299 * r + 0.587 * g + 0.114 * b
            gray = gray.astype(np.uint8)
            
            # Apply style-specific processing
            if style == 'high_contrast':
                # Apply CLAHE for high contrast
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            elif style == 'film_noir':
                # Dramatic shadows and highlights
                gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=-30)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            elif style == 'soft':
                # Soft, low-contrast B&W
                clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
                # Slight Gaussian blur for softness
                gray = cv2.GaussianBlur(gray, (3, 3), 0.5)
            elif style == 'selenium':
                # Selenium toning effect (cool tones, slight blue tint)
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            else:
                # Classic B&W with subtle contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray = clahe.apply(gray)
            
            # Apply additional contrast adjustment
            if contrast != 0:
                # Map contrast (-50 to +50) to alpha (0.5 to 1.5)
                alpha = 1.0 + (contrast / 100.0)
                beta = -contrast / 2
                gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            
            # Convert back to BGR for consistency
            bw = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            # Apply selenium toning if selected
            if style == 'selenium':
                # Add subtle cool blue tint for selenium effect
                bw_float = bw.astype(np.float32)
                bw_float[:, :, 0] = np.clip(bw_float[:, :, 0] * 1.05, 0, 255)  # Slight blue boost
                bw = bw_float.astype(np.uint8)
            
            if output_path:
                cv2.imwrite(output_path, bw)
                logger.info(f"Professional B&W ({style}, contrast: {contrast}) created and saved to {output_path}")
                return output_path
            else:
                bw_rgb = cv2.cvtColor(bw, cv2.COLOR_BGR2RGB)
                return Image.fromarray(bw_rgb)
                
        except Exception as e:
            logger.error(f"Professional B&W creation failed: {e}")
            raise


# Global instance
_artistic_effects = None

def get_artistic_effects():
    """Get or create the global artistic effects instance"""
    global _artistic_effects
    if _artistic_effects is None:
        _artistic_effects = ArtisticEffects()
    return _artistic_effects
