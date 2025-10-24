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
    
    def __init__(self):
        self.min_photo_area = 200000
        self.max_photo_area_ratio = 0.85
        self.min_aspect_ratio = 0.3
        self.max_aspect_ratio = 4.0
        self.contour_area_threshold = 0.008
        self.enable_perspective_correction = True
        self.enable_edge_refinement = True
        
        # Multi-scale detection parameters (removed small scale to avoid tiny detections)
        self.scales = [1.0, 0.85]
        
        # Detection confidence thresholds (increased to reduce false positives)
        self.min_confidence = 0.72
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
                
            logger.info(f"Starting advanced photo detection on {image_path}")
            
            height, width = image.shape[:2]
            if height * width > 25000000:
                logger.error(f"Image too large: {width}x{height} pixels. Maximum: 25MP")
                return []
            
            original_area = width * height
            
            # Strategy 1: Multi-scale pyramid detection
            all_detections = []
            all_detections.extend(self._multi_scale_detection(image, original_area))
            
            # Strategy 2: Polaroid-specific detection (white border)
            all_detections.extend(self._detect_polaroids(image, original_area))
            
            # Strategy 3: Faded/low-contrast photo detection
            all_detections.extend(self._detect_faded_photos(image, original_area))
            
            # Strategy 4: Watershed segmentation for touching photos
            all_detections.extend(self._watershed_detection(image, original_area))
            
            # Merge overlapping detections (NMS - Non-Maximum Suppression)
            merged_detections = self._merge_overlapping_detections(all_detections)
            
            # Sort by confidence
            merged_detections.sort(key=lambda p: p['confidence'], reverse=True)
            
            # Limit to top 15 detections
            if len(merged_detections) > 15:
                merged_detections = merged_detections[:15]
            
            logger.info(f"Detected {len(merged_detections)} photos with advanced detection")
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
        
        # Filter by minimum area
        min_area = processed.shape[0] * processed.shape[1] * self.contour_area_threshold
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
        
        # Require minimum dimensions to avoid small items within photos
        # Photos should be at least 400x400 pixels in both dimensions to avoid clothing/small objects
        if w < 400 or h < 400:
            return False
        
        # Additional perimeter check to filter out thin/small objects
        perimeter = 2 * (w + h)
        if perimeter < 1800:
            return False
        
        return True
    
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
        """Get refined corner points with sub-pixel accuracy"""
        # Approximate to polygon
        epsilon = 0.015 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) == 4:
            corners = approx.reshape(4, 2)
        else:
            # Use minimum area rectangle
            rect = cv2.minAreaRect(contour)
            corners = cv2.boxPoints(rect).astype(int)
        
        # Scale back if needed
        if scale != 1.0:
            corners = corners / scale
        
        return corners.astype(int)
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points: top-left, top-right, bottom-right, bottom-left"""
        sorted_pts = pts[np.argsort(pts[:, 1]), :]
        
        top_pts = sorted_pts[:2]
        top_pts = top_pts[np.argsort(top_pts[:, 0]), :]
        tl, tr = top_pts
        
        bottom_pts = sorted_pts[2:]
        bottom_pts = bottom_pts[np.argsort(bottom_pts[:, 0]), :]
        bl, br = bottom_pts
        
        return np.array([tl, tr, br, bl], dtype=np.float32)
    
    def _apply_perspective_transform(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """Apply perspective transformation"""
        ordered_corners = self._order_points(corners)
        tl, tr, br, bl = ordered_corners
        
        width_top = float(np.linalg.norm(tr - tl))
        width_bottom = float(np.linalg.norm(br - bl))
        max_width = int(max(width_top, width_bottom))
        
        height_left = float(np.linalg.norm(bl - tl))
        height_right = float(np.linalg.norm(br - tr))
        max_height = int(max(height_left, height_right))
        
        dst_pts = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype=np.float32)
        
        matrix = cv2.getPerspectiveTransform(ordered_corners, dst_pts)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
        
        return warped
    
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
