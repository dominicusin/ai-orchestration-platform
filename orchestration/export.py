"""Export functionality for DAG results"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("orchestration.export")


class Exporter:
    """Base exporter"""
    
    def export(self, data: Any, path: str):
        raise NotImplementedError


class JSONExporter(Exporter):
    """Export to JSON"""
    
    def export(self, data: Any, path: str):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


class CSVExporter(Exporter):
    """Export to CSV"""
    
    def export(self, data: Any, path: str):
        import csv
        
        if isinstance(data, list) and data:
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)


class HTMLExporter(Exporter):
    """Export to HTML"""
    
    def export(self, data: Dict, path: str):
        html = f"""<!DOCTYPE html>
<html>
<head><title>DAG Execution Report</title></head>
<body>
<h1>DAG Execution Report</h1>
<p>Generated: {datetime.now().isoformat()}</p>
<pre>{json.dumps(data, indent=2)}</pre>
</body>
</html>"""
        with open(path, "w") as f:
            f.write(html)


class MarkdownExporter(Exporter):
    """Export to Markdown"""
    
    def export(self, data: Dict, path: str):
        md = f"""# DAG Execution Report

Generated: {datetime.now().isoformat()}

## Summary

- Total Tasks: {data.get("total_tasks", 0)}
- Completed: {data.get("completed", 0)}
- Failed: {data.get("failed", 0)}
- Success Rate: {data.get("success_rate", 0):.1%}

## Details

```
{json.dumps(data, indent=2)}
```
"""
        with open(path, "w") as f:
            f.write(md)


class ExporterFactory:
    """Create exporter"""
    
    @staticmethod
    def create(format: str) -> Exporter:
        if format == "json":
            return JSONExporter()
        elif format == "csv":
            return CSVExporter()
        elif format == "html":
            return HTMLExporter()
        elif format == "md":
            return MarkdownExporter()
        raise ValueError(f"Unknown format: {format}")


def export_results(data: Any, path: str, format: str = None):
    """Export results"""
    if format is None:
        format = Path(path).suffix[1:]
    
    exporter = ExporterFactory.create(format)
    exporter.export(data, path)
