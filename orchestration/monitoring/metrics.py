"""
Monitoring: Prometheus metrics, OpenTelemetry tracing
"""

import os
import time
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("orchestration.monitoring")


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Базовый класс метрики"""
    name: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class InMemoryMetrics:
    """In-memory хранилище метрик для простоты"""
    
    def __init__(self):
        self._metrics: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        self._histograms: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def increment(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Инкремент счётчика"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value
    
    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Установка gauge"""
        key = self._make_key(name, labels)
        with self._lock:
            self._metrics[key] = value
    
    def histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Запись в гистограмму"""
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_prometheus_format(self) -> str:
        """Экспорт в Prometheus format"""
        lines = []
        with self._lock:
            # Gauges
            for key, value in self._metrics.items():
                lines.append(f"{key} {value}")
            
            # Counters
            for key, value in self._counters.items():
                lines.append(f"{key}_total {value}")
            
            # Histograms
            for key, values in self._histograms.items():
                if values:
                    lines.append(f"{key}_sum {sum(values)}")
                    lines.append(f"{key}_count {len(values)}")
                    lines.append(f"{key}_avg {sum(values)/len(values)}")
        
        return "\n".join(lines)


class PrometheusExporter:
    """Prometheus /metrics endpoint"""
    
    def __init__(self, port: int = 9090):
        self.port = port
        self._metrics = InMemoryMetrics()
        self._server = None
    
    @property
    def metrics(self) -> InMemoryMetrics:
        return self._metrics
    
    def start(self):
        """Запуск HTTP сервера для /metrics"""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading
            
            class MetricsHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == "/metrics":
                        self.send_response(200)
                        self.send_header("Content-Type", "text/plain")
                        self.end_headers()
                        self.wfile.write(
                            self._metrics.get_prometheus_format().encode()
                        )
                    elif self.path == "/health":
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(b'{"status": "ok"}')
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, format, *args):
                    pass  # Suppress logging
            
            self._server = HTTPServer(("0.0.0.0", self.port), MetricsHandler)
            thread = threading.Thread(target=self._server.serve_forever)
            thread.daemon = True
            thread.start()
            logger.info(f"Prometheus endpoint started on :{self.port}")
        except Exception as e:
            logger.warning(f"Failed to start Prometheus endpoint: {e}")
    
    def stop(self):
        if self._server:
            self._server.shutdown()


class PipelineMetrics:
    """
    Метрики pipeline для мониторинга:
    - Фазы
    - AI вызовы
    - Ошибки
    - Длительность
    """
    
    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus
        
        if enable_prometheus:
            port = int(os.getenv("PROMETHEUS_PORT", "9090"))
            self._prometheus = PrometheusExporter(port)
            self._prometheus.start()
        else:
            self._prometheus = None
        
        # Phase durations
        self.phase_durations: Dict[str, float] = {}
        
        # AI metrics
        self.ai_calls: Dict[str, int] = {}
        self.ai_errors: Dict[str, int] = {}
        self.ai_tokens: Dict[str, int] = {}
        self.ai_latency: Dict[str, list] = {}
        
        # Cache metrics
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        
        # Errors
        self.errors: list = []
        
        # Start time
        self.start_time = time.time()
        
        # Lock
        self._lock = threading.Lock()
    
    def record_phase(self, name: str, duration: float):
        """Запись длительности фазы"""
        with self._lock:
            self.phase_durations[name] = duration
            
            if self._prometheus:
                self._prometheus.metrics.gauge(
                    "pipeline_phase_duration_seconds",
                    duration,
                    {"phase": name}
                )
    
    def record_ai_call(
        self,
        provider: str,
        latency: float,
        tokens: int = 0,
        success: bool = True,
    ):
        """Запись вызова AI"""
        with self._lock:
            self.ai_calls[provider] = self.ai_calls.get(provider, 0) + 1
            
            if not success:
                self.ai_errors[provider] = self.ai_errors.get(provider, 0) + 1
            
            if provider not in self.ai_latency:
                self.ai_latency[provider] = []
            self.ai_latency[provider].append(latency)
            
            if tokens > 0:
                self.ai_tokens[provider] = self.ai_tokens.get(provider, 0) + tokens
            
            if self._prometheus:
                self._prometheus.metrics.increment("ai_calls_total", 1, {"provider": provider})
                self._prometheus.metrics.histogram("ai_latency_seconds", latency, {"provider": provider})
                if tokens > 0:
                    self._prometheus.metrics.histogram("ai_tokens", tokens, {"provider": provider})
    
    def record_cache_hit(self):
        """Кэш hit"""
        with self._lock:
            self.cache_hits += 1
            if self._prometheus:
                self._prometheus.metrics.increment("cache_hits_total")
    
    def record_cache_miss(self):
        """Кэш miss"""
        with self._lock:
            self.cache_misses += 1
            if self._prometheus:
                self._prometheus.metrics.increment("cache_misses_total")
    
    def record_error(self, error: str, context: str = ""):
        """Запись ошибки"""
        with self._lock:
            self.errors.append({
                "error": error,
                "context": context,
                "timestamp": time.time(),
            })
            
            if self._prometheus:
                self._prometheus.metrics.increment("pipeline_errors_total", 1, {"context": context})
    
    def get_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        with self._lock:
            total_ai_calls = sum(self.ai_calls.values())
            total_ai_errors = sum(self.ai_errors.values())
            total_tokens = sum(self.ai_tokens.values())
            total_cache = self.cache_hits + self.cache_misses
            
            avg_latency = {}
            for provider, latencies in self.ai_latency.items():
                if latencies:
                    avg_latency[provider] = sum(latencies) / len(latencies)
            
            return {
                "runtime_seconds": time.time() - self.start_time,
                "phases": self.phase_durations,
                "ai": {
                    "total_calls": total_ai_calls,
                    "total_errors": total_ai_errors,
                    "total_tokens": total_tokens,
                    "by_provider": {
                        p: {
                            "calls": c,
                            "errors": self.ai_errors.get(p, 0),
                            "tokens": self.ai_tokens.get(p, 0),
                            "avg_latency": avg_latency.get(p, 0),
                        }
                        for p, c in self.ai_calls.items()
                    },
                },
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_rate": self.cache_hits / total_cache if total_cache > 0 else 0,
                },
                "errors": len(self.errors),
            }
    
    def export_json(self, path: Path):
        """Экспорт метрик в JSON"""
        summary = self.get_summary()
        path.write_text(json.dumps(summary, indent=2))
        logger.info(f"Metrics exported to {path}")
    
    def close(self):
        """Закрытие и очистка"""
        if self._prometheus:
            self._prometheus.stop()


# ============================================================================
# OPENTELEMETRY (опционально)
# ============================================================================

class OpenTelemetryTracer:
    """
    OpenTelemetry tracing - опционально, требует установки:
    pip install opentelemetry-api opentelemetry-sdk
    """
    
    def __init__(self, service_name: str = "orchestration"):
        self.service_name = service_name
        self._tracer = None
        self._init_tracer()
    
    def _init_tracer(self):
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            
            # Создаём tracer
            resource = Resource.create({"service.name": self.service_name})
            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)
            
            # Пытаемся подключиться к OTLP collector
            try:
                otlp_endpoint = os.getenv("OTLP_ENDPOINT", "localhost:4317")
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"OpenTelemetry tracing enabled, endpoint: {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"OTLP exporter not available: {e}")
            
            self._tracer = trace.get_tracer(__name__)
            
        except ImportError:
            logger.warning("OpenTelemetry not installed, tracing disabled")
            self._tracer = None
    
    def start_span(self, name: str, **attributes):
        """Начать span"""
        if not self._tracer:
            return NoOpSpan()
        
        span = self._tracer.start_span(name)
        for key, value in attributes.items():
            span.set_attribute(key, value)
        return SpanContext(span)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


class SpanContext:
    """Контекст span для использования с with"""
    
    def __init__(self, span):
        self._span = span
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self._span.end()
    
    def set_attribute(self, key: str, value: Any):
        self._span.set_attribute(key, str(value))


class NoOpSpan:
    """No-op span для случаев когда OTEL не доступен"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def set_attribute(self, key: str, value: Any):
        pass


# ============================================================================
# ФАБРИКА
# ============================================================================

def create_metrics(enable_prometheus: bool = None) -> PipelineMetrics:
    """Создание метрик pipeline"""
    if enable_prometheus is None:
        enable_prometheus = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"
    
    return PipelineMetrics(enable_prometheus=enable_prometheus)


def create_tracer(service_name: str = None) -> OpenTelemetryTracer:
    """Создание tracer"""
    if service_name is None:
        service_name = os.getenv("OTEL_SERVICE_NAME", "orchestration")
    
    return OpenTelemetryTracer(service_name)
