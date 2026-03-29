"""
Кэш для результатов генерации с поддержкой инвалидации и инкрементальной обработки
"""

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("orchestration.cache")


class CachePolicy(Enum):
    """Политика кэширования"""
    CACHE_FIRST = "cache_first"   # Пробуем кэш, потом AI
    AI_FIRST = "ai_first"         # Сначала AI, потом кэш
    SKIP_CACHE = "skip_cache"     # Пропускать кэш


@dataclass
class CacheEntry:
    """Запись в кэше"""
    source_hash: str
    result: str
    operation: str
    source_path: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Статистика кэша"""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    invalidations: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class FileCache:
    """
    Кэш результатов генерации с:
    - In-memory кэш для быстрого доступа
    - File-based persistence
    - Инвалидация по hash содержимого
    - Инкрементальная обработка (отслеживание обработанных файлов)
    """

    def __init__(
        self,
        cache_dir: Path,
        policy: CachePolicy = CachePolicy.CACHE_FIRST,
        max_memory_entries: int = 1000,
    ):
        self.cache_dir = cache_dir
        self.policy = policy
        self.max_memory_entries = max_memory_entries

        # Создаём директорию
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Thread-safe lock
        self._lock = threading.RLock()

        # In-memory кэш
        self._memory_cache: dict[str, CacheEntry] = {}

        # Инкрементальная обработка - отслеживание обработанных файлов
        self._processed_files: dict[str, float] = {}  # path -> timestamp

        # Статистика
        self.stats = CacheStats()

        # Загружаем метаданные
        self._load_metadata()

        logger.debug(f"Кэш инициализирован: {cache_dir}, policy={policy.value}")

    def _get_key(self, source_path: str, operation: str) -> str:
        """Генерация ключа кэша"""
        return hashlib.sha256(
            f"{operation}:{source_path}".encode()
        ).hexdigest()[:16]

    def _get_source_hash(self, source_content: str) -> str:
        """Хэш содержимого источника"""
        return hashlib.md5(source_content.encode()).hexdigest()

    def _load_metadata(self):
        """Загрузка метаданных кэша"""
        metadata_file = self.cache_dir / "metadata.json"
        if metadata_file.exists():
            try:
                data = json.loads(metadata_file.read_text())
                self.stats = CacheStats(**data.get("stats", {}))
                self._processed_files = data.get("processed_files", {})
                logger.debug(f"Загружено {len(self._processed_files)} обработанных файлов")
            except Exception as e:
                logger.warning(f"Ошибка загрузки метаданных: {e}")

    def _save_metadata(self):
        """Сохранение метаданных кэша"""
        metadata_file = self.cache_dir / "metadata.json"
        try:
            metadata_file.write_text(json.dumps({
                "stats": {
                    "hits": self.stats.hits,
                    "misses": self.stats.misses,
                    "writes": self.stats.writes,
                    "invalidations": self.stats.invalidations,
                    "errors": self.stats.errors,
                },
                "processed_files": self._processed_files,
            }, indent=2))
        except Exception as e:
            logger.warning(f"Ошибка сохранения метаданных: {e}")

    def get(
        self,
        source_path: str,
        operation: str,
        source_content: str
    ) -> str | None:
        """
        Получение результата из кэша

        Returns:
            Кэшированный результат или None если нет в кэше
        """
        if self.policy == CachePolicy.SKIP_CACHE:
            return None

        key = self._get_key(source_path, operation)
        source_hash = self._get_source_hash(source_content)

        # Проверяем in-memory кэш
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if entry.source_hash == source_hash:
                    self.stats.hits += 1
                    logger.debug(f"Кэш hit (memory): {source_path}:{operation}")
                    return entry.result

        # Проверяем file-based кэш
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                if data.get("source_hash") == source_hash:
                    # Добавляем в memory cache
                    with self._lock:
                        entry = CacheEntry(
                            source_hash=source_hash,
                            result=data["result"],
                            operation=operation,
                            source_path=source_path,
                            timestamp=data.get("timestamp", time.time()),
                        )
                        self._memory_cache[key] = entry
                        self._evict_if_needed()

                    self.stats.hits += 1
                    logger.debug(f"Кэш hit (file): {source_path}:{operation}")
                    return data["result"]
            except json.JSONDecodeError as e:
                logger.warning(f"Ошибка чтения кэша {cache_file}: {e}")
                self.stats.errors += 1
            except Exception as e:
                logger.warning(f"Ошибка кэша: {e}")
                self.stats.errors += 1

        self.stats.misses += 1
        logger.debug(f"Кэш miss: {source_path}:{operation}")
        return None

    def set(
        self,
        source_path: str,
        operation: str,
        source_content: str,
        result: str,
        metadata: dict[str, Any] = None,
    ):
        """Сохранение результата в кэш"""
        key = self._get_key(source_path, operation)
        source_hash = self._get_source_hash(source_content)

        # Сохраняем в memory
        with self._lock:
            entry = CacheEntry(
                source_hash=source_hash,
                result=result,
                operation=operation,
                source_path=source_path,
                timestamp=time.time(),
                metadata=metadata or {},
            )
            self._memory_cache[key] = entry
            self._evict_if_needed()

        # Сохраняем в файл
        cache_file = self.cache_dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps({
                "source_hash": source_hash,
                "result": result,
                "operation": operation,
                "source_path": source_path,
                "timestamp": time.time(),
                "metadata": metadata or {},
            }, indent=2))
            self.stats.writes += 1
        except Exception as e:
            logger.warning(f"Ошибка записи кэша: {e}")
            self.stats.errors += 1

        # Отмечаем файл как обработанный
        self.mark_processed(source_path, operation)

    def _evict_if_needed(self):
        """Вытеснение старых записей если превышен лимит"""
        if len(self._memory_cache) <= self.max_memory_entries:
            return

        # Удаляем самые старые записи
        sorted_entries = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1].timestamp
        )

        to_remove = len(self._memory_cache) - self.max_memory_entries + 100
        for key, _ in sorted_entries[:to_remove]:
            del self._memory_cache[key]

    def mark_processed(self, source_path: str, operation: str):
        """Отметка файла как обработанного"""
        with self._lock:
            self._processed_files[f"{operation}:{source_path}"] = time.time()
        self._save_metadata()

    def is_processed(self, source_path: str, operation: str) -> bool:
        """Проверка обработан ли файл"""
        key = f"{operation}:{source_path}"
        return key in self._processed_files

    def get_unprocessed(
        self,
        files: list[str],
        operation: str,
        source_content_getter: callable = None,
    ) -> list[str]:
        """
        Получение списка необработанных файлов

        Args:
            files: Список файлов для проверки
            operation: Операция
            source_content_getter: Функция для получения содержимого файла

        Returns:
            Список необработанных файлов
        """
        unprocessed = []

        for f in files:
            key = f"{operation}:{f}"
            if key not in self._processed_files:
                unprocessed.append(f)
                continue

            # Если есть getter - проверяем изменился ли файл
            if source_content_getter:
                try:
                    content = source_content_getter(f)
                    if content:
                        cached = self.get(f, operation, content)
                        if cached is None:
                            unprocessed.append(f)
                except Exception:
                    unprocessed.append(f)

        return unprocessed

    def invalidate(self, source_path: str = None, operation: str = None):
        """Инвалидация кэша"""
        with self._lock:
            if source_path and operation:
                key = self._get_key(source_path, operation)
                if key in self._memory_cache:
                    del self._memory_cache[key]

                cache_file = self.cache_dir / f"{key}.json"
                if cache_file.exists():
                    cache_file.unlink()

                processed_key = f"{operation}:{source_path}"
                if processed_key in self._processed_files:
                    del self._processed_files[processed_key]

                self.stats.invalidations += 1
            elif operation:
                # Инвалидация всех записей для операции
                to_remove = [
                    k for k in self._memory_cache.keys()
                    if self._memory_cache[k].operation == operation
                ]
                for k in to_remove:
                    del self._memory_cache[k]

                for f in list(self._processed_files.keys()):
                    if f.startswith(f"{operation}:"):
                        del self._processed_files[f]

                self.stats.invalidations += len(to_remove)
            else:
                # Полная очистка
                self._memory_cache.clear()
                self._processed_files.clear()
                self.stats.invalidations += 1

        self._save_metadata()

    def clear(self):
        """Очистка всего кэша"""
        with self._lock:
            self._memory_cache.clear()

        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except Exception as e:
                logger.warning(f"Ошибка удаления {f}: {e}")

        self._processed_files.clear()
        self._save_metadata()
        logger.info("Кэш очищен")

    def get_stats(self) -> dict:
        """Получение статистики кэша"""
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "writes": self.stats.writes,
            "invalidations": self.stats.invalidations,
            "errors": self.stats.errors,
            "hit_rate": self.stats.hit_rate,
            "memory_entries": len(self._memory_cache),
            "processed_files": len(self._processed_files),
        }

    def cleanup_old_entries(self, max_age_days: int = 30):
        """Очистка старых записей"""
        cutoff = time.time() - (max_age_days * 86400)

        with self._lock:
            # Чистим memory
            to_remove = [
                k for k, v in self._memory_cache.items()
                if v.timestamp < cutoff
            ]
            for k in to_remove:
                del self._memory_cache[k]

            # Чистим processed files
            processed_to_remove = [
                k for k, v in self._processed_files.items()
                if v < cutoff
            ]
            for k in processed_to_remove:
                del self._processed_files[k]

        # Чистим файлы
        for f in self.cache_dir.glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except Exception as e:
                logger.warning(f"Ошибка удаления {f}: {e}")

        logger.info(f"Удалено {len(to_remove)} старых записей кэша")
