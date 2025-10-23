"""
AI-Powered Photo Restoration using Replicate API
Provides access to state-of-the-art AI models for photo restoration
"""

import os
import logging
import requests
from typing import Dict, Tuple, Optional
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)

# Optional replicate import
try:
    import replicate
    REPLICATE_AVAILABLE = True
    logger.info("Replicate API available - AI restoration features enabled")
except ImportError as e:
    replicate = None
    REPLICATE_AVAILABLE = False
    logger.warning(f"Replicate not available - AI restoration features disabled: {e}")


class AIRestoration:
    """AI-powered photo restoration using state-of-the-art models"""
    
    # Model identifiers
    GFPGAN_MODEL = "tencentarc/gfpgan:9283608cc6b7be6b65a8e44983db012355fde4132009bf99d976b2f0896856a3"
    CODEFORMER_MODEL = "sczhou/codeformer:7de2ea26c616d5bf2245ad0d5e24f0ff9a6204578a5c876db53142edd9d2cd56"
    
    def __init__(self):
        """Initialize AI restoration service"""
        if not REPLICATE_AVAILABLE:
            logger.warning("Replicate not available - AI restoration features disabled")
            self.enabled = False
            return
        
        # Check for API token
        self.api_token = os.environ.get('REPLICATE_API_TOKEN')
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not set - AI restoration features disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("AI restoration service initialized successfully")
    
    def restore_with_gfpgan(self, image_path: str, output_path: str = None,
                           scale: int = 2, version: str = "v1.4") -> Tuple[str, Dict]:
        """
        Restore photo using GFPGAN (best for face restoration, preserving identity)
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, creates temp file)
            scale: Upscaling factor (1, 2, or 4)
            version: Model version ("v1.3" or "v1.4")
            
        Returns:
            Tuple of (output_path, restoration_stats)
        """
        if not self.enabled:
            raise RuntimeError("AI restoration not available - check Replicate API token")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Restoring with GFPGAN (scale={scale}, version={version}): {image_path}")
        
        try:
            # Run GFPGAN model with file handle
            with open(image_path, 'rb') as f:
                output = replicate.run(
                    self.GFPGAN_MODEL,
                    input={
                        "img": f,
                        "version": version,
                        "scale": scale
                    }
                )
            
            # Download result
            if output_path is None:
                output_path = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
            
            response = requests.get(output, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Get image dimensions for stats
            img = Image.open(output_path)
            width, height = img.size
            
            stats = {
                'model': 'GFPGAN',
                'version': version,
                'scale': scale,
                'output_width': width,
                'output_height': height,
                'method': 'ai_restoration',
                'provider': 'replicate'
            }
            
            logger.info(f"GFPGAN restoration completed successfully: {output_path}")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error in GFPGAN restoration: {e}")
            raise
    
    def restore_with_codeformer(self, image_path: str, output_path: str = None,
                               fidelity: float = 0.5, upscale: int = 2,
                               background_enhance: bool = True,
                               face_upsample: bool = True) -> Tuple[str, Dict]:
        """
        Restore photo using CodeFormer (best for severely damaged faces)
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, creates temp file)
            fidelity: Balance between quality and identity preservation (0-1)
                     Lower values = higher quality, more AI enhancement
                     Higher values = closer to original, preserves identity
            upscale: Upscaling factor (1, 2, or 4)
            background_enhance: Whether to enhance background with Real-ESRGAN
            face_upsample: Whether to upsample faces
            
        Returns:
            Tuple of (output_path, restoration_stats)
        """
        if not self.enabled:
            raise RuntimeError("AI restoration not available - check Replicate API token")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Restoring with CodeFormer (fidelity={fidelity}, upscale={upscale}): {image_path}")
        
        try:
            # Run CodeFormer model with file handle
            with open(image_path, 'rb') as f:
                output = replicate.run(
                    self.CODEFORMER_MODEL,
                    input={
                        "image": f,
                        "codeformer_fidelity": fidelity,
                        "upscale": upscale,
                        "background_enhance": background_enhance,
                        "face_upsample": face_upsample
                    }
                )
            
            # Download result
            if output_path is None:
                output_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
            
            response = requests.get(output, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Get image dimensions for stats
            img = Image.open(output_path)
            width, height = img.size
            
            stats = {
                'model': 'CodeFormer',
                'fidelity': fidelity,
                'upscale': upscale,
                'background_enhance': background_enhance,
                'face_upsample': face_upsample,
                'output_width': width,
                'output_height': height,
                'method': 'ai_restoration',
                'provider': 'replicate'
            }
            
            logger.info(f"CodeFormer restoration completed successfully: {output_path}")
            return output_path, stats
            
        except Exception as e:
            logger.error(f"Error in CodeFormer restoration: {e}")
            raise
    
    def auto_restore(self, image_path: str, output_path: str = None,
                    quality: str = 'balanced') -> Tuple[str, Dict]:
        """
        Automatically choose best restoration model based on quality setting
        
        Args:
            image_path: Path to input image
            output_path: Path for output (if None, creates temp file)
            quality: Quality preset ('fast', 'balanced', 'quality', 'maximum')
            
        Returns:
            Tuple of (output_path, restoration_stats)
        """
        if quality == 'fast':
            # GFPGAN with minimal upscaling
            return self.restore_with_gfpgan(image_path, output_path, scale=1, version="v1.3")
        
        elif quality == 'balanced':
            # GFPGAN v1.4 with 2x upscaling (best for most cases)
            return self.restore_with_gfpgan(image_path, output_path, scale=2, version="v1.4")
        
        elif quality == 'quality':
            # CodeFormer with balanced fidelity
            return self.restore_with_codeformer(
                image_path, output_path,
                fidelity=0.7,
                upscale=2,
                background_enhance=True,
                face_upsample=True
            )
        
        elif quality == 'maximum':
            # CodeFormer with maximum quality settings
            return self.restore_with_codeformer(
                image_path, output_path,
                fidelity=0.5,
                upscale=4,
                background_enhance=True,
                face_upsample=True
            )
        
        else:
            raise ValueError(f"Invalid quality preset: {quality}. Use 'fast', 'balanced', 'quality', or 'maximum'")


# Global instance
ai_restoration = AIRestoration()


# Convenience functions
def restore_with_ai(image_path: str, output_path: str = None,
                   model: str = 'auto', quality: str = 'balanced') -> Tuple[str, Dict]:
    """
    Restore photo using AI (convenience function)
    
    Args:
        image_path: Path to input image
        output_path: Path for output
        model: Model to use ('gfpgan', 'codeformer', or 'auto')
        quality: Quality preset for auto mode
        
    Returns:
        Tuple of (output_path, restoration_stats)
    """
    if model == 'gfpgan':
        return ai_restoration.restore_with_gfpgan(image_path, output_path)
    elif model == 'codeformer':
        return ai_restoration.restore_with_codeformer(image_path, output_path)
    else:
        return ai_restoration.auto_restore(image_path, output_path, quality=quality)
