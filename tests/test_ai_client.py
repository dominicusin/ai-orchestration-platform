"""Tests for AI Client (LLM)"""

import pytest
import asyncio

from orchestration.ai_client import (
    LLMProvider,
    LLMResponse,
    LLMMetrics,
    BaseLLMClient,
    OpenAIClient,
    OllamaClient,
    GroqClient,
    DeepSeekClient,
    MistralClient,
    CohereClient,
    LLMManager,
    LLMRater,
    get_llm_manager,
)


class TestLLMResponse:
    """Test LLMResponse"""

    def test_creation(self):
        """Test creation"""
        response = LLMResponse(
            content="test response",
            model="gpt-4",
            provider=LLMProvider.OPENAI,
            tokens_used=100,
            latency=0.5,
        )
        assert response.content == "test response"
        assert response.model == "gpt-4"


class TestOpenAIClient:
    """Test OpenAI client"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return OpenAIClient()

    @pytest.mark.asyncio
    async def test_generate(self, client):
        """Test generate"""
        response = await client.generate("Hello", model="gpt-4o-mini")
        assert response.content is not None
        assert response.provider == LLMProvider.OPENAI

    @pytest.mark.asyncio
    async def test_generate_stream(self, client):
        """Test generate stream"""
        chars = []
        async for char in client.generate_stream("Hello"):
            chars.append(char)
        assert len(chars) > 0


class TestOllamaClient:
    """Test Ollama client"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_generate(self, client):
        """Test generate"""
        response = await client.generate("Hello", model="llama3.2")
        assert response.content is not None
        assert response.provider == LLMProvider.OLLAMA


class TestGroqClient:
    """Test Groq client"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return GroqClient()

    @pytest.mark.asyncio
    async def test_generate(self, client):
        """Test generate"""
        response = await client.generate("Hello")
        assert response.content is not None
        assert response.provider == LLMProvider.GROQ


class TestDeepSeekClient:
    """Test DeepSeek client"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return DeepSeekClient()

    @pytest.mark.asyncio
    async def test_generate(self, client):
        """Test generate"""
        response = await client.generate("Hello")
        assert response.content is not None
        assert response.provider == LLMProvider.DEEPSEEK


class TestMistralClient:
    """Test Mistral client"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return MistralClient()

    @pytest.mark.asyncio
    async def test_generate(self, client):
        """Test generate"""
        response = await client.generate("Hello")
        assert response.content is not None
        assert response.provider == LLMProvider.MISTRAL


class TestCohereClient:
    """Test Cohere client"""

    @pytest.fixture
    def client(self):
        """Create client"""
        return CohereClient()

    @pytest.mark.asyncio
    async def test_generate(self, client):
        """Test generate"""
        response = await client.generate("Hello")
        assert response.content is not None
        assert response.provider == LLMProvider.COHERE


class TestLLMManager:
    """Test LLM Manager"""

    @pytest.fixture
    def manager(self):
        """Create manager"""
        return LLMManager()

    def test_creation(self, manager):
        """Test creation"""
        assert manager is not None

    def test_register_client(self, manager):
        """Test register client"""
        client = OpenAIClient()
        manager.register_client(LLMProvider.OPENAI, client)
        assert manager.get_client(LLMProvider.OPENAI) is not None

    def test_get_available_providers(self, manager):
        """Test get available providers"""
        manager.register_client(LLMProvider.OPENAI, OpenAIClient())
        providers = manager.get_available_providers()
        assert LLMProvider.OPENAI in providers


class TestLLMRater:
    """Test LLM Rater"""

    def test_get_rating(self):
        """Test get rating"""
        rating = LLMRater.get_rating(LLMProvider.GROQ)
        assert "speed" in rating
        assert "quality" in rating
        assert "cost" in rating

    def test_rank_by_speed(self):
        """Test rank by speed"""
        ranked = LLMRater.rank_by_speed()
        assert len(ranked) > 0
        # Groq should be fastest
        assert ranked[0][0] == LLMProvider.GROQ

    def test_rank_by_quality(self):
        """Test rank by quality"""
        ranked = LLMRater.rank_by_quality()
        assert len(ranked) > 0
        # Paid models should have highest quality
        assert ranked[0][0] in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]

    def test_rank_by_cost(self):
        """Test rank by cost"""
        ranked = LLMRater.rank_by_cost()
        assert len(ranked) > 0
        # Free models should be first
        assert ranked[0][0] in [LLMProvider.OLLAMA, LLMProvider.GROQ, LLMProvider.DEEPSEEK]

    def test_rank_overall(self):
        """Test rank overall"""
        ranked = LLMRater.rank_overall()
        assert len(ranked) > 0
        # Groq should rank high overall (free + fast + good quality)
        assert ranked[0][0] == LLMProvider.GROQ


class TestLLMProvider:
    """Test LLM Provider enum"""

    def test_values(self):
        """Test enum values"""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.GROQ.value == "groq"


class TestGetLLMManager:
    """Test get_llm_manager singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_llm_manager()
        m2 = get_llm_manager()
        assert m1 is m2

    def test_default_clients(self):
        """Test default clients registered"""
        manager = get_llm_manager()
        # Should have free providers by default
        assert manager.get_client(LLMProvider.OLLAMA) is not None
        assert manager.get_client(LLMProvider.GROQ) is not None
        assert manager.get_client(LLMProvider.DEEPSEEK) is not None