#!/usr/bin/env python3
"""
Многофазный AI-конвейер конвертации C++ → Haskell (Улучшенная версия v3)
Поддержка множественных AI провайдеров с параллелизацией и батчингом.
"""

import os
import re
import json
import time
import sys
import subprocess
import hashlib
import signal
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Protocol
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod
from enum import Enum

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

# Конфигурация из .env или默认值
CONFIG = {
    # Модели
    "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "cerebras_model": os.getenv("CEREBRAS_MODEL", "llama-3.3-70b"),
    "hyperbolic_model": os.getenv("HYPERBOLIC_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    "ollama_model": os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b"),
    "huggingface_model": os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
    
    # Параметры
    "max_tokens": int(os.getenv("MAX_TOKENS", "8192")),
    "temperature": float(os.getenv("TEMPERATURE", "0.05")),
    "max_workers": int(os.getenv("MAX_WORKERS", "4")),
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "retry_base_delay": float(os.getenv("RETRY_BASE_DELAY", "1.0")),
    
    # Валидация
    "validate_with_ghc": os.getenv("VALIDATE_WITH_GHC", "true").lower() == "true",
    
    # Логирование
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "log_file": os.getenv("LOG_FILE", "pipeline.log"),
}

# Настройка логирования
def setup_logging():
    """Настройка логирования с ротацией и уровнями"""
    logger = logging.getLogger("orchestration")
    logger.setLevel(getattr(logging, CONFIG["log_level"]))
    
    # Форматтер
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler
    try:
        file_handler = logging.FileHandler(CONFIG["log_file"])
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Не удалось создать file handler: {e}")
    
    return logger

logger = setup_logging()

# Загрузка .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().strip().split("\n"):
        if line and "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


# ============================================================================
# ТИПЫ ДАННЫХ (Dataclasses)
# ============================================================================

@dataclass
class AIRequest:
    """Запрос к AI провайдеру"""
    prompt: str
    model: str = "auto"
    max_tokens: int = 8192
    temperature: float = 0.05
    operation: str = "default"


@dataclass
class AIResponse:
    """Ответ от AI провайдера"""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    success: bool = True
    error: Optional[str] = None


@dataclass
class CacheEntry:
    """Кэш для сгенерированных файлов"""
    source_hash: str
    result: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class PipelineMetrics:
    """Метрики конвейера"""
    phase_durations: Dict[str, float] = field(default_factory=dict)
    api_calls_by_provider: Dict[str, int] = field(default_factory=dict)
    api_errors_by_provider: Dict[str, int] = field(default_factory=dict)
    rate_limits: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    
    # Примерная стоимость за 1M токенов (USD)
    COST_PER_MILLION = {
        "groq": 0.59,
        "cerebras": 0.60,
        "hyperbolic": 0.40,
        "gemini": 0.15,
        "ollama": 0.0,  # локальный
        "huggingface": 0.0,  # бесплатный лимит
    }

    def add_call(self, provider: str, tokens: int = 0, cost: float = 0.0):
        self.api_calls_by_provider[provider] = self.api_calls_by_provider.get(provider, 0) + 1
        self.total_tokens += tokens
        self.total_cost += cost

    def add_error(self, provider: str):
        self.api_errors_by_provider[provider] = self.api_errors_by_provider.get(provider, 0) + 1

    def to_dict(self) -> dict:
        return {
            "phase_durations": self.phase_durations,
            "api_calls": self.api_calls_by_provider,
            "api_errors": self.api_errors_by_provider,
            "rate_limits": self.rate_limits,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
        }


# ============================================================================
# ИНТЕРФЕЙС ДЛЯ ТЕСТИРУЕМОСТИ
# ============================================================================

class AIClientProtocol(Protocol):
    """Протокол AI клиента для тестирования и мокирования"""
    
    def call(self, prompt: str, model: str = "auto", max_tokens: int = 8192) -> str:
        """Выполнить одиночный запрос"""
        ...
    
    def call_batch(self, prompts: List[Dict], model: str = "auto") -> List[Dict]:
        """Выполнить батч запросов"""
        ...


class MockAIClient:
    """Mock AI клиент для тестирования"""
    
    def __init__(self, response: str = "mock response"):
        self.response = response
        self.call_count = 0
    
    def call(self, prompt: str, model: str = "auto", max_tokens: int = 8192) -> str:
        self.call_count += 1
        return self.response
    
    def call_batch(self, prompts: List[Dict], model: str = "auto") -> List[Dict]:
        return [{"operation": p.get("operation", "default"), "result": self.response} 
                for p in prompts]


# ============================================================================
# КЭШ
# ============================================================================

