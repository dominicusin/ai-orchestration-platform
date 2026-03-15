"""Notification system for pipeline events"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.notifications")


class NotificationType(Enum):
    """Notification types"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    PUSH = "push"


@dataclass
class Notification:
    """Notification"""
    type: str
    title: str
    message: str
    severity: str = "info"  # info, warning, error, success
    metadata: Dict[str, Any] = None


class NotificationChannel:
    """Base notification channel"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = True
    
    async def send(self, notification: Notification) -> bool:
        """Send notification"""
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    """Email notifications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.smtp_host = self.config.get("smtp_host", os.getenv("SMTP_HOST"))
        self.smtp_port = self.config.get("smtp_port", 587)
        self.username = self.config.get("username", os.getenv("SMTP_USER"))
        self.password = self.config.get("password", os.getenv("SMTP_PASS"))
        self.from_addr = self.config.get("from", os.getenv("SMTP_FROM"))
        self.to_addrs = self.config.get("to", os.getenv("SMTP_TO", "").split(","))
    
    async def send(self, notification: Notification) -> bool:
        """Send email"""
        if not self.smtp_host:
            return False
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg["Subject"] = f"[{notification.severity.upper()}] {notification.title}"
            
            body = f"""
{notification.message}

---
AI Pipeline Notification
{datetime.now().isoformat()}
"""
            msg.attach(MIMEText(body, "plain"))
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
            )
            
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False


class SlackChannel(NotificationChannel):
    """Slack notifications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.webhook_url = self.config.get("webhook_url", os.getenv("SLACK_WEBHOOK"))
    
    async def send(self, notification: Notification) -> bool:
        """Send Slack notification"""
        if not self.webhook_url:
            return False
        
        import aiohttp
        
        colors = {
            "info": "#36a64f",
            "warning": "#ff9800",
            "error": "#f44336",
            "success": "#4caf50",
        }
        
        payload = {
            "attachments": [{
                "color": colors.get(notification.severity, "#36a64f"),
                "title": notification.title,
                "text": notification.message,
                "footer": "AI Pipeline",
                "ts": datetime.now().timestamp(),
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False


class DiscordChannel(NotificationChannel):
    """Discord notifications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.webhook_url = self.config.get("webhook_url", os.getenv("DISCORD_WEBHOOK"))
    
    async def send(self, notification: Notification) -> bool:
        """Send Discord notification"""
        if not self.webhook_url:
            return False
        
        import aiohttp
        
        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }
        
        payload = {
            "embeds": [{
                "title": f"{emojis.get(notification.severity, 'ℹ️')} {notification.title}",
                "description": notification.message,
                "color": 3447003,  # Blue
                "footer": {"text": "AI Pipeline"},
                "timestamp": datetime.now().isoformat(),
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return False


class TelegramChannel(NotificationChannel):
    """Telegram notifications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.bot_token = self.config.get("bot_token", os.getenv("TELEGRAM_BOT_TOKEN"))
        self.chat_id = self.config.get("chat_id", os.getenv("TELEGRAM_CHAT_ID"))
    
    async def send(self, notification: Notification) -> bool:
        """Send Telegram notification"""
        if not self.bot_token or not self.chat_id:
            return False
        
        import aiohttp
        
        emojis = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }
        
        text = f"{emojis.get(notification.severity, 'ℹ️')} *{notification.title}*\n{notification.message}"
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False


class NotificationManager:
    """Manage notifications"""
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self._setup_channels()
    
    def _setup_channels(self):
        """Setup notification channels"""
        # Email
        if os.getenv("SMTP_HOST"):
            self.channels["email"] = EmailChannel()
        
        # Slack
        if os.getenv("SLACK_WEBHOOK"):
            self.channels["slack"] = SlackChannel()
        
        # Discord
        if os.getenv("DISCORD_WEBHOOK"):
            self.channels["discord"] = DiscordChannel()
        
        # Telegram
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.channels["telegram"] = TelegramChannel()
    
    async def notify(
        self,
        title: str,
        message: str,
        severity: str = "info",
        channels: List[str] = None,
    ):
        """Send notification"""
        notification = Notification(
            type="pipeline",
            title=title,
            message=message,
            severity=severity,
        )
        
        channels = channels or list(self.channels.keys())
        
        tasks = []
        for channel_name in channels:
            if channel_name in self.channels:
                tasks.append(self.channels[channel_name].send(notification))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return any(r for r in results if r is True)
        
        return False
    
    async def notify_pipeline_complete(self, stats: Dict[str, Any]):
        """Notify pipeline complete"""
        await self.notify(
            title="Pipeline Complete",
            message=f"Runtime: {stats.get('runtime_seconds', 0):.1f}s, Files: {stats.get('total_files', 0)}",
            severity="success",
        )
    
    async def notify_pipeline_error(self, error: str):
        """Notify pipeline error"""
        await self.notify(
            title="Pipeline Error",
            message=error,
            severity="error",
        )
    
    async def notify_phase_complete(self, phase: str, files: int):
        """Notify phase complete"""
        await self.notify(
            title=f"Phase Complete: {phase}",
            message=f"Converted {files} files",
            severity="info",
        )


# Global manager
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get notification manager"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager