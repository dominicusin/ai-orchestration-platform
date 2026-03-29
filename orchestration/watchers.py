"""
Watchers for file system and other resources
Наблюдатели за файловой системой и другими ресурсами
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger("orchestration.watchers")


class Watcher:
    """Базовый класс наблюдателя"""

    def start(self):
        """Запуск наблюдения"""
        raise NotImplementedError

    def stop(self):
        """Остановка наблюдения"""
        raise NotImplementedError


class FileWatcher(Watcher):
    """Наблюдатель за файловой системой"""

    def __init__(
        self,
        path: str,
        callback: Callable,
        event_types: list = None,
        recursive: bool = False,
        interval: float = 1.0,
    ):
        self.path = Path(path)
        self.callback = callback
        self.event_types = event_types or ["modified", "created", "deleted"]
        self.recursive = recursive
        self.interval = interval
        self._running = False
        self._last_mtimes = {}

    def start(self):
        """Запуск наблюдения"""
        self._running = True
        self._update_mtimes()
        logger.info(f"Started watching: {self.path}")

    def stop(self):
        """Остановка наблюдения"""
        self._running = False
        logger.info(f"Stopped watching: {self.path}")

    def _update_mtimes(self):
        """Обновление времени модификации"""
        if not self.path.exists():
            return

        if self.path.is_file():
            try:
                self._last_mtimes[str(self.path)] = self.path.stat().st_mtime
            except OSError:
                pass
        elif self.recursive:
            for p in self.path.rglob("*"):
                if p.is_file():
                    try:
                        self._last_mtimes[str(p)] = p.stat().st_mtime
                    except OSError:
                        pass

    def check_changes(self) -> list:
        """Проверка изменений"""
        changes = []

        if not self.path.exists():
            return changes

        if self.path.is_file():
            try:
                current_mtime = self.path.stat().st_mtime
                last_mtime = self._last_mtimes.get(str(self.path))

                if last_mtime is None:
                    self._last_mtimes[str(self.path)] = current_mtime
                elif current_mtime > last_mtime:
                    changes.append({
                        "type": "modified",
                        "path": str(self.path),
                    })
                    self._last_mtimes[str(self.path)] = current_mtime

            except OSError:
                pass

        elif self.recursive:
            current_files = {}
            for p in self.path.rglob("*"):
                if p.is_file():
                    try:
                        current_files[str(p)] = p.stat().st_mtime
                    except OSError:
                        pass

            # Check for new and modified files
            for path, mtime in current_files.items():
                if path not in self._last_mtimes:
                    changes.append({"type": "created", "path": path})
                elif mtime > self._last_mtimes[path]:
                    changes.append({"type": "modified", "path": path})

            # Check for deleted files
            for path in list(self._last_mtimes.keys()):
                if path not in current_files:
                    changes.append({"type": "deleted", "path": path})

            self._last_mtimes = current_files

        return changes

    def watch(self, duration: float = None):
        """Наблюдение в течение указанного времени"""
        self.start()
        start_time = time.time()

        while self._running:
            if duration and (time.time() - start_time) >= duration:
                break

            changes = self.check_changes()
            for change in changes:
                try:
                    self.callback(change)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            time.sleep(self.interval)

        self.stop()


class PeriodicWatcher(Watcher):
    """Периодический наблюдатель"""

    def __init__(self, interval: float, callback: Callable):
        self.interval = interval
        self.callback = callback
        self._running = False

    def start(self):
        """Запуск"""
        self._running = True
        logger.info(f"Started periodic watcher: {self.interval}s")

    def stop(self):
        """Остановка"""
        self._running = False
        logger.info("Stopped periodic watcher")

    def watch(self, duration: float = None):
        """Наблюдение"""
        self.start()
        start_time = time.time()

        while self._running:
            if duration and (time.time() - start_time) >= duration:
                break

            try:
                self.callback()
            except Exception as e:
                logger.error(f"Callback error: {e}")

            time.sleep(self.interval)

        self.stop()


class ResourceWatcher(Watcher):
    """Наблюдатель за ресурсами системы"""

    def __init__(self, callback: Callable, interval: float = 5.0):
        self.callback = callback
        self.interval = interval
        self._running = False

    def start(self):
        """Запуск"""
        self._running = True

    def stop(self):
        """Остановка"""
        self._running = False

    def watch(self, duration: float = None):
        """Наблюдение"""
        self.start()
        start_time = time.time()

        while self._running:
            if duration and (time.time() - start_time) >= duration:
                break

            try:
                import psutil
                self.callback({
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage("/").percent,
                })
            except ImportError:
                logger.warning("psutil not available")
                break
            except Exception as e:
                logger.error(f"Resource check error: {e}")

            time.sleep(self.interval)

        self.stop()


# Factory functions

def watch_file(path: str, callback: Callable, **kwargs):
    """Создание файлового наблюдателя"""
    watcher = FileWatcher(path, callback, **kwargs)
    return watcher


def watch_periodic(interval: float, callback: Callable):
    """Создание периодического наблюдателя"""
    return PeriodicWatcher(interval, callback)


def watch_resources(callback: Callable, interval: float = 5.0):
    """Создание наблюдателя ресурсов"""
    return ResourceWatcher(callback, interval)
