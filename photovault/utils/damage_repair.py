"""
Photo Damage Repair Utilities
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Advanced restoration features for damaged photographs
"""

import numpy as np
from PIL import Image
import os
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Optional OpenCV import for enhanced features
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV available - full damage repair features enabled")
except ImportError as e:
    cv2 = None
    OPENCV_AVAILABLE = False
    logger.warning(f"OpenCV not available - limited damage repair features: {e}")


class DamageRepair:
    """Advanced damage repair for old and damaged photographs"""
    
    def __init__(self):
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available - damage repair features disabled")
    
    def remove_scratches_and_dust(self, image_path: str, output_path: str = None,
                                   sensitivity: int = 5, inpaint_radius: int = 3,
                                   apply_enhancement: bool = True) -> Tuple[str, Dict]:
        """
        Remove scratches and dust spots from damaged photos using morphological operations
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            sensitivity: Detection sensitivity (1-10, lower = more sensitive)
            inpaint_radius: Radius for inpainting (1-10, larger = broader repair)
            apply_enhancement: Whether to apply post-processing enhancement (default True)
            
        Returns:
            Tuple of (output_path, repair_stats)
        """
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV required for scratch removal")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Removing scratches and dust from: {image_path}")
        
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect scratches using morphological operations
            # Create kernel for scratch detection (vertical and horizontal)
            kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
            kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
            
            # Detect vertical scratches
            scratch_v = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_v)
            # Detect horizontal scratches
            scratch_h = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_h)
            
            # Combine scratch detections
            scratches = cv2.add(scratch_v, scratch_h)
            
            # Detect dust spots using morphological operations
            kernel_dust = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dust = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_dust)
            
            # Combine scratches and dust
            damage_mask = cv2.add(scratches, dust)
            
            # Threshold to create binary mask based on sensitivity
            threshold_value = max(10, 30 - (sensitivity * 2))
            _, mask = cv2.threshold(damage_mask, threshold_value, 255, cv2.THRESH_BINARY)
            
            # Dilate mask slightly to ensure complete coverage
            mask = cv2.dilate(mask, np.ones((2, 2), np.uint8), iterations=1)
            
            # Count damaged pixels for stats
            damage_pixels = np.count_nonzero(mask)
            total_pixels = mask.shape[0] * mask.shape[1]
            damage_percent = (damage_pixels / total_pixels) * 100
            
            # Inpaint the damaged areas
            repaired = cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)
            
            # Apply post-processing enhancement if requested
            if apply_enhancement:
                repaired = self.denoise_preserve_edges(repaired)
                repaired = self.enhance_contrast_clahe(repaired, clip_limit=2.5)
                repaired = self.sharpen_image(repaired, strength=1.3)
            
            # Save repaired image
            if output_path is None:
                output_path = image_path
            
            cv2.imwrite(output_path, repaired, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            stats = {
                'damage_pixels': int(damage_pixels),
                'total_pixels': int(total_pixels),
                'damage_percentage': round(damage_percent, 2),
                'sensitivity': sensitivity,
                'inpaint_radius': inpaint_radius,
                'method': 'morphological_inpainting',
                'enhanced': apply_enhancement
            }
            
            logger.info(f"Scratch removal completed: {damage_percent:.2f}% damage repaired")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error removing scratches: {e}")
            raise
    
    def remove_stains(self, image_path: str, output_path: str = None,
                      strength: float = 1.5) -> Tuple[str, Dict]:
        """
        Remove stains and discoloration from old photos
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            strength: Stain removal strength (1.0-3.0)
            
        Returns:
            Tuple of (output_path, repair_stats)
        """
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV required for stain removal")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Removing stains from: {image_path}")
        
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to LAB color space for better color manipulation
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply bilateral filter to L channel to smooth stains while preserving edges
            l_filtered = cv2.bilateralFilter(l, 9, 75, 75)
            
            # Apply CLAHE to improve local contrast
            clahe = cv2.createCLAHE(clipLimit=2.0 * strength, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l_filtered)
            
            # Reduce color casts in a and b channels
            a_mean = np.mean(a)
            b_mean = np.mean(b)
            
            # Shift towards neutral (128 is neutral in LAB)
            a_corrected = ((a - a_mean) * 0.8 + 128).astype(np.uint8)
            b_corrected = ((b - b_mean) * 0.8 + 128).astype(np.uint8)
            
            # Merge channels back
            corrected_lab = cv2.merge([l_enhanced, a_corrected, b_corrected])
            corrected_bgr = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)
            
            # Save result
            if output_path is None:
                output_path = image_path
            
            cv2.imwrite(output_path, corrected_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            stats = {
                'strength': strength,
                'method': 'lab_color_correction',
                'color_shift_a': float(a_mean - 128),
                'color_shift_b': float(b_mean - 128)
            }
            
            logger.info(f"Stain removal completed successfully")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error removing stains: {e}")
            raise
    
    def repair_cracks(self, image_path: str, output_path: str = None,
                     sensitivity: int = 5, apply_enhancement: bool = True) -> Tuple[str, Dict]:
        """
        Detect and repair cracks in old photographs
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            sensitivity: Detection sensitivity (1-10, lower = more sensitive)
            apply_enhancement: Whether to apply post-processing enhancement (default True)
            
        Returns:
            Tuple of (output_path, repair_stats)
        """
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV required for crack repair")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Repairing cracks in: {image_path}")
        
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Detect edges using Canny
            threshold_low = max(30, 50 - (sensitivity * 5))
            threshold_high = threshold_low * 2
            edges = cv2.Canny(blurred, threshold_low, threshold_high)
            
            # Morphological closing to connect broken edges (cracks)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Thin the lines to get crack skeleton
            kernel_thin = np.ones((2, 2), np.uint8)
            crack_mask = cv2.morphologyEx(closed, cv2.MORPH_DILATE, kernel_thin, iterations=1)
            
            # Count crack pixels
            crack_pixels = np.count_nonzero(crack_mask)
            total_pixels = crack_mask.shape[0] * crack_mask.shape[1]
            crack_percent = (crack_pixels / total_pixels) * 100
            
            # Inpaint cracks
            repaired = cv2.inpaint(img, crack_mask, 5, cv2.INPAINT_NS)
            
            # Apply light smoothing to blend repairs
            repaired = cv2.bilateralFilter(repaired, 5, 50, 50)
            
            # Apply post-processing enhancement if requested
            if apply_enhancement:
                repaired = self.enhance_contrast_clahe(repaired, clip_limit=2.5)
                repaired = self.sharpen_image(repaired, strength=1.3)
            
            # Save result
            if output_path is None:
                output_path = image_path
            
            cv2.imwrite(output_path, repaired, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            stats = {
                'crack_pixels': int(crack_pixels),
                'total_pixels': int(total_pixels),
                'crack_percentage': round(crack_percent, 2),
                'sensitivity': sensitivity,
                'method': 'edge_detection_inpainting',
                'enhanced': apply_enhancement
            }
            
            logger.info(f"Crack repair completed: {crack_percent:.2f}% cracks repaired")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error repairing cracks: {e}")
            raise
    
    def repair_severe_cracks(self, image_path: str, output_path: str = None,
                            intensity: str = 'high') -> Tuple[str, Dict]:
        """
        Advanced crack repair for severely damaged photographs with thick, visible cracks
        
        Uses multi-stage detection and inpainting optimized for thick white/light cracks
        that are common in old, damaged photographs.
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            intensity: Repair intensity ('medium', 'high', 'maximum')
            
        Returns:
            Tuple of (output_path, repair_stats)
        """
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV required for crack repair")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Repairing severe cracks with {intensity} intensity: {image_path}")
        
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            h, w = img.shape[:2]
            
            # Convert to LAB for better crack detection
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # Multi-strategy crack detection
            
            # Strategy 1: Detect bright/white cracks (most common in old photos)
            # Threshold the L channel to find very bright pixels (cracks are usually lighter)
            _, bright_mask = cv2.threshold(l_channel, 200, 255, cv2.THRESH_BINARY)
            
            # Strategy 2: Detect thin line structures using morphological operations
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding to handle varying lighting
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                            cv2.THRESH_BINARY, 15, 2)
            adaptive_inv = cv2.bitwise_not(adaptive)
            
            # Strategy 3: Edge detection for crack boundaries
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            edges = cv2.Canny(blurred, 20, 60)
            
            # Morphological operations to connect crack segments
            kernel_connect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges_connected = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_connect, iterations=2)
            
            # Strategy 4: Detect texture discontinuities using Laplacian
            laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=3)
            laplacian_abs = np.absolute(laplacian)
            laplacian_norm = np.uint8(255 * laplacian_abs / laplacian_abs.max())
            _, texture_mask = cv2.threshold(laplacian_norm, 100, 255, cv2.THRESH_BINARY)
            
            # Combine all detection strategies
            combined_mask = cv2.bitwise_or(bright_mask, edges_connected)
            combined_mask = cv2.bitwise_or(combined_mask, adaptive_inv)
            combined_mask = cv2.bitwise_or(combined_mask, texture_mask)
            
            # Clean up mask - remove noise, keep only significant cracks
            kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel_clean)
            
            # Dilate mask slightly to ensure we catch the full width of cracks
            if intensity == 'maximum':
                dilate_size = 5
                inpaint_radius = 20
                passes = 3
            elif intensity == 'high':
                dilate_size = 4
                inpaint_radius = 15
                passes = 2
            else:  # medium
                dilate_size = 3
                inpaint_radius = 10
                passes = 2
            
            kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_size, dilate_size))
            crack_mask = cv2.dilate(combined_mask, kernel_dilate, iterations=1)
            
            # Count crack pixels for statistics
            crack_pixels = np.count_nonzero(crack_mask)
            total_pixels = h * w
            crack_percent = (crack_pixels / total_pixels) * 100
            
            logger.info(f"Detected {crack_percent:.2f}% crack coverage, using {passes} inpainting passes")
            
            # Multi-pass inpainting for severe damage
            repaired = img.copy()
            for i in range(passes):
                # Use Telea algorithm (INPAINT_TELEA) for first pass, NS for refinement
                method = cv2.INPAINT_TELEA if i == 0 else cv2.INPAINT_NS
                repaired = cv2.inpaint(repaired, crack_mask, inpaint_radius, method)
                
                # Reduce mask for subsequent passes to focus on remaining damage
                if i < passes - 1:
                    crack_mask = cv2.erode(crack_mask, kernel_clean, iterations=1)
            
            # Edge-aware smoothing to blend repairs seamlessly
            # Use bilateral filter to preserve edges while smoothing crack repairs
            repaired = cv2.bilateralFilter(repaired, 7, 75, 75)
            
            # Apply guided filter for better texture preservation
            # This helps maintain the original photo's texture while removing cracks
            radius = 8
            epsilon = 0.1 ** 2
            mean_I = cv2.boxFilter(repaired, cv2.CV_64F, (radius, radius))
            mean_p = mean_I
            corr_I = cv2.boxFilter(repaired.astype(np.float64) ** 2, cv2.CV_64F, (radius, radius))
            var_I = corr_I - mean_I ** 2
            
            a = var_I / (var_I + epsilon)
            b = mean_p - a * mean_I
            
            mean_a = cv2.boxFilter(a, cv2.CV_64F, (radius, radius))
            mean_b = cv2.boxFilter(b, cv2.CV_64F, (radius, radius))
            
            repaired_guided = mean_a * repaired.astype(np.float64) + mean_b
            repaired = np.uint8(np.clip(repaired_guided, 0, 255))
            
            # Final enhancement pipeline
            # 1. Denoise while preserving edges
            repaired = self.denoise_preserve_edges(repaired)
            
            # 2. Gentle contrast enhancement
            repaired = self.enhance_contrast_clahe(repaired, clip_limit=2.0)
            
            # 3. Subtle sharpening to restore detail
            repaired = self.sharpen_image(repaired, strength=1.2)
            
            # 4. Final brightness/contrast normalization
            repaired = self.normalize_brightness_contrast(repaired)
            
            # Save result
            if output_path is None:
                output_path = image_path
            
            cv2.imwrite(output_path, repaired, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            stats = {
                'crack_pixels': int(crack_pixels),
                'total_pixels': int(total_pixels),
                'crack_percentage': round(crack_percent, 2),
                'intensity': intensity,
                'inpaint_radius': inpaint_radius,
                'inpaint_passes': passes,
                'method': 'multi_stage_severe_damage',
                'strategies': 'brightness+edges+adaptive+texture+multi_pass_inpaint+guided_filter'
            }
            
            logger.info(f"Severe crack repair completed: {crack_percent:.2f}% damage repaired with {passes} passes")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error repairing severe cracks: {e}")
            raise
    
    def sharpen_image(self, img: np.ndarray, strength: float = 1.5) -> np.ndarray:
        """
        Apply unsharp masking to sharpen image details
        
        Args:
            img: Input image (BGR format)
            strength: Sharpening strength (0.5-3.0, default 1.5)
            
        Returns:
            Sharpened image
        """
        # Create blurred version
        blurred = cv2.GaussianBlur(img, (0, 0), 3)
        
        # Unsharp mask = original + (original - blurred) * strength
        sharpened = cv2.addWeighted(img, 1.0 + strength, blurred, -strength, 0)
        
        return sharpened
    
    def enhance_contrast_clahe(self, img: np.ndarray, clip_limit: float = 3.0) -> np.ndarray:
        """
        Apply adaptive contrast enhancement using CLAHE
        
        Args:
            img: Input image (BGR format)
            clip_limit: Contrast clipping limit (1.0-5.0, default 3.0)
            
        Returns:
            Contrast-enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel only
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge and convert back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced_bgr
    
    def denoise_preserve_edges(self, img: np.ndarray) -> np.ndarray:
        """
        Apply edge-preserving denoising to reduce blur artifacts
        
        Args:
            img: Input image (BGR format)
            
        Returns:
            Denoised image with preserved edges
        """
        # Use bilateral filter for edge-preserving smoothing
        denoised = cv2.bilateralFilter(img, 7, 50, 50)
        return denoised
    
    def normalize_brightness_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Automatically adjust brightness and contrast for optimal range
        
        Args:
            img: Input image (BGR format)
            
        Returns:
            Normalized image
        """
        # Convert to LAB
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Normalize L channel to use full range
        l_normalized = cv2.normalize(l, None, 5, 250, cv2.NORM_MINMAX)
        
        # Merge and convert back
        normalized_lab = cv2.merge([l_normalized, a, b])
        normalized_bgr = cv2.cvtColor(normalized_lab, cv2.COLOR_LAB2BGR)
        
        return normalized_bgr
    
    def post_process_repair(self, image_path: str, output_path: str = None) -> Tuple[str, Dict]:
        """
        Apply post-processing enhancements to repaired image:
        - Edge-preserving denoising
        - Adaptive contrast enhancement
        - Sharpening
        - Brightness/contrast normalization
        
        Args:
            image_path: Path to repaired image
            output_path: Path for enhanced output
            
        Returns:
            Tuple of (output_path, enhancement_stats)
        """
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV required for post-processing")
        
        logger.info(f"Applying post-processing enhancements to: {image_path}")
        
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Step 1: Edge-preserving denoising to reduce blur artifacts
            img = self.denoise_preserve_edges(img)
            
            # Step 2: Enhance contrast with CLAHE
            img = self.enhance_contrast_clahe(img, clip_limit=3.0)
            
            # Step 3: Sharpen to restore detail
            img = self.sharpen_image(img, strength=1.5)
            
            # Step 4: Normalize brightness and contrast
            img = self.normalize_brightness_contrast(img)
            
            # Save enhanced image
            if output_path is None:
                output_path = image_path
            
            cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            stats = {
                'enhancements_applied': [
                    'edge_preserving_denoising',
                    'adaptive_contrast_enhancement',
                    'unsharp_masking',
                    'brightness_normalization'
                ],
                'quality': 95
            }
            
            logger.info(f"Post-processing completed successfully")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error in post-processing: {e}")
            raise
    
    def comprehensive_repair(self, image_path: str, output_path: str = None,
                            scratch_sensitivity: int = 5,
                            crack_sensitivity: int = 5,
                            stain_strength: float = 1.5) -> Tuple[str, Dict]:
        """
        Apply comprehensive damage repair (all methods) with post-processing enhancement
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            scratch_sensitivity: Scratch detection sensitivity (1-10)
            crack_sensitivity: Crack detection sensitivity (1-10)
            stain_strength: Stain removal strength (1.0-3.0)
            
        Returns:
            Tuple of (output_path, combined_stats)
        """
        if not OPENCV_AVAILABLE:
            raise RuntimeError("OpenCV required for comprehensive repair")
        
        logger.info(f"Starting comprehensive repair for: {image_path}")
        
        try:
            import tempfile
            
            # Create temp file for intermediate results
            temp_path = tempfile.mktemp(suffix='.jpg')
            
            # Step 1: Remove scratches and dust (without enhancement)
            temp_path, scratch_stats = self.remove_scratches_and_dust(
                image_path, temp_path, scratch_sensitivity, apply_enhancement=False
            )
            
            # Step 2: Repair cracks (without enhancement)
            temp_path2 = tempfile.mktemp(suffix='.jpg')
            temp_path2, crack_stats = self.repair_cracks(
                temp_path, temp_path2, crack_sensitivity, apply_enhancement=False
            )
            
            # Step 3: Remove stains
            temp_path3 = tempfile.mktemp(suffix='.jpg')
            temp_path3, stain_stats = self.remove_stains(
                temp_path2, temp_path3, stain_strength
            )
            
            # Step 4: Apply post-processing enhancements
            if output_path is None:
                output_path = image_path
            
            output_path, enhancement_stats = self.post_process_repair(
                temp_path3, output_path
            )
            
            # Clean up temp files
            try:
                os.remove(temp_path)
                os.remove(temp_path2)
                os.remove(temp_path3)
            except:
                pass
            
            # Combine stats
            combined_stats = {
                'method': 'comprehensive_repair_enhanced',
                'scratch_removal': scratch_stats,
                'crack_repair': crack_stats,
                'stain_removal': stain_stats,
                'post_processing': enhancement_stats
            }
            
            logger.info(f"Comprehensive repair with enhancements completed successfully")
            return output_path, combined_stats
            
        except Exception as e:
            logger.error(f"Error in comprehensive repair: {e}")
            raise


# Create global damage repair instance
damage_repair = DamageRepair()


def remove_scratches(image_path: str, output_path: str = None,
                    sensitivity: int = 5, inpaint_radius: int = 3) -> Tuple[str, Dict]:
    """Convenience function for scratch removal"""
    return damage_repair.remove_scratches_and_dust(
        image_path, output_path, sensitivity, inpaint_radius
    )


def remove_stains(image_path: str, output_path: str = None,
                 strength: float = 1.5) -> Tuple[str, Dict]:
    """Convenience function for stain removal"""
    return damage_repair.remove_stains(image_path, output_path, strength)


def repair_cracks(image_path: str, output_path: str = None,
                 sensitivity: int = 5) -> Tuple[str, Dict]:
    """Convenience function for crack repair"""
    return damage_repair.repair_cracks(image_path, output_path, sensitivity)


def repair_severe_cracks(image_path: str, output_path: str = None,
                        intensity: str = 'high') -> Tuple[str, Dict]:
    """Convenience function for severe crack repair"""
    return damage_repair.repair_severe_cracks(image_path, output_path, intensity)


def comprehensive_repair(image_path: str, output_path: str = None,
                        scratch_sensitivity: int = 5,
                        crack_sensitivity: int = 5,
                        stain_strength: float = 1.5) -> Tuple[str, Dict]:
    """Convenience function for comprehensive damage repair"""
    return damage_repair.comprehensive_repair(
        image_path, output_path, scratch_sensitivity,
        crack_sensitivity, stain_strength
    )
