"""Tests for GitLab integration"""

from unittest.mock import AsyncMock, patch

import pytest

from orchestration.gitlab_integration import (
    GitLabClient,
    GitLabConfig,
    GitLabIssue,
    GitLabMergeRequest,
    GitLabPipeline,
)


class TestGitLabConfig:
    """Test GitLab configuration"""

    def test_from_env(self):
        """Test config from env"""
        with patch.dict("os.environ", {
            "GITLAB_TOKEN": "test_token",
            "GITLAB_URL": "https://gitlab.example.com",
            "GITLAB_PROJECT_ID": "12345",
        }):
            config = GitLabConfig.from_env()
            assert config.token == "test_token"
            assert config.url == "https://gitlab.example.com"
            assert config.project_id == "12345"

    def test_config_defaults(self):
        """Test config defaults"""
        config = GitLabConfig()
        assert config.token == ""
        assert config.url == "https://gitlab.com"
        assert config.project_id == ""


class TestGitLabClient:
    """Test GitLab client"""

    @pytest.fixture
    def client(self):
        """Create client with test config"""
        config = GitLabConfig(
            token="test_token",
            url="https://gitlab.example.com",
            project_id="12345",
        )
        return GitLabClient(config)

    def test_client_init(self, client):
        """Test client initialization"""
        assert client.config.token == "test_token"
        assert client.config.url == "https://gitlab.example.com"
        assert client.config.project_id == "12345"

    @pytest.mark.asyncio
    async def test_get_project(self, client):
        """Test get project"""
        mock_response = {
            "id": 12345,
            "name": "Test Project",
            "star_count": 10,
            "forks_count": 5,
            "open_issues_count": 3,
            "default_branch": "main",
            "visibility": "private",
            "archived": False,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_project()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_project_stats(self, client):
        """Test get project stats"""
        mock_response = {
            "star_count": 10,
            "forks_count": 5,
            "open_issues_count": 3,
            "default_branch": "main",
            "visibility": "private",
            "archived": False,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_project_stats()
            assert result["stars"] == 10
            assert result["open_issues"] == 3

    @pytest.mark.asyncio
    async def test_create_issue(self, client):
        """Test create issue"""
        mock_response = {
            "id": 10001,
            "iid": 1,
            "title": "Test Issue",
            "description": "Description",
            "state": "opened",
            "labels": ["bug"],
            "assignees": [{"id": 1, "username": "user1"}],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_issue("Test Issue", "Description")
            assert result is not None
            assert result.iid == 1
            assert result.title == "Test Issue"

    @pytest.mark.asyncio
    async def test_get_issue(self, client):
        """Test get issue"""
        mock_response = {
            "id": 10001,
            "iid": 1,
            "title": "Test Issue",
            "description": "Description",
            "state": "opened",
            "labels": ["bug"],
            "assignees": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.get_issue(1)
            assert result is not None
            assert result.iid == 1

    @pytest.mark.asyncio
    async def test_list_issues(self, client):
        """Test list issues"""
        mock_response = [
            {
                "id": 10001,
                "iid": 1,
                "title": "Issue 1",
                "description": "Desc 1",
                "state": "opened",
                "labels": [],
                "assignees": [],
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
            },
        ]

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.list_issues()
            assert len(result) == 1
            assert result[0].iid == 1

    @pytest.mark.asyncio
    async def test_create_merge_request(self, client):
        """Test create merge request"""
        mock_response = {
            "id": 10001,
            "iid": 1,
            "title": "Test MR",
            "description": "MR Description",
            "state": "opened",
            "source_branch": "feature",
            "target_branch": "main",
            "labels": [],
            "draft": False,
            "merged_at": None,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_merge_request(
                "Test MR", "Description", "feature", "main"
            )
            assert result is not None
            assert result.iid == 1
            assert result.source_branch == "feature"

    @pytest.mark.asyncio
    async def test_list_merge_requests(self, client):
        """Test list merge requests"""
        mock_response = [
            {
                "id": 10001,
                "iid": 1,
                "title": "MR 1",
                "description": "Desc",
                "state": "opened",
                "source_branch": "feature",
                "target_branch": "main",
                "labels": [],
                "draft": False,
                "merged_at": None,
            },
        ]

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.list_merge_requests()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_pipeline(self, client):
        """Test create pipeline"""
        mock_response = {
            "id": 10001,
            "status": "pending",
            "ref": "main",
            "sha": "abc123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "web_url": "https://gitlab.com/pipelines/10001",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_pipeline("main")
            assert result is not None
            assert result.id == 10001
            assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_list_pipelines(self, client):
        """Test list pipelines"""
        mock_response = [
            {
                "id": 10001,
                "status": "success",
                "ref": "main",
                "sha": "abc123",
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
                "web_url": "https://gitlab.com/pipelines/10001",
            },
        ]

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.list_pipelines()
            assert len(result) == 1
            assert result[0].status == "success"

    @pytest.mark.asyncio
    async def test_create_release(self, client):
        """Test create release"""
        mock_response = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0",
            "description": "Release description",
            "created_at": "2024-01-01T00:00:00Z",
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.create_release("v1.0.0", "Release description")
            assert result is not None
            assert result.tag_name == "v1.0.0"

    @pytest.mark.asyncio
    async def test_list_releases(self, client):
        """Test list releases"""
        mock_response = [
            {
                "tag_name": "v1.0.0",
                "name": "Release 1.0",
                "description": "Desc",
                "created_at": "2024-01-01",
            },
        ]

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await client.list_releases()
            assert len(result) == 1


class TestGitLabIssue:
    """Test GitLab issue dataclass"""

    def test_issue_creation(self):
        """Test issue creation"""
        issue = GitLabIssue(
            id=10001,
            iid=1,
            title="Test",
            description="Description",
            state="opened",
            labels=["bug"],
        )
        assert issue.iid == 1
        assert issue.title == "Test"
        assert "bug" in issue.labels


class TestGitLabMergeRequest:
    """Test GitLab MR dataclass"""

    def test_mr_creation(self):
        """Test MR creation"""
        mr = GitLabMergeRequest(
            id=10001,
            iid=1,
            title="Test MR",
            description="Desc",
            state="opened",
            source_branch="feature",
            target_branch="main",
        )
        assert mr.iid == 1
        assert mr.source_branch == "feature"


class TestGitLabPipeline:
    """Test GitLab pipeline dataclass"""

    def test_pipeline_creation(self):
        """Test pipeline creation"""
        pipeline = GitLabPipeline(
            id=10001,
            status="running",
            ref="main",
            sha="abc123",
        )
        assert pipeline.id == 10001
        assert pipeline.status == "running"
        assert pipeline.ref == "main"
