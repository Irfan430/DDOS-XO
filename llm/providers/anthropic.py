# Path: llm/providers/anthropic.py
# FIXED: BUG-005 - Replaced synchronous requests with async aiohttp
import os
import aiohttp
import logging
from typing import Optional, Dict, Any

class AnthropicProvider:
    """
    Anthropic API Provider for LUNA-ULTRA.
    Uses async aiohttp for non-blocking HTTP requests.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            return "Error: Anthropic API Key not found."
        
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate"}
        messages = [{"role": "user", "content": prompt}]
        
        data = {"model": "claude-3-opus-20240229", "messages": messages, "max_tokens": 1024}
        if system_prompt:
            data["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["content"][0]["text"]
        except aiohttp.ClientError as e:
            logging.error(f"AnthropicProvider: HTTP error: {e}")
            return f"Anthropic API Error: {str(e)}"
        except Exception as e:
            logging.error(f"AnthropicProvider: Unexpected error: {e}")
            return f"Anthropic API Error: {str(e)}"
