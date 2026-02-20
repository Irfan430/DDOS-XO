# Path: llm/providers/openai.py
# FIXED: BUG-004 - Replaced synchronous requests with async aiohttp
import os
import aiohttp
import logging
from typing import Optional, Dict, Any

class OpenAIProvider:
    """
    OpenAI API Provider for LUNA-ULTRA.
    Uses async aiohttp for non-blocking HTTP requests.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            return "Error: OpenAI API Key not found."
        
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {"model": "gpt-4", "messages": messages, "stream": False}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            logging.error(f"OpenAIProvider: HTTP error: {e}")
            return f"OpenAI API Error: {str(e)}"
        except Exception as e:
            logging.error(f"OpenAIProvider: Unexpected error: {e}")
            return f"OpenAI API Error: {str(e)}"
