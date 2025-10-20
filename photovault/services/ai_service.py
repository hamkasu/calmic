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

class AIService:
    """Handles AI-powered image processing using Google Gemini"""
    
    def __init__(self):
        """Initialize AI service with Google Gemini client"""
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found - AI features will be disabled")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("AI service initialized successfully with Google Gemini")
    
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


# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get or create singleton AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
