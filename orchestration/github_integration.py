"""
GitHub API integration
Автоматизация работы с GitHub: issues, PRs, releases, workflows
"""

import json
import logging
import os
from dataclasses import dataclass, field

import aiohttp

logger = logging.getLogger("orchestration.github")


@dataclass
class GitHubConfig:
    """Конфигурация GitHub"""
    token: str = ""
    owner: str = ""
    repo: str = ""
    api_url: str = "https://api.github.com"

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        return cls(
            token=os.getenv("GITHUB_TOKEN", ""),
            owner=os.getenv("GITHUB_OWNER", ""),
            repo=os.getenv("GITHUB_REPO", ""),
            api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
        )


@dataclass
class GitHubIssue:
    """GitHub Issue"""
    number: int
    title: str
    body: str
    state: str
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class GitHubPullRequest:
    """GitHub Pull Request"""
    number: int
    title: str
    body: str
    state: str
    head: str
    base: str
    labels: list[str] = field(default_factory=list)
    draft: bool = False
    merged: bool = False


@dataclass
class GitHubRelease:
    """GitHub Release"""
    id: int
    tag_name: str
    name: str
    body: str
    draft: bool = False
    prerelease: bool = False
    published_at: str = ""


class GitHubClient:
    """
    GitHub API клиент с поддержкой:
    - Issues (создание, обновление, закрытие)
    - Pull Requests
    - Releases
    - Workflows (запуск, статус)
    - Repository info
    """

    def __init__(self, config: GitHubConfig = None):
        self.config = config or GitHubConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

        # Fallback на локальный git для данных
        self._git_integration = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
            )
        return self._session

    def _headers(self) -> dict:
        """Base headers"""
        return {
            "Authorization": f"Bearer {self.config.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(
        self,
        method: str,
        path: str,
        data: dict = None,
        params: dict = None,
    ) -> dict | list | None:
        """Выполнение запроса к GitHub API"""
        if not self.config.token:
            logger.warning("GitHub token not configured")
            return None

        url = f"{self.config.api_url}{path}"
        session = await self._get_session()

        try:
            async with session.request(
                method,
                url,
                json=data,
                params=params,
            ) as resp:
                if resp.status == 204:
                    return None

                content = await resp.text()
                if not content:
                    return None

                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Non-JSON response: {content[:200]}")
                    return {"raw": content}

        except aiohttp.ClientError as e:
            logger.error(f"GitHub API error: {e}")
            return None

    # ========================================================================
    # REPOSITORY
    # ========================================================================

    async def get_repo_info(self) -> dict | None:
        """Получение информации о репозитории"""
        if not self.config.owner or not self.config.repo:
            return None

        return await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}",
        )

    async def get_repo_stats(self) -> dict | None:
        """Получение статистики репозитория"""
        info = await self.get_repo_info()
        if not info:
            return None

        return {
            "stars": info.get("stargazers_count", 0),
            "forks": info.get("forks_count", 0),
            "watchers": info.get("watchers_count", 0),
            "open_issues": info.get("open_issues_count", 0),
            "language": info.get("language"),
            "size": info.get("size"),
            "license": info.get("license", {}).get("name"),
        }

    # ========================================================================
    # ISSUES
    # ========================================================================

    async def create_issue(
        self,
        title: str,
        body: str = "",
        labels: list[str] = None,
        assignees: list[str] = None,
    ) -> GitHubIssue | None:
        """Создание issue"""
        if not self.config.owner or not self.config.repo:
            return None

        data = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/issues",
            data={
                "title": title,
                "body": body,
                "labels": labels or [],
                "assignees": assignees or [],
            },
        )

        if data and "number" in data:
            return GitHubIssue(
                number=data["number"],
                title=data["title"],
                body=data.get("body", ""),
                state=data.get("state", "open"),
                labels=[label.get("name") for label in data.get("labels", [])],
                assignees=[a.get("login") for a in data.get("assignees", [])],
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            )
        return None

    async def get_issue(self, number: int) -> GitHubIssue | None:
        """Получение issue по номеру"""
        if not self.config.owner or not self.config.repo:
            return None

        data = await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/issues/{number}",
        )

        if data and "number" in data:
            return GitHubIssue(
                number=data["number"],
                title=data["title"],
                body=data.get("body", ""),
                state=data.get("state", "open"),
                labels=[label.get("name") for label in data.get("labels", [])],
                assignees=[a.get("login") for a in data.get("assignees", [])],
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            )
        return None

    async def list_issues(
        self,
        state: str = "open",
        labels: list[str] = None,
        per_page: int = 30,
    ) -> list[GitHubIssue]:
        """Список issues"""
        if not self.config.owner or not self.config.repo:
            return []

        params = {"state": state, "per_page": per_page}
        if labels:
            params["labels"] = ",".join(labels)

        data = await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/issues",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitHubIssue(
                number=item["number"],
                title=item["title"],
                body=item.get("body", ""),
                state=item.get("state", "open"),
                labels=[label.get("name") for label in item.get("labels", [])],
                assignees=[a.get("login") for a in item.get("assignees", [])],
                created_at=item.get("created_at", ""),
                updated_at=item.get("updated_at", ""),
            )
            for item in data
            if "pull_request" not in item  # Filter out PRs
        ]

    async def close_issue(self, number: int) -> bool:
        """Закрытие issue"""
        if not self.config.owner or not self.config.repo:
            return False

        result = await self._request(
            "PATCH",
            f"/repos/{self.config.owner}/{self.config.repo}/issues/{number}",
            data={"state": "closed"},
        )
        return result is not None

    async def add_issue_comment(self, number: int, body: str) -> bool:
        """Добавление комментария к issue"""
        if not self.config.owner or not self.config.repo:
            return False

        result = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/issues/{number}/comments",
            data={"body": body},
        )
        return result is not None

    # ========================================================================
    # PULL REQUESTS
    # ========================================================================

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False,
    ) -> GitHubPullRequest | None:
        """Создание Pull Request"""
        if not self.config.owner or not self.config.repo:
            return None

        data = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/pulls",
            data={
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft,
            },
        )

        if data and "number" in data:
            return GitHubPullRequest(
                number=data["number"],
                title=data["title"],
                body=data.get("body", ""),
                state=data.get("state", "open"),
                head=data.get("head", {}).get("ref", ""),
                base=data.get("base", {}).get("ref", ""),
                labels=[label.get("name") for label in data.get("labels", [])],
                draft=data.get("draft", False),
                merged=data.get("merged", False),
            )
        return None

    async def list_pull_requests(
        self,
        state: str = "open",
        per_page: int = 30,
    ) -> list[GitHubPullRequest]:
        """Список Pull Requests"""
        if not self.config.owner or not self.config.repo:
            return []

        params = {"state": state, "per_page": per_page}

        data = await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/pulls",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitHubPullRequest(
                number=item["number"],
                title=item["title"],
                body=item.get("body", ""),
                state=item.get("state", "open"),
                head=item.get("head", {}).get("ref", ""),
                base=item.get("base", {}).get("ref", ""),
                labels=[label.get("name") for label in item.get("labels", [])],
                draft=item.get("draft", False),
                merged=item.get("merged", False),
            )
            for item in data
        ]

    async def merge_pull_request(self, number: int, message: str = "") -> bool:
        """Merge Pull Request"""
        if not self.config.owner or not self.config.repo:
            return False

        result = await self._request(
            "PUT",
            f"/repos/{self.config.owner}/{self.config.repo}/pulls/{number}/merge",
            data={"merge_method": "squash", "commit_message": message},
        )
        return result and result.get("merged", False)

    # ========================================================================
    # RELEASES
    # ========================================================================

    async def create_release(
        self,
        tag_name: str,
        name: str = "",
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
    ) -> GitHubRelease | None:
        """Создание release"""
        if not self.config.owner or not self.config.repo:
            return None

        data = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/releases",
            data={
                "tag_name": tag_name,
                "name": name or tag_name,
                "body": body,
                "draft": draft,
                "prerelease": prerelease,
            },
        )

        if data and "id" in data:
            return GitHubRelease(
                id=data["id"],
                tag_name=data.get("tag_name", ""),
                name=data.get("name", ""),
                body=data.get("body", ""),
                draft=data.get("draft", False),
                prerelease=data.get("prerelease", False),
                published_at=data.get("published_at", ""),
            )
        return None

    async def list_releases(self, per_page: int = 30) -> list[GitHubRelease]:
        """Список releases"""
        if not self.config.owner or not self.config.repo:
            return []

        params = {"per_page": per_page}
        data = await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/releases",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitHubRelease(
                id=item["id"],
                tag_name=item.get("tag_name", ""),
                name=item.get("name", ""),
                body=item.get("body", ""),
                draft=item.get("draft", False),
                prerelease=item.get("prerelease", False),
                published_at=item.get("published_at", ""),
            )
            for item in data
        ]

    # ========================================================================
    # WORKFLOWS
    # ========================================================================

    async def list_workflows(self) -> list[dict]:
        """Список workflows"""
        if not self.config.owner or not self.config.repo:
            return []

        data = await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/actions/workflows",
        )

        if data and "workflows" in data:
            return data["workflows"]
        return []

    async def run_workflow(
        self,
        workflow_id: str,
        ref: str = "main",
        inputs: dict = None,
    ) -> bool:
        """Запуск workflow"""
        if not self.config.owner or not self.config.repo:
            return False

        result = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/actions/workflows/{workflow_id}/dispatches",
            data={
                "ref": ref,
                "inputs": inputs or {},
            },
        )
        return result is not None

    async def get_workflow_runs(
        self,
        workflow_id: str = None,
        per_page: int = 10,
    ) -> list[dict]:
        """Получение запусков workflow"""
        if not self.config.owner or not self.config.repo:
            return []

        path = f"/repos/{self.config.owner}/{self.config.repo}/actions/workflows"
        if workflow_id:
            path = f"{path}/{workflow_id}/runs"

        params = {"per_page": per_page}
        data = await self._request("GET", path, params=params)

        if data and "workflow_runs" in data:
            return data["workflow_runs"]
        return []

    # ========================================================================
    # ACTIONS
    # ========================================================================

    async def get_workflow_run_status(self, run_id: int) -> dict | None:
        """Получение статуса запуска workflow"""
        if not self.config.owner or not self.config.repo:
            return None

        return await self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/actions/runs/{run_id}",
        )

    async def cancel_workflow_run(self, run_id: int) -> bool:
        """Отмена запуска workflow"""
        if not self.config.owner or not self.config.repo:
            return False

        result = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/actions/runs/{run_id}/cancel",
        )
        return result is not None

    async def rerun_workflow(self, run_id: int) -> bool:
        """Перезапуск workflow"""
        if not self.config.owner or not self.config.repo:
            return False

        result = await self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/actions/runs/{run_id}/rerun",
        )
        return result is not None

    # ========================================================================
    # UTILS
    # ========================================================================

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton
_github_client: GitHubClient | None = None


