# Path: llm/providers/gemini.py
# FIXED: BUG-006 - Replaced synchronous requests with async aiohttp
import os
import aiohttp
import logging
from typing import Optional, Dict, Any

class GeminiProvider:
    """
    Gemini API Provider for LUNA-ULTRA.
    Uses async aiohttp for non-blocking HTTP requests.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            return "Error: Gemini API Key not found."
        
        url = f"{self.base_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json", "Accept-Encoding": "gzip, deflate"}
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        data = {"contents": [{"parts": [{"text": full_prompt}]}]}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
        except aiohttp.ClientError as e:
            logging.error(f"GeminiProvider: HTTP error: {e}")
            return f"Gemini API Error: {str(e)}"
        except Exception as e:
            logging.error(f"GeminiProvider: Unexpected error: {e}")
            return f"Gemini API Error: {str(e)}"
