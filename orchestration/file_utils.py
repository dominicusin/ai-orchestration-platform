"""
File utilities
Утилиты для работы с файлами
"""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path


def ensure_dir(path: str) -> Path:
    """Создание директории если не существует"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_parent_dir(file_path: str) -> Path:
    """Создание родительской директории"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p.parent


def safe_write(file_path: str, content: str | bytes, mode: str = "w"):
    """Безопасная запись файла"""
    ensure_parent_dir(file_path)

    if mode == "wb" or isinstance(content, bytes):
        with open(file_path, "wb") as f:
            f.write(content)
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


def safe_read(file_path: str, mode: str = "r") -> str | bytes:
    """Безопасное чтение файла"""
    if mode == "rb":
        with open(file_path, "rb") as f:
            return f.read()
    else:
        with open(file_path, encoding="utf-8") as f:
            return f.read()


def get_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Получение хеша файла"""
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_dir_size(path: str) -> int:
    """Получение размера директории в байтах"""
    total = 0
    for entry in Path(path).rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def copy_tree(src: str, dst: str, ignore_patterns: list = None) -> None:
    """Копирование дерева директорий"""
    src_path = Path(src)
    dst_path = Path(dst)

    if ignore_patterns:
        ignore = shutil.ignore_patterns(*ignore_patterns)
    else:
        ignore = None

    shutil.copytree(src_path, dst_path, ignore=ignore, dirs_exist_ok=True)


def move_tree(src: str, dst: str) -> None:
    """Перемещение дерева директорий"""
    shutil.move(src, dst)


def clean_dir(path: str, keep_patterns: list = None) -> int:
    """Очистка директории"""
    removed = 0
    path_obj = Path(path)

    if not path_obj.exists():
        return 0

    for item in path_obj.iterdir():
        if keep_patterns and any(item.match(p) for p in keep_patterns):
            continue

        if item.is_file():
            item.unlink()
            removed += 1
        elif item.is_dir():
            shutil.rmtree(item)
            removed += 1

    return removed


def find_files(
    directory: str,
    pattern: str = "*",
    recursive: bool = True,
) -> list[Path]:
    """Поиск файлов по паттерну"""
    path = Path(directory)

    if recursive:
        return list(path.rglob(pattern))
    else:
        return list(path.glob(pattern))


def get_temp_dir(prefix: str = "orchestration_") -> Path:
    """Получение временной директории"""
    return Path(tempfile.mkdtemp(prefix=prefix))


def get_temp_file(suffix: str = "", prefix: str = "orchestration_") -> Path:
    """Получение временного файла"""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return Path(path)


class FileLock:
    """Блокировка файла"""

    def __init__(self, lock_file: str):
        self.lock_file = Path(lock_file)
        self._lock = None

    def __enter__(self):
        while self.lock_file.exists():
            import time
            time.sleep(0.1)
        self.lock_file.touch()
        return self

    def __exit__(self, *args):
        if self.lock_file.exists():
            self.lock_file.unlink()


def atomic_write(file_path: str, content: str | bytes):
    """Атомарная запись файла"""
    path = Path(file_path)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        safe_write(str(temp_path), content)
        temp_path.replace(path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def watch_file(file_path: str, callback: callable):
    """Наблюдение за изменением файла (polling)"""
    import time
    mtime = os.path.getmtime(file_path)

    while True:
        time.sleep(1)
        new_mtime = os.path.getmtime(file_path)
        if new_mtime != mtime:
            mtime = new_mtime
            callback(file_path)
