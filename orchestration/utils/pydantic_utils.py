"""Pydantic utilities"""

from typing import Any, Dict
try:
    from pydantic import BaseModel, Field, validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


def create_model(name: str, fields: Dict[str, Any]):
    """Create pydantic model"""
    if not HAS_PYDANTIC:
        raise ImportError("pydantic not installed")
    return type(name, (BaseModel,), fields)


def model_to_dict(model) -> Dict:
    """Convert model to dict"""
    if HAS_PYDANTIC and isinstance(model, BaseModel):
        return model.dict()
    return {}


def model_from_dict(model_class, data: Dict):
    """Create model from dict"""
    if HAS_PYDANTIC:
        return model_class(**data)
    return None
