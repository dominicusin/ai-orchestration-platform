"""Pipeline watchers for file monitoring"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Callable

logger = logging.getLogger("orchestration.watchers")


class FileWatcher:
    """Watch files for changes"""
    
    def __init__(self, path: str, callback: Callable):
        self.path = Path(path)
        self.callback = callback
        self.last_mtime = {}
    
    def check(self):
        """Check for changes"""
        if not self.path.exists():
            return
        
        for file in self.path.rglob("*"):
            if not file.is_file():
                continue
            
            mtime = file.stat().st_mtime
            key = str(file)
            
            if key not in self.last_mtime:
                self.last_mtime[key] = mtime
                continue
            
            if mtime > self.last_mtime[key]:
                self.last_mtime[key] = mtime
                self.callback(file)


class WatcherManager:
    """Manage watchers"""
    
    def __init__(self):
        self.watchers = []
    
    def add(self, watcher: FileWatcher):
        self.watchers.append(watcher)
    
    def check_all(self):
        for watcher in self.watchers:
            watcher.check()
