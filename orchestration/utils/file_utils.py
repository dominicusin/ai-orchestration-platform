"""File utilities"""

import shutil
from pathlib import Path


def ensure_dir(path: str) -> Path:
    """Ensure directory exists"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_files(path: str, pattern: str = "*", recursive: bool = False) -> list[str]:
    """List files in directory"""
    p = Path(path)
    if recursive:
        return [str(f) for f in p.rglob(pattern) if f.is_file()]
    return [str(f) for f in p.glob(pattern) if f.is_file()]


def read_text(path: str) -> str:
    """Read text file"""
    return Path(path).read_text()


def write_text(path: str, content: str):
    """Write text file"""
    ensure_dir(str(Path(path).parent))
    Path(path).write_text(content)


def copy(src: str, dst: str):
    """Copy file"""
    ensure_dir(str(Path(dst).parent))
    shutil.copy2(src, dst)


def move(src: str, dst: str):
    """Move file"""
    ensure_dir(str(Path(dst).parent))
    shutil.move(src, dst)


def delete(path: str):
    """Delete file or directory"""
    p = Path(path)
    if p.is_file():
        p.unlink()
    elif p.is_dir():
        shutil.rmtree(p)


def get_size(path: str) -> int:
    """Get file size in bytes"""
    return Path(path).stat().st_size


def exists(path: str) -> bool:
    """Check if path exists"""
    return Path(path).exists()
