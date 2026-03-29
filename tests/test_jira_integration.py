"""Tests for Jira integration"""

from unittest.mock import AsyncMock, patch

import pytest

from orchestration.jira_integration import (
    JiraClient,
    JiraConfig,
    JiraIssue,
    JiraTransition,
)


class TestJiraConfig:
    """Test Jira configuration"""

    def test_from_env(self):
        """Test config from env"""
        with patch.dict("os.environ", {
            "JIRA_URL": "https://jira.example.com",
            "JIRA_USER": "admin",
            "JIRA_TOKEN": "secret_token",
            "JIRA_PROJECT_KEY": "PROJ",
        }):
            config = JiraConfig.from_env()
            assert config.url == "https://jira.example.com"
            assert config.user == "admin"
            assert config.token == "secret_token"
            assert config.project_key == "PROJ"

    def test_config_defaults(self):
        """Test config defaults"""
        config = JiraConfig()
        assert config.url == ""
        assert config.user == ""
        assert config.token == ""
        assert config.project_key == ""


class TestJiraClient:
    """Test Jira client"""

    @pytest.fixture
    def client(self):
        """Create client with test config"""
        config = JiraConfig(
            url="https://jira.example.com",
            user="admin",
            token="secret",
            project_key="PROJ",
        )
        return JiraClient(config)

    def test_client_init(self, client):
        """Test client initialization"""
        assert client.config.url == "https://jira.example.com"
        assert client.config.user == "admin"
        assert client.config.project_key == "PROJ"

    @pytest.mark.asyncio
    async def test_get_project(self, client):
        """Test get project"""
        mock_response = {
            "id": 10001,
            "key": "PROJ",
            "name": "Test Project",
            "star_count": 10,
            "forks_count": 5,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_project()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_project_stats(self, client):
        """Test get project stats"""
        mock_response = {
            "id": 10001,
            "key": "PROJ",
            "name": "Test Project",
            "starCount": 10,
            "forksCount": 5,
            "issueCount": 3,
            "visibility": "private",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_project_stats()
            assert result["star_count"] == 10
            assert result["open_issues"] == 3

    @pytest.mark.asyncio
    async def test_create_issue(self, client):
        """Test create issue"""
        mock_response = {
            "id": 10001,
            "key": "PROJ-1",
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_issue("Test Issue", "Description")
            assert result is not None
            assert result.key == "PROJ-1"

    @pytest.mark.asyncio
    async def test_get_issue(self, client):
        """Test get issue"""
        mock_response = {
            "id": 10001,
            "key": "PROJ-1",
            "fields": {
                "summary": "Test",
                "description": None,
                "status": {"name": "Open"},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"},
                "labels": ["bug"],
                "assignee": {"displayName": "John"},
                "created": "2024-01-01",
                "updated": "2024-01-01",
            },
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_issue("PROJ-1")
            assert result is not None
            assert result.key == "PROJ-1"
            assert result.summary == "Test"

    @pytest.mark.asyncio
    async def test_list_issues(self, client):
        """Test list issues"""
        mock_response = {
            "issues": [
                {
                    "id": 10001,
                    "key": "PROJ-1",
                    "fields": {
                        "summary": "Issue 1",
                        "description": None,
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Task"},
                        "priority": {"name": "High"},
                        "labels": [],
                        "assignee": None,
                        "created": "2024-01-01",
                        "updated": "2024-01-01",
                    },
                },
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.list_issues()
            assert len(result) == 1
            assert result[0].key == "PROJ-1"

    @pytest.mark.asyncio
    async def test_get_transitions(self, client):
        """Test get transitions"""
        mock_response = {
            "transitions": [
                {"id": "1", "name": "To Do", "to": {"name": "To Do"}},
                {"id": "2", "name": "In Progress", "to": {"name": "In Progress"}},
                {"id": "3", "name": "Done", "to": {"name": "Done"}},
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_transitions("PROJ-1")
            assert len(result) == 3
            assert result[0].name == "To Do"

    @pytest.mark.asyncio
    async def test_search(self, client):
        """Test search"""
        mock_response = {
            "issues": [
                {
                    "id": 10001,
                    "key": "PROJ-1",
                    "fields": {
                        "summary": "Found",
                        "description": None,
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Task"},
                        "priority": {"name": "Medium"},
                        "labels": [],
                        "assignee": None,
                        "created": "2024-01-01",
                        "updated": "2024-01-01",
                    },
                },
            ]
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.search("project = PROJ")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_add_comment(self, client):
        """Test add comment"""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": 101}
            result = await client.add_comment("PROJ-1", "Test comment")
            assert result is True


class TestJiraIssue:
    """Test Jira issue dataclass"""

    def test_issue_creation(self):
        """Test issue creation"""
        issue = JiraIssue(
            key="PROJ-1",
            id=10001,
            summary="Test",
            description="Description",
            status="Open",
            issue_type="Task",
            priority="High",
            labels=["bug"],
            assignee="John",
        )
        assert issue.key == "PROJ-1"
        assert issue.summary == "Test"
        assert "bug" in issue.labels


class TestJiraTransition:
    """Test Jira transition dataclass"""

    def test_transition_creation(self):
        """Test transition creation"""
        transition = JiraTransition(
            id="1",
            name="To Do",
            to_status="To Do",
        )
        assert transition.id == "1"
        assert transition.name == "To Do"
