"""Webhook system for external integrations"""

import os
import asyncio
import logging
import hmac
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger("orchestration.webhooks")


class WebhookEvent(Enum):
    """Webhook events"""
    PIPELINE_START = "pipeline.start"
    PIPELINE_COMPLETE = "pipeline.complete"
    PIPELINE_ERROR = "pipeline.error"
    PHASE_COMPLETE = "phase.complete"
    FILE_CONVERTED = "file.converted"


@dataclass
class Webhook:
    """Webhook configuration"""
    id: str
    url: str
    events: List[str]
    secret: str = ""
    enabled: bool = True
    retry_count: int = 3
    timeout: int = 30


@dataclass
class WebhookDelivery:
    """Webhook delivery record"""
    id: str
    webhook_id: str
    event: str
    payload: Dict
    status: str  # pending, success, failed
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: str
    delivered_at: Optional[str] = None
    attempts: int = 0
    error: Optional[str] = None


class WebhookClient:
    """HTTP client for webhooks"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def deliver(
        self,
        url: str,
        payload: Dict,
        secret: str = "",
    ) -> Dict[str, Any]:
        """Deliver webhook payload"""
        import aiohttp
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Pipeline-Webhook/1.0",
        }
        
        # Add signature if secret provided
        if secret:
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                ) as resp:
                    return {
                        "success": resp.status < 400,
                        "status_code": resp.status,
                        "body": await resp.text(),
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "status_code": 0,
                "body": "Timeout",
                "error": "Request timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "body": "",
                "error": str(e),
            }


class WebhookManager:
    """Manage webhooks"""
    
    def __init__(self, webhooks_dir: str = "./webhooks"):
        self.webhooks_dir = Path(webhooks_dir)
        self.webhooks_dir.mkdir(parents=True, exist_ok=True)
        
        self.webhooks: Dict[str, Webhook] = {}
        self.deliveries: List[WebhookDelivery] = []
        
        self.client = WebhookClient()
        
        self._load_webhooks()
    
    def _load_webhooks(self):
        """Load webhooks from config"""
        # Check environment for webhooks
        webhooks_config = os.getenv("WEBHOOKS", "")
        
        if webhooks_config:
            for i, url in enumerate(webhooks_config.split(",")):
                webhook = Webhook(
                    id=f"webhook_{i}",
                    url=url.strip(),
                    events=["*"],  # All events
                )
                self.webhooks[webhook.id] = webhook
    
    def register_webhook(
        self,
        url: str,
        events: List[str],
        secret: str = "",
    ) -> str:
        """Register a new webhook"""
        import uuid
        
        webhook_id = f"webhook_{uuid.uuid4().hex[:8]}"
        
        webhook = Webhook(
            id=webhook_id,
            url=url,
            events=events,
            secret=secret,
        )
        
        self.webhooks[webhook_id] = webhook
        
        logger.info(f"Registered webhook: {webhook_id} -> {url}")
        
        return webhook_id
    
    def unregister_webhook(self, webhook_id: str):
        """Unregister a webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info(f"Unregistered webhook: {webhook_id}")
    
    def get_webhooks_for_event(self, event: str) -> List[Webhook]:
        """Get webhooks subscribed to an event"""
        result = []
        
        for webhook in self.webhooks.values():
            if not webhook.enabled:
                continue
            
            if "*" in webhook.events or event in webhook.events:
                result.append(webhook)
        
        return result
    
    async def trigger(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
    ) -> List[WebhookDelivery]:
        """Trigger webhooks for an event"""
        webhooks = self.get_webhooks_for_event(event.value)
        
        if not webhooks:
            return []
        
        payload = {
            "event": event.value,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        
        deliveries = []
        
        for webhook in webhooks:
            delivery = await self._deliver(webhook, event.value, payload)
            deliveries.append(delivery)
            self.deliveries.append(delivery)
        
        # Keep only last 1000 deliveries
        self.deliveries = self.deliveries[-1000:]
        
        return deliveries
    
    async def _deliver(
        self,
        webhook: Webhook,
        event: str,
        payload: Dict,
    ) -> WebhookDelivery:
        """Deliver webhook with retry"""
        import uuid
        
        delivery = WebhookDelivery(
            id=str(uuid.uuid4()),
            webhook_id=webhook.id,
            event=event,
            payload=payload,
            status="pending",
            created_at=datetime.now().isoformat(),
        )
        
        for attempt in range(webhook.retry_count):
            delivery.attempts = attempt + 1
            
            result = await self.client.deliver(
                webhook.url,
                payload,
                webhook.secret,
            )
            
            delivery.response_code = result.get("status_code")
            delivery.response_body = result.get("body")
            delivery.delivered_at = datetime.now().isoformat()
            
            if result["success"]:
                delivery.status = "success"
                logger.info(f"Webhook delivered: {webhook.id}")
                break
            else:
                delivery.error = result.get("error")
                delivery.status = "failed"
                
                if attempt < webhook.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        if delivery.status == "failed":
            logger.error(f"Webhook failed: {webhook.id} - {delivery.error}")
        
        return delivery
    
    def get_deliveries(
        self,
        webhook_id: str = None,
        status: str = None,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        """Get delivery history"""
        result = self.deliveries
        
        if webhook_id:
            result = [d for d in result if d.webhook_id == webhook_id]
        
        if status:
            result = [d for d in result if d.status == status]
        
        return result[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        total = len(self.deliveries)
        success = sum(1 for d in self.deliveries if d.status == "success")
        failed = sum(1 for d in self.deliveries if d.status == "failed")
        
        return {
            "total_deliveries": total,
            "successful": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0,
            "registered_webhooks": len(self.webhooks),
        }


# Convenience functions
async def trigger_pipeline_complete(stats: Dict[str, Any]):
    """Trigger pipeline complete webhooks"""
    manager = WebhookManager()
    await manager.trigger(WebhookEvent.PIPELINE_COMPLETE, stats)


async def trigger_file_converted(file_path: str, format: str):
    """Trigger file converted webhooks"""
    manager = WebhookManager()
    await manager.trigger(
        WebhookEvent.FILE_CONVERTED,
        {"file_path": file_path, "format": format},
    )


# Global webhook manager
_webhook_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    """Get webhook manager"""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager