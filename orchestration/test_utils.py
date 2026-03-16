"""Test utilities and helpers"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """Test result"""
    name: str
    passed: bool
    duration: float
    error: Optional[str] = None


class TestRunner:
    """Test runner for pipeline components"""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
    async def run_async_test(self, name: str, test_func) -> TestResult:
        """Run async test"""
        import time
        
        start = time.time()
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            
            return TestResult(
                name=name,
                passed=True,
                duration=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                duration=time.time() - start,
                error=str(e),
            )
    
    def run_sync_test(self, name: str, test_func) -> TestResult:
        """Run sync test"""
        import time
        
        start = time.time()
        
        try:
            test_func()
            
            return TestResult(
                name=name,
                passed=True,
                duration=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                name=name,
                passed=False,
                duration=time.time() - start,
                error=str(e),
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "total_duration": sum(r.duration for r in self.results),
        }


class MockAIProvider:
    """Mock AI provider for testing"""
    
    def __init__(self, response: str = "Test response"):
        self.response = response
        self.call_count = 0
    
    async def call(self, prompt: str, mode: str, max_tokens: int) -> str:
        self.call_count += 1
        return self.response
    
    async def call_batch(self, prompts: List[Dict]) -> List[Dict]:
        self.call_count += len(prompts)
        return [{"result": self.response} for _ in prompts]


class MockCache:
    """Mock cache for testing"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.get_count = 0
        self.set_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        self.get_count += 1
        return self.data.get(key)
    
    def set(self, key: str, value: Any):
        self.set_count += 1
        self.data[key] = value
    
    def clear(self):
        self.data = {}
    
    def get_stats(self) -> Dict:
        return {
            "size": len(self.data),
            "gets": self.get_count,
            "sets": self.set_count,
        }


class MockFileSystem:
    """Mock file system for testing"""
    
    def __init__(self):
        self.files: Dict[str, str] = {}
    
    def write(self, path: str, content: str):
        self.files[path] = content
    
    def read(self, path: str) -> str:
        return self.files.get(path, "")
    
    def exists(self, path: str) -> bool:
        return path in self.files
    
    def delete(self, path: str):
        if path in self.files:
            del self.files[path]
    
    def list(self, pattern: str = "*") -> List[str]:
        return list(self.files.keys())


# Test fixtures
def create_test_config() -> Dict[str, Any]:
    """Create test configuration"""
    return {
        "project_path": "./test_project",
        "output_path": "./test_output",
        "max_workers": 2,
        "default_provider": "mock",
        "log_format": "text",
    }


def create_test_pipeline_state() -> Dict[str, Any]:
    """Create test pipeline state"""
    return {
        "project_path": "./test_project",
        "output_path": "./test_output",
        "started_at": datetime.now().isoformat(),
        "status": "running",
        "phase1_done": False,
        "phase2_done": False,
        "phase3_done": False,
        "phase4_done": False,
        "phase5_done": False,
        "last_class_idx": 0,
    }


def create_test_analysis() -> Dict[str, Any]:
    """Create test analysis data"""
    return {
        "summary": {
            "total_classes": 10,
            "total_structs": 5,
            "total_btrieve": 3,
            "total_reports": 2,
            "total_widgets": 4,
            "total_sql_queries": 6,
        },
        "classes": [
            {"name": "TestClass", "file": "test.h", "methods": ["method1", "method2"]}
        ],
        "structs": [
            {"name": "TestStruct", "fields": [{"type": "int", "name": "id"}]}
        ],
    }


# Assertion helpers
def assert_file_exists(path: Path):
    """Assert file exists"""
    assert path.exists(), f"File not found: {path}"


def assert_file_contains(path: Path, text: str):
    """Assert file contains text"""
    content = path.read_text()
    assert text in content, f"File {path} does not contain '{text}'"


def assert_json_valid(text: str):
    """Assert valid JSON"""
    import json
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON: {e}")


# Async test utilities
async def run_with_timeout(coro, timeout: float = 5.0):
    """Run coroutine with timeout"""
    return await asyncio.wait_for(coro, timeout=timeout)


# Performance testing
class PerformanceTimer:
    """Timer for performance testing"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        import time
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
