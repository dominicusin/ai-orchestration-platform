```
"""Advanced JSON parsing utilities"""

import re
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("orchestration.utils.json_utils")


class JSONParser:
    """Advanced JSON parser с обработкой ошибок"""
    
    @staticmethod
    def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
        """Парсинг JSON из AI ответа"""
        
        # Method 1: Direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Method 2: Remove markdown code blocks
        cleaned = re.sub(r'^```json\s*', '', text.strip())
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass
        
        # Method 3: Find JSON in text
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Method 4: Try to fix common issues
        fixed = JSONParser._fix_json(text)
        if fixed:
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass
        
        # Method 5: Extract key-value pairs manually
        return JSONParser._extract_kv(text)
    
    @staticmethod
    def _fix_json(text: str) -> Optional[str]:
        """Исправление распространённых проблем JSON"""
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix single quotes to double quotes (basic)
        # Note: This is basic, won't handle all cases
        text = re.sub(r"'([^']*)'", r'"\1"', text)
        
        # Remove comments
        text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        # Fix unquoted keys
        text = re.sub(r'(\w+):', r'"\1":', text)
        
        return text.strip()
    
    @staticmethod
    def _extract_kv(text: str) -> Optional[Dict[str, Any]]:
        """Извлечение ключ-значение из текста"""
        result = {}
        
        # Look for key: value patterns
        patterns = [
            r'"(\w+)":\s*"([^"]*)"',  # "key": "value"
            r'"(\w+)":\s*(\d+)',       # "key": 123
            r'"(\w+)":\s*(true|false)', # "key": true/false
            r'(\w+):\s*"([^"]*)"',      # key: "value"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    key, value = match
                    result[key] = value
        
        return result if result else None
    
    @staticmethod
    def parse_array_response(text: str) -> Optional[list]:
        """Парсинг JSON массива"""
        
        # Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Find array
        match = re.search(r'\[[^\]]*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        return None


class SmartJSONEncoder(json.JSONEncoder):
    """Enhanced JSON encoder"""
    
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super().default(obj)


def to_json(data: Any, pretty: bool = False) -> str:
    """Convert to JSON string"""
    indent = 2 if pretty else None
    return json.dumps(data, cls=SmartJSONEncoder, indent=indent, ensure_ascii=False)


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safe JSON parse с default значением"""
    try:
        return JSONParser.parse_json_response(text)
    except Exception:
        return default


# Usage examples
if __name__ == "__main__":
    # Test cases
    test_cases = [
        '{"key": "value"}',
        '```json\n{"key": "value"}\n```',
        '{"key": "value", "nested": {"inner": 123}}',
        'Some text {"key": "value"} more text',
        '{"key": "value", "trailing": "comma",}',
    ]
    
    for test in test_cases:
        result = JSONParser.parse_json_response(test)
        print(f"Input: {test[:50]}...")
        print(f"Output: {result}\n")
```