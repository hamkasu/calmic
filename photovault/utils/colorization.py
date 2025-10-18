"""
Photo Colorization Utility
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Automatic colorization of black and white photos using deep learning.
"""

import cv2
import numpy as np
import os
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class PhotoColorizer:
    """Handles automatic colorization of black and white photos"""
    
    def __init__(self):
        """Initialize the colorizer with pre-trained model paths"""
        self.initialized = False
        self.prototxt_path = None
        self.model_path = None
        self.pts_npy_path = None
        self.net = None
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_dir, 'models', 'colorization')
        
        self.prototxt_path = os.path.join(models_dir, 'colorization_deploy_v2.prototxt')
        self.model_path = os.path.join(models_dir, 'colorization_release_v2.caffemodel')
        self.pts_npy_path = os.path.join(models_dir, 'pts_in_hull.npy')
        
        # Check if models exist, if not try to download them
        if not all(os.path.exists(p) for p in [self.prototxt_path, self.model_path, self.pts_npy_path]):
            logger.info("Colorization models not found, attempting to download...")
            try:
                from .download_models import download_colorization_models
                download_colorization_models()
            except Exception as e:
                logger.warning(f"Failed to download models: {e}")
        
        # Load model if all files exist
        if all(os.path.exists(p) for p in [self.prototxt_path, self.model_path, self.pts_npy_path]):
            self._load_model()
        else:
            logger.warning("Colorization model files not available - colorization will use basic method")
    
    def _load_model(self):
        """Load the pre-trained colorization model"""
        try:
            if not self.prototxt_path or not self.model_path or not self.pts_npy_path:
                raise RuntimeError("Model paths not initialized")
            
            self.net = cv2.dnn.readNetFromCaffe(self.prototxt_path, self.model_path)
            
            pts = np.load(self.pts_npy_path, allow_pickle=True)
            
            class8 = self.net.getLayerId("class8_ab")
            conv8 = self.net.getLayerId("conv8_313_rh")
            pts = pts.transpose().reshape(2, 313, 1, 1)
            self.net.getLayer(class8).blobs = [pts.astype("float32")]
            self.net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]
            
            self.initialized = True
            logger.info("Colorization model loaded successfully (DNN-based)")
        except Exception as e:
            logger.error(f"Failed to load colorization model: {e}")
            self.initialized = False
    
    def colorize_dnn(self, image_array):
        """
        Colorize using deep learning model
        
        Args:
            image_array: numpy array of the grayscale image (BGR format)
            
        Returns:
            numpy array of colorized image (BGR format)
        """
        if not self.initialized or self.net is None:
            raise RuntimeError("DNN colorization model not initialized")
        
        scaled = image_array.astype("float32") / 255.0
        lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)
        
        resized = cv2.resize(lab, (224, 224))
        L = cv2.split(resized)[0]
        L -= 50
        
        self.net.setInput(cv2.dnn.blobFromImage(L))
        ab = self.net.forward()[0, :, :, :].transpose((1, 2, 0))
        
        ab = cv2.resize(ab, (image_array.shape[1], image_array.shape[0]))
        
        L = cv2.split(lab)[0]
        colorized = np.concatenate((L[:, :, np.newaxis], ab), axis=2)
        
        colorized = cv2.cvtColor(colorized, cv2.COLOR_LAB2BGR)
        colorized = np.clip(colorized, 0, 1)
        colorized = (255 * colorized).astype("uint8")
        
        return colorized
    
    def colorize_basic(self, image_array):
        """
        Basic colorization using sepia tone effect
        
        Args:
            image_array: numpy array of the grayscale image (BGR format)
            
        Returns:
            numpy array of colorized image (BGR format)
        """
        if len(image_array.shape) == 2:
            gray = image_array
        else:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        
        sepia_kernel = np.array([[0.272, 0.534, 0.131],
                                 [0.349, 0.686, 0.168],
                                 [0.393, 0.769, 0.189]])
        
        gray_3channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
        sepia = cv2.transform(gray_3channel, sepia_kernel)
        sepia = np.clip(sepia, 0, 255).astype(np.uint8)
        
        return sepia
    
    def colorize_image(self, image_path, output_path=None, method='auto'):
        """
        Colorize a black and white photo
        
        Args:
            image_path: Path to the input grayscale image
            output_path: Path to save the colorized image (optional)
            method: 'auto', 'dnn', or 'basic' - colorization method to use
            
        Returns:
            tuple: (result, method_used) where result is the path to the colorized image
                   if output_path provided, else PIL Image object. method_used is the
                   actual method that was used ('dnn' or 'basic')
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            method_used = method
            if method == 'auto':
                if self.initialized:
                    colorized = self.colorize_dnn(image)
                    method_used = 'dnn'
                else:
                    colorized = self.colorize_basic(image)
                    method_used = 'basic'
            elif method == 'dnn':
                if not self.initialized:
                    raise RuntimeError("DNN model not available, use 'basic' or 'auto' method")
                colorized = self.colorize_dnn(image)
                method_used = 'dnn'
            elif method == 'basic':
                colorized = self.colorize_basic(image)
                method_used = 'basic'
            else:
                raise ValueError(f"Unknown colorization method: {method}")
            
            if output_path:
                cv2.imwrite(output_path, colorized)
                logger.info(f"Colorized image saved to {output_path} using {method_used} method")
                return output_path, method_used
            else:
                colorized_rgb = cv2.cvtColor(colorized, cv2.COLOR_BGR2RGB)
                return Image.fromarray(colorized_rgb), method_used
                
        except Exception as e:
            logger.error(f"Colorization failed: {e}")
            raise
    
    def is_grayscale(self, image_path):
        """
        Check if an image is grayscale
        
        Args:
            image_path: Path to the image
            
        Returns:
            bool: True if image is grayscale, False otherwise
            
        Raises:
            FileNotFoundError: If the image file cannot be read
            RuntimeError: If the image is corrupted or invalid
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise RuntimeError(f"Failed to read image file (corrupted or invalid format): {image_path}")
            
            if len(image.shape) == 2:
                return True
            
            b, g, r = cv2.split(image)
            
            diff_bg = cv2.absdiff(b, g)
            diff_br = cv2.absdiff(b, r)
            diff_gr = cv2.absdiff(g, r)
            
            max_diff = max(diff_bg.max(), diff_br.max(), diff_gr.max())
            
            # Use a more realistic threshold to account for compression artifacts
            # and scanning imperfections in black and white photos
            return bool(max_diff < 30)
            
        except (FileNotFoundError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Failed to check if image is grayscale: {e}")
            raise RuntimeError(f"Error checking image color mode: {e}") from e


_colorizer_instance = None


def get_colorizer():
    """Get or create a singleton colorizer instance"""
    global _colorizer_instance
    if _colorizer_instance is None:
        _colorizer_instance = PhotoColorizer()
    return _colorizer_instance


def colorize_photo(image_path, output_path=None, method='auto'):
    """
    Convenience function to colorize a photo
    
    Args:
        image_path: Path to the input grayscale image
        output_path: Path to save the colorized image (optional)
        method: 'auto', 'dnn', or 'basic' - colorization method to use
        
    Returns:
        tuple: (result, method_used) where result is the path to the colorized image
               if output_path provided, else PIL Image object. method_used is the
               actual method that was used ('dnn' or 'basic')
    """
    colorizer = get_colorizer()
    return colorizer.colorize_image(image_path, output_path, method)
