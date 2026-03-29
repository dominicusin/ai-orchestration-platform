"""
Quotas management
Управление квотами
"""

import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Quota:
    """Квота"""
    name: str
    limit: int
    used: int = 0
    reset_at: float = field(default_factory=lambda: time.time() + 86400)
    unlimited: bool = False


class QuotaManager:
    """
    Менеджер квот
    """

    def __init__(self):
        self._quotas: dict[str, Quota] = {}

    def create_quota(
        self,
        name: str,
        limit: int,
        reset_interval_seconds: int = 86400,
    ):
        """Создание квоты"""
        reset_at = time.time() + reset_interval_seconds
        self._quotas[name] = Quota(
            name=name,
            limit=limit,
            reset_at=reset_at,
        )

    def check(self, name: str, amount: int = 1) -> bool:
        """Проверка доступности квоты"""
        if name not in self._quotas:
            return True

        quota = self._quotas[name]
        if quota.unlimited:
            return True

        # Reset if needed
        if time.time() >= quota.reset_at:
            quota.used = 0
            quota.reset_at = time.time() + 86400

        return (quota.used + amount) <= quota.limit

    def consume(self, name: str, amount: int = 1) -> bool:
        """Потребление квоты"""
        if not self.check(name, amount):
            return False

        if name in self._quotas:
            self._quotas[name].used += amount
        return True

    def get_usage(self, name: str) -> dict:
        """Получение использования квоты"""
        if name not in self._quotas:
            return {"error": "Quota not found"}

        quota = self._quotas[name]
        return {
            "name": quota.name,
            "limit": quota.limit,
            "used": quota.used,
            "remaining": max(0, quota.limit - quota.used),
            "reset_at": datetime.fromtimestamp(quota.reset_at).isoformat(),
        }

    def set_unlimited(self, name: str, unlimited: bool = True):
        """Установка безлимитной квоты"""
        if name in self._quotas:
            self._quotas[name].unlimited = unlimited


# Singleton
_quota_manager: QuotaManager | None = None


def get_quota_manager() -> QuotaManager:
    """Получение менеджера квот"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
