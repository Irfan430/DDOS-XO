# Path: llm/providers/deepseek.py
# FIXED: BUG-003 - Replaced synchronous requests with async aiohttp for non-blocking HTTP
import os
import aiohttp
import logging
from typing import Optional, Dict, Any

class DeepSeekProvider:
    """
    DeepSeek API Provider for LUNA-ULTRA.
    Uses async aiohttp for non-blocking HTTP requests.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            return "Error: DeepSeek API Key not found."
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {"model": "deepseek-chat", "messages": messages, "stream": False}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 400:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get("message", "")
                        if "context_length_exceeded" in error_msg or "token_limit" in error_msg:
                            return f"TOKEN_LIMIT_ERROR: {error_msg}"
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            logging.error(f"DeepSeekProvider: HTTP error: {e}")
            return f"DeepSeek API Error: {str(e)}"
        except Exception as e:
            logging.error(f"DeepSeekProvider: Unexpected error: {e}")
            return f"DeepSeek API Error: {str(e)}"
