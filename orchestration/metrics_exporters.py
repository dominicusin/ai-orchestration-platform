"""Pipeline metrics exporters"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger("orchestration.metrics_exporters")


class MetricsExporter:
    """Base metrics exporter"""
    
    def export(self, metrics: Dict):
        raise NotImplementedError


class JSONExporter(MetricsExporter):
    """Export to JSON"""
    
    def __init__(self, path: str = None):
        self.path = path
    
    def export(self, metrics: Dict):
        data = json.dumps(metrics, indent=2)
        if self.path:
            open(self.path, "w").write(data)
        return data


class PrometheusExporter(MetricsExporter):
    """Export to Prometheus format"""
    
    def export(self, metrics: Dict):
        lines = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                lines.append(f"pipeline_{key} {value}")
        return "\n".join(lines)


class ExporterFactory:
    """Create exporters"""
    
    @staticmethod
    def create(format: str, **kwargs) -> MetricsExporter:
        if format == "json":
            return JSONExporter(**kwargs)
        elif format == "prometheus":
            return PrometheusExporter()
        raise ValueError(f"Unknown format: {format}")