class FileCache:
    """Кэш результатов генерации"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = __import__("threading").Lock()
        self._memory_cache: Dict[str, CacheEntry] = {}
        logger.debug(f"Инициализирован кэш: {cache_dir}")

    def _get_key(self, source_path: str, operation: str) -> str:
        return hashlib.sha256(f"{operation}:{source_path}".encode()).hexdigest()[:16]

    def get(
        self, source_path: str, operation: str, source_content: str
    ) -> Optional[str]:
        key = self._get_key(source_path, operation)
        source_hash = hashlib.md5(source_content.encode()).hexdigest()

        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if entry.source_hash == source_hash:
                    logger.debug(f"Кэш hit: {source_path}:{operation}")
                    return entry.result

        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                if data.get("source_hash") == source_hash:
                    with self._lock:
                        self._memory_cache[key] = CacheEntry(
                            source_hash=source_hash, result=data["result"]
                        )
                    logger.debug(f"Кэш hit (файл): {source_path}:{operation}")
                    return data["result"]
            except json.JSONDecodeError as e:
                logger.warning(f"Ошибка чтения кэша {cache_file}: {e}")
            except Exception as e:
                logger.warning(f"Ошибка кэша: {e}")
        
        logger.debug(f"Кэш miss: {source_path}:{operation}")
        return None

    def set(self, source_path: str, operation: str, source_content: str, result: str):
        key = self._get_key(source_path, operation)
        source_hash = hashlib.md5(source_content.encode()).hexdigest()

        with self._lock:
            self._memory_cache[key] = CacheEntry(source_hash=source_hash, result=result)

        cache_file = self.cache_dir / f"{key}.json"
        try:
            cache_file.write_text(
                json.dumps(
                    {
                        "source_hash": source_hash,
                        "result": result,
                        "source_path": source_path,
                        "operation": operation,
                        "timestamp": time.time(),
                    }
                )
            )
        except Exception as e:
            logger.warning(f"Ошибка записи кэша: {e}")

    def clear(self):
        """Очистка кэша"""
        with self._lock:
            self._memory_cache.clear()
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except Exception as e:
                logger.warning(f"Ошибка удаления {f}: {e}")
        logger.info("Кэш очищен")


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

PROMPTS = {
    "cpp_to_haskell": """Ты - эксперт по конвертации C++ в Haskell.
Конвертируй следующий C++ код в чистый Haskell.

ВАЖНЫЕ ПРАВИЛА:
1. Используй Haskell 2010, без расширений
2. Типы C++ → Haskell:
   - int → Int
   - float → Double  
   - double → Double
   - bool → Bool
   - char → Char
   - std::string → Text
   - std::vector<a> → [a]
   - std::map<k,v> → Map k v
   - std::shared_ptr<a> → Maybe a
   - std::unique_ptr<a> → Maybe a
   - nullptr → Nothing
   - class → data type с record синтаксисом
   - public/private → не используй (Haskell все публичное)
   - virtual → не нужно (полиморфизм через type classes)
   - void → () (unit type)
   - const -> не нужен в Haskell
   - * (указатель) → Maybe или IO
   - & (reference) → var

3. Функции-члены класса → standalone функции или тип class
4. Конструкторы → mkName или similar factory functions
5. Деструкторы → не нужны (GC в Haskell)

Верни ТОЛЬКО Haskell код, без пояснений.

```cpp
{code}
```

Haskell:""",
    "sql_ddl": """Ты - эксперт по PostgreSQL.
Конвертируй C++ структуру в PostgreSQL DDL.

ПРАВИЛА:
1. Используй snake_case для имен таблиц и колонок
2. Типы:
   - char[N] → CHAR(N) или VARCHAR(N)
   - int → INTEGER
   - uint → INTEGER
   - long → BIGINT
   - float → REAL
   - double → DOUBLE PRECISION
   - bool → BOOLEAN
   - time_t → TIMESTAMP
   - date → DATE
   
3. Добавь PRIMARY KEY если есть ID или类似 поле
4. Добавь NOT NULL где логично
5. Добавь комментарии с оригинальным названием

Верни ТОЛЬКО SQL.

{struct_info}

SQL:""",
    "qml_convert": """Ты - эксперт по Qt → QML.
Конвертируй Qt C++ код в QML.

ПРАВИЛА:
1. QPushButton → Button
2. QLineEdit → TextField  
3. QLabel → Text
4. QTableWidget → TableView
5. QListWidget → ListView
6. QMainWindow → Window с MenuBar
7. QDialog → Dialog
8. setText() → text: "value"
9. setVisible() → visible: true/false
10. connect() → Connections или onClicked:

Верни ТОЛЬКО QML код.

```cpp
{code}
```

QML:""",
    "report_convert": """Ты - эксперт по конвертации отчётов.
Конвертируй Crystal Reports в JasperReports (JRXML), Pentaho (xaction), pdf-slave (YAML).

Для каждого формата верни:
1. jasper - JRXML код
2. pentaho - Pentaho xaction XML  
3. pdfslave - YAML конфигурация

Верни JSON с ключами jasper, pentaho, pdfslave.

```cpp
{code}
```

