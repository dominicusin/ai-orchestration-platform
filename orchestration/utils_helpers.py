"""
Utility helpers
Вспомогательные утилиты
"""

import os
from pathlib import Path
from typing import Any


def get_env(key: str, default: Any = None, required: bool = False) -> Any:
    """Получение переменной окружения"""
    value = os.environ.get(key, default)
    if required and value is None:
        raise ValueError(f"Required env variable {key} is not set")
    return value


def set_env(key: str, value: str):
    """Установка переменной окружения"""
    os.environ[key] = value


def get_project_root() -> Path:
    """Получение корня проекта"""
    current = Path(__file__).resolve()
    return current.parent.parent


def get_config_dir() -> Path:
    """Получение директории конфигов"""
    return get_project_root() / "config"


def ensure_config_dir():
    """Создание директории конфигов"""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_version() -> str:
    """Получение версии"""
    try:
        from orchestration import __version__
        return __version__
    except ImportError:
        return "0.0.0"


def is_debug() -> bool:
    """Проверка debug режима"""
    return os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def is_production() -> bool:
    """Проверка production режима"""
    env = os.environ.get("ENV", "development").lower()
    return env == "production"


def get_hostname() -> str:
    """Получение имени хоста"""
    return os.environ.get("HOSTNAME", "localhost")


def get_pid() -> int:
    """Получение PID процесса"""
    return os.getpid()


def get_cpu_count() -> int:
    """Получение количества CPU"""
    return os.cpu_count() or 1


def get_memory_limit() -> int | None:
    """Получение лимита памяти в байтах"""
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        return soft if soft != resource.RLIM_INFINITY else None
    except Exception:
        return None


def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """Обрезание текста"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def deep_get(dictionary: dict, path: str, default: Any = None) -> Any:
    """Получение значения по пути"""
    keys = path.split(".")
    value = dictionary
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        if value is None:
            return default
    return value


def deep_set(dictionary: dict, path: str, value: Any):
    """Установка значения по пути"""
    keys = path.split(".")
    current = dictionary
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def merge_dicts(*dicts: dict) -> dict:
    """Объединение словарей"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Выпрямление словаря"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: list, chunk_size: int) -> list:
    """Разбиение списка на чанки"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def unique_list(lst: list) -> list:
    """Уникальный список с сохранением порядка"""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Декоратор для повтора при ошибке"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


class LazyLoader:
    """Ленивая загрузка"""

    def __init__(self, loader: callable):
        self._loader = loader
        self._loaded = None

    def get(self):
        """Получение значения"""
        if self._loaded is None:
            self._loaded = self._loader()
        return self._loaded


class ConfigProxy:
    """Прокси для конфига"""

    def __init__(self, config: dict):
        self._config = config

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения"""
        return self._config.get(key, default)

    def __getattr__(self, key: str) -> Any:
        return self._config.get(key)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]
