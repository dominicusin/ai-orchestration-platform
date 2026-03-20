"""Prompt templates for AI"""

from typing import Dict, List


TEMPLATES = {
    "analyze": "Analyze the following code: {code}",
    "convert": "Convert from {source} to {target}: {code}",
    "validate": "Validate: {content}",
    "summarize": "Summarize: {content}",
}


def get_template(name: str, **kwargs) -> str:
    """Get prompt template"""
    template = TEMPLATES.get(name, "")
    return template.format(**kwargs)


def list_templates() -> List[str]:
    """List all templates"""
    return list(TEMPLATES.keys())
