```python
"""File utilities for pipeline"""

import os
import shutil
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("orchestration.file_utils")


def ensure_dir(path: str) -> Path:
    """Ensure directory exists"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def copy_file(src: str, dst: str, create_dirs: bool = True) -> bool:
    """Copy file with error handling"""
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            logger.warning(f"Source file not found: {src}")
            return False
        
        if create_dirs:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src_path, dst_path)
        return True
        
    except Exception as e:
        logger.error(f"Copy failed: {e}")
        return False


def move_file(src: str, dst: str, create_dirs: bool = True) -> bool:
    """Move file with error handling"""
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return False
        
        if create_dirs:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(src_path), str(dst_path))
        return True
        
    except Exception as e:
        logger.error(f"Move failed: {e}")
        return False


def delete_file(path: str) -> bool:
    """Delete file"""
    try:
        Path(path).unlink()
        return True
    except Exception:
        return False


def delete_dir(path: str) -> bool:
    """Delete directory"""
    try:
        shutil.rmtree(path)
        return True
    except Exception:
        return False


def get_file_hash(path: str, algorithm: str = "sha256") -> Optional[str]:
    """Get file hash"""
    try:
        path = Path(path)
        
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha1":
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()
        
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
        
    except Exception as e:
        logger.error(f"Hash failed: {e}")
        return None


def get_dir_size(path: str) -> int:
    """Get directory size in bytes"""
    total = 0
    
    for entry in Path(path).rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    
    return total


def find_files(
    directory: str,
    pattern: str = "*",
    recursive: bool = True,
    exclude_dirs: List[str] = None,
) -> List[Path]:
    """Find files matching pattern"""
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return []
    
    exclude = exclude_dirs or [".git", "__pycache__", ".cache", "node_modules"]
    
    if recursive:
        files = dir_path.rglob(pattern)
    else:
        files = dir_path.glob(pattern)
    
    return [
        f for f in files 
        if f.is_file() and not any(ex in f.parts for ex in exclude)
    ]


def get_file_info(path: str) -> Dict[str, Any]:
    """Get file information"""
    p = Path(path)
    
    if not p.exists():
        return {}
    
    stat = p.stat()
    
    return {
        "name": p.name,
        "path": str(p),
        "size": stat.st_size,
        "size_kb": stat.st_size / 1024,
        "size_mb": stat.st_size / 1024 / 1024,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "extension": p.suffix,
    }


def read_lines(path: str, limit: int = None) -> List[str]:
    """Read file lines"""
    p = Path(path)
    
    if not p.exists():
        return []
    
    lines = p.read_text().splitlines()
    
    if limit:
        lines = lines[:limit]
    
    return lines


def write_lines(path: str, lines: List[str], append: bool = False):
    """Write lines to file"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    mode = "a" if append else "w"
    
    with open(p, mode) as f:
        f.write("\n".join(lines))
        f.write("\n")


def glob_match(path: str, patterns: List[str]) -> bool:
    """Check if path matches any glob pattern"""
    from fnmatch import fnmatch
    
    for pattern in patterns:
        if fnmatch(path, pattern):
            return True
    
    return False


class FileWatcher:
    """Watch files for changes"""
    
    def __init__(self, directory: str, patterns: List[str] = None):
        self.directory = Path(directory)
        self.patterns = patterns or ["*"]
        self.last_state: Dict[str, float] = {}
    
    def get_changed(self) -> List[Path]:
        """Get changed files since last check"""
        changed = []
        
        for file in find_files(str(self.directory), recursive=True):
            mtime = file.stat().st_mtime
            
            if str(file) not in self.last_state:
                changed.append(file)
            elif mtime > self.last_state[str(file)]:
                changed.append(file)
            
            self.last_state[str(file)] = mtime
        
        return changed


class TempFileManager:
    """Manage temporary files"""
    
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.created_files: List[Path] = []
    
    def create_temp(self, prefix: str = "tmp", suffix: str = "") -> Path:
        """Create temporary file"""
        import uuid
        
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}{suffix}"
        temp_path = self.temp_dir / filename
        
        temp_path.touch()
        self.created_files.append(temp_path)
        
        return temp_path
    
    def cleanup(self):
        """Clean up all temporary files"""
        for f in self.created_files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        
        self.created_files = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()
