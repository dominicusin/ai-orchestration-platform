"""Tests for AI Pipeline"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock

# Set test environment
os.environ["LOG_FORMAT"] = "text"
os.environ["OLLAMA_MODEL"] = "gemma3:1b"


class TestProviders:
    """Test AI providers"""
    
    def test_provider_list(self):
        """Test provider list loads"""
        from orchestration.ai.providers import OPENAI_COMPATIBLE_PROVIDERS
        assert len(OPENAI_COMPATIBLE_PROVIDERS) >= 90
        assert "ollama" in OPENAI_COMPATIBLE_PROVIDERS
        assert "deepseek" in OPENAI_COMPATIBLE_PROVIDERS
        assert "groq" in OPENAI_COMPATIBLE_PROVIDERS
    
    def test_provider_config(self):
        """Test provider config"""
        from orchestration.ai.providers import OPENAI_COMPATIBLE_PROVIDERS
        ollama = OPENAI_COMPATIBLE_PROVIDERS["ollama"]
        assert ollama.base_url == "http://localhost:11434"
        assert ollama.model is not None
    
    def test_provider_manager(self):
        """Test provider manager"""
        from orchestration.ai.providers import get_provider_manager
        pm = get_provider_manager()
        assert pm is not None
        # Ollama should be available if running
        # providers = pm.list_available()


class TestCircuitBreaker:
    """Test circuit breaker"""
    
    def test_breaker_creation(self):
        """Test circuit breaker creation"""
        from orchestration.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker(name="test")
        assert cb.name == "test"
        assert cb.state is not None


class TestCache:
    """Test caching"""
    
    def test_cache_creation(self):
        """Test cache creation"""
        from orchestration.cache.cache import FileCache
        import tempfile
        import shutil
        from pathlib import Path
        
        tmpdir = tempfile.mkdtemp()
        try:
            cache = FileCache(Path(tmpdir), max_memory_entries=10)
            assert cache is not None
        finally:
            shutil.rmtree(tmpdir)


class TestValidators:
    """Test validators"""
    
    def test_haskell_validator(self):
        """Test Haskell validation"""
        from orchestration.validators.validators import HaskellValidator
        
        validator = HaskellValidator(use_ghc=False, use_hlint=False)
        
        # Valid Haskell
        result = validator.validate("""
module Main where

main :: IO ()
main = putStrLn "Hello"
        """)
        
        assert result.valid
    
    def test_qml_validator(self):
        """Test QML validation"""
        from orchestration.validators.validators import QMLValidator
        
        validator = QMLValidator()
        
        # Valid QML
        result = validator.validate("""
import QtQuick 2.0

Rectangle {
    width: 100
    height: 100
    color: "red"
}
        """)
        
        assert result.valid
    
    def test_sql_validator(self):
        """Test SQL validation"""
        from orchestration.validators.validators import SQLValidator
        
        validator = SQLValidator()
        
        # Valid SQL
        result = validator.validate("""
SELECT * FROM users WHERE id = 1;
        """)
        
        assert result.valid


class TestPrompts:
    """Test prompts"""
    
    def test_prompts_exist(self):
        """Test all prompts are defined"""
        from orchestration.pipeline.pipeline import PROMPTS
        
        required = ["cpp_to_haskell", "qml_convert", "report_convert", "sql_ddl"]
        for key in required:
            assert key in PROMPTS
            assert len(PROMPTS[key]) > 0


class TestWebUI:
    """Test web UI"""
    
    def test_web_ui_import(self):
        """Test web UI imports"""
        from orchestration.web_ui import PipelineHandler
        assert PipelineHandler is not None
    
    def test_dashboard_html(self):
        """Test dashboard generates HTML"""
        from orchestration.web_ui import PipelineHandler
        handler = PipelineHandler.__new__(PipelineHandler)
        html = handler.dashboard()
        assert "AI Pipeline Monitor" in html
        assert "Haskell" in html


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_ai_client_creation(self):
        """Test AI client can be created"""
        from orchestration.ai.client import AsyncAIClient, AIConfig
        
        config = AIConfig(
            groq_model="llama-3.3-70b-versatile",
            ollama_model="gemma3:1b",
        )
        
        client = AsyncAIClient(config)
        assert client is not None
        await client.close()
    
    def test_pipeline_init(self):
        """Test pipeline can be initialized"""
        from orchestration.pipeline import ConversionPipeline
        import tempfile
        import shutil
        
        tmpin = tempfile.mkdtemp()
        tmpout = tempfile.mkdtemp()
        
        try:
            pipeline = ConversionPipeline(
                tmpin,
                tmpout,
                max_workers=2,
            )
            assert pipeline is not None
        finally:
            shutil.rmtree(tmpin)
            shutil.rmtree(tmpout)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
