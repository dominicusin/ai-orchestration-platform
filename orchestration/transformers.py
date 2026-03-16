"""Pipeline transformers for data conversion"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("orchestration.transformers")


class Transformer:
    """Base transformer"""
    
    def transform(self, data: Any) -> Any:
        """Transform data"""
        raise NotImplementedError


class RenameKeysTransformer(Transformer):
    """Rename dictionary keys"""
    
    def __init__(self, mappings: Dict[str, str]):
        self.mappings = mappings
    
    def transform(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        
        result = {}
        
        for key, value in data.items():
            new_key = self.mappings.get(key, key)
            result[new_key] = value
        
        return result


class FlattenTransformer(Transformer):
    """Flatten nested dictionary"""
    
    def transform(self, data: dict, parent_key: str = "", sep: str = "_") -> dict:
        items = []
        
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self.transform(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)


class MapValuesTransformer(Transformer):
    """Map values using function"""
    
    def __init__(self, key: str, mapper: callable):
        self.key = key
        self.mapper = mapper
    
    def transform(self, data: dict) -> dict:
        if self.key in data:
            data[self.key] = self.mapper(data[self.key])
        return data


class SelectKeysTransformer(Transformer):
    """Select only specified keys"""
    
    def __init__(self, keys: List[str]):
        self.keys = set(keys)
    
    def transform(self, data: dict) -> dict:
        return {k: v for k, v in data.items() if k in self.keys}


class TransformerPipeline:
    """Pipeline of transformers"""
    
    def __init__(self):
        self.transformers: List[Transformer] = []
    
    def add(self, transformer: Transformer):
        self.transformers.append(transformer)
    
    def transform(self, data: Any) -> Any:
        for transformer in self.transformers:
            data = transformer.transform(data)
        return data
