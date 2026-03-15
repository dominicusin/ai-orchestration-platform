"""Security utilities"""

import os
import hashlib
import hmac
import secrets
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger("orchestration.security")


class SecurityConfig:
    """Security configuration"""
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    api_key_header: str = "X-API-Key"
    rate_limit_per_minute: int = 60
    max_request_size: int = 10 * 1024 * 1024  # 10MB


class APIKeyManager:
    """API key management"""
    
    def __init__(self):
        self.keys: dict = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load keys from env"""
        keys_env = os.getenv("API_KEYS", "")
        if keys_env:
            for key in keys_env.split(","):
                if key.strip():
                    self.keys[key.strip()] = {
                        "created": datetime.now().isoformat(),
                        "rate_limit": 100,
                    }
    
    def verify_key(self, api_key: str) -> bool:
        """Verify API key"""
        if not api_key:
            return False
        
        # Check key exists and not expired
        if api_key in self.keys:
            key_data = self.keys[api_key]
            # Could check expiration here
            return True
        
        return False
    
    def generate_key(self, name: str) -> str:
        """Generate new API key"""
        key = f"sk_{secrets.token_hex(24)}"
        self.keys[key] = {
            "name": name,
            "created": datetime.now().isoformat(),
            "rate_limit": 100,
        }
        return key
    
    def revoke_key(self, api_key: str):
        """Revoke API key"""
        if api_key in self.keys:
            del self.keys[api_key]


class RateLimiter:
    """Rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        minute_key = now.strftime("%Y%m%d%H%M")
        
        key = f"{identifier}:{minute_key}"
        count = self.requests.get(key, 0)
        
        if count >= self.requests_per_minute:
            return False
        
        self.requests[key] = count + 1
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests"""
        now = datetime.now()
        minute_key = now.strftime("%Y%m%d%H%M")
        key = f"{identifier}:{minute_key}"
        
        return max(0, self.requests_per_minute - self.requests.get(key, 0))


class InputSanitizer:
    """Sanitize user input"""
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path"""
        # Remove null bytes
        path = path.replace("\x00", "")
        
        # Remove dangerous patterns
        dangerous = ["../", "..\\", "~/.ssh", "/etc/passwd"]
        for pattern in dangerous:
            path = path.replace(pattern, "")
        
        return path
    
    @staticmethod
    def sanitize_code(code: str, max_length: int = 100000) -> str:
        """Sanitize code input"""
        # Limit length
        if len(code) > max_length:
            code = code[:max_length]
        
        # Remove null bytes
        code = code.replace("\x00", "")
        
        return code
    
    @staticmethod
    def detect_secrets(text: str) -> bool:
        """Detect potential secrets in text"""
        patterns = [
            r'api[_-]?key["\s:=]+["\']?[\w-]{20,}',
            r'secret["\s:=]+["\']?[\w-]{20,}',
            r'password["\s:=]+["\']?[\w-]{8,}',
            r'token["\s:=]+["\']?[\w-]{20,}',
            r'-----BEGIN (RSA|EC|DSA) PRIVATE KEY-----',
        ]
        
        import re
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False


class HashUtils:
    """Hashing utilities"""
    
    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Hash prompt for caching"""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
    
    @staticmethod
    def hash_file(content: bytes) -> str:
        """Hash file content"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def verify_hmac(data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        expected = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)


class SecurityMiddleware:
    """Security middleware"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.sanitizer = InputSanitizer()
        self.api_keys = APIKeyManager()
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """Check rate limit"""
        allowed = self.rate_limiter.is_allowed(identifier)
        remaining = self.rate_limiter.get_remaining(identifier)
        return allowed, remaining
    
    def sanitize_input(self, data: str, input_type: str = "text") -> str:
        """Sanitize input"""
        if input_type == "path":
            return self.sanitizer.sanitize_path(data)
        elif input_type == "code":
            return self.sanitizer.sanitize_code(data)
        return data
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key"""
        return self.api_keys.verify_key(api_key)


# Decorators
def rate_limit(requests_per_minute: int = 60):
    """Rate limit decorator"""
    limiter = RateLimiter(requests_per_minute)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            identifier = kwargs.get("identifier", "default")
            
            if not limiter.is_allowed(identifier):
                raise Exception("Rate limit exceeded")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_api_key(func):
    """Require API key decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        api_key = kwargs.get("api_key")
        
        if not api_key:
            raise Exception("API key required")
        
        keys = APIKeyManager()
        if not keys.verify_key(api_key):
            raise Exception("Invalid API key")
        
        return await func(*args, **kwargs)
    return wrapper


# Security check
def check_security():
    """Run security checks"""
    issues = []
    
    # Check secret key
    if os.getenv("SECRET_KEY") == "changeme":
        issues.append("SECRET_KEY is set to default value")
    
    # Check API keys
    if not os.getenv("API_KEYS"):
        issues.append("No API keys configured")
    
    # Check permissions
    test_file = Path("./test_security_write")
    try:
        test_file.write_text("test")
        test_file.unlink()
    except:
        issues.append("Cannot write to directory")
    
    if issues:
        logger.warning(f"Security issues: {issues}")
    
    return len(issues) == 0


from pathlib import Path