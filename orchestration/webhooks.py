"""Webhook system for notifications"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import aiohttp

logger = logging.getLogger("orchestration.webhooks")


class EventType(Enum):
    """Webhook event types"""
    PIPELINE_START = "pipeline.start"
    PIPELINE_COMPLETE = "pipeline.complete"
    PIPELINE_ERROR = "pipeline.error"
    PHASE_START = "phase.start"
    PHASE_COMPLETE = "phase.complete"
    FILE_CONVERTED = "file.converted"
    FILE_FAILED = "file.failed"


@dataclass
class WebhookEvent:
    """Webhook event"""
    event_type: str
    timestamp: str
    data: Dict[str, Any]
    source: str = "ai-pipeline"


class Webhook:
    """Single webhook endpoint"""
    
    def __init__(self, url: str, events: List[str] = None, secret: str = None):
        self.url = url
        self.events = events or ["*"]  # All events by default
        self.secret = secret
        self.enabled = True
    
    def should_fire(self, event_type: str) -> bool:
        """Check if this webhook should fire for event"""
        if "*" in self.events:
            return True
        return event_type in self.events


class WebhookManager:
    """Manage webhooks"""
    
    def __init__(self):
        self.webhooks: List[Webhook] = []
        self._load_from_env()
    
    def _load_from_env(self):
        """Load webhooks from environment"""
        # Multiple webhooks: WEBHOOK_URLS=url1,url2,url3
        urls = os.getenv("WEBHOOK_URLS", "").split(",")
        
        for url in urls:
            if url.strip():
                events = os.getenv("WEBHOOK_EVENTS", "*").split(",")
                secret = os.getenv("WEBHOOK_SECRET")
                self.add(Webhook(url.strip(), events, secret))
    
    def add(self, webhook: Webhook):
        """Add webhook"""
        self.webhooks.append(webhook)
        logger.info(f"Added webhook: {webhook.url}")
    
    def remove(self, url: str):
        """Remove webhook"""
        self.webhooks = [w for w in self.webhooks if w.url != url]
    
    async def fire(self, event: WebhookEvent):
        """Fire webhook for event"""
        tasks = []
        
        for webhook in self.webhooks:
            if not webhook.enabled:
                continue
            
            if not webhook.should_fire(event.event_type):
                continue
            
            task = self._send_webhook(webhook, event)
            tasks.append(task)
        
        # Wait for all (don't block)
        if tasks:
            asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_webhook(self, webhook: Webhook, event: WebhookEvent):
        """Send webhook request"""
        import hmac
        import hashlib
        import json
        from datetime import datetime
        
        payload = {
            "event": event.event_type,
            "timestamp": event.timestamp or datetime.now().isoformat(),
            "data": event.data,
        }
        
        # Sign payload if secret provided
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(
                webhook.secret.encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers["X-Signature"] = signature
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.ok:
                        logger.debug(f"Webhook sent: {webhook.url}")
                    else:
                        logger.warning(f"Webhook failed: {resp.status}")
                        
        except Exception as e:
            logger.error(f"Webhook error: {e}")


# Convenience functions
def create_event(event_type: str, data: Dict[str, Any]) -> WebhookEvent:
    """Create webhook event"""
    from datetime import datetime
    return WebhookEvent(
        event_type=event_type,
        timestamp=datetime.now().isoformat(),
        data=data,
    )


async def notify_pipeline_complete(success: bool, stats: Dict[str, Any]):
    """Send pipeline complete notification"""
    manager = WebhookManager()
    
    event_type = EventType.PIPELINE_COMPLETE.value if success else EventType.PIPELINE_ERROR.value
    event = create_event(event_type, stats)
    
    await manager.fire(event)


# Example: Slack webhook
class SlackWebhook(Webhook):
    """Slack-specific webhook"""
    
    def __init__(self, url: str):
        super().__init__(url, ["pipeline.complete", "pipeline.error"])
    
    def format_message(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format message for Slack"""
        is_error = event.event_type == EventType.PIPELINE_ERROR.value
        
        return {
            "attachments": [{
                "color": "#ff0000" if is_error else "#00ff00",
                "title": "Pipeline Complete" if not is_error else "Pipeline Failed",
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in event.data.items()
                ]
            }]
        }


# Example: Discord webhook
class DiscordWebhook(Webhook):
    """Discord-specific webhook"""
    
    def __init__(self, url: str):
        super().__init__(url, ["pipeline.complete", "pipeline.error"])
    
    def format_message(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format message for Discord"""
        is_error = event.event_type == EventType.PIPELINE_ERROR.value
        
        return {
            "embeds": [{
                "title": "✅ Pipeline Complete" if not is_error else "❌ Pipeline Failed",
                "color": 65280 if not is_error else 16711680,
                "fields": [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in event.data.items()
                ]
            }]
        }
