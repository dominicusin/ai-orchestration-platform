"""
Structured logging utilities
Поддержка JSON логов для парсинга (Datadog, Grafana, ELK).
"""

import os
import sys
import json
import logging
import traceback
import threading
from datetime import datetime
from typing import Any, Dict
from enum import Enum


class LogFormat(Enum):
    TEXT = "text"
    JSON = "json"
    PRETTY = "pretty"


class StructuredFormatter(logging.Formatter):
    """Форматтер для структурированных JSON логов"""
    
    def __init__(self, format_type: LogFormat = LogFormat.JSON):
        super().__init__()
        self.format_type = format_type
        self._lock = threading.Lock()
    
    def format(self, record: logging.LogRecord) -> str:
        # Создаём базовую структуру
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем exception info если есть
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Добавляем extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Добавляем context если есть
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        if self.format_type == LogFormat.JSON:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        elif self.format_type == LogFormat.PRETTY:
            return json.dumps(log_data, ensure_ascii=False, indent=2, default=str)
        else:
            # Text format
            return (
                f"{log_data['timestamp']} "
                f"[{log_data['level']}] "
                f"{log_data['logger']}: "
                f"{log_data['message']}"
            )


class ContextFilter(logging.Filter):
    """Фильтр для добавления контекста ко всем логам"""
    
    def __init__(self, context: Dict[str, Any] = None):
        super().__init__()
        self._context = context or {}
        self._lock = threading.Lock()
    
    def filter(self, record: logging.LogRecord) -> bool:
        with self._lock:
            record.context = self._context.copy()
        return True
    
    def update_context(self, **kwargs):
        with self._lock:
            self._context.update(kwargs)


class PipelineLogger:
    """
    Специализированный логгер для pipeline с поддержкой:
    - Structured JSON logging
    - Context (run_id, phase, etc.)
    - Rotation
    - Multiple outputs
    """
    
    def __init__(
        self,
        name: str = "orchestration",
        log_file: str = "pipeline.log",
        log_level: str = "INFO",
        format_type: LogFormat = LogFormat.JSON,
        context: Dict[str, Any] = None,
    ):
        self.name = name
        self.log_file = log_file
        self.format_type = format_type
        self._context = context or {}
        
        # Создаём logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers = []
        
        # Форматтер
        formatter = StructuredFormatter(format_type)
        
        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        self.logger.addHandler(console)
        
        # File handler с ротацией
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Не удалось создать file handler: {e}")
        
        # Context filter
        self._context_filter = ContextFilter(self._context)
        self.logger.addFilter(self._context_filter)
    
    def set_context(self, **kwargs):
        """Обновление контекста"""
        self._context_filter.update_context(**kwargs)
        self._context.update(kwargs)
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra={"extra": kwargs} if kwargs else {})
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra={"extra": kwargs} if kwargs else {})
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra={"extra": kwargs} if kwargs else {})
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra={"extra": kwargs} if kwargs else {})
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra={"extra": kwargs} if kwargs else {})
    
    def log_phase(self, phase: str, status: str, **kwargs):
        """Логирование этапа pipeline"""
        self.info(
            f"Phase {phase}: {status}",
            phase=phase,
            status=status,
            **kwargs
        )
    
    def log_metric(self, name: str, value: Any, **kwargs):
        """Логирование метрики"""
        self.info(
            f"Metric {name}={value}",
            metric=name,
            value=value,
            **kwargs
        )
    
    def log_ai_call(
        self,
        provider: str,
        model: str,
        latency: float,
        tokens: int = 0,
        success: bool = True,
        **kwargs
    ):
        """Логирование вызова AI"""
        self.info(
            f"AI call to {provider}: {'success' if success else 'failed'}",
            provider=provider,
            model=model,
            latency_ms=round(latency * 1000, 2),
            tokens=tokens,
            success=success,
            **kwargs
        )


def setup_logging(
    name: str = "orchestration",
    log_file: str = "pipeline.log",
    log_level: str = "INFO",
    format_type: LogFormat = LogFormat.JSON,
    context: Dict[str, Any] = None,
) -> PipelineLogger:
    """
    Настройка логирования
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        log_level: Уровень логирования
        format_type: Формат логов (text/json/pretty)
        context: Начальный контекст
        
    Returns:
        PipelineLogger instance
    """
    # Загружаем из .env
    log_file = os.getenv("LOG_FILE", log_file)
    log_level = os.getenv("LOG_LEVEL", log_level)
    format_str = os.getenv("LOG_FORMAT", "json").lower()
    
    if format_str == "json":
        format_type = LogFormat.JSON
    elif format_str == "pretty":
        format_type = LogFormat.PRETTY
    else:
        format_type = LogFormat.TEXT
    
    return PipelineLogger(
        name=name,
        log_file=log_file,
        log_level=log_level,
        format_type=format_type,
        context=context,
    )
