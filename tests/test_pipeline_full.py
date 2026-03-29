"""Tests for Pipeline prompts and templates"""


# Skip full pipeline tests due to complex imports
# Test just the prompts and templates

from orchestration.pipeline.pipeline import (
    FALLBACK_TEMPLATES,
    PROMPTS,
)


class TestPrompts:
    """Test prompt templates"""

    def test_cpp_to_haskell_prompt(self):
        """Test C++ to Haskell prompt"""
        prompt = PROMPTS["cpp_to_haskell"]
        assert "Haskell" in prompt
        assert "{code}" in prompt

    def test_sql_ddl_prompt(self):
        """Test SQL DDL prompt"""
        prompt = PROMPTS["sql_ddl"]
        assert "PostgreSQL" in prompt
        assert "{struct_info}" in prompt

    def test_qml_convert_prompt(self):
        """Test QML conversion prompt"""
        prompt = PROMPTS["qml_convert"]
        assert "QML" in prompt
        assert "QPushButton" in prompt

    def test_report_convert_prompt(self):
        """Test report conversion prompt"""
        prompt = PROMPTS["report_convert"]
        assert "JasperReports" in prompt
        assert "Pentaho" in prompt


class TestFallbackTemplates:
    """Test fallback templates"""

    def test_haskell_fallback(self):
        """Test Haskell fallback"""
        template = FALLBACK_TEMPLATES["haskell"]
        assert "module" in template
        assert "{name}" in template

    def test_sql_fallback(self):
        """Test SQL fallback"""
        template = FALLBACK_TEMPLATES["sql"]
        assert "CREATE TABLE" in template
        assert "{table_name}" in template

    def test_haskell_fallback_format(self):
        """Test Haskell fallback formatting"""
        result = FALLBACK_TEMPLATES["haskell"].format(
            name="User",
            fields="field1 :: Int, field2 :: Text",
            defaults="field1, field2",
        )
        assert "User" in result
        assert "field1 :: Int" in result

    def test_sql_fallback_format(self):
        """Test SQL fallback formatting"""
        result = FALLBACK_TEMPLATES["sql"].format(
            name="users",
            table_name="users",
            columns="name TEXT, age INTEGER",
        )
        assert "users" in result
        assert "name TEXT" in result
