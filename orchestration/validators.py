"""Validators for input validation"""

import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger("orchestration.validators")


class Validator:
    """Base validator"""
    
    def validate(self, value: Any) -> bool:
        raise NotImplementedError


class StringValidator(Validator):
    """Validate string"""
    
    def __init__(self, min_len: int = 0, max_len: int = 1000):
        self.min_len = min_len
        self.max_len = max_len
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return self.min_len <= len(value) <= self.max_len


class EmailValidator(Validator):
    """Validate email"""
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, value))


class URLValidator(Validator):
    """Validate URL"""
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        pattern = r'^https?://[\w\.-]+\.\w+'
        return bool(re.match(pattern, value))


class TaskValidator:
    """Validate task configuration"""
    
    def validate(self, task: Dict) -> List[str]:
        errors = []
        
        if "id" not in task:
            errors.append("Missing task id")
        
        if "handler" not in task and "subtasks" not in task:
            errors.append("Task must have handler or subtasks")
        
        return errors


def validate_task(task: Dict) -> bool:
    """Validate task"""
    validator = TaskValidator()
    return len(validator.validate(task)) == 0
