# Path: llm/response_parser.py
# FIXED: BUG-008 - Added fallback raw JSON extraction for non-markdown LLM responses
import re
import json
from typing import Optional, Any

class ResponseParser:
    """
    Parses LLM responses to extract structured data or code blocks.
    """
    @staticmethod
    def extract_code(text: str, language: str = "python") -> str:
        # Try specific language block first
        pattern = rf"```{language}\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        # Fallback: generic code block
        generic = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
        if generic:
            return generic.group(1)
        return ""

    @staticmethod
    def extract_json(text: str) -> Optional[str]:
        # Try ```json block first
        pattern = r"```json\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # FIXED: Fallback - try to extract raw JSON object or array
        raw_obj = re.search(r"(\{.*\})", text, re.DOTALL)
        if raw_obj:
            try:
                json.loads(raw_obj.group(1))  # Validate it's real JSON
                return raw_obj.group(1)
            except json.JSONDecodeError:
                pass
        
        raw_arr = re.search(r"(\[.*\])", text, re.DOTALL)
        if raw_arr:
            try:
                json.loads(raw_arr.group(1))
                return raw_arr.group(1)
            except json.JSONDecodeError:
                pass
        
        return None

    @staticmethod
    def parse_json_safe(text: str) -> Optional[Any]:
        """Safely parse JSON from LLM response, trying multiple formats."""
        extracted = ResponseParser.extract_json(text)
        if extracted:
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                return None
        return None
