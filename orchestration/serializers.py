"""Pipeline serializers"""

import json
import logging
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger("orchestration.serializers")


class Serializer:
    """Base serializer"""
    
    def serialize(self, data: Any) -> str:
        raise NotImplementedError
    
    def deserialize(self, data: str) -> Any:
        raise NotImplementedError


class JSONSerializer(Serializer):
    """JSON serializer"""
    
    def __init__(self, indent: int = 2):
        self.indent = indent
    
    def serialize(self, data: Any) -> str:
        return json.dumps(data, indent=self.indent, default=str)
    
    def deserialize(self, data: str) -> Any:
        return json.loads(data)


class PipelineMetadataSerializer(Serializer):
    """Serialize pipeline metadata"""
    
    def serialize(self, data: Dict) -> str:
        meta = {
            "generated_at": datetime.now().isoformat(),
            "version": "4.0.0",
            "data": data,
        }
        return json.dumps(meta, indent=2)
    
    def deserialize(self, data: str) -> Dict:
        return json.loads(data)


def serialize_result(result: Any, format: str = "json") -> str:
    """Serialize result"""
    if format == "json":
        return json.dumps(result, indent=2, default=str)
    return str(result)
