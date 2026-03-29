"""
Webhook handlers for external integrations
Обработчики вебхуков для внешних интеграций
"""

import asyncio
import hashlib
import hmac
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp

logger = logging.getLogger("orchestration.webhooks")


@dataclass
class WebhookEvent:
    """Событие вебхука"""
    event_type: str
    source: str
    payload: dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    signature: str = ""


@dataclass
class WebhookConfig:
    """Конфигурация вебхука"""
    url: str = ""
    secret: str = ""
    events: list[str] = field(default_factory=list)
    enabled: bool = True
    retry_count: int = 3
    timeout: float = 30.0


class WebhookHandler:
    """
    Обработчик вебхуков с поддержкой:
    - Подпись и верификация
    - Retry логика
    - Событийная модель
    - Multiple providers
    """

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._configs: dict[str, WebhookConfig] = {}

    def register_handler(self, event_type: str, handler: Callable):
        """Регистрация обработчика события"""
        self._handlers[event_type] = handler
        logger.info(f"Registered webhook handler: {event_type}")

    def register_config(self, name: str, config: WebhookConfig):
        """Регистрация конфигурации"""
        self._configs[name] = config

    async def handle_event(self, event: WebhookEvent) -> Any:
        """Обработка события"""
        handler = self._handlers.get(event.event_type)
        if not handler:
            logger.warning(f"No handler for event: {event.event_type}")
            return None

        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(event)
            return handler(event)
        except Exception as e:
            logger.error(f"Handler error for {event.event_type}: {e}")
            return None

    def verify_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """Верификация подписи"""
        if not secret:
            return True

        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)


class WebhookSender:
    """
    Отправитель вебхуков
    """

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def send(
        self,
        url: str,
        payload: dict,
        secret: str = None,
        timeout: float = 30.0,
        retry_count: int = 3,
    ) -> bool:
        """Отправка вебхука"""
        # Добавляем подпись если есть secret
        headers = {"Content-Type": "application/json"}
        if secret:
            import json
            payload_str = json.dumps(payload)
            signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature

        session = await self._get_session()

        for attempt in range(retry_count):
            try:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status < 400:
                        logger.info(f"Webhook sent successfully to {url}")
                        return True
                    else:
                        logger.warning(f"Webhook failed: {resp.status}")

            except aiohttp.ClientError as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1 * (attempt + 1))

        return False

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


# Provider-specific handlers

class GitHubWebhookHandler(WebhookHandler):
    """Обработчик GitHub вебхуков"""

    def __init__(self):
        super().__init__()
        self.register_handler("push", self._handle_push)
        self.register_handler("pull_request", self._handle_pull_request)
        self.register_handler("issues", self._handle_issues)
        self.register_handler("release", self._handle_release)

    async def _handle_push(self, event: WebhookEvent) -> dict:
        """Обработка push события"""
        payload = event.payload
        commits = payload.get("commits", [])
        repo = payload.get("repository", {}).get("full_name", "")

        logger.info(f"Push to {repo}: {len(commits)} commits")
        return {"action": "push", "commits": len(commits), "repo": repo}

    async def _handle_pull_request(self, event: WebhookEvent) -> dict:
        """Обработка PR события"""
        payload = event.payload
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        number = pr.get("number", 0)

        logger.info(f"PR #{number}: {action}")
        return {"event": "pull_request", "pr_number": number, "action": action}

    async def _handle_issues(self, event: WebhookEvent) -> dict:
        """Обработка issues"""
        payload = event.payload
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        number = issue.get("number", 0)

        logger.info(f"Issue #{number}: {action}")
        return {"event": "issues", "issue_number": number, "action": action}

    async def _handle_release(self, event: WebhookEvent) -> dict:
        """Обработка release"""
        payload = event.payload
        action = payload.get("action", "")
        release = payload.get("release", {})
        tag = release.get("tag_name", "")

        logger.info(f"Release: {action} {tag}")
        return {"event": "release", "tag": tag, "action": action}


class GitLabWebhookHandler(WebhookHandler):
    """Обработчик GitLab вебхуков"""

    def __init__(self):
        super().__init__()
        self.register_handler("push", self._handle_push)
        self.register_handler("merge_request", self._handle_merge_request)
        self.register_handler("tag_push", self._handle_tag_push)

    async def _handle_push(self, event: WebhookEvent) -> dict:
        """Обработка push"""
        payload = event.payload
        commits = payload.get("commits", [])
        project = payload.get("project", {}).get("path_with_namespace", "")

        logger.info(f"Push to {project}: {len(commits)} commits")
        return {"action": "push", "commits": len(commits), "project": project}

    async def _handle_merge_request(self, event: WebhookEvent) -> dict:
        """Обработка MR"""
        payload = event.payload
        action = payload.get("object_attributes", {}).get("action", "")
        iid = payload.get("object_attributes", {}).get("iid", 0)

        logger.info(f"MR !{iid}: {action}")
        return {"event": "merge_request", "mr_iid": iid, "action": action}

    async def _handle_tag_push(self, event: WebhookEvent) -> dict:
        """Обработка tag push"""
        payload = event.payload
        tag = payload.get("ref", "").replace("refs/tags/", "")

        logger.info(f"Tag pushed: {tag}")
        return {"action": "tag_push", "tag": tag}


class SlackWebhookHandler(WebhookHandler):
    """Обработчик Slack вебхуков"""

    def __init__(self):
        super().__init__()
        self.register_handler("url_verification", self._handle_url_verification)
        self.register_handler("event_callback", self._handle_event_callback)

    async def _handle_url_verification(self, event: WebhookEvent) -> dict:
        """Обработка URL verification"""
        payload = event.payload
        challenge = payload.get("challenge", "")
        return {"challenge": challenge}

    async def _handle_event_callback(self, event: WebhookEvent) -> dict:
        """Обработка event callback"""
        payload = event.payload
        event_type = payload.get("event", {}).get("type", "")
        logger.info(f"Slack event: {event_type}")
        return {"action": "event_callback", "event_type": event_type}


# Singleton handlers
_github_handler: GitHubWebhookHandler | None = None
_gitlab_handler: GitLabWebhookHandler | None = None
_slack_handler: SlackWebhookHandler | None = None


def get_github_handler() -> GitHubWebhookHandler:
    """Получение GitHub обработчика"""
    global _github_handler
    if _github_handler is None:
        _github_handler = GitHubWebhookHandler()
    return _github_handler


def get_gitlab_handler() -> GitLabWebhookHandler:
    """Получение GitLab обработчика"""
    global _gitlab_handler
    if _gitlab_handler is None:
        _gitlab_handler = GitLabWebhookHandler()
    return _gitlab_handler


def get_slack_handler() -> SlackWebhookHandler:
    """Получение Slack обработчика"""
    global _slack_handler
    if _slack_handler is None:
        _slack_handler = SlackWebhookHandler()
    return _slack_handler
