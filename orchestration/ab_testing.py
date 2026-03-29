"""
A/B Testing for prompts
A/B тестирование промптов с отслеживанием метрик
"""

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("orchestration.ab_testing")


@dataclass
class ABTestVariant:
    """Вариант A/B теста"""
    id: str
    name: str
    prompt_name: str
    prompt_version: str
    weight: int  # 0-100, relative weight
    enabled: bool = True


@dataclass
class ABTestResult:
    """Результат A/B теста"""
    variant_id: str
    success: bool
    response_time: float
    quality_score: float = 0.0
    tokens_used: int = 0
    error: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class ABTestStats:
    """Статистика A/B теста"""
    test_id: str
    variant_id: str
    impressions: int = 0
    successes: int = 0
    failures: int = 0
    total_response_time: float = 0.0
    total_quality_score: float = 0.0
    total_tokens: int = 0

    @property
    def success_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.successes / self.impressions

    @property
    def avg_response_time(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.total_response_time / self.impressions

    @property
    def avg_quality(self) -> float:
        if self.successes == 0:
            return 0.0
        return self.total_quality_score / self.successes


class ABTestingManager:
    """
    Менеджер A/B тестирования промптов
    """

    def __init__(self, results_dir: Path = None):
        self.results_dir = results_dir or Path("ab_test_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._tests: dict[str, list[ABTestVariant]] = {}
        self._stats: dict[str, dict[str, ABTestStats]] = {}
        self._load_stats()

    def _load_stats(self):
        """Загрузка статистики из файлов"""
        for f in self.results_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                test_id = f.stem
                self._stats[test_id] = {}
                for var_id, stats in data.get("variants", {}).items():
                    self._stats[test_id][var_id] = ABTestStats(
                        test_id=test_id,
                        variant_id=var_id,
                        impressions=stats.get("impressions", 0),
                        successes=stats.get("successes", 0),
                        failures=stats.get("failures", 0),
                        total_response_time=stats.get("total_response_time", 0.0),
                        total_quality_score=stats.get("total_quality_score", 0.0),
                        total_tokens=stats.get("total_tokens", 0),
                    )
            except Exception as e:
                logger.warning(f"Error loading stats {f}: {e}")

    def _save_stats(self, test_id: str):
        """Сохранение статистики"""
        if test_id not in self._stats:
            return

        data = {
            "test_id": test_id,
            "updated_at": datetime.now().isoformat(),
            "variants": {
                var_id: {
                    "impressions": stats.impressions,
                    "successes": stats.successes,
                    "failures": stats.failures,
                    "total_response_time": stats.total_response_time,
                    "total_quality_score": stats.total_quality_score,
                    "total_tokens": stats.total_tokens,
                }
                for var_id, stats in self._stats[test_id].items()
            },
        }

        path = self.results_dir / f"{test_id}.json"
        path.write_text(json.dumps(data, indent=2))

    def create_test(
        self,
        test_id: str,
        variants: list[ABTestVariant],
    ) -> bool:
        """Создание A/B теста"""
        if not variants or len(variants) < 2:
            logger.warning("A/B test requires at least 2 variants")
            return False

        total_weight = sum(v.weight for v in variants)
        if total_weight == 0:
            logger.warning("Total weight must be > 0")
            return False

        self._tests[test_id] = variants
        self._stats[test_id] = {
            v.id: ABTestStats(test_id=test_id, variant_id=v.id)
            for v in variants
        }
        self._save_stats(test_id)

        logger.info(f"Created A/B test: {test_id} with {len(variants)} variants")
        return True

    def select_variant(self, test_id: str) -> ABTestVariant | None:
        """Выбор варианта для теста"""
        variants = self._tests.get(test_id)
        if not variants:
            return None

        enabled = [v for v in variants if v.enabled]
        if not enabled:
            return None

        # Weighted random selection
        total_weight = sum(v.weight for v in enabled)
        rand = random.randint(1, total_weight)

        cumulative = 0
        for v in enabled:
            cumulative += v.weight
            if rand <= cumulative:
                # Record impression
                if test_id in self._stats and v.id in self._stats[test_id]:
                    self._stats[test_id][v.id].impressions += 1
                    self._save_stats(test_id)
                return v

        return enabled[-1]

    def record_result(self, test_id: str, result: ABTestResult):
        """Запись результата"""
        if test_id not in self._stats:
            return

        stats = self._stats[test_id].get(result.variant_id)
        if not stats:
            return

        if result.success:
            stats.successes += 1
            stats.total_quality_score += result.quality_score
        else:
            stats.failures += 1

        stats.total_response_time += result.response_time
        stats.total_tokens += result.tokens_used

        self._save_stats(test_id)

    def get_stats(self, test_id: str) -> dict[str, ABTestStats] | None:
        """Получение статистики теста"""
        return self._stats.get(test_id)

    def get_winner(self, test_id: str) -> ABTestVariant | None:
        """Определение победителя (по success rate)"""
        variants = self._tests.get(test_id)
        stats = self._stats.get(test_id)
        if not variants or not stats:
            return None

        best = None
        best_rate = -1

        for v in variants:
            v_stats = stats.get(v.id)
            if v_stats and v_stats.impressions > 0:
                rate = v_stats.success_rate
                if rate > best_rate:
                    best_rate = rate
                    best = v

        return best

    def get_leaderboard(self, test_id: str) -> list[dict]:
        """Получение рейтинга вариантов"""
        stats = self._stats.get(test_id, {})
        variants = self._tests.get(test_id, [])

        leaderboard = []
        for v in variants:
            v_stats = stats.get(v.id)
            if v_stats:
                leaderboard.append({
                    "variant": v.name,
                    "impressions": v_stats.impressions,
                    "success_rate": f"{v_stats.success_rate:.1%}",
                    "avg_response_time": f"{v_stats.avg_response_time:.2f}s",
                    "avg_quality": f"{v_stats.avg_quality:.2f}",
                })

        # Sort by success rate
        leaderboard.sort(
            key=lambda x: float(x["success_rate"].rstrip("%")),
            reverse=True,
        )
        return leaderboard

    def stop_test(self, test_id: str) -> bool:
        """Остановка теста"""
        variants = self._tests.get(test_id)
        if not variants:
            return False

        for v in variants:
            v.enabled = False

        logger.info(f"Stopped A/B test: {test_id}")
        return True

    def delete_test(self, test_id: str) -> bool:
        """Удаление теста"""
        if test_id in self._tests:
            del self._tests[test_id]
        if test_id in self._stats:
            del self._stats[test_id]

        path = self.results_dir / f"{test_id}.json"
        if path.exists():
            path.unlink()

        return True

    def list_tests(self) -> list[str]:
        """Список тестов"""
        return list(self._tests.keys())


# Singleton
_ab_testing_manager: ABTestingManager | None = None


def get_ab_testing_manager(results_dir: Path = None) -> ABTestingManager:
    """Получение менеджера A/B тестирования"""
    global _ab_testing_manager
    if _ab_testing_manager is None:
        _ab_testing_manager = ABTestingManager(results_dir)
    return _ab_testing_manager
