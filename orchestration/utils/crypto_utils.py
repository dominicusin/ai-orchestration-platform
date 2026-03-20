"""Cryptography utilities"""

import hashlib
import hmac
import base64
import secrets
from typing import Optional


def generate_token(length: int = 32) -> str:
    """Generate random token"""
    return secrets.token_urlsafe(length)


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{base64.b64encode(hashed).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password"""
    try:
        salt, data = hashed.split(':')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(data, base64.b64encode(new_hash).decode())
    except:
        return False


def generate_key() -> str:
    """Generate encryption key"""
    return base64.b64encode(secrets.token_bytes(32)).decode()


def md5(text: str) -> str:
    """MD5 hash"""
    return hashlib.md5(text.encode()).hexdigest()


def sha256(text: str) -> str:
    """SHA256 hash"""
    return hashlib.sha256(text.encode()).hexdigest()