JSON:""",
}


# ============================================================================
# AI КЛИЕНТ
# ============================================================================

class AIClient:
    """Унифицированный AI клиент с множественными провайдерами"""

    def __init__(self, max_workers: int = 4):
        self.stats = {"calls": 0, "errors": 0, "rate_limits": 0, "by_provider": {}}
        self.max_workers = max_workers
        self._lock = __import__("threading").Lock()
        self.metrics = PipelineMetrics()
        self._init_all_providers()

    def _init_all_providers(self):
        logger.info("🔌 Инициализация AI провайдеров:")

        self.groq = None
        try:
            from groq import Groq

            key = os.getenv("GROQ_API_KEY")
            if key:
                self.groq = Groq(api_key=key)
                logger.info("   ✅ Groq")
        except ImportError:
            logger.warning("   ❌ Groq: библиотека не установлена")
        except Exception as e:
            logger.warning(f"   ❌ Groq: {e}")

        self.gemini = None
        try:
            from google import genai
            from google.genai import types

            key = os.getenv("GEMINI_API_KEY")
            if key:
                self.gemini = genai.Client(api_key=key)
                self.gemini_types = types
                logger.info("   ✅ Gemini")
        except ImportError:
            logger.warning("   ❌ Gemini: библиотека не установлена")
        except Exception as e:
            logger.warning(f"   ❌ Gemini: {e}")

        self.cerebras = None
        try:
            key = os.getenv("CEREBRAS_API_KEY")
            if key:
                from cerebras.cloud.sdk import Cerebras

                self.cerebras = Cerebras(api_key=key)
                logger.info("   ✅ Cerebras")
        except ImportError:
            logger.warning("   ❌ Cerebras: библиотека не установлена")
        except Exception as e:
            logger.warning(f"   ❌ Cerebras: {e}")

        self.hyperbolic = None
        try:
            key = os.getenv("HYPERBOLIC_API_KEY")
            if key:
                self.hyperbolic = {"api_key": key}
                logger.info("   ✅ Hyperbolic")
        except Exception as e:
            logger.warning(f"   ❌ Hyperbolic: {e}")

        self.huggingface = None
        try:
            key = os.getenv("HF_TOKEN")
            if key:
                self.huggingface = {"token": key}
                logger.info("   ✅ HuggingFace")
        except Exception as e:
            logger.warning(f"   ❌ HuggingFace: {e}")

        self.ollama = None
        try:
            import requests

            url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            r = requests.get(f"{url}/api/tags", timeout=2)
            if r.ok:
                models = [m["name"] for m in r.json().get("models", [])]
                self.ollama = {"url": url, "models": models}
                logger.info(f"   ✅ Ollama ({len(models)} моделей)")
        except Exception as e:
            logger.warning(f"   ⚠️ Ollama: недоступен - {e}")

        logger.info("")

    def _get_providers(self, task_type: str) -> list:
        if task_type in ("sql", "groq"):
            return ["groq", "cerebras", "hyperbolic", "gemini"]
        if task_type in ("haskell", "qml", "ollama"):
            if self.ollama:
                return ["ollama"]  # GPU Ollama is fastest
            return ["cerebras", "groq", "gemini"]
        if task_type in ("analysis", "gemini"):
            return ["gemini", "cerebras", "groq"]
        return ["groq", "cerebras", "gemini", "ollama"]

    def _exponential_backoff(self, attempt: int, base_delay: float = None) -> float:
        """Exponential backoff с jitter"""
        if base_delay is None:
            base_delay = CONFIG["retry_base_delay"]
        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
        logger.debug(f"Retry attempt {attempt + 1}, wait {delay:.2f}s")
        return min(delay, 60)  # max 60 seconds

    def call(self, prompt: str, model: str = "auto", max_tokens: int = None) -> str:
        """Выполнить запрос с retry логикой"""
        if max_tokens is None:
            max_tokens = CONFIG["max_tokens"]
            
        providers = self._get_providers(model)
        max_retries = CONFIG["max_retries"]
        
        last_error = None
        for provider in providers:
            for attempt in range(max_retries):
                try:
                    result = self._call_provider(provider, prompt, max_tokens)
                    if result:
                        return result
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    if "429" in str(e) or "rate_limit" in error_str or "rate_limit" in error_str:
                        with self._lock:
                            self.stats["rate_limits"] += 1
                            self.metrics.rate_limits += 1
                        logger.warning(f"   ⚠️ Rate limit {provider}, attempt {attempt + 1}/{max_retries}")
                        time.sleep(self._exponential_backoff(attempt))
                    elif "429" in error_str:  # HTTP 429
                        logger.warning(f"   ⚠️ HTTP 429 от {provider}, attempt {attempt + 1}/{max_retries}")
                        time.sleep(self._exponential_backoff(attempt))
                    else:
                        # Другие ошибки - пробуем следующий провайдер
                        logger.debug(f"   ⚠️ {provider}: {str(e)[:80]}")
                        break
        
        with self._lock:
            self.stats["errors"] += 1
        logger.error(f"Все провайдеры недоступны: {last_error}")
        return ""

    def call_batch(self, prompts: List[Dict], model: str = "auto") -> List[Dict]:
        """Параллельная обработка нескольких промптов"""
        results = [None] * len(prompts)

        def worker(idx: int, prompt: str, op: str) -> tuple:
            result = self.call(prompt, model)
            return idx, op, result

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for idx, p in enumerate(prompts):
                prompt = p.get("prompt", "")
                op = p.get("operation", "default")
                future = executor.submit(worker, idx, prompt, op)
                futures[future] = idx

            for future in as_completed(futures):
                try:
                    idx, op, result = future.result(timeout=120)
                    results[idx] = {"operation": op, "result": result}
                except Exception as e:
                    idx = futures[future]
                    results[idx] = {
                        "operation": prompts[idx].get("operation", "default"),
                        "result": "",
                        "error": str(e),
                    }
                    logger.error(f"Ошибка в батче {idx}: {e}")

        return results

    def _call_provider(self, provider: str, prompt: str, max_tokens: int) -> str:
        temperature = CONFIG["temperature"]
        
        if provider == "groq" and self.groq:
            time.sleep(0.5)
            resp = self.groq.chat.completions.create(
                model=CONFIG["groq_model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            self._record_call("groq", tokens=resp.usage.total_tokens if hasattr(resp, 'usage') else 0)
            return resp.choices[0].message.content or ""

        if provider == "cerebras" and self.cerebras:
            time.sleep(0.3)
            resp = self.cerebras.chat.completions.create(
                model=CONFIG["cerebras_model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            self._record_call("cerebras", tokens=resp.usage.total_tokens if hasattr(resp, 'usage') else 0)
            return resp.choices[0].message.content or ""

        if provider == "hyperbolic" and self.hyperbolic:
            import requests

            time.sleep(0.3)
            resp = requests.post(
                "https://api.hyperbolic.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.hyperbolic['api_key']}"},
                json={
                    "model": CONFIG["hyperbolic_model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                tokens = data.get('usage', {}).get('total_tokens', 0)
                self._record_call("hyperbolic", tokens=tokens)
                return data["choices"][0]["message"]["content"]

        if provider == "gemini" and self.gemini:
            time.sleep(1)
            resp = self.gemini.models.generate_content(
                model=CONFIG["gemini_model"],
                contents=prompt,
                config=self.gemini_types.GenerateContentConfig(
                    max_output_tokens=max_tokens, temperature=temperature
                ),
            )
            self._record_call("gemini")
            return resp.text or ""

        if provider == "ollama" and self.ollama:
            import requests

            resp = requests.post(
                f"{self.ollama['url']}/api/generate",
                json={
                    "model": CONFIG["ollama_model"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_ctx": 8192},
                },
                timeout=300,
            )
            if resp.ok:
                self._record_call("ollama")
                return resp.json().get("response", "")

        if provider == "huggingface" and self.huggingface:
            import requests

            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{CONFIG['huggingface_model']}",
                headers={"Authorization": f"Bearer {self.huggingface['token']}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
                timeout=60,
            )
            if resp.ok:
                self._record_call("huggingface")
                return resp.json()[0]["generated_text"]

        raise Exception(f"Provider {provider} not available")

    def _record_call(self, provider: str, tokens: int = 0):
        with self._lock:
            self.stats["calls"] += 1
            self.stats["by_provider"][provider] = (
                self.stats["by_provider"].get(provider, 0) + 1
            )
        
        # Метрики
        cost = (tokens / 1_000_000) * self.metrics.COST_PER_MILLION.get(provider, 0)
        self.metrics.add_call(provider, tokens=tokens, cost=cost)


# Fallback templates for when AI fails
FALLBACK_TEMPLATES = {
    "haskell": """module {name} where

