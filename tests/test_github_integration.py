"""Tests for GitHub integration"""

from unittest.mock import AsyncMock, patch

import pytest

from orchestration.github_integration import (
    GitHubClient,
    GitHubConfig,
    GitHubIssue,
    GitHubPullRequest,
)


class TestGitHubConfig:
    """Test GitHub configuration"""

    def test_from_env(self):
        """Test config from env"""
        with patch.dict("os.environ", {
            "GITHUB_TOKEN": "test_token",
            "GITHUB_OWNER": "test_owner",
            "GITHUB_REPO": "test_repo",
        }):
            config = GitHubConfig.from_env()
            assert config.token == "test_token"
            assert config.owner == "test_owner"
            assert config.repo == "test_repo"

    def test_config_defaults(self):
        """Test config defaults"""
        config = GitHubConfig()
        assert config.token == ""
        assert config.owner == ""
        assert config.repo == ""
        assert config.api_url == "https://api.github.com"


class TestGitHubClient:
    """Test GitHub client"""

    @pytest.fixture
    def client(self):
        """Create client with test config"""
        config = GitHubConfig(token="test_token", owner="test_owner", repo="test_repo")
        return GitHubClient(config)

    def test_client_init(self, client):
        """Test client initialization"""
        assert client.config.token == "test_token"
        assert client.config.owner == "test_owner"
        assert client.config.repo == "test_repo"

    @pytest.mark.asyncio
    async def test_get_repo_info(self, client):
        """Test get repo info"""
        mock_response = {
            "stargazers_count": 100,
            "forks_count": 50,
            "watchers_count": 25,
            "open_issues_count": 10,
            "language": "Python",
            "size": 1000,
            "license": {"name": "MIT"},
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_repo_info()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_repo_stats(self, client):
        """Test get repo stats"""
        mock_response = {
            "stargazers_count": 100,
            "forks_count": 50,
            "watchers_count": 25,
            "open_issues_count": 10,
            "language": "Python",
            "size": 1000,
            "license": {"name": "MIT"},
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_repo_stats()
            assert result["stars"] == 100
            assert result["forks"] == 50

    @pytest.mark.asyncio
    async def test_create_issue(self, client):
        """Test create issue"""
        mock_response = {
            "number": 1,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "user1"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_issue("Test Issue", "Test body")
            assert result is not None
            assert result.number == 1
            assert result.title == "Test Issue"

    @pytest.mark.asyncio
    async def test_list_issues(self, client):
        """Test list issues"""
        mock_response = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "Body 1",
                "state": "open",
                "labels": [],
                "assignees": [],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "Body 2",
                "state": "closed",
                "labels": [],
                "assignees": [],
                "created_at": "2024-01-02T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            },
        ]

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.list_issues()
            assert len(result) == 2
            assert result[0].number == 1

    @pytest.mark.asyncio
    async def test_create_pull_request(self, client):
        """Test create pull request"""
        mock_response = {
            "number": 1,
            "title": "Test PR",
            "body": "PR body",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "labels": [],
            "draft": False,
            "merged": False,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_pull_request("Test PR", "PR body", "feature-branch")
            assert result is not None
            assert result.number == 1
            assert result.head == "feature-branch"


class TestGitHubIssue:
    """Test GitHub issue dataclass"""

    def test_issue_creation(self):
        """Test issue creation"""
        issue = GitHubIssue(
            number=1,
            title="Test",
            body="Body",
            state="open",
            labels=["bug"],
            assignees=["user1"],
        )
        assert issue.number == 1
        assert issue.title == "Test"
        assert "bug" in issue.labels


class TestGitHubPullRequest:
    """Test GitHub PR dataclass"""

    def test_pr_creation(self):
        """Test PR creation"""
        pr = GitHubPullRequest(
            number=1,
            title="Test PR",
            body="Body",
            state="open",
            head="feature",
            base="main",
            draft=False,
        )
        assert pr.number == 1
        assert pr.head == "feature"
        assert pr.base == "main"
