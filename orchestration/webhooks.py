"""Webhooks for notifications"""

import logging

logger = logging.getLogger("orchestration.webhooks")


class Webhook:
    """Webhook notification"""

    def __init__(self, url: str, event: str, secret: str = None):
        self.url = url
        self.event = event
        self.secret = secret

    def send(self, payload: dict):
        """Send webhook"""
        # Placeholder - would use HTTP client
        logger.info(f"Webhook {self.event} to {self.url}")


class WebhookManager:
    """Manage webhooks"""

    def __init__(self):
        self.webhooks: list[Webhook] = []

    def register(self, webhook: Webhook):
        self.webhooks.append(webhook)

    def trigger(self, event: str, payload: dict):
        """Trigger webhooks for event"""
        for webhook in self.webhooks:
            if webhook.event == event:
                webhook.send(payload)