def get_github_client(config: GitHubConfig = None) -> GitHubClient:
    """Получение GitHub клиента"""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient(config)
    return _github_client


# Sync wrapper для обратной совместимости
class GitHubIntegration:
    """Sync wrapper для GitHub API"""

    def __init__(self, config: GitHubConfig = None):
        self.config = config or GitHubConfig.from_env()
        self._client = GitHubClient(self.config)

    async def create_issue_async(self, title: str, body: str = "", **kwargs) -> GitHubIssue | None:
        return await self._client.create_issue(title, body, **kwargs)

    def create_issue(self, title: str, body: str = "", **kwargs) -> GitHubIssue | None:
        """Sync создание issue"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Если уже в async контексте - нельзя
                logger.warning("Cannot use sync method in async context")
                return None
            return loop.run_until_complete(self.create_issue_async(title, body, **kwargs))
        except RuntimeError:
            # Нет event loop
            return asyncio.run(self.create_issue_async(title, body, **kwargs))

    async def get_repo_stats_async(self) -> dict | None:
        return await self._client.get_repo_stats()

    def get_repo_stats(self) -> dict | None:
        """Sync получение статистики"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            return loop.run_until_complete(self.get_repo_stats_async())
        except RuntimeError:
            return asyncio.run(self.get_repo_stats_async())
