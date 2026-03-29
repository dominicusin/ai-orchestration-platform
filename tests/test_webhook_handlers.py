"""Tests for Webhook Handlers"""

import hashlib
import hmac

import pytest

from orchestration.webhook_handlers import (
    GitHubWebhookHandler,
    GitLabWebhookHandler,
    SlackWebhookHandler,
    WebhookConfig,
    WebhookEvent,
    WebhookHandler,
    WebhookSender,
)


class TestWebhookConfig:
    """Test WebhookConfig"""

    def test_creation(self):
        """Test creation"""
        config = WebhookConfig(
            url="https://example.com/webhook",
            secret="secret",
            events=["push", "pull_request"],
        )
        assert config.url == "https://example.com/webhook"
        assert config.secret == "secret"
        assert "push" in config.events


class TestWebhookEvent:
    """Test WebhookEvent"""

    def test_creation(self):
        """Test creation"""
        event = WebhookEvent(
            event_type="push",
            source="github",
            payload={"commits": []},
        )
        assert event.event_type == "push"
        assert event.source == "github"
        assert event.timestamp != ""


class TestWebhookHandler:
    """Test WebhookHandler"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return WebhookHandler()

    def test_register_handler(self, handler):
        """Test register handler"""
        def test_func(e):
            return "handled"

        handler.register_handler("test_event", test_func)
        assert "test_event" in handler._handlers

    def test_register_config(self, handler):
        """Test register config"""
        config = WebhookConfig(url="https://test.com")
        handler.register_config("test", config)
        assert "test" in handler._configs

    @pytest.mark.asyncio
    async def test_handle_event(self, handler):
        """Test handle event"""
        async def test_handler(e):
            return f"handled: {e.event_type}"

        handler.register_handler("test", test_handler)
        event = WebhookEvent(event_type="test", source="test", payload={})

        result = await handler.handle_event(event)
        assert result == "handled: test"

    def test_verify_signature(self, handler):
        """Test signature verification"""
        payload = '{"test": "data"}'
        secret = "my_secret"

        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert handler.verify_signature(payload, signature, secret) is True
        assert handler.verify_signature(payload, "wrong", secret) is False

    def test_verify_no_secret(self, handler):
        """Test verify with no secret"""
        payload = '{"test": "data"}'
        assert handler.verify_signature(payload, "signature", "") is True


class TestWebhookSender:
    """Test WebhookSender"""

    @pytest.fixture
    def sender(self):
        """Create sender"""
        return WebhookSender()

    def test_sender_init(self, sender):
        """Test init"""
        assert sender._session is None


class TestGitHubWebhookHandler:
    """Test GitHubWebhookHandler"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return GitHubWebhookHandler()

    def test_creation(self, handler):
        """Test creation"""
        assert "push" in handler._handlers
        assert "pull_request" in handler._handlers

    @pytest.mark.asyncio
    async def test_handle_push(self, handler):
        """Test handle push"""
        event = WebhookEvent(
            event_type="push",
            source="github",
            payload={
                "commits": [{"id": "1"}, {"id": "2"}],
                "repository": {"full_name": "test/repo"},
            },
        )
        result = await handler._handle_push(event)
        assert result["commits"] == 2
        assert result["repo"] == "test/repo"

    @pytest.mark.asyncio
    async def test_handle_pull_request(self, handler):
        """Test handle PR"""
        event = WebhookEvent(
            event_type="pull_request",
            source="github",
            payload={
                "action": "opened",
                "pull_request": {"number": 1},
            },
        )
        result = await handler._handle_pull_request(event)
        assert result["pr_number"] == 1
        assert result["action"] == "opened"


class TestGitLabWebhookHandler:
    """Test GitLabWebhookHandler"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return GitLabWebhookHandler()

    def test_creation(self, handler):
        """Test creation"""
        assert "push" in handler._handlers

    @pytest.mark.asyncio
    async def test_handle_push(self, handler):
        """Test handle push"""
        event = WebhookEvent(
            event_type="push",
            source="gitlab",
            payload={
                "commits": [{"id": "1"}],
                "project": {"path_with_namespace": "group/project"},
            },
        )
        result = await handler._handle_push(event)
        assert result["project"] == "group/project"


class TestSlackWebhookHandler:
    """Test SlackWebhookHandler"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return SlackWebhookHandler()

    def test_creation(self, handler):
        """Test creation"""
        assert "url_verification" in handler._handlers

    @pytest.mark.asyncio
    async def test_handle_url_verification(self, handler):
        """Test URL verification"""
        event = WebhookEvent(
            event_type="url_verification",
            source="slack",
            payload={"challenge": "test_challenge"},
        )
        result = await handler._handle_url_verification(event)
        assert result["challenge"] == "test_challenge"
