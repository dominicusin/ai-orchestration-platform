"""Input validators for user input"""

import os
import re
import logging
from typing import Any, List

logger = logging.getLogger("orchestration.input_validators")


class PathValidator:
    """Validate file paths"""
    
    def validate(self, path: str) -> bool:
        if not isinstance(path, str):
            return False
        if ".." in path:
            return False
        if path.startswith("/"):
            return not path.startswith("/etc")
        return True


class CommandValidator:
    """Validate shell commands"""
    
    def validate(self, cmd: str) -> bool:
        dangerous = [";", "|", "&", "$", "`", ">", "<"]
        return not any(c in cmd for c in dangerous)


def validate_path(path: str) -> bool:
    return PathValidator().validate(path)


def validate_command(cmd: str) -> bool:
    return CommandValidator().validate(cmd)