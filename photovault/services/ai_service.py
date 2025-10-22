"""
AI Service for PhotoVault
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Handles Google Gemini integration for AI-powered image processing
"""

import os
import logging
from typing import Dict, Optional, Tuple
from PIL import Image
import io
import json

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Optional OpenAI import for inpainting
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available - AI inpainting features disabled")

class AIService:
    """Handles AI-powered image processing using Google Gemini and OpenAI"""
    
    def __init__(self):
        """Initialize AI service with Google Gemini and OpenAI clients"""
        # Initialize Gemini
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not found - Gemini AI features will be disabled")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.gemini_api_key)
            logger.info("AI service initialized successfully with Google Gemini")
        
        # Initialize OpenAI
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_api_key or not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - AI inpainting features will be disabled")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("AI service initialized successfully with OpenAI")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
    
    def colorize_image_ai(self, image_path: str, output_path: str) -> Tuple[str, Dict]:
        """
        Colorize black and white image using AI
        
        Args:
            image_path: Path to the input grayscale image
            output_path: Path to save the colorized image
            
        Returns:
            Tuple of (output_path, metadata_dict)
        """
        if not self.is_available():
            raise RuntimeError("AI service not available - GEMINI_API_KEY not configured")
        
        try:
            # Read image as bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Request AI colorization guidance using Gemini
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg",
                    ),
                    "Analyze this black and white photo in detail. Provide realistic color suggestions for different elements in the image. Be specific about colors, tones, and natural appearances for the main subjects, background, clothing, objects, and any other visible elements. Describe what colors would be most natural and historically accurate."
                ],
            )
            
            color_guidance = response.text if response.text else "No guidance available"
            logger.info(f"AI colorization guidance generated: {len(color_guidance)} chars")
            
            # Use the existing DNN colorization but store AI guidance
            from photovault.utils.colorization import get_colorizer
            colorizer = get_colorizer()
            
            # Use DNN colorization if available, otherwise basic
            result_path, method = colorizer.colorize_image(image_path, output_path, method='auto')
            
            metadata = {
                'method': 'ai_guided_' + method,
                'ai_guidance': color_guidance,
                'model': 'gemini-2.0-flash-exp'
            }
            
            return result_path, metadata
            
        except Exception as e:
            logger.error(f"AI colorization failed: {e}")
            raise
    
    def enhance_image_ai(self, image_path: str) -> Dict:
        """
        Analyze image and provide AI-powered enhancement suggestions
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with enhancement suggestions
        """
        if not self.is_available():
            raise RuntimeError("AI service not available - GEMINI_API_KEY not configured")
        
        try:
            # Read image as bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            system_prompt = (
                "You are a professional photo restoration and enhancement expert. "
                "Analyze photos and provide specific, actionable suggestions for improvement. "
                "Respond in JSON format with: "
                "{'needs_enhancement': boolean, 'suggestions': [list of suggestions], "
                "'priority': 'low'|'medium'|'high', 'issues': [list of detected issues]}"
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg",
                    ),
                    "Analyze this photo and suggest enhancements. Identify issues like: low contrast, poor lighting, color fading, scratches, dust, blurriness, or any other quality problems. Provide specific enhancement suggestions."
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            
            result_text = response.text if response.text else "{}"
            result = json.loads(result_text)
            logger.info(f"AI enhancement analysis completed: {result.get('priority', 'unknown')} priority")
            
            return result
            
        except Exception as e:
            logger.error(f"AI enhancement analysis failed: {e}")
            raise
    
    def analyze_image(self, image_path: str) -> str:
        """
        Analyze image content and provide detailed description
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Detailed description of the image
        """
        if not self.is_available():
            raise RuntimeError("AI service not available - GEMINI_API_KEY not configured")
        
        try:
            # Read image as bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg",
                    ),
                    "Analyze this photo in detail. Describe the content, setting, subjects, time period (if identifiable), and any notable elements. This will be used for photo organization and tagging."
                ],
            )
            
            analysis = response.text if response.text else "No analysis available"
            logger.info(f"Image analysis completed: {len(analysis)} chars")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise
    
    def detect_damage(self, image_path: str) -> Dict:
        """
        Analyze photo damage using AI
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with damage detection results
        """
        if not self.is_available():
            raise RuntimeError("AI service not available - GEMINI_API_KEY not configured")
        
        try:
            # Read image as bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            system_prompt = (
                "You are a professional photo restoration expert. "
                "Analyze photos for damage and provide specific assessments. "
                "Respond in JSON format with: "
                "{'has_damage': boolean, 'damage_types': [list of damage types], "
                "'severity': 'low'|'medium'|'high'|'severe', "
                "'damaged_areas': [descriptions of where damage is located], "
                "'repair_recommendations': [specific repair suggestions]}"
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg",
                    ),
                    "Analyze this photo for damage. Identify: scratches, tears, cracks, stains, water damage, fading, missing sections, dust spots, or any other physical damage. Describe location and severity of each issue."
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            
            result_text = response.text if response.text else "{}"
            result = json.loads(result_text)
            logger.info(f"Damage detection completed: {result.get('severity', 'unknown')} severity")
            
            return result
            
        except Exception as e:
            logger.error(f"Damage detection failed: {e}")
            raise
    
    def inpaint_damage_ai(self, image_path: str, output_path: str, 
                          mask_path: Optional[str] = None,
                          prompt: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Use AI to inpaint damaged or missing areas in photos
        
        Args:
            image_path: Path to the damaged image
            output_path: Path to save the repaired image
            mask_path: Optional path to damage mask (white = damaged areas to repair)
            prompt: Optional prompt to guide the AI repair
            
        Returns:
            Tuple of (output_path, metadata)
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI not available - cannot perform AI inpainting. Please set OPENAI_API_KEY")
        
        try:
            import numpy as np
            import cv2
            
            # If no mask provided, try to detect damage automatically
            if mask_path is None:
                logger.info("No mask provided, using OpenCV to detect damage areas")
                from photovault.utils.damage_repair import damage_repair
                
                # Create temp mask by detecting scratches
                img = cv2.imread(image_path)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Detect damage using multiple methods
                kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
                kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
                scratch_v = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_v)
                scratch_h = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel_h)
                damage_mask = cv2.add(scratch_v, scratch_h)
                
                _, mask = cv2.threshold(damage_mask, 20, 255, cv2.THRESH_BINARY)
                mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)
                
                # Save temp mask
                import tempfile
                mask_path = tempfile.mktemp(suffix='.png')
                cv2.imwrite(mask_path, mask)
            
            # Default prompt if not provided
            if prompt is None:
                prompt = "Professionally restore this damaged photograph, maintaining the original style and quality"
            
            # Load images for OpenAI
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
            
            with open(mask_path, "rb") as mask_file:
                mask_data = mask_file.read()
            
            # Call OpenAI image edit API for inpainting
            response = self.openai_client.images.edit(
                image=image_data,
                mask=mask_data,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            # Download the result
            import requests
            image_url = response.data[0].url
            repaired_image = requests.get(image_url).content
            
            # Save repaired image
            with open(output_path, 'wb') as out_file:
                out_file.write(repaired_image)
            
            metadata = {
                'method': 'openai_inpainting',
                'model': 'dall-e-2',
                'prompt': prompt,
                'had_mask': mask_path is not None
            }
            
            logger.info(f"AI inpainting completed successfully")
            return output_path, metadata
            
        except Exception as e:
            logger.error(f"AI inpainting failed: {e}")
            raise


# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get or create singleton AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
