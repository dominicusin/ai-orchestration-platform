"""
Валидаторы для Haskell, SQL, QML
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass

logger = logging.getLogger("orchestration.validators")


@dataclass
class ValidationResult:
    """Результат валидации"""
    valid: bool
    errors: list[str] = None
    warnings: list[str] = None
    tool_output: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class HaskellValidator:
    """Валидация Haskell кода"""

    def __init__(self, use_ghc: bool = True, use_hlint: bool = True):
        self.use_ghc = use_ghc
        self.use_hlint = use_hlint

        # Проверяем наличие инструментов
        self._ghc_available = self._check_tool("ghc")
        self._hlint_available = self._check_tool("hlint")

    def _check_tool(self, tool: str) -> bool:
        """Проверка наличия инструмента"""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def validate_syntax(self, content: str) -> ValidationResult:
        """Базовая проверка синтаксиса"""
        errors = []
        warnings = []

        if not content or len(content) < 10:
            return ValidationResult(False, errors=["Empty or too short content"])

        # Проверка на наличие module declaration
        if "module" not in content and "import" not in content:
            warnings.append("No module or import declarations found")

        # Проверка баланса скобок
        if not self._check_brackets(content):
            errors.append("Unbalanced brackets or parentheses")

        # Проверка типов в сигнатурах
        if "::" in content:
            # Проверяем что после :: есть тип
            for match in re.finditer(r"(\w+)\s*::\s*([^\n=]+)", content):
                type_sig = match.group(2).strip()
                if not type_sig or type_sig == "":
                    errors.append(f"Empty type signature for {match.group(1)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _check_brackets(self, content: str) -> bool:
        """Проверка баланса скобок"""
        stack = []
        pairs = {')': '(', ']': '[', '}': '{'}

        for char in content:
            if char in '([{':
                stack.append(char)
            elif char in ')]}':
                if not stack or stack[-1] != pairs[char]:
                    return False
                stack.pop()

        return len(stack) == 0

    def validate_ghc(self, content: str, timeout: int = 30) -> ValidationResult:
        """Валидация через GHC"""
        if not self._ghc_available:
            return ValidationResult(
                True,
                warnings=["GHC not available, skipping GHC validation"]
            )

        try:
            result = subprocess.run(
                ["ghc", "-fno-code", "-e", "return ()"],
                input=content,
                capture_output=True,
                timeout=timeout,
                text=True,
            )

            if result.returncode == 0:
                return ValidationResult(
                    valid=True,
                    tool_output=result.stdout,
                )
            else:
                errors = result.stderr.split("\n")[:5]  # First 5 lines
                return ValidationResult(
                    valid=False,
                    errors=errors,
                    tool_output=result.stderr,
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                False,
                errors=["GHC validation timeout"],
            )
        except Exception as e:
            return ValidationResult(
                False,
                errors=[f"GHC validation error: {str(e)}"],
            )

    def validate_hlint(self, content: str, timeout: int = 30) -> ValidationResult:
        """Валидация через HLint"""
        if not self._hlint_available:
            return ValidationResult(
                True,
                warnings=["HLint not available, skipping linting"]
            )

        try:
            result = subprocess.run(
                ["hlint", "-", "--quiet"],
                input=content,
                capture_output=True,
                timeout=timeout,
                text=True,
            )

            # HLint returns non-zero if there are hints
            output = result.stdout.strip()

            if result.returncode == 0 or not output:
                return ValidationResult(
                    valid=True,
                    tool_output=output,
                )
            else:
                # Parse hints
                warnings = output.split("\n")[:10]
                return ValidationResult(
                    valid=True,  # HLint warnings are not errors
                    warnings=warnings,
                    tool_output=output,
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                True,
                warnings=["HLint timeout"],
            )
        except Exception as e:
            return ValidationResult(
                True,
                warnings=[f"HLint error: {str(e)}"],
            )

    def validate(self, content: str, strict: bool = False) -> ValidationResult:
        """Полная валидация"""
        # Syntax check
        syntax_result = self.validate_syntax(content)
        if not syntax_result.valid:
            return syntax_result

        # GHC check
        if self.use_ghc:
            ghc_result = self.validate_ghc(content)
            if not ghc_result.valid:
                return ghc_result

        # HLint check (warnings only)
        if self.use_hlint and strict:
            hlint_result = self.validate_hlint(content)
            return hlint_result

        return ValidationResult(valid=True)


class SQLValidator:
    """Валидация SQL кода"""

    def __init__(self, use_pgformatter: bool = True):
        self.use_pgformatter = use_pgformatter
        self._pgformatter_available = self._check_tool("pg_format")

    def _check_tool(self, tool: str) -> bool:
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def validate_syntax(self, content: str) -> ValidationResult:
        """Базовая проверка синтаксиса SQL"""
        errors = []
        warnings = []

        if not content or len(content) < 10:
            return ValidationResult(False, errors=["Empty or too short SQL"])

        # Проверка CREATE TABLE
        if "CREATE TABLE" not in content.upper():
            warnings.append("No CREATE TABLE statements found")

        # Проверка баланса скобок
        if content.count('(') != content.count(')'):
            errors.append("Unbalanced parentheses")

        # Проверка завершающих ;
        statements = [s.strip() for s in content.split(';') if s.strip()]
        for stmt in statements[:5]:  # Check first 5
            if not stmt.upper().startswith((
                "CREATE", "ALTER", "DROP", "INSERT", "UPDATE", "DELETE",
                "COMMENT", "GRANT", "REVOKE"
            )):
                warnings.append(f"Unknown statement type: {stmt[:30]}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_pgformat(self, content: str) -> ValidationResult:
        """Форматирование через pg_format"""
        if not self._pgformatter_available:
            return ValidationResult(
                True,
                warnings=["pg_format not available"],
            )

        try:
            result = subprocess.run(
                ["pg_format", "-"],
                input=content,
                capture_output=True,
                timeout=10,
                text=True,
            )

            if result.returncode == 0:
                return ValidationResult(
                    valid=True,
                    tool_output=result.stdout,
                )
            else:
                return ValidationResult(
                    valid=False,
                    errors=[result.stderr],
                )
        except Exception as e:
            return ValidationResult(
                False,
                errors=[f"pg_format error: {str(e)}"],
            )

    def validate(self, content: str) -> ValidationResult:
        """Полная валидация SQL"""
        syntax_result = self.validate_syntax(content)
        if not syntax_result.valid:
            return syntax_result

        if self.use_pgformatter:
            return self.validate_pgformat(content)

        return ValidationResult(valid=True)


class QMLValidator:
    """Валидация QML кода"""

    def validate_syntax(self, content: str) -> ValidationResult:
        """Базовая проверка синтаксиса QML"""
        errors = []
        warnings = []

        if not content or len(content) < 10:
            return ValidationResult(False, errors=["Empty or too short QML"])

        # Проверка импортов
        if "import" not in content:
            warnings.append("No import statements found")

        # Проверка базовых элементов
        has_root = False
        for item in ["Item", "Rectangle", "Button", "Text", "Window", "ApplicationWindow"]:
            if re.search(rf'^\s*<{item}\s', content, re.MULTILINE):
                has_root = True
                break

        if not has_root:
            warnings.append("No root QML element found")

        # Check balanced brackets
        if content.count('{') != content.count('}'):
            errors.append("Unbalanced curly braces")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate(self, content: str) -> ValidationResult:
        return self.validate_syntax(content)


# ============================================================================
# ВАЛИДАТОРЫ ПО УМОЛЧАНИЮ
# ============================================================================

def get_haskell_validator() -> HaskellValidator:
    """Получение валидатора Haskell"""
    return HaskellValidator(
        use_ghc=os.getenv("VALIDATE_WITH_GHC", "true").lower() == "true",
        use_hlint=os.getenv("USE_HLINT", "true").lower() == "true",
    )


def get_sql_validator() -> SQLValidator:
    """Получение валидатора SQL"""
    return SQLValidator(
        use_pgformatter=os.getenv("USE_PGFORMAT", "true").lower() == "true",
    )


def get_qml_validator() -> QMLValidator:
    """Получение валидатора QML"""
    return QMLValidator()
