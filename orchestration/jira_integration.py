"""
Jira integration
Управление задачами в Jira
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import aiohttp

logger = logging.getLogger("orchestration.jira")


@dataclass
class JiraConfig:
    """Конфигурация Jira"""
    url: str = ""
    user: str = ""
    token: str = ""
    project_key: str = ""

    @classmethod
    def from_env(cls) -> "JiraConfig":
        return cls(
            url=os.getenv("JIRA_URL", ""),
            user=os.getenv("JIRA_USER", ""),
            token=os.getenv("JIRA_TOKEN", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", ""),
        )


@dataclass
class JiraIssue:
    """Jira Issue"""
    key: str
    id: int
    summary: str
    description: str
    status: str
    issue_type: str
    priority: str = "Medium"
    labels: list[str] = field(default_factory=list)
    assignee: str = ""
    created: str = ""
    updated: str = ""


@dataclass
class JiraTransition:
    """Jira Transition"""
    id: str
    name: str
    to_status: str


class JiraClient:
    """
    Jira API клиент с поддержкой:
    - Создание/обновление/удаление задач
    - Transitions (смена статуса)
    - Комментарии
    - Attachments
    - Поиск (JQL)
    """

    def __init__(self, config: JiraConfig = None):
        self.config = config or JiraConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        if self._session is None or self._session.closed:
            auth = aiohttp.BasicAuth(self.config.user, self.config.token)
            self._session = aiohttp.ClientSession(
                auth=auth,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
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
        """Выполнение запроса к Jira API"""
        if not self.config.url or not self.config.token:
            logger.warning("Jira not configured")
            return None

        url = f"{self.config.url}/rest/api/3{path}"
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
            logger.error(f"Jira API error: {e}")
            return None

    # ========================================================================
    # ISSUES
    # ========================================================================

    async def create_issue(
        self,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
        priority: str = "Medium",
        labels: list[str] = None,
        assignee: str = None,
    ) -> JiraIssue | None:
        """Создание задачи"""
        if not self.config.project_key:
            logger.warning("Jira project key not configured")
            return None

        data = {
            "fields": {
                "project": {
                    "key": self.config.project_key,
                },
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description,
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {
                    "name": issue_type,
                },
                "priority": {
                    "name": priority,
                },
            }
        }

        if labels:
            data["fields"]["labels"] = labels
        if assignee:
            data["fields"]["assignee"] = {"name": assignee}

        result = await self._request("POST", "/issue", data=data)

        if result and "key" in result:
            return JiraIssue(
                key=result["key"],
                id=result["id"],
                summary=summary,
                description=description,
                status="Open",
                issue_type=issue_type,
                priority=priority,
                labels=labels or [],
                created=result.get("created", ""),
                updated=result.get("updated", ""),
            )
        return None

    async def get_issue(self, issue_key: str) -> JiraIssue | None:
        """Получение задачи по ключу"""
        result = await self._request("GET", f"/issue/{issue_key}")

        if result and "key" in result:
            fields = result.get("fields", {})
            return JiraIssue(
                key=result["key"],
                id=result["id"],
                summary=fields.get("summary", ""),
                description=self._extract_description(fields.get("description")),
                status=fields.get("status", {}).get("name", ""),
                issue_type=fields.get("issuetype", {}).get("name", ""),
                priority=fields.get("priority", {}).get("name", "Medium"),
                labels=fields.get("labels", []),
                assignee=(fields.get("assignee") or {}).get("displayName", ""),
                created=fields.get("created", ""),
                updated=fields.get("updated", ""),
            )
        return None

    def _extract_description(self, desc: Any) -> str:
        """Извлечение текста из Jira ADF документа"""
        if not desc:
            return ""
        if isinstance(desc, str):
            return desc

        try:
            content = desc.get("content", [])
            if content and isinstance(content, list):
                paras = content[0].get("content", [])
                if paras and isinstance(paras, list):
                    return paras[0].get("text", "")
        except (AttributeError, KeyError, IndexError):
            pass
        return ""

    async def update_issue(
        self,
        issue_key: str,
        summary: str = None,
        description: str = None,
        priority: str = None,
        labels: list[str] = None,
    ) -> bool:
        """Обновление задачи"""
        fields = {}
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description,
                            }
                        ],
                    }
                ],
            }
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = labels

        if not fields:
            return False

        result = await self._request(
            "PUT",
            f"/issue/{issue_key}",
            data={"fields": fields},
        )
        return result is not None

    async def delete_issue(self, issue_key: str) -> bool:
        """Удаление задачи"""
        result = await self._request("DELETE", f"/issue/{issue_key}")
        return result is not None

    # ========================================================================
    # PROJECT
    # ========================================================================

    async def get_project(self) -> dict | None:
        """Получение информации о проекте"""
        if not self.config.project_key:
            return None

        # URL encode the project key
        import urllib.parse
        encoded = urllib.parse.quote(self.config.project_key, safe="")

        return await self._request("GET", f"/project/{encoded}")

    async def get_project_stats(self) -> dict | None:
        """Получение статистики проекта"""
        project = await self.get_project()
        if not project:
            return None

        return {
            "id": project.get("id"),
            "key": project.get("key"),
            "name": project.get("name"),
            "star_count": project.get("starCount", 0),
            "forks_count": project.get("forksCount", 0),
            "open_issues": project.get("issueCount", 0),
            "visibility": project.get("visibility"),
        }

    # ========================================================================
    # ISSUES LIST
    # ========================================================================

    async def list_issues(
        self,
        state: str = "open",
        max_results: int = 50,
    ) -> list[JiraIssue]:
        """Список задач проекта"""
        if not self.config.project_key:
            return []

        jql = f"project = {self.config.project_key}"
        if state == "open":
            jql += " AND statusCategory != Done"
        elif state == "closed":
            jql += " AND statusCategory = Done"

        return await self.search(jql, max_results)

    # ========================================================================
    # TRANSITIONS
    # ========================================================================

    async def get_transitions(self, issue_key: str) -> list[JiraTransition]:
        """Получение доступных переходов"""
        result = await self._request(
            "GET",
            f"/issue/{issue_key}/transitions",
        )

        if not result or "transitions" not in result:
            return []

        return [
            JiraTransition(
                id=t["id"],
                name=t["name"],
                to_status=t.get("to", {}).get("name", ""),
            )
            for t in result["transitions"]
        ]

    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str = None,
        transition_name: str = None,
    ) -> bool:
        """Переход задачи в другой статус"""
        if not transition_id and not transition_name:
            return False

        if transition_name:
            transitions = await self.get_transitions(issue_key)
            for t in transitions:
                if t.name.lower() == transition_name.lower():
                    transition_id = t.id
                    break

        if not transition_id:
            return False

        result = await self._request(
            "POST",
            f"/issue/{issue_key}/transitions",
            data={
                "transition": {
                    "id": transition_id,
                }
            },
        )
        return result is not None

    async def close_issue(self, issue_key: str) -> bool:
        """Закрытие задачи"""
        return await self.transition_issue(issue_key, transition_name="Done")

    async def resolve_issue(self, issue_key: str) -> bool:
        """Resolved задачи"""
        return await self.transition_issue(issue_key, transition_name="Resolved")

    # ========================================================================
    # COMMENTS
    # ========================================================================

    async def add_comment(
        self,
        issue_key: str,
        body: str,
        visibility: str = None,
    ) -> bool:
        """Добавление комментария"""
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": body,
                            }
                        ],
                    }
                ],
            }
        }

        if visibility:
            data["visibility"] = {
                "type": "role",
                "value": visibility,
            }

        result = await self._request(
            "POST",
            f"/issue/{issue_key}/comment",
            data=data,
        )
        return result is not None

    async def get_comments(self, issue_key: str) -> list[dict]:
        """Получение комментариев"""
        result = await self._request(
            "GET",
            f"/issue/{issue_key}/comment",
        )

        if result and "comments" in result:
            return result["comments"]
        return []

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search(
        self,
        jql: str = None,
        max_results: int = 50,
        fields: list[str] = None,
    ) -> list[JiraIssue]:
        """Поиск задач по JQL"""
        if not jql and self.config.project_key:
            jql = f"project = {self.config.project_key} ORDER BY created DESC"

        params = {
            "jql": jql,
            "maxResults": max_results,
        }

        if fields:
            params["fields"] = ",".join(fields)

        result = await self._request("GET", "/search", params=params)

        if not result or "issues" not in result:
            return []

        issues = []
        for item in result["issues"]:
            fields = item.get("fields", {})
            issues.append(JiraIssue(
                key=item["key"],
                id=item["id"],
                summary=fields.get("summary", ""),
                description=self._extract_description(fields.get("description")),
                status=fields.get("status", {}).get("name", ""),
                issue_type=fields.get("issuetype", {}).get("name", ""),
                priority=fields.get("priority", {}).get("name", "Medium"),
                labels=fields.get("labels", []),
                assignee=(fields.get("assignee") or {}).get("displayName", ""),
                created=fields.get("created", ""),
                updated=fields.get("updated", ""),
            ))

        return issues

    async def get_my_issues(
        self,
        status: str = None,
        max_results: int = 20,
    ) -> list[JiraIssue]:
        """Получение своих задач"""
        jql = "assignee = currentUser()"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY updated DESC"

        return await self.search(jql, max_results)

    # ========================================================================
    # ATTACHMENTS
    # ========================================================================

    async def add_attachment(
        self,
        issue_key: str,
        file_path: str,
    ) -> bool:
        """Добавление вложения"""
        if not self.config.url or not self.config.token:
            return False

        url = f"{self.config.url}/rest/api/3/issue/{issue_key}/attachments"

        try:
            session = await self._get_session()
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field(
                    "file",
                    f,
                    filename=os.path.basename(file_path),
                    content_type="application/octet-stream",
                )

                async with session.post(
                    url,
                    data=form,
                    headers={
                        "Authorization": aiohttp.BasicAuth(
                            self.config.user, self.config.token
                        ),
                        "X-Atlassian-Token": "no-check",
                    },
                ) as resp:
                    return resp.status in (200, 201)
        except Exception as e:
            logger.error(f"Jira attachment error: {e}")
            return False

    # ========================================================================
    # UTILS
    # ========================================================================

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton
_jira_client: JiraClient | None = None


def get_jira_client(config: JiraConfig = None) -> JiraClient:
    """Получение Jira клиента"""
    global _jira_client
    if _jira_client is None:
        _jira_client = JiraClient(config)
    return _jira_client


class JiraIntegration:
    """Sync wrapper для Jira"""

    def __init__(self, config: JiraConfig = None):
        self.config = config or JiraConfig.from_env()
        self._client = JiraClient(self.config)

    async def create_issue_async(self, summary: str, description: str = "", **kwargs) -> JiraIssue | None:
        return await self._client.create_issue(summary, description, **kwargs)

    def create_issue(self, summary: str, description: str = "", **kwargs) -> JiraIssue | None:
        """Sync создание задачи"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            return loop.run_until_complete(self.create_issue_async(summary, description, **kwargs))
        except RuntimeError:
            return asyncio.run(self.create_issue_async(summary, description, **kwargs))

    async def search_async(self, jql: str = None, **kwargs) -> list[JiraIssue]:
        return await self._client.search(jql, **kwargs)

    def search(self, jql: str = None, **kwargs) -> list[JiraIssue]:
        """Sync поиск"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            return loop.run_until_complete(self.search_async(jql, **kwargs))
        except RuntimeError:
            return asyncio.run(self.search_async(jql, **kwargs))
