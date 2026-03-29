"""
Slack integration
Отправка уведомлений в Slack каналы
"""

import logging
import os
from dataclasses import dataclass, field

import aiohttp

logger = logging.getLogger("orchestration.slack")


@dataclass
class SlackConfig:
    """Конфигурация Slack"""
    webhook_url: str = ""
    bot_token: str = ""
    channel: str = ""
    username: str = "AI Pipeline Bot"
    icon_emoji: str = ":robot_face:"

    @classmethod
    def from_env(cls) -> "SlackConfig":
        return cls(
            webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
            channel=os.getenv("SLACK_CHANNEL", ""),
            username=os.getenv("SLACK_USERNAME", "AI Pipeline Bot"),
            icon_emoji=os.getenv("SLACK_ICON", ":robot_face:"),
        )


@dataclass
class SlackMessage:
    """Slack сообщение"""
    channel: str = ""
    text: str = ""
    blocks: list[dict] = field(default_factory=list)
    attachments: list[dict] = field(default_factory=list)


class SlackClient:
    """
    Slack клиент с поддержкой:
    - Incoming Webhooks
    - Bot API (chat.postMessage, etc.)
    - Блоки и attachments
    - Threading
    """

    def __init__(self, config: SlackConfig = None):
        self.config = config or SlackConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # ========================================================================
    # INCOMING WEBHOOKS
    # ========================================================================

    async def send_webhook(
        self,
        text: str = "",
        blocks: list[dict] = None,
        attachments: list[dict] = None,
    ) -> bool:
        """Отправка через incoming webhook"""
        if not self.config.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        session = await self._get_session()

        payload = {}
        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks
        if attachments:
            payload["attachments"] = attachments

        try:
            async with session.post(
                self.config.webhook_url,
                json=payload,
            ) as resp:
                return resp.status == 200
        except aiohttp.ClientError as e:
            logger.error(f"Slack webhook error: {e}")
            return False

    # ========================================================================
    # BOT API
    # ========================================================================

    async def _api_request(
        self,
        method: str,
        data: dict = None,
    ) -> dict | None:
        """Выполнение запроса к Slack API"""
        if not self.config.bot_token:
            logger.warning("Slack bot token not configured")
            return None

        url = f"https://slack.com/api/{method}"
        session = await self._get_session()

        try:
            async with session.post(
                url,
                json=data,
                headers={
                    "Authorization": f"Bearer {self.config.bot_token}",
                    "Content-Type": "application/json",
                },
            ) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result
                else:
                    logger.warning(f"Slack API error: {result.get('error')}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Slack API error: {e}")
            return None

    async def chat_post_message(
        self,
        channel: str,
        text: str = "",
        blocks: list[dict] = None,
        attachments: list[dict] = None,
        thread_ts: str = None,
        username: str = None,
        icon_emoji: str = None,
    ) -> dict | None:
        """Отправка сообщения"""
        data = {
            "channel": channel,
            "text": text or "",
        }

        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        if thread_ts:
            data["thread_ts"] = thread_ts
        if username:
            data["username"] = username
        if icon_emoji:
            data["icon_emoji"] = icon_emoji

        return await self._api_request("chat.postMessage", data)

    async def chat_update(
        self,
        channel: str,
        ts: str,
        text: str = "",
        blocks: list[dict] = None,
    ) -> dict | None:
        """Обновление сообщения"""
        data = {
            "channel": channel,
            "ts": ts,
            "text": text or "",
        }

        if blocks:
            data["blocks"] = blocks

        return await self._api_request("chat.update", data)

    async def chat_delete(
        self,
        channel: str,
        ts: str,
    ) -> dict | None:
        """Удаление сообщения"""
        return await self._api_request("chat.delete", {
            "channel": channel,
            "ts": ts,
        })

    # ========================================================================
    # BUILDER METHODS
    # ========================================================================

    def build_section_text(self, text: str, emoji: bool = True) -> dict:
        """Создание section с текстом"""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        }

    def build_section_fields(self, fields: list[str]) -> dict:
        """Создание section с полями"""
        return {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f,
                }
                for f in fields
            ],
        }

    def build_divider(self) -> dict:
        """Создание divider"""
        return {"type": "divider"}

    def build_actions(self, elements: list[dict]) -> dict:
        """Создание actions блока"""
        return {
            "type": "actions",
            "elements": elements,
        }

    def build_button(
        self,
        text: str,
        action_id: str,
        url: str = None,
        style: str = None,
        emoji: bool = True,
    ) -> dict:
        """Создание кнопки"""
        button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": emoji,
            },
            "action_id": action_id,
        }

        if url:
            button["url"] = url
        if style:
            button["style"] = style

        return button

    def build_header(self, text: str) -> dict:
        """Создание header"""
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True,
            },
        }

    def build_context(self, elements: list[dict]) -> dict:
        """Создание context блока"""
        return {
            "type": "context",
            "elements": elements,
        }

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    async def notify_pipeline_start(
        self,
        project: str,
        phase: str,
        channel: str = None,
    ) -> bool:
        """Уведомление о начале фазы pipeline"""
        blocks = [
            self.build_header(":hourglass_flowing_sand: Pipeline Started"),
            self.build_section_text(f"*Project:* {project}\n*Phase:* {phase}"),
            self.build_divider(),
        ]

        return await self.send(
            channel=channel,
            text=f"Pipeline started for {project}, phase: {phase}",
            blocks=blocks,
        )

    async def notify_pipeline_complete(
        self,
        project: str,
        duration: float,
        files_generated: int,
        errors: int = 0,
        channel: str = None,
    ) -> bool:
        """Уведомление о завершении pipeline"""
        status_emoji = ":white_check_mark:" if errors == 0 else ":warning:"
        status_text = "Completed" if errors == 0 else f"Completed with {errors} errors"

        blocks = [
            self.build_header(f"{status_emoji} Pipeline {status_text}"),
            self.build_section_fields([
                f"*Project:*\n{project}",
                f"*Duration:*\n{duration:.1f}s",
                f"*Files:*\n{files_generated}",
                f"*Errors:*\n{errors}",
            ]),
            self.build_divider(),
        ]

        return await self.send(
            channel=channel,
            text=f"Pipeline completed for {project}: {files_generated} files in {duration:.1f}s",
            blocks=blocks,
        )

    async def notify_error(
        self,
        project: str,
        error: str,
        phase: str = None,
        channel: str = None,
    ) -> bool:
        """Уведомление об ошибке"""
        blocks = [
            self.build_header(":x: Pipeline Error"),
            self.build_section_text(f"*Project:* {project}"),
            self.build_section_text(f"*Error:* ```{error[:500]}```"),
        ]

        if phase:
            blocks.insert(1, self.build_section_text(f"*Phase:* {phase}"))

        return await self.send(
            channel=channel,
            text=f"Pipeline error in {project}: {error[:100]}",
            blocks=blocks,
        )

    async def notify_conversion(
        self,
        file_type: str,
        count: int,
        channel: str = None,
    ) -> bool:
        """Уведомление о конвертации файлов"""
        emoji_map = {
            "haskell": ":haskell:",
            "qml": ":desktop_computer:",
            "sql": ":database:",
            "reports": ":page_facing_up:",
        }

        emoji = emoji_map.get(file_type.lower(), ":file_folder:")

        blocks = [
            self.build_section_text(f"{emoji} *{count}* {file_type} files converted"),
        ]

        return await self.send(
            channel=channel,
            text=f"Converted {count} {file_type} files",
            blocks=blocks,
        )

    async def send(
        self,
        text: str = "",
        blocks: list[dict] = None,
        attachments: list[dict] = None,
        channel: str = None,
    ) -> bool:
        """Универсальная отправка"""
        channel = channel or self.config.channel

        if self.config.webhook_url:
            return await self.send_webhook(text, blocks, attachments)
        elif self.config.bot_token and channel:
            result = await self.chat_post_message(
                channel=channel,
                text=text,
                blocks=blocks,
                attachments=attachments,
                username=self.config.username,
                icon_emoji=self.config.icon_emoji,
            )
            return result is not None
        else:
            logger.warning("No Slack configuration available")
            return False

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton
_slack_client: SlackClient | None = None


def get_slack_client(config: SlackConfig = None) -> SlackClient:
    """Получение Slack клиента"""
    global _slack_client
    if _slack_client is None:
        _slack_client = SlackClient(config)
    return _slack_client


class SlackIntegration:
    """Sync wrapper для Slack"""

    def __init__(self, config: SlackConfig = None):
        self.config = config or SlackConfig.from_env()
        self._client = SlackClient(self.config)

    async def notify_pipeline_complete_async(self, **kwargs) -> bool:
        return await self._client.notify_pipeline_complete(**kwargs)

    def notify_pipeline_complete(self, **kwargs) -> bool:
        """Sync уведомление о завершении"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return False
            return loop.run_until_complete(self.notify_pipeline_complete_async(**kwargs))
        except RuntimeError:
            return asyncio.run(self.notify_pipeline_complete_async(**kwargs))
