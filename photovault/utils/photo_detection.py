"""
PhotoVault Advanced Photo Detection System
Multi-scale, adaptive edge detection with special handling for challenging scenarios
Handles: overlapping photos, glare, shadows, Polaroids, faded photos, small photos
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV available for photo detection")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available - photo detection disabled")

class AdvancedPhotoDetector:
    """Advanced multi-strategy photo detection with robust edge detection"""
    
    def __init__(self, fast_mode=True):
        self.min_photo_area = 150000
        self.max_photo_area_ratio = 0.85
        self.min_aspect_ratio = 0.3
        self.max_aspect_ratio = 4.0
        self.enable_perspective_correction = True
        self.enable_edge_refinement = True
        self.fast_mode = fast_mode
        self.min_dimension = 300
        
        # Multi-scale detection parameters (single scale for fast mode)
        self.scales = [1.0] if fast_mode else [1.0, 0.85]
        
        # Detection confidence thresholds (balanced to avoid photo content while detecting real photos)
        self.min_confidence = 0.60
        self.high_confidence = 0.85
        
    def detect_photos(self, image_path: str) -> List[Dict]:
        """
        Detect rectangular photos using multi-strategy approach
        """
        if not OPENCV_AVAILABLE:
            logger.warning("Photo detection not available - OpenCV not installed")
            return []
            
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []
            
        image = None
        try:
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
                
            mode = "fast" if self.fast_mode else "comprehensive"
            logger.info(f"Starting photo detection ({mode} mode) on {image_path}")
            
            height, width = image.shape[:2]
            if height * width > 25000000:
                logger.error(f"Image too large: {width}x{height} pixels. Maximum: 25MP")
                return []
            
            original_area = width * height
            
            # Fast mode: use only primary detection
            all_detections = []
            if self.fast_mode:
                # Single-scale optimized detection
                all_detections.extend(self._fast_detection(image, original_area))
            else:
                # Full multi-strategy detection
                all_detections.extend(self._multi_scale_detection(image, original_area))
                all_detections.extend(self._detect_polaroids(image, original_area))
                all_detections.extend(self._detect_faded_photos(image, original_area))
                all_detections.extend(self._watershed_detection(image, original_area))
            
            # Merge overlapping detections (NMS - Non-Maximum Suppression)
            merged_detections = self._merge_overlapping_detections(all_detections)
            
            # Sort by confidence
            merged_detections.sort(key=lambda p: p['confidence'], reverse=True)
            
            # Limit to top 15 detections
            if len(merged_detections) > 15:
                merged_detections = merged_detections[:15]
            
            mode = "fast" if self.fast_mode else "comprehensive"
            logger.info(f"Detected {len(merged_detections)} photos using {mode} detection")
            return merged_detections
            
        except MemoryError:
            logger.error(f"Out of memory during photo detection for {image_path}")
            return []
        except Exception as e:
            logger.error(f"Photo detection failed for {image_path}: {e}")
            return []
        finally:
            if image is not None:
                del image
    
    def _multi_scale_detection(self, image: np.ndarray, original_area: int) -> List[Dict]:
        """Detect photos at multiple scales to catch both large and small photos"""
        all_candidates = []
        
        for scale in self.scales:
            if scale != 1.0:
                scaled_width = int(image.shape[1] * scale)
                scaled_height = int(image.shape[0] * scale)
                scaled_image = cv2.resize(image, (scaled_width, scaled_height))
            else:
                scaled_image = image
            
            # Apply advanced preprocessing
            processed = self._advanced_preprocessing(scaled_image)
            
            # Find contours with hierarchical detection
            contours, hierarchy = self._find_contours_hierarchical(processed)
            
            # Validate candidates
            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                
                # Scale back to original coordinates
                if scale != 1.0:
                    x = int(x / scale)
                    y = int(y / scale)
                    w = int(w / scale)
                    h = int(h / scale)
                
                area = w * h
                
                if not self._is_valid_photo_region(x, y, w, h, original_area):
                    continue
                
                # Enhanced confidence calculation
                confidence = self._calculate_advanced_confidence(
                    contour, x, y, w, h, image, hierarchy, i if hierarchy is not None else None
                )
                
                if confidence > self.min_confidence:
                    corners = self._get_photo_corners_refined(contour, scale)
                    all_candidates.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'area': int(area),
                        'confidence': float(confidence),
                        'aspect_ratio': float(w/h),
                        'contour': contour.tolist(),
                        'corners': corners.tolist(),
                        'detection_method': f'multi_scale_{scale}'
                    })
        
        return all_candidates
    
    def _fast_detection(self, image: np.ndarray, original_area: int) -> List[Dict]:
        """Fast, optimized photo detection for production use with enhanced preprocessing"""
        all_candidates = []
        
        # Step 1: Shadow removal to handle phone shadows
        shadow_removed = self._fast_shadow_removal(image)
        
        # Step 2: Convert to grayscale
        gray = cv2.cvtColor(shadow_removed, cv2.COLOR_BGR2GRAY)
        
        # Step 3: Enhanced illumination normalization with bilateral filtering
        # Bilateral filter preserves edges while smoothing noise
        bilateral = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        
        # Step 4: CLAHE for better contrast on photo borders
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(bilateral)
        
        # Step 5: Adaptive thresholding to handle varying lighting conditions
        # This helps detect photo edges even in uneven lighting
        adaptive_thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, blockSize=11, C=2
        )
        
        # Step 6: Dual-strategy edge detection for robustness
        # Strategy 1: Canny with adaptive thresholds
        median_val = float(np.median(enhanced))
        sigma = 0.33
        lower = int(max(0, (1.0 - sigma) * median_val))
        upper = int(min(255, (1.0 + sigma) * median_val))
        canny_edges = cv2.Canny(enhanced, lower, upper, apertureSize=3)
        
        # Strategy 2: Combine with adaptive threshold edges
        combined_edges = cv2.bitwise_or(canny_edges, cv2.bitwise_not(adaptive_thresh))
        
        # Step 7: Morphological operations to connect broken edges
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
        # Dilate to strengthen edges
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(closed, kernel_dilate, iterations=1)
        
        # Find contours
        contours, hierarchy = cv2.findContours(
            dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Sort and filter by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # Use 50% of min_photo_area as contour threshold
        min_area = self.min_photo_area * 0.5
        filtered = [c for c in contours if cv2.contourArea(c) > min_area][:20]
        
        # Process candidates with stricter filtering
        for i, contour in enumerate(filtered):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            if not self._is_valid_photo_region(x, y, w, h, original_area):
                continue
            
            # CRITICAL: Check if contour is actually a 4-sided polygon (rectangle)
            # This filters out irregular shapes that aren't photos
            corners = self._get_photo_corners_refined(contour, 1.0)
            if len(corners) != 4:
                continue
            
            # Validate corner angles - must be close to 90 degrees for rectangles
            corner_angles = self._calculate_corner_angles(corners)
            valid_corners = sum([1 for angle in corner_angles if 60 < angle < 120])
            if valid_corners < 3:  # Require at least 3 valid corners
                continue
            
            # Fast confidence calculation with perimeter edge validation
            confidence = self._calculate_fast_confidence(contour, x, y, w, h, image, dilated)
            
            if confidence > self.min_confidence:
                all_candidates.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(area),
                    'confidence': float(confidence),
                    'aspect_ratio': float(w/h),
                    'contour': contour.tolist(),
                    'corners': corners.tolist(),
                    'detection_method': 'fast'
                })
        
        return all_candidates
    
    def _calculate_fast_confidence(
        self, contour, x: int, y: int, w: int, h: int, image: np.ndarray, edges: np.ndarray = None
    ) -> float:
        """Fast confidence calculation with perimeter edge validation"""
        confidence = 0.0
        
        # Shape rectangularity (0.0 - 0.25) - soft scoring
        contour_area = cv2.contourArea(contour)
        bbox_area = w * h
        area_ratio = contour_area / bbox_area if bbox_area > 0 else 0
        
        # Soft penalty for low rectangularity (no hard cutoff)
        # Strong penalty below 0.60 (very irregular), gradual above
        if area_ratio < 0.60:
            rectangularity_score = 0.0
        elif area_ratio < 0.75:
            # Proportional penalty: 0.60->0.10, 0.75->0.20
            rectangularity_score = 0.10 + (area_ratio - 0.60) * (0.10 / 0.15)
        else:
            # Full score above 0.75
            rectangularity_score = 0.20 + (area_ratio - 0.75) * 0.20
        
        confidence += rectangularity_score
        
        # Aspect ratio match (0.0 - 0.2) - reduced weight
        aspect_ratio = w / h
        common_ratios = [1.0, 4/3, 3/2, 16/9, 5/4, 0.75, 0.67]
        min_diff = min([abs(aspect_ratio - ratio) for ratio in common_ratios])
        aspect_score = max(0, 1 - min_diff * 2) * 0.2
        confidence += aspect_score
        
        # Corner quality (0.0 - 0.15) - reduced weight to be more tolerant
        corners = self._get_photo_corners_refined(contour, 1.0)
        if len(corners) == 4:
            corner_angles = self._calculate_corner_angles(corners)
            angle_score = sum([1 for angle in corner_angles if 70 < angle < 110]) / 4
            confidence += angle_score * 0.15
        
        # Perimeter edge validation (0.0 - 0.40) - NEW: highest weight
        # This is the KEY to distinguishing photo borders from internal content
        if edges is not None:
            perimeter_score = self._validate_perimeter_edges(edges, x, y, w, h)
            # Reject only if no edges detected (score 0), allow partial credit
            if perimeter_score == 0.0:
                return 0.0
            confidence += perimeter_score * 0.40
        else:
            # If no edges provided, rely on other factors with adjusted weights
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _advanced_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """
        Advanced preprocessing pipeline:
        - Shadow removal
        - Glare detection and mitigation
        - Illumination normalization
        - Adaptive edge detection
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Step 1: Illumination normalization
        normalized = self._normalize_illumination(gray)
        
        # Step 2: Shadow removal
        shadow_removed = self._remove_shadows(image, normalized)
        
        # Step 3: Glare mitigation
        glare_reduced = self._reduce_glare(shadow_removed)
        
        # Step 4: Adaptive contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(glare_reduced)
        
        # Step 5: Noise reduction while preserving edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Step 6: Multi-strategy edge detection
        edges = self._multi_strategy_edge_detection(denoised)
        
        return edges
    
    def _normalize_illumination(self, gray: np.ndarray) -> np.ndarray:
        """Normalize non-uniform illumination"""
        blur = cv2.GaussianBlur(gray, (0, 0), sigmaX=15, sigmaY=15)
        normalized = cv2.divide(gray, blur, scale=255)
        return normalized
    
    def _remove_shadows(self, image: np.ndarray, gray: np.ndarray) -> np.ndarray:
        """Remove shadows using illumination-invariant approach"""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Use L channel for shadow detection
        blur_l = cv2.GaussianBlur(l, (0, 0), sigmaX=20, sigmaY=20)
        shadow_mask = cv2.divide(l, blur_l, scale=255)
        
        # Normalize L channel
        l_normalized = cv2.normalize(shadow_mask, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Merge back and convert to grayscale
        lab_normalized = cv2.merge([l_normalized, a, b])
        result = cv2.cvtColor(lab_normalized, cv2.COLOR_LAB2BGR)
        result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        
        return result_gray
    
    def _fast_shadow_removal(self, image: np.ndarray) -> np.ndarray:
        """
        Fast shadow detection and removal optimized for phone shadows.
        Uses adaptive illumination correction to brighten shadowed areas.
        """
        # Convert to LAB color space (better for illumination)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Detect shadow regions using adaptive threshold
        # Darker areas are likely shadows from phone blocking light
        mean_l = np.mean(l)
        shadow_threshold = int(mean_l * 0.6)  # 60% of mean brightness
        _, shadow_mask = cv2.threshold(l, shadow_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Clean up shadow mask (remove noise)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_CLOSE, kernel)
        shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_OPEN, kernel)
        
        # Create illumination correction map
        # Blur the L channel to get base illumination
        blur_l = cv2.GaussianBlur(l, (0, 0), sigmaX=25, sigmaY=25)
        
        # Calculate correction factor for shadowed areas
        # This will brighten dark regions while preserving bright areas
        correction_factor = cv2.divide(l, blur_l, scale=255)
        correction_factor = cv2.normalize(correction_factor, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Apply stronger correction to shadowed regions
        alpha = shadow_mask.astype(float) / 255.0  # Shadow weight (0-1)
        corrected_l = l.astype(float) * (1 - alpha * 0.5) + correction_factor.astype(float) * alpha * 0.5
        corrected_l = np.clip(corrected_l, 0, 255).astype(np.uint8)
        
        # Additional brightness boost for very dark shadows
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        corrected_l = clahe.apply(corrected_l)
        
        # Merge back to BGR
        lab_corrected = cv2.merge([corrected_l, a, b])
        result = cv2.cvtColor(lab_corrected, cv2.COLOR_LAB2BGR)
        
        return result
    
    def _reduce_glare(self, gray: np.ndarray) -> np.ndarray:
        """Detect and reduce glare/bright spots"""
        # Detect very bright regions (glare)
        _, glare_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        # Inpaint glare regions
        kernel = np.ones((3, 3), np.uint8)
        glare_mask_dilated = cv2.dilate(glare_mask, kernel, iterations=2)
        
        result = cv2.inpaint(gray, glare_mask_dilated, 3, cv2.INPAINT_TELEA)
        
        return result
    
    def _multi_strategy_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """Combine multiple edge detection strategies"""
        # Strategy 1: Adaptive Canny
        median_val = float(np.median(image))
        sigma = 0.33
        lower = int(max(0, (1.0 - sigma) * median_val))
        upper = int(min(255, (1.0 + sigma) * median_val))
        canny_edges = cv2.Canny(image, lower, upper, apertureSize=3, L2gradient=True)
        
        # Strategy 2: Sobel edges
        sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        sobel_edges = np.sqrt(sobelx**2 + sobely**2)
        sobel_edges = np.uint8(255 * sobel_edges / np.max(sobel_edges))
        _, sobel_binary = cv2.threshold(sobel_edges, 50, 255, cv2.THRESH_BINARY)
        
        # Combine strategies
        combined = cv2.bitwise_or(canny_edges, sobel_binary)
        
        # Morphological operations to close gaps
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close)
        
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(closed, kernel_dilate, iterations=2)
        
        return dilated
    
    def _find_contours_hierarchical(self, processed: np.ndarray) -> Tuple[List, Optional[np.ndarray]]:
        """Find contours with hierarchy to detect overlapping photos"""
        contours, hierarchy = cv2.findContours(
            processed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Sort by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Filter by minimum area (use 50% of min_photo_area for liberal contour filtering)
        min_area = self.min_photo_area * 0.5
        filtered = [c for c in contours if cv2.contourArea(c) > min_area]
        
        return filtered[:25], hierarchy
    
    def _detect_polaroids(self, image: np.ndarray, original_area: int) -> List[Dict]:
        """Detect Polaroid-style photos by looking for white borders with strict validation"""
        candidates = []
        
        # Convert to LAB color space for better white detection
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # Detect very bright regions (white borders) - increased threshold to be more selective
        _, white_mask = cv2.threshold(l_channel, 220, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to clean up noise
        kernel = np.ones((5, 5), np.uint8)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours in white regions
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            if not self._is_valid_photo_region(x, y, w, h, original_area):
                continue
            
            # Check if this has the characteristic Polaroid shape
            aspect_ratio = w / h
            if 0.8 <= aspect_ratio <= 1.2:  # Polaroids are typically square-ish
                # Additional validation: check for strong rectangular edges
                contour_area = cv2.contourArea(contour)
                bbox_area = w * h
                rectangularity = contour_area / bbox_area if bbox_area > 0 else 0
                
                # Only accept if it's very rectangular (>0.88) to avoid clothing
                if rectangularity < 0.88:
                    continue
                
                # Check edge strength - real photos have strong edges
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                roi = gray[y:y+h, x:x+w]
                edges = cv2.Canny(roi, 50, 150)
                edge_density = np.sum(edges > 0) / (w * h)
                
                # Require minimum edge density (photos have defined borders)
                if edge_density < 0.025:
                    continue
                
                confidence = 0.65
                corners = self._get_photo_corners_refined(contour, 1.0)
                
                candidates.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(area),
                    'confidence': float(confidence),
                    'aspect_ratio': float(aspect_ratio),
                    'contour': contour.tolist(),
                    'corners': corners.tolist(),
                    'detection_method': 'polaroid'
                })
        
        return candidates
    
    def _detect_faded_photos(self, image: np.ndarray, original_area: int) -> List[Dict]:
        """Detect low-contrast/faded photos using enhanced preprocessing"""
        candidates = []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aggressive contrast enhancement for faded photos
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        
        # Adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Find edges in adaptive threshold
        edges = cv2.Canny(adaptive_thresh, 50, 150)
        
        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=3)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            if not self._is_valid_photo_region(x, y, w, h, original_area):
                continue
            
            confidence = self._calculate_advanced_confidence(
                contour, x, y, w, h, image, None, None
            ) * 0.9
            
            if confidence > self.min_confidence:
                corners = self._get_photo_corners_refined(contour, 1.0)
                
                candidates.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': int(area),
                    'confidence': float(confidence),
                    'aspect_ratio': float(w/h),
                    'contour': contour.tolist(),
                    'corners': corners.tolist(),
                    'detection_method': 'faded'
                })
        
        return candidates
    
    def _watershed_detection(self, image: np.ndarray, original_area: int) -> List[Dict]:
        """Use watershed segmentation to separate touching photos"""
        candidates = []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Threshold
        _, thresh = cv2.threshold(gray.astype(np.uint8), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Remove noise
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        
        # Sure background
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        
        # Sure foreground using distance transform
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.5 * dist_transform.max(), 255, 0)
        
        # Unknown region
        sure_fg_uint8 = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg_uint8)
        
        # Marker labelling
        _, markers = cv2.connectedComponents(sure_fg_uint8)
        markers = markers + 1
        markers[unknown == 255] = 0
        
        # Apply watershed
        markers = cv2.watershed(image, markers)
        
        # Extract regions
        for label in np.unique(markers):
            if label <= 1:
                continue
            
            mask = np.zeros(gray.shape, dtype=np.uint8)
            mask[markers == label] = 255
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                if not self._is_valid_photo_region(x, y, w, h, original_area):
                    continue
                
                confidence = self._calculate_advanced_confidence(
                    contour, x, y, w, h, image, None, None
                ) * 0.85
                
                if confidence > self.min_confidence:
                    corners = self._get_photo_corners_refined(contour, 1.0)
                    
                    candidates.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'area': int(area),
                        'confidence': float(confidence),
                        'aspect_ratio': float(w/h),
                        'contour': contour.tolist(),
                        'corners': corners.tolist(),
                        'detection_method': 'watershed'
                    })
        
        return candidates
    
    def _merge_overlapping_detections(self, detections: List[Dict]) -> List[Dict]:
        """Merge overlapping detections using Non-Maximum Suppression"""
        if not detections:
            return []
        
        # Sort by confidence
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        merged = []
        used = set()
        
        for i, det in enumerate(detections):
            if i in used:
                continue
            
            # Check overlap with higher confidence detections
            overlaps = False
            for j in range(len(merged)):
                if self._calculate_iou(det, merged[j]) > 0.5:
                    overlaps = True
                    break
            
            if not overlaps:
                merged.append(det)
                used.add(i)
        
        return merged
    
    def _calculate_iou(self, det1: Dict, det2: Dict) -> float:
        """Calculate Intersection over Union"""
        x1, y1, w1, h1 = det1['x'], det1['y'], det1['width'], det1['height']
        x2, y2, w2, h2 = det2['x'], det2['y'], det2['width'], det2['height']
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Calculate union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0
    
    def _is_valid_photo_region(self, x: int, y: int, w: int, h: int, original_area: int) -> bool:
        """Validate if a region could be a photo"""
        area = w * h
        aspect_ratio = w / h
        
        if area < self.min_photo_area:
            return False
        
        if area > original_area * self.max_photo_area_ratio:
            return False
        
        if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
            return False
        
        if x < 5 or y < 5:
            return False
        
        # Require minimum dimensions (stricter to avoid detecting photo content)
        if w < self.min_dimension or h < self.min_dimension:
            return False
        
        # Additional perimeter check to filter out thin/small objects
        # For 300x300 minimum: perimeter = 1200
        perimeter = 2 * (w + h)
        if perimeter < 1200:
            return False
        
        return True
    
    def _validate_perimeter_edges(self, edges: np.ndarray, x: int, y: int, w: int, h: int) -> float:
        """
        Validate that edges exist on all 4 sides of the detected region.
        Real photo borders have strong continuous edges around the entire perimeter.
        Content inside photos only has edges in specific areas (people, objects).
        Returns a score from 0.0 to 1.0 indicating perimeter edge quality.
        """
        if edges is None or x < 0 or y < 0:
            return 0.0
        
        # Safety check for bounds
        img_h, img_w = edges.shape[:2]
        if x + w > img_w or y + h > img_h:
            return 0.0
        
        # Define narrow border strips to specifically check photo borders
        # Use thinner strips (3-5% of dimension) to focus on actual borders
        border_width = max(int(w * 0.05), 3)
        border_height = max(int(h * 0.05), 3)
        
        # Extract edge density from each side
        try:
            # Top edge
            top_strip = edges[y:y+border_height, x:x+w]
            top_density = np.sum(top_strip > 0) / top_strip.size if top_strip.size > 0 else 0
            
            # Bottom edge
            bottom_strip = edges[y+h-border_height:y+h, x:x+w]
            bottom_density = np.sum(bottom_strip > 0) / bottom_strip.size if bottom_strip.size > 0 else 0
            
            # Left edge
            left_strip = edges[y:y+h, x:x+border_width]
            left_density = np.sum(left_strip > 0) / left_strip.size if left_strip.size > 0 else 0
            
            # Right edge
            right_strip = edges[y:y+h, x+w-border_width:x+w]
            right_density = np.sum(right_strip > 0) / right_strip.size if right_strip.size > 0 else 0
            
            # Check for continuous edges along each side (not just scattered pixels)
            # Real photo borders have continuous lines, not scattered edge pixels
            top_continuous = self._check_edge_continuity(top_strip, axis=1)  # horizontal continuity
            bottom_continuous = self._check_edge_continuity(bottom_strip, axis=1)
            left_continuous = self._check_edge_continuity(left_strip, axis=0)  # vertical continuity
            right_continuous = self._check_edge_continuity(right_strip, axis=0)
            
            # Real photo borders have higher edge density (stronger borders)
            # Balanced threshold to detect album photos while avoiding false positives
            min_edge_density = 0.12  # At least 12% edge pixels on each side
            
            # Count sides with both strong edges AND continuity
            sides_with_strong_edges = sum([
                top_density >= min_edge_density and top_continuous,
                bottom_density >= min_edge_density and bottom_continuous,
                left_density >= min_edge_density and left_continuous,
                right_density >= min_edge_density and right_continuous
            ])
            
            # Require at least 2 strong sides for a valid photo border
            # This allows detection of photos with faded/worn edges while still rejecting
            # internal content (people, objects) which typically only have edges on 1 side
            if sides_with_strong_edges < 2:
                return 0.0
            elif sides_with_strong_edges == 2:
                return 0.65  # 2 sides - acceptable for photos with faded edges
            elif sides_with_strong_edges == 3:
                return 0.85  # 3 sides - good detection
            else:
                return 1.0  # 4 sides - perfect rectangular border
                
        except Exception as e:
            logger.warning(f"Perimeter edge validation error: {e}")
            return 0.0
    
    def _check_edge_continuity(self, edge_strip: np.ndarray, axis: int) -> bool:
        """
        Check if edges are continuous along the specified axis.
        Real photo borders have continuous lines, not scattered pixels.
        axis=0: check vertical continuity (for left/right borders)
        axis=1: check horizontal continuity (for top/bottom borders)
        """
        if edge_strip.size == 0:
            return False
        
        # Project edges onto the specified axis
        projection = np.sum(edge_strip > 0, axis=axis)
        
        # Check what percentage of the line has edges
        # Real borders should have edges along most of the length
        if len(projection) == 0:
            return False
        
        coverage = np.sum(projection > 0) / len(projection)
        
        # Require at least 50% coverage for continuity
        # Balanced threshold to handle worn/faded borders while rejecting scattered edges
        return coverage >= 0.50
    
    def _calculate_advanced_confidence(
        self, contour, x: int, y: int, w: int, h: int, 
        image: np.ndarray, hierarchy, contour_idx: Optional[int]
    ) -> float:
        """
        Advanced confidence calculation with:
        - Geometric shape analysis
        - Texture analysis
        - Border detection
        """
        confidence = 0.0
        
        # Factor 1: Shape rectangularity (0.0 - 0.3)
        contour_area = cv2.contourArea(contour)
        bbox_area = w * h
        area_ratio = contour_area / bbox_area if bbox_area > 0 else 0
        confidence += area_ratio * 0.3
        
        # Factor 2: Aspect ratio match with common photo sizes (0.0 - 0.25)
        aspect_ratio = w / h
        common_ratios = [1.0, 4/3, 3/2, 16/9, 5/4, 0.75, 0.67]
        min_diff = min([abs(aspect_ratio - ratio) for ratio in common_ratios])
        aspect_score = max(0, 1 - min_diff * 2) * 0.25
        confidence += aspect_score
        
        # Factor 3: Corner quality (0.0 - 0.2)
        corners = self._get_photo_corners_refined(contour, 1.0)
        if len(corners) == 4:
            corner_angles = self._calculate_corner_angles(corners)
            # Good rectangles have ~90 degree corners
            angle_score = sum([1 for angle in corner_angles if 70 < angle < 110]) / 4
            confidence += angle_score * 0.2
        
        # Factor 4: Size appropriateness (0.0 - 0.15)
        if 5000 < bbox_area < 800000:
            confidence += 0.15
        elif 2000 < bbox_area < 5000 or 800000 < bbox_area < 1500000:
            confidence += 0.08
        
        # Factor 5: Texture analysis (0.0 - 0.1)
        if image is not None:
            texture_score = self._analyze_texture(image, x, y, w, h)
            confidence += texture_score * 0.1
        
        return min(1.0, confidence)
    
    def _calculate_corner_angles(self, corners: np.ndarray) -> List[float]:
        """Calculate angles at each corner of the quadrilateral"""
        angles = []
        n = len(corners)
        
        for i in range(n):
            p1 = corners[(i - 1) % n]
            p2 = corners[i]
            p3 = corners[(i + 1) % n]
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
            angles.append(angle)
        
        return angles
    
    def _analyze_texture(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> float:
        """Analyze texture to distinguish photos from random patterns"""
        # Extract region
        y1, y2 = max(0, y), min(image.shape[0], y + h)
        x1, x2 = max(0, x), min(image.shape[1], x + w)
        
        if y2 <= y1 or x2 <= x1:
            return 0.0
        
        region = image[y1:y2, x1:x2]
        
        if region.size == 0:
            return 0.0
        
        gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if len(region.shape) == 3 else region
        
        # Calculate variance (photos have moderate variance)
        variance = float(np.var(gray_region))
        
        # Photos typically have variance between 500 and 5000
        if 500 < variance < 5000:
            return 1.0
        elif 200 < variance < 500 or 5000 < variance < 8000:
            return 0.5
        else:
            return 0.2
    
    def _get_photo_corners_refined(self, contour, scale: float) -> np.ndarray:
        """
        Get refined corner points using optimized Douglas-Peucker approximation.
        This method finds the 4 corners of a rectangular photo with sub-pixel accuracy.
        """
        perimeter = cv2.arcLength(contour, True)
        
        # Try multiple epsilon values to find the best 4-corner approximation
        # Start with stricter approximation and relax if needed
        best_approx = None
        for epsilon_factor in [0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05]:
            epsilon = epsilon_factor * perimeter
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                # Found a good 4-corner approximation
                best_approx = approx
                break
            elif len(approx) < 4 and best_approx is None:
                # Over-simplified, keep the previous approximation
                break
        
        if best_approx is not None and len(best_approx) == 4:
            corners = best_approx.reshape(4, 2)
        else:
            # Fallback: use minimum area rectangle
            # This works well for rotated rectangles
            rect = cv2.minAreaRect(contour)
            corners = cv2.boxPoints(rect)
        
        # Scale back if needed
        if scale != 1.0:
            corners = corners / scale
        
        # Ensure corners are in the correct data type
        corners = corners.astype(np.float32)
        
        return corners
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """
        Order points in clockwise order: top-left, top-right, bottom-right, bottom-left.
        This method handles rotated rectangles correctly by using centroid-based ordering.
        """
        # Ensure we have exactly 4 points
        if len(pts) != 4:
            # If not 4 points, try to use minimum area rectangle
            logger.warning(f"Expected 4 corners, got {len(pts)}. Using centroid-based ordering.")
        
        # Convert to float32 for calculations
        pts = pts.astype(np.float32)
        
        # Calculate centroid
        centroid = np.mean(pts, axis=0)
        
        # Calculate angles from centroid to each point
        # This works for any rotation angle
        angles = []
        for pt in pts:
            angle = np.arctan2(pt[1] - centroid[1], pt[0] - centroid[0])
            angles.append(angle)
        
        # Sort points by angle (counter-clockwise from right)
        sorted_indices = np.argsort(angles)
        sorted_pts = pts[sorted_indices]
        
        # Find which point is top-left (closest to origin)
        # Top-left has smallest sum of coordinates
        sums = sorted_pts[:, 0] + sorted_pts[:, 1]
        tl_idx = np.argmin(sums)
        
        # Rotate array so top-left is first
        ordered = np.roll(sorted_pts, -tl_idx, axis=0)
        
        # Verify ordering by checking if points are in clockwise order
        # If not, reverse (except first point)
        if ordered.shape[0] == 4:
            # Calculate cross product to determine if clockwise
            v1 = ordered[1] - ordered[0]
            v2 = ordered[2] - ordered[0]
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            
            if cross < 0:  # Counter-clockwise, need to reverse
                ordered = np.array([ordered[0], ordered[3], ordered[2], ordered[1]], dtype=np.float32)
        
        return ordered.astype(np.float32)
    
    def _apply_perspective_transform(self, image: np.ndarray, corners: np.ndarray) -> Optional[np.ndarray]:
        """
        Apply perspective transformation with quality validation.
        This corrects tilted/rotated photos to be perfectly rectangular.
        """
        try:
            # Order corners correctly
            ordered_corners = self._order_points(corners)
            
            # Ensure we have valid corners
            if ordered_corners.shape[0] != 4:
                logger.warning("Invalid number of corners for perspective transform")
                return None
            
            tl, tr, br, bl = ordered_corners
            
            # Calculate target dimensions
            # Use the maximum width and height to preserve all photo content
            width_top = float(np.linalg.norm(tr - tl))
            width_bottom = float(np.linalg.norm(br - bl))
            width_left = float(np.linalg.norm(tl - bl))
            width_right = float(np.linalg.norm(tr - br))
            
            # Average the measurements for more stable results
            max_width = int(max(width_top, width_bottom))
            max_height = int(max(width_left, width_right))
            
            # Validate aspect ratio of output
            if max_width == 0 or max_height == 0:
                logger.warning("Invalid dimensions for perspective transform")
                return None
            
            aspect_ratio = max_width / max_height
            if aspect_ratio < 0.2 or aspect_ratio > 5.0:
                logger.warning(f"Unrealistic aspect ratio {aspect_ratio:.2f} for photo")
                return None
            
            # Validate output size is reasonable
            if max_width < 100 or max_height < 100:
                logger.warning(f"Output too small: {max_width}x{max_height}")
                return None
            
            if max_width > 10000 or max_height > 10000:
                logger.warning(f"Output too large: {max_width}x{max_height}")
                return None
            
            # Define destination rectangle (perfect rectangle)
            dst_pts = np.array([
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1]
            ], dtype=np.float32)
            
            # Calculate perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(ordered_corners, dst_pts)
            
            # Apply warp with high-quality interpolation
            warped = cv2.warpPerspective(
                image, matrix, (max_width, max_height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255, 255, 255)  # White border for photos
            )
            
            # Validate output is not blank or corrupted
            if warped is None or warped.size == 0:
                logger.warning("Warped image is empty")
                return None
            
            # Check if the warped image has reasonable content
            if len(warped.shape) == 3:
                mean_intensity = np.mean(warped)
                if mean_intensity < 5 or mean_intensity > 250:
                    logger.warning(f"Warped image has suspicious intensity: {mean_intensity:.1f}")
                    return None
            
            return warped
            
        except Exception as e:
            logger.warning(f"Perspective transform failed: {e}")
            return None
    
    def _refine_edges(self, image: np.ndarray) -> np.ndarray:
        """Refine edges of extracted photo"""
        try:
            if len(image.shape) == 3:
                filtered = cv2.bilateralFilter(image, 9, 75, 75)
            else:
                filtered = image
            
            border_size = 2
            h, w = image.shape[:2]
            
            if h > 2*border_size and w > 2*border_size:
                result = filtered[border_size:h-border_size, border_size:w-border_size]
                return result
            
            return filtered
        except Exception as e:
            logger.warning(f"Edge refinement failed: {e}")
            return image
    
    def extract_photos(self, image_path: str, output_dir: str, detected_photos: List[Dict]) -> List[Dict]:
        """Extract detected photos and save them"""
        if not OPENCV_AVAILABLE:
            return []
        
        image = None
        try:
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            height, width = image.shape[:2]
            if height * width > 30000000:
                logger.error(f"Image too large for extraction: {width}x{height} pixels")
                return []
            
            os.makedirs(output_dir, exist_ok=True)
            
            extracted_photos = []
            base_filename = os.path.splitext(os.path.basename(image_path))[0]
            
            for i, photo in enumerate(detected_photos):
                try:
                    x, y, w, h = photo['x'], photo['y'], photo['width'], photo['height']
                    contour = np.array(photo.get('contour', []), dtype=np.int32)
                    
                    extracted_region = None
                    if self.enable_perspective_correction and len(contour) > 0:
                        try:
                            corners = self._get_photo_corners_refined(contour, 1.0)
                            extracted_region = self._apply_perspective_transform(image, corners)
                            logger.info(f"Applied perspective correction to photo {i+1}")
                        except Exception as e:
                            logger.warning(f"Perspective correction failed for photo {i+1}: {e}")
                            extracted_region = None
                    
                    if extracted_region is None:
                        padding = max(5, int(min(w, h) * 0.02))
                        x_start = max(0, x - padding)
                        y_start = max(0, y - padding)
                        x_end = min(image.shape[1], x + w + padding)
                        y_end = min(image.shape[0], y + h + padding)
                        extracted_region = image[y_start:y_end, x_start:x_end]
                    
                    if self.enable_edge_refinement and extracted_region is not None:
                        extracted_region = self._refine_edges(extracted_region)
                    
                    method = photo.get('detection_method', 'standard')
                    output_filename = f"{base_filename}_photo_{i+1:02d}_{method}_conf{photo['confidence']:.2f}.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    success = cv2.imwrite(output_path, extracted_region, 
                                        [cv2.IMWRITE_JPEG_QUALITY, 95])
                    if not success:
                        logger.error(f"Failed to save extracted photo: {output_path}")
                        continue
                    
                    final_height, final_width = extracted_region.shape[:2]
                    
                    extracted_info = {
                        'original_region': photo,
                        'filename': output_filename,
                        'file_path': output_path,
                        'extracted_width': final_width,
                        'extracted_height': final_height,
                        'confidence': photo['confidence'],
                        'detection_method': method,
                        'perspective_corrected': self.enable_perspective_correction and len(contour) > 0
                    }
                    
                    extracted_photos.append(extracted_info)
                    logger.info(f"Extracted photo {i+1}: {output_filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to extract photo {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(extracted_photos)} photos from {image_path}")
            return extracted_photos
            
        except MemoryError:
            logger.error(f"Out of memory during photo extraction for {image_path}")
            return []
        except Exception as e:
            logger.error(f"Photo extraction failed for {image_path}: {e}")
            return []
        finally:
            if image is not None:
                del image

# Backward compatibility alias
PhotoDetector = AdvancedPhotoDetector

# Global instance
photo_detector = AdvancedPhotoDetector()

def detect_photos_in_image(image_path: str) -> List[Dict]:
    """Convenience function for detecting photos in an image"""
    return photo_detector.detect_photos(image_path)

def extract_detected_photos(image_path: str, output_dir: str, detected_photos: List[Dict]) -> List[Dict]:
    """Convenience function for extracting detected photos"""
    return photo_detector.extract_photos(image_path, output_dir, detected_photos)
