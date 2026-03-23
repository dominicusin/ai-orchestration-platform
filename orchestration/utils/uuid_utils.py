"""UUID utilities"""

import uuid
from typing import UUID


def uuid4() -> str:
    """Generate UUID4"""
    return str(uuid.uuid4())


def uuid1() -> str:
    """Generate UUID1"""
    return str(uuid.uuid1())


def uuid5(name: str, namespace: str = None) -> str:
    """Generate UUID5"""
    if namespace:
        return str(uuid.uuid5(uuid.UUID(namespace), name))
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))


def is_valid_uuid(id: str) -> bool:
    """Check if valid UUID"""
    try:
        uuid.UUID(id)
        return True
    except:
        return False


def parse_uuid(id: str) -> UUID:
    """Parse UUID string"""
    return uuid.UUID(id)
