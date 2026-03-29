"""
GitLab API integration
Автоматизация работы с GitLab: issues, MRs, pipelines, releases
"""

import json
import logging
import os
from dataclasses import dataclass, field

import aiohttp

logger = logging.getLogger("orchestration.gitlab")


@dataclass
class GitLabConfig:
    """Конфигурация GitLab"""
    token: str = ""
    url: str = "https://gitlab.com"
    project_id: str = ""  # can be ID or path like "namespace/project"

    @classmethod
    def from_env(cls) -> "GitLabConfig":
        return cls(
            token=os.getenv("GITLAB_TOKEN", ""),
            url=os.getenv("GITLAB_URL", "https://gitlab.com"),
            project_id=os.getenv("GITLAB_PROJECT_ID", ""),
        )


@dataclass
class GitLabIssue:
    """GitLab Issue"""
    id: int
    iid: int
    title: str
    description: str
    state: str
    labels: list[str] = field(default_factory=list)
    assignees: list[dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class GitLabMergeRequest:
    """GitLab Merge Request"""
    id: int
    iid: int
    title: str
    description: str
    state: str
    source_branch: str
    target_branch: str
    labels: list[str] = field(default_factory=list)
    draft: bool = False
    merged: bool = False
    merged_at: str = ""


@dataclass
class GitLabPipeline:
    """GitLab Pipeline"""
    id: int
    status: str
    ref: str
    sha: str
    created_at: str = ""
    updated_at: str = ""
    web_url: str = ""


@dataclass
class GitLabRelease:
    """GitLab Release"""
    tag_name: str
    name: str
    description: str
    created_at: str = ""


class GitLabClient:
    """
    GitLab API клиент с поддержкой:
    - Issues (создание, обновление, закрытие)
    - Merge Requests
    - Pipelines
    - Releases
    - Projects
    """

    def __init__(self, config: GitLabConfig = None):
        self.config = config or GitLabConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "PRIVATE-TOKEN": self.config.token,
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def _request(
        self,
        method: str,
        path: str,
        data: dict = None,
        params: dict = None,
    ) -> dict | list | None:
        """Выполнение запроса к GitLab API"""
        if not self.config.token:
            logger.warning("GitLab token not configured")
            return None

        url = f"{self.config.url}/api/v4{path}"
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
            logger.error(f"GitLab API error: {e}")
            return None

    def _project_id(self) -> str:
        """Получение ID проекта"""
        return str(self.config.project_id)

    # ========================================================================
    # PROJECTS
    # ========================================================================

    async def get_project(self) -> dict | None:
        """Получение информации о проекте"""
        project_id = self._project_id()
        if not project_id:
            return None

        # URL encode the project path
        import urllib.parse
        encoded = urllib.parse.quote(project_id, safe="")

        return await self._request(
            "GET",
            f"/projects/{encoded}",
        )

    async def get_project_stats(self) -> dict | None:
        """Получение статистики проекта"""
        project = await self.get_project()
        if not project:
            return None

        return {
            "stars": project.get("star_count", 0),
            "forks": project.get("forks_count", 0),
            "open_issues": project.get("open_issues_count", 0),
            "default_branch": project.get("default_branch"),
            "visibility": project.get("visibility"),
            "archived": project.get("archived", False),
        }

    # ========================================================================
    # ISSUES
    # ========================================================================

    async def create_issue(
        self,
        title: str,
        description: str = "",
        labels: list[str] = None,
        assignee_ids: list[int] = None,
    ) -> GitLabIssue | None:
        """Создание issue"""
        project_id = self._project_id()
        if not project_id:
            return None

        data = await self._request(
            "POST",
            f"/projects/{project_id}/issues",
            data={
                "title": title,
                "description": description,
                "labels": ",".join(labels) if labels else "",
                "assignee_ids": assignee_ids or [],
            },
        )

        if data and "id" in data:
            return GitLabIssue(
                id=data["id"],
                iid=data["iid"],
                title=data["title"],
                description=data.get("description", ""),
                state=data.get("state", "opened"),
                labels=data.get("labels", []),
                assignees=data.get("assignees", []),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            )
        return None

    async def get_issue(self, issue_iid: int) -> GitLabIssue | None:
        """Получение issue по IID"""
        project_id = self._project_id()
        if not project_id:
            return None

        data = await self._request(
            "GET",
            f"/projects/{project_id}/issues/{issue_iid}",
        )

        if data and "id" in data:
            return GitLabIssue(
                id=data["id"],
                iid=data["iid"],
                title=data["title"],
                description=data.get("description", ""),
                state=data.get("state", "opened"),
                labels=data.get("labels", []),
                assignees=data.get("assignees", []),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
            )
        return None

    async def list_issues(
        self,
        state: str = "opened",
        labels: list[str] = None,
        per_page: int = 30,
    ) -> list[GitLabIssue]:
        """Список issues"""
        project_id = self._project_id()
        if not project_id:
            return []

        params = {"state": state, "per_page": per_page}
        if labels:
            params["labels"] = ",".join(labels)

        data = await self._request(
            "GET",
            f"/projects/{project_id}/issues",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitLabIssue(
                id=item["id"],
                iid=item["iid"],
                title=item["title"],
                description=item.get("description", ""),
                state=item.get("state", "opened"),
                labels=item.get("labels", []),
                assignees=item.get("assignees", []),
                created_at=item.get("created_at", ""),
                updated_at=item.get("updated_at", ""),
            )
            for item in data
        ]

    async def close_issue(self, issue_iid: int) -> bool:
        """Закрытие issue"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "PUT",
            f"/projects/{project_id}/issues/{issue_iid}",
            data={"state_event": "close"},
        )
        return result is not None

    async def add_issue_note(self, issue_iid: int, body: str) -> bool:
        """Добавление комментария к issue"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "POST",
            f"/projects/{project_id}/issues/{issue_iid}/notes",
            data={"body": body},
        )
        return result is not None

    # ========================================================================
    # MERGE REQUESTS
    # ========================================================================

    async def create_merge_request(
        self,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str = "main",
        labels: list[str] = None,
        draft: bool = False,
    ) -> GitLabMergeRequest | None:
        """Создание Merge Request"""
        project_id = self._project_id()
        if not project_id:
            return None

        data = await self._request(
            "POST",
            f"/projects/{project_id}/merge_requests",
            data={
                "title": title,
                "description": description,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "labels": ",".join(labels) if labels else "",
                "draft": draft,
            },
        )

        if data and "id" in data:
            return GitLabMergeRequest(
                id=data["id"],
                iid=data["iid"],
                title=data["title"],
                description=data.get("description", ""),
                state=data.get("state", "opened"),
                source_branch=data.get("source_branch", ""),
                target_branch=data.get("target_branch", ""),
                labels=data.get("labels", []),
                draft=data.get("draft", False),
                merged=data.get("merged_at") is not None,
                merged_at=data.get("merged_at", ""),
            )
        return None

    async def list_merge_requests(
        self,
        state: str = "opened",
        per_page: int = 30,
    ) -> list[GitLabMergeRequest]:
        """Список Merge Requests"""
        project_id = self._project_id()
        if not project_id:
            return []

        params = {"state": state, "per_page": per_page}

        data = await self._request(
            "GET",
            f"/projects/{project_id}/merge_requests",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitLabMergeRequest(
                id=item["id"],
                iid=item["iid"],
                title=item["title"],
                description=item.get("description", ""),
                state=item.get("state", "opened"),
                source_branch=item.get("source_branch", ""),
                target_branch=item.get("target_branch", ""),
                labels=item.get("labels", []),
                draft=item.get("draft", False),
                merged=item.get("merged_at") is not None,
                merged_at=item.get("merged_at", ""),
            )
            for item in data
        ]

    async def accept_merge_request(
        self,
        mr_iid: int,
        should_remove_source_branch: bool = True,
    ) -> bool:
        """Accept Merge Request"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "PUT",
            f"/projects/{project_id}/merge_requests/{mr_iid}/merge",
            data={
                "should_remove_source_branch": should_remove_source_branch,
                "merge_when_pipeline_succeeds": False,
            },
        )
        return result and result.get("state") == "merged"

    # ========================================================================
    # PIPELINES
    # ========================================================================

    async def create_pipeline(
        self,
        ref: str = "main",
        variables: dict = None,
    ) -> GitLabPipeline | None:
        """Создание pipeline"""
        project_id = self._project_id()
        if not project_id:
            return None

        data = await self._request(
            "POST",
            f"/projects/{project_id}/pipeline",
            data={
                "ref": ref,
                "variables": [
                    {"key": k, "value": str(v)}
                    for k, v in (variables or {}).items()
                ],
            },
        )

        if data and "id" in data:
            return GitLabPipeline(
                id=data["id"],
                status=data.get("status", ""),
                ref=data.get("ref", ""),
                sha=data.get("sha", ""),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
                web_url=data.get("web_url", ""),
            )
        return None

    async def get_pipeline(self, pipeline_id: int) -> GitLabPipeline | None:
        """Получение pipeline по ID"""
        project_id = self._project_id()
        if not project_id:
            return None

        data = await self._request(
            "GET",
            f"/projects/{project_id}/pipelines/{pipeline_id}",
        )

        if data and "id" in data:
            return GitLabPipeline(
                id=data["id"],
                status=data.get("status", ""),
                ref=data.get("ref", ""),
                sha=data.get("sha", ""),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
                web_url=data.get("web_url", ""),
            )
        return None

    async def list_pipelines(
        self,
        ref: str = None,
        status: str = None,
        per_page: int = 30,
    ) -> list[GitLabPipeline]:
        """Список pipelines"""
        project_id = self._project_id()
        if not project_id:
            return []

        params = {"per_page": per_page}
        if ref:
            params["ref"] = ref
        if status:
            params["status"] = status

        data = await self._request(
            "GET",
            f"/projects/{project_id}/pipelines",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitLabPipeline(
                id=item["id"],
                status=item.get("status", ""),
                ref=item.get("ref", ""),
                sha=item.get("sha", ""),
                created_at=item.get("created_at", ""),
                updated_at=item.get("updated_at", ""),
                web_url=item.get("web_url", ""),
            )
            for item in data
        ]

    async def cancel_pipeline(self, pipeline_id: int) -> bool:
        """Отмена pipeline"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "POST",
            f"/projects/{project_id}/pipelines/{pipeline_id}/cancel",
        )
        return result is not None

    async def retry_pipeline(self, pipeline_id: int) -> bool:
        """Перезапуск pipeline"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "POST",
            f"/projects/{project_id}/pipelines/{pipeline_id}/retry",
        )
        return result is not None

    # ========================================================================
    # RELEASES
    # ========================================================================

    async def create_release(
        self,
        tag_name: str,
        description: str,
        name: str = None,
    ) -> GitLabRelease | None:
        """Создание release"""
        project_id = self._project_id()
        if not project_id:
            return None

        data = await self._request(
            "POST",
            f"/projects/{project_id}/releases",
            data={
                "tag_name": tag_name,
                "name": name or tag_name,
                "description": description,
            },
        )

        if data and "tag_name" in data:
            return GitLabRelease(
                tag_name=data.get("tag_name", ""),
                name=data.get("name", ""),
                description=data.get("description", ""),
                created_at=data.get("created_at", ""),
            )
        return None

    async def list_releases(self, per_page: int = 30) -> list[GitLabRelease]:
        """Список releases"""
        project_id = self._project_id()
        if not project_id:
            return []

        params = {"per_page": per_page}
        data = await self._request(
            "GET",
            f"/projects/{project_id}/releases",
            params=params,
        )

        if not isinstance(data, list):
            return []

        return [
            GitLabRelease(
                tag_name=item.get("tag_name", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                created_at=item.get("created_at", ""),
            )
            for item in data
        ]

    # ========================================================================
    # JOBS (for CI/CD)
    # ========================================================================

    async def get_job(self, job_id: int) -> dict | None:
        """Получение job по ID"""
        project_id = self._project_id()
        if not project_id:
            return None

        return await self._request(
            "GET",
            f"/projects/{project_id}/jobs/{job_id}",
        )

    async def cancel_job(self, job_id: int) -> bool:
        """Отмена job"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "POST",
            f"/projects/{project_id}/jobs/{job_id}/cancel",
        )
        return result is not None

    async def retry_job(self, job_id: int) -> bool:
        """Перезапуск job"""
        project_id = self._project_id()
        if not project_id:
            return False

        result = await self._request(
            "POST",
            f"/projects/{project_id}/jobs/{job_id}/retry",
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
_gitlab_client: GitLabClient | None = None


def get_gitlab_client(config: GitLabConfig = None) -> GitLabClient:
    """Получение GitLab клиента"""
    global _gitlab_client
    if _gitlab_client is None:
        _gitlab_client = GitLabClient(config)
    return _gitlab_client


class GitLabIntegration:
    """Sync wrapper для GitLab API"""

    def __init__(self, config: GitLabConfig = None):
        self.config = config or GitLabConfig.from_env()
        self._client = GitLabClient(self.config)

    async def create_issue_async(self, title: str, description: str = "", **kwargs) -> GitLabIssue | None:
        return await self._client.create_issue(title, description, **kwargs)

    def create_issue(self, title: str, description: str = "", **kwargs) -> GitLabIssue | None:
        """Sync создание issue"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            return loop.run_until_complete(self.create_issue_async(title, description, **kwargs))
        except RuntimeError:
            return asyncio.run(self.create_issue_async(title, description, **kwargs))

    async def get_project_stats_async(self) -> dict | None:
        return await self._client.get_project_stats()

    def get_project_stats(self) -> dict | None:
        """Sync получение статистики"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            return loop.run_until_complete(self.get_project_stats_async())
        except RuntimeError:
            return asyncio.run(self.get_project_stats_async())
