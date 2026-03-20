"""Watcher utilities"""

import time
from typing import Callable, Dict, List
from pathlib import Path


class FileWatcher:
    """Watch files for changes"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.callbacks: List[Callable] = []
        self.file_mtimes: Dict[str, float] = {}
    
    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)
    
    def watch(self, paths: List[str]):
        for path in paths:
            p = Path(path)
            if p.exists():
                self.file_mtimes[str(p)] = p.stat().st_mtime
    
    def check(self) -> List[str]:
        changed = []
        for path, last_mtime in list(self.file_mtimes.items()):
            p = Path(path)
            if p.exists():
                mtime = p.stat().st_mtime
                if mtime > last_mtime:
                    changed.append(path)
                    self.file_mtimes[path] = mtime
        return changed
    
    def run(self, duration: float = None):
        start = time.time()
        while True:
            changed = self.check()
            for path in changed:
                for callback in self.callbacks:
                    callback(path)
            time.sleep(self.interval)
            if duration and time.time() - start > duration:
                break
