"""Pipeline input validators"""

import re
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger("orchestration.input_validators")


@dataclass
class ValidationError:
    """Validation error"""
    field: str
    message: str


class Validator:
    """Base validator"""
    
    def validate(self, data: Dict) -> List[ValidationError]:
        """Validate data"""
        raise NotImplementedError


class ProjectValidator(Validator):
    """Validate project configuration"""
    
    def validate(self, data: Dict) -> List[ValidationError]:
        errors = []
        
        # Validate project_path
        if "project_path" not in data or not data["project_path"]:
            errors.append(ValidationError("project_path", "Required"))
        
        # Validate output_path
        if "output_path" not in data or not data["output_path"]:
            errors.append(ValidationError("output_path", "Required"))
        
        # Validate max_workers
        max_workers = data.get("max_workers")
        if max_workers is not None:
            if not isinstance(max_workers, int):
                errors.append(ValidationError("max_workers", "Must be integer"))
            elif max_workers < 1 or max_workers > 32:
                errors.append(ValidationError("max_workers", "Must be 1-32"))
        
        return errors


class FilePathValidator(Validator):
    """Validate file paths"""
    
    def validate(self, data: Dict) -> List[ValidationError]:
        errors = []
        
        path = data.get("path", "")
        
        # Check for path traversal
        if ".." in path:
            errors.append(ValidationError("path", "Path traversal not allowed"))
        
        # Check for invalid characters
        if re.search(r'[<>"|?*]', path):
            errors.append(ValidationError("path", "Invalid characters in path"))
        
        return errors


class ProviderValidator(Validator):
    """Validate AI provider config"""
    
    def validate(self, data: Dict) -> List[ValidationError]:
        errors = []
        
        provider = data.get("provider", "")
        valid_providers = ["ollama", "groq", "openai", "anthropic", "deepseek", "mistral"]
        
        if provider and provider not in valid_providers:
            errors.append(ValidationError("provider", f"Must be one of: {valid_providers}"))
        
        return errors


class ValidatorChain:
    """Chain multiple validators"""
    
    def __init__(self):
        self.validators: List[Validator] = []
    
    def add(self, validator: Validator):
        """Add validator"""
        self.validators.append(validator)
    
    def validate(self, data: Dict) -> List[ValidationError]:
        """Validate with all validators"""
        errors = []
        
        for validator in self.validators:
            errors.extend(validator.validate(data))
        
        return errors
