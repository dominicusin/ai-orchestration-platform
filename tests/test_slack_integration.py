"""Tests for Slack integration"""

from unittest.mock import patch

import pytest

from orchestration.slack_integration import (
    SlackClient,
    SlackConfig,
)


class TestSlackConfig:
    """Test Slack configuration"""

    def test_from_env(self):
        """Test config from env"""
        with patch.dict("os.environ", {
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_CHANNEL": "#test",
        }):
            config = SlackConfig.from_env()
            assert config.webhook_url == "https://hooks.slack.com/test"
            assert config.bot_token == "xoxb-test"
            assert config.channel == "#test"

    def test_config_defaults(self):
        """Test config defaults"""
        config = SlackConfig()
        assert config.webhook_url == ""
        assert config.bot_token == ""
        assert config.channel == ""
        assert config.username == "AI Pipeline Bot"
        assert config.icon_emoji == ":robot_face:"


class TestSlackClient:
    """Test Slack client"""

    @pytest.fixture
    def client(self):
        """Create client with test config"""
        config = SlackConfig(
            webhook_url="https://hooks.slack.com/test",
            channel="#test",
        )
        return SlackClient(config)

    def test_client_init(self, client):
        """Test client initialization"""
        assert client.config.webhook_url == "https://hooks.slack.com/test"
        assert client.config.channel == "#test"

    @pytest.mark.asyncio
    async def test_send_webhook_no_url(self, client):
        """Test webhook without URL"""
        client.config.webhook_url = ""
        result = await client.send_webhook("Test message")
        assert result is False

    def test_build_section_text(self, client):
        """Test section text builder"""
        result = client.build_section_text("Hello world")
        assert result["type"] == "section"
        assert result["text"]["type"] == "mrkdwn"
        assert result["text"]["text"] == "Hello world"

    def test_build_divider(self, client):
        """Test divider builder"""
        result = client.build_divider()
        assert result["type"] == "divider"

    def test_build_header(self, client):
        """Test header builder"""
        result = client.build_header("Test Header")
        assert result["type"] == "header"
        assert result["text"]["text"] == "Test Header"

    def test_build_button(self, client):
        """Test button builder"""
        result = client.build_button("Click me", "action_id", "https://example.com")
        assert result["type"] == "button"
        assert result["text"]["text"] == "Click me"
        assert result["action_id"] == "action_id"
        assert result["url"] == "https://example.com"

    def test_build_actions(self, client):
        """Test actions builder"""
        button = client.build_button("Click", "action")
        result = client.build_actions([button])
        assert result["type"] == "actions"
        assert len(result["elements"]) == 1

    def test_build_section_fields(self, client):
        """Test section fields builder"""
        fields = ["Field 1", "Field 2"]
        result = client.build_section_fields(fields)
        assert result["type"] == "section"
        assert len(result["fields"]) == 2

    def test_build_context(self, client):
        """Test context builder"""
        element = {"type": "image", "image_url": "http://test.png", "alt_text": "test"}
        result = client.build_context([element])
        assert result["type"] == "context"
        assert len(result["elements"]) == 1
