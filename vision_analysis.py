"""AI-powered vision analysis for StealthCrawler v17."""

import asyncio
import logging
from typing import Optional, Dict, Any
import base64

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    AI-powered vision analysis using OpenAI and Anthropic.
    
    Features:
    - Screenshot analysis
    - Content extraction from images
    - Element detection
    - Multi-provider support
    """
    
    def __init__(
        self,
        provider: str = 'openai',
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key
        
    async def analyze_screenshot(
        self,
        screenshot_bytes: bytes,
        prompt: str = "Describe what you see in this screenshot."
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a screenshot using AI vision.
        
        Args:
            screenshot_bytes: Screenshot image bytes
            prompt: Analysis prompt
            
        Returns:
            Analysis results or None
        """
        if not self.api_key:
            logger.warning("No API key configured for vision analysis")
            return None
        
        try:
            if self.provider == 'openai':
                return await self._analyze_with_openai(screenshot_bytes, prompt)
            elif self.provider == 'anthropic':
                return await self._analyze_with_anthropic(screenshot_bytes, prompt)
            else:
                logger.error(f"Unknown provider: {self.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    async def _analyze_with_openai(
        self,
        screenshot_bytes: bytes,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze using OpenAI GPT-4 Vision."""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.api_key)
            
            # Encode image to base64
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            response = await client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            result = {
                'provider': 'openai',
                'description': response.choices[0].message.content,
                'model': response.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
            logger.info("OpenAI vision analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI vision analysis failed: {e}")
            return None
    
    async def _analyze_with_anthropic(
        self,
        screenshot_bytes: bytes,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze using Anthropic Claude."""
        try:
            from anthropic import AsyncAnthropic
            
            client = AsyncAnthropic(api_key=self.api_key)
            
            # Encode image to base64
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            response = await client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            result = {
                'provider': 'anthropic',
                'description': response.content[0].text,
                'model': response.model,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
            
            logger.info("Anthropic vision analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Anthropic vision analysis failed: {e}")
            return None
    
    async def detect_elements(
        self,
        screenshot_bytes: bytes,
        element_types: list = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect specific elements in screenshot.
        
        Args:
            screenshot_bytes: Screenshot image bytes
            element_types: Types of elements to detect (buttons, forms, links, etc.)
            
        Returns:
            Detected elements or None
        """
        if element_types is None:
            element_types = ['buttons', 'forms', 'links', 'images']
        
        prompt = f"Identify and list all {', '.join(element_types)} visible in this screenshot."
        
        return await self.analyze_screenshot(screenshot_bytes, prompt)
    
    async def extract_text(
        self,
        screenshot_bytes: bytes
    ) -> Optional[str]:
        """
        Extract all visible text from screenshot.
        
        Args:
            screenshot_bytes: Screenshot image bytes
            
        Returns:
            Extracted text or None
        """
        result = await self.analyze_screenshot(
            screenshot_bytes,
            "Extract and list all visible text from this screenshot."
        )
        
        if result:
            return result.get('description')
        
        return None
