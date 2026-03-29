"""ID utilities"""

import hashlib
import uuid
from datetime import datetime


def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate short ID"""
    return uuid.uuid4().hex[:length]


def generate_numeric_id(length: int = 10) -> str:
    """Generate numeric ID"""
    import random
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def generate_hash_id(text: str) -> str:
    """Generate hash-based ID"""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def parse_id(id_str: str) -> dict:
    """Parse ID to get info"""
    return {
        "id": id_str,
        "timestamp": datetime.now().isoformat(),
    }
