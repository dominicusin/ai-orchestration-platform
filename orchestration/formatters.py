"""Code formatter utilities"""

import re
import logging
from typing import Optional

logger = logging.getLogger("orchestration.formatters")


class CodeFormatter:
    """Format code output"""

    @staticmethod
    def format_haskell(code: str) -> str:
        """Format Haskell code"""
        lines = code.split("\n")
        formatted = []

        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()

            # Fix indentation
            if line.startswith("data ") or line.startswith("type "):
                formatted.append("")

            formatted.append(line)

        # Remove extra blank lines
        result = []
        prev_empty = False

        for line in formatted:
            is_empty = not line.strip()

            if is_empty and prev_empty:
                continue

            result.append(line)
            prev_empty = is_empty

        return "\n".join(result)

    @staticmethod
    def format_qml(code: str) -> str:
        """Format QML code"""
        lines = code.split("\n")
        formatted = []
        indent = 0

        for line in lines:
            line = line.strip()

            if not line:
                formatted.append("")
                continue

            # Decrease indent for closing braces
            if line.startswith("}") or line.startswith("]"):
                indent = max(0, indent - 1)

            # Add indentation
            formatted.append("    " * indent + line)

            # Increase indent for opening braces
            if line.endswith("{"):
                indent += 1

        return "\n".join(formatted)

    @staticmethod
    def format_sql(code: str) -> str:
        """Format SQL code"""
        # Uppercase keywords
        keywords = [
            "SELECT", "FROM", "WHERE", "AND", "OR", "INSERT", "UPDATE", "DELETE",
            "CREATE", "TABLE", "INDEX", "DROP", "ALTER", "JOIN", "LEFT", "RIGHT",
            "INNER", "OUTER", "ON", "ORDER", "BY", "GROUP", "HAVING", "LIMIT",
        ]

        result = code
        for keyword in keywords:
            result = re.sub(
                rf'\b{keyword}\b',
                keyword,
                result,
                flags=re.IGNORECASE,
            )

        return result

    @staticmethod
    def remove_markdown(code: str) -> str:
        """Remove markdown code blocks"""
        # Remove ```haskell, ```qml, etc
        code = re.sub(r'```\w*\n?', '', code)

        # Remove leading/trailing whitespace
        code = code.strip()

        return code

    @staticmethod
    def normalize(code: str) -> str:
        """Normalize code"""
        # Remove BOM
        code = code.replace("\ufeff", "")

        # Normalize line endings
        code = code.replace("\r\n", "\n")

        # Remove multiple blank lines
        code = re.sub(r'\n\n\n+', '\n\n', code)

        return code


class CodeLinter:
    """Lint code for common issues"""

    @staticmethod
    def lint_haskell(code: str) -> list:
        """Lint Haskell code"""
        issues = []

        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for tabs
            if "\t" in line:
                issues.append(f"Line {i}: Use spaces instead of tabs")

            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append(f"Line {i}: Trailing whitespace")

            # Check line length
            if len(line) > 100:
                issues.append(f"Line {i}: Line too long ({len(line)} chars)")

        return issues

    @staticmethod
    def lint_qml(code: str) -> list:
        """Lint QML code"""
        issues = []

        # Check balanced braces
        if code.count("{") != code.count("}"):
            issues.append("Unbalanced curly braces")

        if code.count("[") != code.count("]"):
            issues.append("Unbalanced square brackets")

        if code.count("(") != code.count(")"):
            issues.append("Unbalanced parentheses")

        return issues


def format_code(code: str, language: str) -> str:
    """Format code based on language"""
    formatter = CodeFormatter()

    code = formatter.normalize(code)
    code = formatter.remove_markdown(language)

    if language == "haskell":
        return formatter.format_haskell(code)
    elif language == "qml":
        return formatter.format_qml(code)
    elif language == "sql":
        return formatter.format_sql(code)

    return code


def lint_code(code: str, language: str) -> list:
    """Lint code"""
    linter = CodeLinter()

    if language == "haskell":
        return linter.lint_haskell(code)
    elif language == "qml":
        return linter.lint_qml(code)

    return []