"""
Photo Damage Repair Utilities
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
                                   sensitivity: int = 5, inpaint_radius: int = 3) -> Tuple[str, Dict]:
        """
        Remove scratches and dust spots from damaged photos using morphological operations
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            sensitivity: Detection sensitivity (1-10, lower = more sensitive)
            inpaint_radius: Radius for inpainting (1-10, larger = broader repair)
            
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
                'method': 'morphological_inpainting'
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
                     sensitivity: int = 5) -> Tuple[str, Dict]:
        """
        Detect and repair cracks in old photographs
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, overwrites original)
            sensitivity: Detection sensitivity (1-10, lower = more sensitive)
            
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
            
            # Save result
            if output_path is None:
                output_path = image_path
            
            cv2.imwrite(output_path, repaired, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            stats = {
                'crack_pixels': int(crack_pixels),
                'total_pixels': int(total_pixels),
                'crack_percentage': round(crack_percent, 2),
                'sensitivity': sensitivity,
                'method': 'edge_detection_inpainting'
            }
            
            logger.info(f"Crack repair completed: {crack_percent:.2f}% cracks repaired")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error repairing cracks: {e}")
            raise
    
    def comprehensive_repair(self, image_path: str, output_path: str = None,
                            scratch_sensitivity: int = 5,
                            crack_sensitivity: int = 5,
                            stain_strength: float = 1.5) -> Tuple[str, Dict]:
        """
        Apply comprehensive damage repair (all methods)
        
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
            
            # Step 1: Remove scratches and dust
            temp_path, scratch_stats = self.remove_scratches_and_dust(
                image_path, temp_path, scratch_sensitivity
            )
            
            # Step 2: Repair cracks
            temp_path2 = tempfile.mktemp(suffix='.jpg')
            temp_path2, crack_stats = self.repair_cracks(
                temp_path, temp_path2, crack_sensitivity
            )
            
            # Step 3: Remove stains
            if output_path is None:
                output_path = image_path
            
            output_path, stain_stats = self.remove_stains(
                temp_path2, output_path, stain_strength
            )
            
            # Clean up temp files
            try:
                os.remove(temp_path)
                os.remove(temp_path2)
            except:
                pass
            
            # Combine stats
            combined_stats = {
                'method': 'comprehensive_repair',
                'scratch_removal': scratch_stats,
                'crack_repair': crack_stats,
                'stain_removal': stain_stats
            }
            
            logger.info(f"Comprehensive repair completed successfully")
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


def comprehensive_repair(image_path: str, output_path: str = None,
                        scratch_sensitivity: int = 5,
                        crack_sensitivity: int = 5,
                        stain_strength: float = 1.5) -> Tuple[str, Dict]:
    """Convenience function for comprehensive damage repair"""
    return damage_repair.comprehensive_repair(
        image_path, output_path, scratch_sensitivity,
        crack_sensitivity, stain_strength
    )
