"""Metrics exporters for various backends"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("orchestration.metrics.exporters")


class MetricsExporter:
    """Base metrics exporter"""

    def export(self, metrics: dict[str, Any]) -> bool:
        raise NotImplementedError


class JSONExporter(MetricsExporter):
    """Export to JSON file"""

    def __init__(self, path: str = "./Surypus2/metrics.json"):
        self.path = Path(path)

    def export(self, metrics: dict[str, Any]) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(metrics, indent=2))
            return True
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False


class PrometheusExporter(MetricsExporter):
    """Export to Prometheus format"""

    def __init__(self, port: int = 9090):
        self.port = port
        self._server = None

    def export(self, metrics: dict[str, Any]) -> bool:
        # Prometheus format output
        lines = []

        # Runtime
        runtime = metrics.get("runtime_seconds", 0)
        lines.append("# TYPE pipeline_runtime_seconds gauge")
        lines.append(f"pipeline_runtime_seconds {runtime}")

        # Phases
        for phase, duration in metrics.get("phases", {}).items():
            phase_name = phase.replace("-", "_")
            lines.append(f"# TYPE phase_{phase_name}_seconds gauge")
            lines.append(f"phase_{phase_name}_seconds {duration}")

        # AI calls
        ai = metrics.get("ai", {})
        lines.append("# TYPE ai_total_calls counter")
        lines.append(f"ai_total_calls {ai.get('total_calls', 0)}")
        lines.append("# TYPE ai_total_tokens counter")
        lines.append(f"ai_total_tokens {ai.get('total_tokens', 0)}")

        # Cache
        cache = metrics.get("cache", {})
        lines.append("# TYPE cache_hit_rate gauge")
        lines.append(f"cache_hit_rate {cache.get('hit_rate', 0)}")

        return True

    def format_prometheus(self, metrics: dict[str, Any]) -> str:
        self.export(metrics)
        return "\n".join([
            "# HELP pipeline_runtime_seconds Pipeline runtime",
            "# TYPE pipeline_runtime_seconds gauge",
            f"pipeline_runtime_seconds {metrics.get('runtime_seconds', 0)}",
            "",
            "# HELP ai_calls_total Total AI API calls",
            "# TYPE ai_calls_total counter",
            f"ai_calls_total {metrics.get('ai', {}).get('total_calls', 0)}",
        ])


class InfluxDBExporter(MetricsExporter):
    """Export to InfluxDB"""

    def __init__(self, url: str = None, token: str = None, org: str = None):
        self.url = url or os.getenv("INFLUX_URL")
        self.token = token or os.getenv("INFLUX_TOKEN")
        self.org = org or os.getenv("INFLUX_ORG")

    def export(self, metrics: dict[str, Any]) -> bool:
        if not self.url:
            return False


        data = {
            "measurement": "pipeline",
            "tags": {
                "status": "completed" if metrics.get("errors", 0) == 0 else "failed"
            },
            "fields": {
                "runtime_seconds": metrics.get("runtime_seconds", 0),
                "total_calls": metrics.get("ai", {}).get("total_calls", 0),
                "total_tokens": metrics.get("ai", {}).get("total_tokens", 0),
                "errors": metrics.get("errors", 0),
            },
            "timestamp": int(time.time() * 1e9)
        }

        # Note: Would need actual HTTP call here
        logger.info(f"InfluxDB: would send {data}")
        return True


class GrafanaJSONExporter(MetricsExporter):
    """Grafana-compatible JSON with timestamps"""

    def __init__(self, path: str = "./Surypus2/grafana-metrics.json"):
        self.path = Path(path)

    def export(self, metrics: dict[str, Any]) -> bool:
        try:
            # Convert to Grafana format
            grafana_data = {
                "app": "ai-pipeline",
                "timestamp": datetime.now().isoformat(),
                "series": []
            }

            # Runtime
            grafana_data["series"].append({
                "name": "runtime_seconds",
                "value": metrics.get("runtime_seconds", 0),
                "timestamp": datetime.now().isoformat()
            })

            # Phases
            for phase, duration in metrics.get("phases", {}).items():
                grafana_data["series"].append({
                    "name": f"phase_{phase}_seconds",
                    "value": duration,
                    "timestamp": datetime.now().isoformat()
                })

            self.path.write_text(json.dumps(grafana_data, indent=2))
            return True
        except Exception as e:
            logger.error(f"Grafana export failed: {e}")
            return False


class StatsDExporter(MetricsExporter):
    """Export to StatsD/Datadog"""

    def __init__(self, host: str = "localhost", port: int = 8125):
        self.host = host
        self.port = port

    def export(self, metrics: dict[str, Any]) -> bool:
        # Would send UDP packets
        logger.info(f"StatsD: runtime={metrics.get('runtime_seconds', 0)}")
        return True


class MultiExporter:
    """Export to multiple backends"""

    def __init__(self, exporters: list = None):
        self.exporters = exporters or [
            JSONExporter(),
            GrafanaJSONExporter(),
        ]

    def export(self, metrics: dict[str, Any]) -> bool:
        results = []
        for exporter in self.exporters:
            results.append(exporter.export(metrics))
        return any(results)

    def export_all(self, metrics: dict[str, Any]) -> dict[str, bool]:
        return {type(e).__name__: e.export(metrics) for e in self.exporters}


def get_exporter(config: str = None) -> MetricsExporter:
    """Get exporter based on config"""
    config = config or os.getenv("METRICS_EXPORTER", "json")

    if config == "prometheus":
        return PrometheusExporter()
    elif config == "influxdb":
        return InfluxDBExporter()
    elif config == "grafana":
        return GrafanaJSONExporter()
    elif config == "statsd":
        return StatsDExporter()
    elif config == "multi":
        return MultiExporter()
    else:
        return JSONExporter()