import Data.Text (Text)
import Data.Maybe (Maybe(..))

-- Auto-generated from C++ struct
data {name} = {name}
    {{ {fields} }}
    deriving (Show, Eq)

-- Placeholder functions
{name} :: {name}
{name} = {name} {{ {defaults} }}
""",
    "sql": """-- {name}
CREATE TABLE IF NOT EXISTS {table_name} (
    id SERIAL PRIMARY KEY,
    {columns}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
}


# ============================================================================
# КОНВЕЙЕР
# ============================================================================

class ConversionPipeline:
    """Многофазный конвейер конвертации с улучшениями v3"""

    def __init__(self, project_path: str, output_path: str, max_workers: int = None):
        self.project_path = Path(project_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

        if max_workers is None:
            max_workers = CONFIG["max_workers"]
        self.max_workers = max_workers
        
        self.ai = AIClient(max_workers=max_workers)
        self.cache = FileCache(self.output_path / ".cache")
        self.metrics = self.ai.metrics
        
        # Graceful shutdown
        self._shutdown_requested = False
        self._setup_signal_handlers()

        # State for resume
        self.state_file = self.output_path / ".pipeline_state.json"
        self.state = self._load_state()

    def _setup_signal_handlers(self):
        """Настройка обработки сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.warning(f"Получен сигнал {sig_name}, сохраняю состояние...")
            self._shutdown_requested = True
            self._save_state()
            logger.info("Состояние сохранено. Выход.")
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except (ValueError, OSError) as e:
            logger.warning(f"Не удалось установить обработчик сигналов: {e}")

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except json.JSONDecodeError as e:
                logger.warning(f"Ошибка чтения state: {e}")
        return {
            "phase1_done": False,
            "phase2_done": False,
            "phase3_done": False,
            "phase4_done": False,
            "phase5_done": False,
            "last_class_idx": 0,
        }

    def _save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _log(self, msg: str, level: str = "info"):
        log_func = getattr(logger, level, logger.info)
        log_func(msg)

    def _bar(self, current: int, total: int, name: str = ""):
        if total == 0:
            return
        pct = (current / total) * 100
        filled = int(15 * current / total)
        bar = "█" * filled + "░" * (15 - filled)
        sys.stdout.write(f"\r[{name}] {bar} {pct:5.1f}%")
        sys.stdout.flush()

    def _extract_sql_queries(self, content: str) -> List[str]:
        """Извлечение SQL запросов из C++ кода"""
        queries = []

        # ODBC/Btrieve patterns
        patterns = [
            r'SQLExecDirect\([^,]+,\s*"([^"]+)"',
            r'SQLPrepare\([^,]+,\s*"([^"]+)"',
            r'execute\([^,]*\s*,\s*"([^"]+)"',
            r'cbExec\([^,]+,\s*"([^"]+)"',
            r'SQL\(["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            queries.extend(re.findall(pattern, content, re.IGNORECASE))

        return list(set(queries))

    def _extract_dependencies(self, content: str) -> List[str]:
        """Извлечение зависимостей (вызовов других классов/функций)"""
        deps = []

        # Class instantiations
        deps.extend(re.findall(r"\b(\w+)\s+(\w+)\s*;", content))

        # Method calls on objects
        deps.extend(re.findall(r"\b(\w+)\s*->\s*(\w+)\s*\(", content))
        deps.extend(re.findall(r"\b(\w+)\s*\.(\w+)\s*\(", content))

        return list(set([d[0] for d in deps if d[0] != "this"]))

    def _validate_haskell(self, content: str) -> bool:
        """Базовая валидация Haskell кода"""
        if not content or len(content) < 20:
            return False
        if "module" not in content and "import" not in content:
            return False
        return True

    def _validate_haskell_ghc(self, content: str) -> bool:
        """Валидация Haskell через GHC"""
        if not CONFIG["validate_with_ghc"]:
            return self._validate_haskell(content)
            
        try:
            result = subprocess.run(
                ["ghc", "-fno-code", "-e", "return ()"],
                input=content,
                capture_output=True,
                timeout=30,
                text=True
            )
            if result.returncode == 0:
                logger.debug("GHC валидация: OK")
                return True
            else:
                logger.debug(f"GHC валидация: ошибка - {result.stderr[:100]}")
                return False
        except FileNotFoundError:
            logger.debug("GHC не найден, используем базовую валидацию")
            return self._validate_haskell(content)
        except subprocess.TimeoutExpired:
            logger.warning("GHC валидация: timeout")
            return self._validate_haskell(content)
        except Exception as e:
            logger.warning(f"GHC валидация: {e}")
            return self._validate_haskell(content)

    def _validate_sql(self, content: str) -> bool:
        """Валидация SQL"""
        if not content or len(content) < 10:
            return False
        if "CREATE TABLE" not in content.upper():
            return False
        return True

    def _fallback_haskell(self, cls: dict) -> str:
        """Fallback шаблон для Haskell"""
        name = cls.get("name", "Unknown")
        fields = cls.get("fields", [])

        if isinstance(fields, list) and fields:
            field_strs = [
                f"{f.get('name', 'field')} :: {self._cpp_to_haskell_type(f.get('type', 'Int'))}"
                for f in fields[:10]
            ]
            defaults = [f.get("name", "field") for f in fields[:5]]
        else:
            field_strs = ["field1 :: Int"]
            defaults = ["0"]

        return FALLBACK_TEMPLATES["haskell"].format(
            name=name, fields=", ".join(field_strs), defaults=", ".join(defaults)
        )

    def _cpp_to_haskell_type(self, cpp_type: str) -> str:
        """Маппинг типов C++ → Haskell"""
        type_map = {
            "int": "Int",
            "long": "Int",
            "short": "Int",
            "uint": "Int",
            "unsigned": "Int",
            "float": "Double",
            "double": "Double",
            "bool": "Bool",
            "char": "Char",
            "string": "Text",
            "std::string": "Text",
            "void": "()",
        }
        cpp_type = cpp_type.strip().replace("*", "").replace("&", "").split()[-1]
        return type_map.get(cpp_type, "Int")

    # ==========================================================================
    # ФАЗА 1: Анализ
    # ==========================================================================
    def phase1_analyze(self, force: bool = False) -> dict:
        """Подробный анализ заголовочных файлов"""
        phase_start = time.time()
        self._log("📊 Фаза 1: Глубокий анализ проекта")

        out_file = self.output_path / "analysis.json"

        if not force and out_file.exists() and self.state.get("phase1_done"):
            analysis = json.loads(out_file.read_text())
            self._log(
                f"   Загружено из кэша: {len(analysis.get('classes', []))} классов"
            )
            return analysis

        src_dir = self.project_path / "Src"
        self._log("   Сканирование файлов...")

        all_classes = {}
        all_structs = {}
        all_includes = {}
        all_functions = {}
        sql_queries = []
        reports = []
        widgets = []
        btrieve_files = []

        for ext in ["*.h", "*.hpp", "*.cpp"]:
            for f in src_dir.rglob(ext):
                if not f.is_file():
                    continue
                
                if self._shutdown_requested:
                    self._log("Прерывание по сигналу", "warning")
                    break

                try:
                    content = f.read_text(errors="ignore")
                    rel = str(f.relative_to(self.project_path))

                    # Includes
                    includes = re.findall(r'#include\s+[<"]([^>"]+)[>"]', content)
                    if includes:
                        all_includes[rel] = includes

                    # SQL queries
                    queries = self._extract_sql_queries(content)
                    if queries:
                        sql_queries.extend([{"file": rel, "query": q} for q in queries])

                    # Classes with inheritance
                    for m in re.finditer(
                        r"class\s+(\w+)\s*[:{]\s*public\s+(\w+)", content
                    ):
                        cls_name = m.group(1)
                        parent = m.group(2)

                        # Extract methods from class body
                        class_body = content[m.start() : m.start() + 8000]
                        methods = re.findall(
                            r"(virtual\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)",
                            class_body,
                        )

                        deps = self._extract_dependencies(class_body)

                        all_classes[cls_name] = {
                            "name": cls_name,
                            "file": rel,
                            "type": "BUSINESS",
                            "parent": parent,
                            "methods": [
                                {"ret": m[1], "name": m[2], "params": m[3]}
                                for m in methods[:30]
                            ],
                            "dependencies": deps[:20],
                            "includes": includes[:10],
                        }

                    # Simple classes
                    for m in re.finditer(r"class\s+(\w+)\s*[:{]", content):
                        cls_name = m.group(1)
                        if cls_name not in all_classes:
                            all_classes[cls_name] = {
                                "name": cls_name,
                                "file": rel,
                                "type": "CLASS",
                                "parent": None,
                                "methods": [],
                                "dependencies": [],
                                "includes": includes[:10],
                            }

                    # Structs
                    for m in re.finditer(
                        r"struct\s+(\w+)\s*\{([^}]{5,2000})\}", content
                    ):
                        name = m.group(1)
                        body = m.group(2)
                        fields = re.findall(r"(\w+(?:\*|\&)?)\s+(\w+)\s*;", body)

                        is_btrieve = any(
                            x in body.lower()
                            for x in ["char", "int", "float", "double", "uint", "short"]
                        )

                        all_structs[name] = {
                            "name": name,
                            "file": rel,
                            "type": "DATA",
                            "fields": [
                                {"type": t.strip(), "name": n.strip()}
                                for t, n in fields[:30]
                            ],
                            "is_btrieve": is_btrieve,
                            "includes": includes[:10],
                        }

                        if is_btrieve:
                            btrieve_files.append(all_structs[name])

                    # Functions
                    for m in re.finditer(
                        r"(?:void|int|bool|float|double|string|auto)\s+(\w+)\s*\([^)]*\)",
                        content,
                    ):
                        fn_name = m.group(1)
                        if fn_name not in [
                            "if",
                            "for",
                            "while",
                            "switch",
                            "return",
                            "sizeof",
                        ]:
                            all_functions[fn_name] = {
                                "name": fn_name,
                                "file": rel,
                                "type": "FUNCTION",
                            }

                    # Qt widgets
                    qt_patterns = [
                        (r"class\s+(\w+)\s*:\s*public\s+QWidget", "QWidget"),
                        (r"class\s+(\w+)\s*:\s*public\s+QMainWindow", "QMainWindow"),
                        (r"class\s+(\w+)\s*:\s*public\s+QDialog", "QDialog"),
                        (r"class\s+(\w+)\s*:\s*public\s+QFrame", "QFrame"),
                        (r"class\s+(\w+)\s*:\s*public\s+QPushButton", "QPushButton"),
                        (r"class\s+(\w+)\s*:\s*public\s+QLineEdit", "QLineEdit"),
                        (r"class\s+(\w+)\s*:\s*public\s+QTableWidget", "QTableWidget"),
                    ]
                    for pattern, widget_type in qt_patterns:
                        if re.search(pattern, content):
                            widgets.append(
                                {
                                    "name": Path(rel).stem,
                                    "file": rel,
                                    "widget_type": widget_type,
                                    "includes": includes[:10],
                                }
                            )
                            break

                    # Crystal Reports
                    if re.search(r"CrystalReport|\.rpt|CRPE|CrpeExport", content, re.I):
                        reports.append(
                            {
                                "name": Path(rel).stem,
                                "file": rel,
                                "includes": includes[:10],
                            }
                        )

                except Exception as e:
                    logger.debug(f"Ошибка при анализе {f}: {e}")

        self._log(f"   Всего файлов: {len(all_includes)}")

        analysis = {
            "summary": {
                "total_files": len(all_includes),
                "total_classes": len(all_classes),
                "total_structs": len(all_structs),
                "total_functions": len(all_functions),
                "total_btrieve": len(btrieve_files),
                "total_reports": len(reports),
                "total_widgets": len(widgets),
                "total_sql_queries": len(sql_queries),
            },
            "classes": list(all_classes.values())[:1000],
            "structs": list(all_structs.values())[:500],
            "functions": list(all_functions.values())[:500],
            "btrieve_files": btrieve_files[:300],
            "reports": reports[:50],
            "qt_widgets": widgets[:100],
            "includes_map": dict(list(all_includes.items())[:200]),
            "sql_queries": sql_queries[:100],
        }

        out_file.write_text(json.dumps(analysis, ensure_ascii=False, indent=2))

        self._log(f"   Найдено:")
        self._log(f"     - Классов: {len(all_classes)}")
        self._log(f"     - Структур: {len(all_structs)}")
        self._log(f"     - Btrieve: {len(btrieve_files)}")
        self._log(f"     - SQL запросов: {len(sql_queries)}")

        self.state["phase1_done"] = True
        self._save_state()
        
        # Метрики
        self.metrics.phase_durations["phase1_analyze"] = time.time() - phase_start
        return analysis

    # ==========================================================================
    # ФАЗА 2: PostgreSQL - батчами
    # ==========================================================================
    def phase2_database(self, analysis: dict):
        """Конвертация Btrieve → PostgreSQL с батчами"""
        phase_start = time.time()
        self._log("\n🗄️ Фаза 2: Btrieve → PostgreSQL")

        schema_file = self.output_path / "schema.sql"

        if (
            schema_file.exists()
            and schema_file.stat().st_size > 500
            and self.state.get("phase2_done")
        ):
            self._log(f"   schema.sql уже есть")
            self.metrics.phase_durations["phase2_database"] = time.time() - phase_start
            return

        tables = analysis.get("btrieve_files", [])[:50]

        # Batch prompts
        batch_size = 5
        batched_prompts = []
        for i in range(0, len(tables), batch_size):
            batch = tables[i : i + batch_size]
            prompt = "Конвертируй ВСЕ структуры в PostgreSQL DDL. Верни SQL для каждой таблицы.\n\n"
            for bt in batch:
                prompt += (
                    f"Таблица: {bt['name']}, Поля: {json.dumps(bt.get('fields', []))}\n"
                )

            batched_prompts.append(
                {
                    "prompt": prompt,
                    "operation": "sql",
                    "tables": [b["name"] for b in batch],
                }
            )

        self._log(f"   Обрабатываем {len(batched_prompts)} батчей...")

        results = self.ai.call_batch(batched_prompts, "sql")

        sql_parts = []
        for r in results:
            if r.get("result"):
                cleaned = re.sub(r"```sql\n?", "", r["result"])
                cleaned = re.sub(r"```\n?", "", cleaned)
                sql_parts.append(cleaned)

        schema_file.write_text("\n\n".join(sql_parts))

        self.state["phase2_done"] = True
        self._save_state()
        self._log(f"\n   ✅ {len(sql_parts)} таблиц")
        
        # Метрики
        self.metrics.phase_durations["phase2_database"] = time.time() - phase_start

    # ==========================================================================
    # ФАЗА 3: Haskell - параллельно + fallback
    # ==========================================================================
    def phase3_haskell(self, analysis: dict):
        """Конвертация C++ → Haskell параллельно"""
        phase_start = time.time()
        self._log("\n⚙️ Фаза 3: C++ → Haskell")

        hs_dir = self.output_path / "src"
        hs_dir.mkdir(parents=True, exist_ok=True)

        classes = analysis.get("classes", [])[:10]
        start_idx = self.state.get("last_class_idx", 0)

        # Попробуем использовать tqdm если доступен
        try:
            from tqdm import tqdm
            iterator = tqdm(classes[start_idx:], desc="Haskell", unit="cls")
        except ImportError:
            iterator = classes[start_idx:]
            self._log("   (tqdm не установлен, используем простой прогресс)")

        for idx, cls in enumerate(iterator):
            if self._shutdown_requested:
                self._log("Прерывание по сигналу", "warning")
                break
            
            if hasattr(iterator, 'set_postfix'):
                iterator.set_postfix({"current": cls.get("name", "?")})
            else:
                self._bar(idx + 1, len(classes) - start_idx, "Haskell")

            source_path = cls["file"]
            cpp_path = self.project_path / source_path.replace(".h", ".cpp").replace(
                ".hpp", ".cpp"
            )
            content = ""

            for p in [cpp_path, self.project_path / source_path]:
                if p.exists():
                    try:
                        content = p.read_text(errors="ignore")[:3000]
                        break
                    except:
                        pass

            if not content:
                continue

            cached = self.cache.get(source_path, "haskell", content)
            if cached:
                (hs_dir / f"{cls['name']}.hs").write_text(cached)
                continue

            # Single call instead of batch
            prompt = PROMPTS["cpp_to_haskell"].format(code=content)
            result = self.ai.call(prompt, "haskell", 4096)

            if result:
                result = re.sub(r"```haskell\n?", "", result)
                result = re.sub(r"```\n?", "", result)

                if self._validate_haskell_ghc(result):
                    self.cache.set(source_path, "haskell", content, result)
                    (hs_dir / f"{cls['name']}.hs").write_text(result)
                else:
                    logger.warning(f"Валидация не пройдена для {cls['name']}, используем fallback")
                    fallback = self._fallback_haskell(cls)
                    (hs_dir / f"{cls['name']}.hs").write_text(fallback)
            else:
                fallback = self._fallback_haskell(cls)
                (hs_dir / f"{cls['name']}.hs").write_text(fallback)

        hs_count = len(list(hs_dir.glob("*.hs")))
        self.state["phase3_done"] = True
        self.state["last_class_idx"] = len(classes)
        self._save_state()
        
        if not hasattr(iterator, '__iter__') or hasattr(iterator, 'close'):
            sys.stdout.write("\n")
            
        self._log(f"   ✅ {hs_count} Haskell файлов")

        # Метрики
        self.metrics.phase_durations["phase3_haskell"] = time.time() - phase_start

    # ==========================================================================
    # ФАЗА 4: QML
    # ==========================================================================
    def phase4_qml(self, analysis: dict):
        """Конвертация Qt → QML"""
        phase_start = time.time()
        self._log("\n🖥️ Фаза 4: Qt → QML")

        qml_dir = self.output_path / "qml"
        qml_dir.mkdir(parents=True, exist_ok=True)

        widgets = analysis.get("qt_widgets", [])[:20]

        if not widgets:
            self._log("   Нет Qt виджетов для конвертации")
            self.state["phase4_done"] = True
            self._save_state()
            self.metrics.phase_durations["phase4_qml"] = time.time() - phase_start
            return

        # tqdm
        try:
            from tqdm import tqdm
            iterator = tqdm(widgets, desc="QML", unit="widget")
        except ImportError:
            iterator = widgets
            self._log("   (tqdm не установлен)")

        for i, w in enumerate(iterator):
            if self._shutdown_requested:
                self._log("Прерывание по сигналу", "warning")
                break

            src = self.project_path / w["file"]
            if not src.exists():
                continue

            try:
                content = src.read_text(errors="ignore")[:2000]
            except:
                continue

            prompt = PROMPTS["qml_convert"].format(code=content)
            result = self.ai.call(prompt, "qml", 2048)

            if result:
                result = re.sub(r"```qml\n?", "", result)
                result = re.sub(r"```\n?", "", result)
                (qml_dir / f"{w['name']}.qml").write_text(result)

        qml_count = len(list(qml_dir.glob("*.qml")))
        self.state["phase4_done"] = True
        self._save_state()
        
        if hasattr(iterator, 'close'):
            iterator.close()
            
        self._log(f"   ✅ {qml_count} QML файлов")

        # Метрики
        self.metrics.phase_durations["phase4_qml"] = time.time() - phase_start

    # ==========================================================================
    # ФАЗА 5: Reports
    # ==========================================================================
    def phase5_reports(self, analysis: dict):
        """Конвертация Crystal Reports"""
        phase_start = time.time()
        self._log("\n📄 Фаза 5: Crystal → Jasper/Pentaho/pdf-slave")

        dirs = {
            "jasper": self.output_path / "reports" / "jasper",
            "pentaho": self.output_path / "reports" / "pentaho",
            "pdfslave": self.output_path / "reports" / "pdfslave",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        reports = analysis.get("reports", [])[:15]

        # tqdm
        try:
            from tqdm import tqdm
            iterator = tqdm(reports, desc="Reports", unit="rpt")
        except ImportError:
            iterator = reports
            self._log("   (tqdm не установлен)")

        for i, rpt in enumerate(iterator):
            if self._shutdown_requested:
                self._log("Прерывание по сигналу", "warning")
                break

            src = self.project_path / rpt["file"]
            if not src.exists():
                continue

            try:
                content = src.read_text(errors="ignore")[:1500]
            except:
                continue

            prompt = PROMPTS["report_convert"].format(code=content)
            result = self.ai.call(prompt, "analysis", 4096)

            if result:
                try:
                    data = json.loads(result)
                    (dirs["jasper"] / f"{rpt['name']}.jrxml").write_text(
                        data.get("jasper", "")
                    )
                    (dirs["pentaho"] / f"{rpt['name']}.xaction").write_text(
                        data.get("pentaho", "")
                    )
                    (dirs["pdfslave"] / f"{rpt['name']}.yaml").write_text(
                        data.get("pdfslave", "")
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка парсинга JSON для {rpt['name']}: {e}")
                except Exception as e:
                    logger.warning(f"Ошибка записи отчёта {rpt['name']}: {e}")

        self.state["phase5_done"] = True
        self._save_state()
        
        if hasattr(iterator, 'close'):
            iterator.close()
            
        self._log(f"   ✅ {len(reports)} отчётов")

        # Метрики
        self.metrics.phase_durations["phase5_reports"] = time.time() - phase_start

    # ==========================================================================
    # Генерация cabal
    # ==========================================================================
    def _generate_cabal(self):
        """Генерация project.cabal"""
        phase_start = time.time()
        
        cabal = """cabal-version: 3.0
name:          converted-project
version:       0.1.0.0
build-type:    Simple

executable converted-project
  main-is:          Main.hs
  hs-source-dirs:   src
  default-language: Haskell2010
  ghc-options:      -Wall
  build-depends:
      base >= 4.14 && < 5
    , text >= 2.0
    , containers >= 0.6
    , time >= 1.9
"""
        (self.output_path / "project.cabal").write_text(cabal)
        
        self.metrics.phase_durations["generate_cabal"] = time.time() - phase_start
        logger.info("   ✅ project.cabal создан")

    def _validate_all_haskell(self) -> bool:
        """Валидация всех Haskell файлов"""
        hs_dir = self.output_path / "src"
        if not hs_dir.exists():
            return False

        valid = True
        for hs_file in hs_dir.glob("*.hs"):
            content = hs_file.read_text()
            if not self._validate_haskell_ghc(content):
                self._log(f"   ⚠️ Невалидный: {hs_file.name}", "warning")
                valid = False
        return valid

    # ==========================================================================
    # ЗАПУСК
    # ==========================================================================
    def run(self, force: bool = False):
        total_start = time.time()
        
        self._log("🚀 Многофазный AI-конвейер C++ → Haskell (v3)")
        self._log(f"   Проект: {self.project_path}")
        self._log(f"   Вывод: {self.output_path}")
        self._log(f"   Workers: {self.max_workers}")
        self._log(f"   Max retries: {CONFIG['max_retries']}")

        try:
            analysis = self.phase1_analyze(force=force)
            
            if not self._shutdown_requested:
                self.phase2_database(analysis)
            
            if not self._shutdown_requested:
                self.phase3_haskell(analysis)
            
            if not self._shutdown_requested:
                self.phase4_qml(analysis)
            
            if not self._shutdown_requested:
                self.phase5_reports(analysis)
            
            if not self._shutdown_requested:
                self._generate_cabal()

            # Validate
            self._log("\n🔍 Валидация...")
            if self._validate_all_haskell():
                self._log("   ✅ Haskell валиден")
            else:
                self._log("   ⚠️ Некоторые Haskell файлы невалидны", "warning")

            # Validate SQL
            schema = self.output_path / "schema.sql"
            if schema.exists():
                content = schema.read_text()
                if self._validate_sql(content):
                    self._log("   ✅ SQL валиден")

            print()
            self._log("📊 Статистика AI:")
            for provider, count in self.ai.stats["by_provider"].items():
                self._log(f"   {provider}: {count} вызовов")
            self._log(f"   Всего: {self.ai.stats['calls']} вызовов")
            self._log(f"   Ошибок: {self.ai.stats['errors']}")
            self._log(f"   Rate limits: {self.ai.stats['rate_limits']}")

            # Метрики
            total_duration = time.time() - total_start
            self.metrics.phase_durations["total"] = total_duration
            
            self._log("\n📈 Метрики:")
            self._log(f"   Общее время: {total_duration:.1f}s")
            for phase, duration in self.metrics.phase_durations.items():
                if phase != "total":
                    self._log(f"   - {phase}: {duration:.1f}s")
            
            if self.metrics.total_cost > 0:
                self._log(f"   Примерная стоимость API: ${self.metrics.total_cost:.4f}")
            
            # Сохраняем метрики
            metrics_file = self.output_path / "metrics.json"
            metrics_file.write_text(json.dumps(self.metrics.to_dict(), indent=2))
            
            self._log("\n✅ Конвейер завершён!")

        except KeyboardInterrupt:
            self._log("\n⚠️ Прервано, состояние сохранено", "warning")
            self._save_state()
        except Exception as e:
            self._log(f"\n❌ Ошибка: {e}", "error")
            import traceback
            traceback.print_exc()
            self._save_state()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-path", default="/home/domini/src/petr/test2/OpenPapyrus"
    )
    parser.add_argument("--output-path", default="/home/domini/src/petr/test2/Surypus2")
    parser.add_argument("--workers", type=int, default=None, help="Max parallel workers")
    parser.add_argument("--force", action="store_true", help="Force re-run all phases")
    parser.add_argument("--log-level", default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    if args.log_level:
        CONFIG["log_level"] = args.log_level
        logger.setLevel(getattr(logging, args.log_level))

    pipeline = ConversionPipeline(
        args.project_path, args.output_path, max_workers=args.workers
    )
    pipeline.run(force=args.force)