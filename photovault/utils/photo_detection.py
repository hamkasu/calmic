"""
PhotoVault Photo Detection - Simple & Robust
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Clean edge detection with accurate rectangular photo extraction
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV available for photo detection")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available - photo detection disabled")


class PhotoDetector:
    """Simple, robust photo detection using clean edge detection"""
    
    def __init__(self):
        # Detection parameters - RELAXED for better detection
        self.min_photo_area = 50000  # Minimum 50k pixels (~224x224) - LOWERED
        self.max_photo_area_ratio = 0.90  # Max 90% of image area
        self.min_aspect_ratio = 0.4  # Width/height ratio limits
        self.max_aspect_ratio = 3.0
        self.min_dimension = 200  # Minimum width or height in pixels - LOWERED
        self.min_rectangularity = 0.65  # Minimum rectangularity score - LOWERED
        self.min_confidence = 0.35  # Minimum confidence - LOWERED
        
        # Edge detection parameters - Multiple sensitivity levels
        self.canny_configs = [
            (50, 150),   # Standard sensitivity
            (30, 100),   # Higher sensitivity for subtle edges
            (20, 80),    # Very high sensitivity for beige-on-beige
        ]
        self.blur_kernel = 5
        
    def detect_photos(self, image_path: str) -> List[Dict]:
        """
        Detect rectangular photos in an image
        Returns list of detected photo regions with bounding boxes
        """
        if not OPENCV_AVAILABLE:
            logger.warning("Photo detection not available - OpenCV not installed")
            return []
            
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []
        
        try:
            # Load image
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            height, width = image.shape[:2]
            logger.info(f"Detecting photos in {width}x{height} image: {image_path}")
            
            # Check image size
            if height * width > 30000000:
                logger.error(f"Image too large: {width}x{height} pixels")
                return []
            
            image_area = width * height
            
            # Find photo candidates
            detections = self._find_photo_rectangles(image, image_area)
            
            # Remove overlapping detections (keep higher confidence)
            final_detections = self._remove_overlaps(detections)
            
            # Limit to top 10 detections
            final_detections = final_detections[:10]
            
            logger.info(f"Found {len(final_detections)} photos")
            return final_detections
            
        except Exception as e:
            logger.error(f"Photo detection failed: {e}", exc_info=True)
            return []
    
    def _find_photo_rectangles(self, image: np.ndarray, image_area: int) -> List[Dict]:
        """Find rectangular photo regions using adaptive multi-level edge detection"""
        all_detections = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)
        
        # Try multiple Canny threshold levels for different edge sensitivities
        for canny_low, canny_high in self.canny_configs:
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, canny_low, canny_high)
            
            # Dilate edges to connect nearby edges
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)
            
            # Find contours
            contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            logger.info(f"Canny({canny_low},{canny_high}): Found {len(contours)} contours")
            
            # Analyze each contour
            valid_count = 0
            rejected_size = 0
            rejected_rectangularity = 0
            rejected_confidence = 0
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Validate size
                if not self._is_valid_size(w, h, area, image_area):
                    rejected_size += 1
                    continue
                
                # Check if contour is rectangular
                rectangularity = self._calculate_rectangularity(contour, w, h)
                if rectangularity < self.min_rectangularity:
                    rejected_rectangularity += 1
                    logger.debug(f"Rejected: rectangularity {rectangularity:.2f} < {self.min_rectangularity}")
                    continue
                
                # Calculate confidence based on edge strength and rectangularity
                confidence = self._calculate_confidence(
                    image, x, y, w, h, rectangularity, edges
                )
                
                if confidence < self.min_confidence:
                    rejected_confidence += 1
                    logger.debug(f"Rejected: confidence {confidence:.2f} < {self.min_confidence}")
                    continue
                
                valid_count += 1
                all_detections.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(area),
                    'confidence': float(confidence),
                    'aspect_ratio': float(w / h),
                    'rectangularity': float(rectangularity),
                    'canny_level': f"{canny_low}-{canny_high}"
                })
            
            logger.info(f"  Valid: {valid_count}, Rejected - Size: {rejected_size}, Rectangularity: {rejected_rectangularity}, Confidence: {rejected_confidence}")
        
        # Sort by confidence
        all_detections.sort(key=lambda d: d['confidence'], reverse=True)
        
        return all_detections
    
    def _is_valid_size(self, width: int, height: int, area: int, image_area: int) -> bool:
        """Check if detection has valid dimensions"""
        # Check minimum dimensions
        if width < self.min_dimension or height < self.min_dimension:
            return False
        
        # Check minimum area
        if area < self.min_photo_area:
            return False
        
        # Check maximum area (shouldn't be the entire image)
        if area > image_area * self.max_photo_area_ratio:
            return False
        
        # Check aspect ratio
        aspect_ratio = width / height
        if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
            return False
        
        return True
    
    def _calculate_rectangularity(self, contour: np.ndarray, width: int, height: int) -> float:
        """
        Calculate how rectangular a contour is (works for rotated rectangles!)
        Uses minimum area rectangle instead of axis-aligned bounding box
        Returns value from 0.0 to 1.0
        """
        contour_area = cv2.contourArea(contour)
        
        if contour_area == 0:
            return 0.0
        
        # Use minimum area rectangle (handles rotated photos correctly)
        # minAreaRect returns ((center_x, center_y), (width, height), angle)
        rect = cv2.minAreaRect(contour)
        min_rect_area = rect[1][0] * rect[1][1]  # width * height of rotated rectangle
        
        if min_rect_area == 0:
            return 0.0
        
        # Rectangularity = contour area / minimum area rectangle area
        # Perfect rectangle (even if rotated) = 1.0
        rectangularity = contour_area / min_rect_area
        
        return min(rectangularity, 1.0)
    
    def _calculate_confidence(
        self,
        image: np.ndarray,
        x: int, y: int, w: int, h: int,
        rectangularity: float,
        edges: np.ndarray
    ) -> float:
        """Calculate detection confidence score (0.0 to 1.0)"""
        
        # Start with rectangularity as base score
        confidence = rectangularity * 0.6
        
        # Check edge strength around perimeter
        edge_strength = self._calculate_edge_strength(edges, x, y, w, h)
        confidence += edge_strength * 0.4
        
        return min(confidence, 1.0)
    
    def _calculate_edge_strength(
        self,
        edges: np.ndarray,
        x: int, y: int, w: int, h: int
    ) -> float:
        """Calculate edge strength around photo perimeter"""
        
        # Define perimeter regions (top, bottom, left, right borders)
        border_width = max(5, min(w, h) // 20)
        
        try:
            # Top border
            top = edges[y:y+border_width, x:x+w]
            # Bottom border
            bottom = edges[y+h-border_width:y+h, x:x+w]
            # Left border
            left = edges[y:y+h, x:x+border_width]
            # Right border
            right = edges[y:y+h, x+w-border_width:x+w]
            
            # Calculate edge pixel density in borders
            total_border_pixels = (top.size + bottom.size + left.size + right.size)
            if total_border_pixels == 0:
                return 0.0
            
            edge_pixels = (
                np.sum(top > 0) + np.sum(bottom > 0) +
                np.sum(left > 0) + np.sum(right > 0)
            )
            
            edge_density = edge_pixels / total_border_pixels
            
            # Normalize to 0-1 range (good photos have ~10-30% edge density)
            normalized = min(edge_density / 0.25, 1.0)
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Edge strength calculation failed: {e}")
            return 0.5
    
    def _remove_overlaps(self, detections: List[Dict]) -> List[Dict]:
        """Remove overlapping detections using Non-Maximum Suppression"""
        if len(detections) <= 1:
            return detections
        
        # Sort by confidence (highest first)
        sorted_detections = sorted(detections, key=lambda d: d['confidence'], reverse=True)
        
        keep = []
        skip_indices = set()
        
        for i, det1 in enumerate(sorted_detections):
            if i in skip_indices:
                continue
            
            keep.append(det1)
            
            # Check for overlaps with remaining detections
            for j in range(i + 1, len(sorted_detections)):
                if j in skip_indices:
                    continue
                
                det2 = sorted_detections[j]
                overlap = self._calculate_overlap(det1, det2)
                
                # If overlap > 50%, skip the lower confidence detection
                if overlap > 0.5:
                    skip_indices.add(j)
        
        return keep
    
    def _calculate_overlap(self, det1: Dict, det2: Dict) -> float:
        """Calculate overlap ratio between two detections"""
        x1, y1, w1, h1 = det1['x'], det1['y'], det1['width'], det1['height']
        x2, y2, w2, h2 = det2['x'], det2['y'], det2['width'], det2['height']
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area
        
        if union_area == 0:
            return 0.0
        
        # Return IoU (Intersection over Union)
        return intersection_area / union_area
    
    def extract_photos(
        self,
        image_path: str,
        output_dir: str,
        detected_photos: List[Dict],
        username: Optional[str] = None
    ) -> List[Dict]:
        """
        Extract detected photos and save them as separate files
        Uses simple cropping - NO perspective transform to avoid warping
        
        Args:
            image_path: Path to source image
            output_dir: Output directory for extracted photos
            detected_photos: List of detected photo dictionaries
            username: Username for filename (format: <username>.detected.<date>.<random>.jpg)
        """
        if not OPENCV_AVAILABLE:
            return []
        
        try:
            import random
            from datetime import datetime
            
            # Load image
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            os.makedirs(output_dir, exist_ok=True)
            
            extracted_photos = []
            date_str = datetime.now().strftime('%Y%m%d')
            
            for i, photo in enumerate(detected_photos):
                try:
                    x, y, w, h = photo['x'], photo['y'], photo['width'], photo['height']
                    
                    # Add small padding (2%)
                    padding = max(5, int(min(w, h) * 0.02))
                    
                    # Calculate padded coordinates (stay within image bounds)
                    x_start = max(0, x - padding)
                    y_start = max(0, y - padding)
                    x_end = min(image.shape[1], x + w + padding)
                    y_end = min(image.shape[0], y + h + padding)
                    
                    # Extract photo region (simple crop - no warping!)
                    extracted = image[y_start:y_end, x_start:x_end]
                    
                    if extracted.size == 0:
                        logger.warning(f"Photo {i+1}: Extraction resulted in empty image")
                        continue
                    
                    # Generate output filename: <username>.detected.<date>.<random>.jpg
                    # Ensure uniqueness by checking for collisions
                    confidence_pct = int(photo['confidence'] * 100)
                    max_retries = 100
                    output_path = None
                    
                    for retry in range(max_retries):
                        random_num = random.randint(10000, 99999)
                        if username:
                            output_filename = f"{username}.detected.{date_str}.{random_num}.jpg"
                        else:
                            # Fallback to old format if no username provided
                            base_filename = os.path.splitext(os.path.basename(image_path))[0]
                            output_filename = f"{base_filename}.detected.{date_str}.{random_num}.jpg"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        # Check if file already exists
                        if not os.path.exists(output_path):
                            break
                        logger.debug(f"Filename collision detected, retrying ({retry+1}/{max_retries})")
                    else:
                        # If all retries exhausted, use UUID for guaranteed uniqueness
                        import uuid
                        unique_id = str(uuid.uuid4())[:8]
                        if username:
                            output_filename = f"{username}.detected.{date_str}.{unique_id}.jpg"
                        else:
                            base_filename = os.path.splitext(os.path.basename(image_path))[0]
                            output_filename = f"{base_filename}.detected.{date_str}.{unique_id}.jpg"
                        output_path = os.path.join(output_dir, output_filename)
                        logger.warning(f"Used UUID for filename uniqueness: {output_filename}")
                    
                    # Save extracted photo
                    cv2.imwrite(output_path, extracted, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    logger.info(f"Extracted photo {i+1}: {output_filename} ({w}x{h}, {confidence_pct}% confidence)")
                    
                    extracted_photos.append({
                        'filename': output_filename,
                        'path': output_path,
                        'width': extracted.shape[1],
                        'height': extracted.shape[0],
                        'confidence': photo['confidence']
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to extract photo {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(extracted_photos)} photos")
            return extracted_photos
            
        except Exception as e:
            logger.error(f"Photo extraction failed: {e}", exc_info=True)
            return []


# Backward compatibility - create alias
AdvancedPhotoDetector = PhotoDetector


# Backward compatible helper functions for legacy code
def detect_photos_in_image(image_path: str, fast_mode: bool = True) -> List[Dict]:
    """
    Legacy helper function - detects photos in an image
    Args:
        image_path: Path to the image file
        fast_mode: Not used anymore (kept for compatibility)
    Returns:
        List of detected photo dictionaries
    """
    detector = PhotoDetector()
    return detector.detect_photos(image_path)


def extract_detected_photos(image_path: str, output_dir: str, detected_photos: List[Dict]) -> List[Dict]:
    """
    Legacy helper function - extracts detected photos
    Args:
        image_path: Path to the source image
        output_dir: Directory to save extracted photos
        detected_photos: List of detection dictionaries from detect_photos_in_image
    Returns:
        List of extracted photo dictionaries
    """
    detector = PhotoDetector()
    return detector.extract_photos(image_path, output_dir, detected_photos)
