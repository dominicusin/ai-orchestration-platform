"""UUID utilities"""

import uuid


def uuid4_str() -> str:
    """Generate UUID4 as string"""
    return str(uuid.uuid4())


def uuid1_str() -> str:
    """Generate UUID1 as string"""
    return str(uuid.uuid1())


def uuid5_str(name: str, namespace: str = None) -> str:
    """Generate UUID5"""
    ns = uuid.UUID(namespace) if namespace else uuid.NAMESPACE_DNS
    return str(uuid.uuid5(ns, name))


def is_valid_uuid_str(s: str) -> bool:
    """Check if valid UUID string"""
    try:
        uuid.UUID(s)
        return True
    except (ValueError, AttributeError):
        return False
