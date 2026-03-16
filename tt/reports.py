"""Report generation utilities"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ReportConfig:
    """Report configuration"""
    title: str
    output_format: str  # html, markdown, json, pdf
    sections: List[str]


class ReportGenerator:
    """Generate pipeline reports"""
    
    def __init__(self, output_dir: str = "./Surypus2"):
        self.output_dir = Path(output_dir)
        self.reports_dir = self.output_dir / "reports" / "generated"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_summary_report(self, output_format: str = "markdown") -> str:
        """Generate summary report"""
        base = self.output_dir
        
        # Collect data
        data = {
            "generated_at": datetime.now().isoformat(),
            "files": {
                "haskell": len(list(base.glob("src/*.hs"))),
                "qml": len(list(base.glob("qml/*.qml"))),
                "jasper": len(list(base.glob("reports/jasper/*.jrxml"))),
                "pentaho": len(list(base.glob("reports/pentaho/*.xaction"))),
                "pdfslave": len(list(base.glob("reports/pdfslave/*.yaml"))),
            },
            "metrics": self._load_metrics(),
            "analysis": self._load_analysis(),
        }
        
        if output_format == "json":
            return json.dumps(data, indent=2)
        
        elif output_format == "markdown":
            return self._format_markdown(data)
        
        elif output_format == "html":
            return self._format_html(data)
        
        return str(data)
    
    def _load_metrics(self) -> Dict:
        """Load metrics"""
        metrics_file = self.output_dir / "metrics.json"
        if metrics_file.exists():
            return json.loads(metrics_file.read_text())
        return {}
    
    def _load_analysis(self) -> Dict:
        """Load analysis"""
        analysis_file = self.output_dir / "analysis.json"
        if analysis_file.exists():
            analysis = json.loads(analysis_file.read_text())
            return analysis.get("summary", {})
        return {}
    
    def _format_markdown(self, data: Dict) -> str:
        """Format as Markdown"""
        files = data["files"]
        total = sum(files.values())
        
        md = f"""# AI Pipeline Report

Generated: {data['generated_at']}

## Summary

| Metric | Count |
|--------|-------|
| Total Files | {total} |
| Haskell | {files['haskell']} |
| QML | {files['qml']} |
| Jasper Reports | {files['jasper']} |
| Pentaho | {files['pentaho']} |
| PDF-Slave | {files['pdfslave']} |

## Metrics

"""
        
        metrics = data.get("metrics", {})
        if metrics:
            md += f"- Runtime: {metrics.get('runtime_seconds', 0):.1f}s\n"
            ai = metrics.get("ai", {})
            md += f"- AI Calls: {ai.get('total_calls', 0)}\n"
            md += f"- AI Tokens: {ai.get('total_tokens', 0)}\n"
        
        analysis = data.get("analysis", {})
        if analysis:
            md += f"\n## Analysis\n"
            md += f"- Classes: {analysis.get('total_classes', 0)}\n"
            md += f"- Structs: {analysis.get('total_structs', 0)}\n"
            md += f"- Btrieve Files: {analysis.get('total_btrieve', 0)}\n"
            md += f"- SQL Queries: {analysis.get('total_sql_queries', 0)}\n"
        
        return md
    
    def _format_html(self, data: Dict) -> str:
        """Format as HTML"""
        files = data["files"]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Pipeline Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f0f0f0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>AI Pipeline Report</h1>
    <p>Generated: {data['generated_at']}</p>
    
    <h2>Summary</h2>
    <table>
        <tr><th>Type</th><th>Count</th></tr>
        <tr><td>Haskell</td><td>{files['haskell']}</td></tr>
        <tr><td>QML</td><td>{files['qml']}</td></tr>
        <tr><td>Jasper</td><td>{files['jasper']}</td></tr>
        <tr><td>Pentaho</td><td>{files['pentaho']}</td></tr>
        <tr><td>PDF-Slave</td><td>{files['pdfslave']}</td></tr>
    </table>
    
    <h2>Metrics</h2>
    <div class="metric">
        Runtime: {data.get('metrics', {}).get('runtime_seconds', 0):.1f}s
    </div>
    <div class="metric">
        AI Calls: {data.get('ai', {}).get('total_calls', 0)}
    </div>
</body>
</html>"""
        return html
    
    def save_report(self, filename: str = "report", format: str = "markdown") -> Path:
        """Save report to file"""
        content = self.generate_summary_report(format)
        
        ext = {"markdown": ".md", "html": ".html", "json": ".json"}.get(format, ".txt")
        output_path = self.reports_dir / f"{filename}{ext}"
        
        output_path.write_text(content)
        return output_path
    
    def generate_diff_report(self) -> str:
        """Generate diff between versions"""
        base = self.output_dir
        
        # Compare current with previous
        # (simplified version)
        files = {
            "haskell": list(base.glob("src/*.hs")),
            "qml": list(base.glob("qml/*.qml")),
        }
        
        report = "# Diff Report\n\n"
        
        for fmt, file_list in files.items():
            report += f"## {fmt.upper()}\n"
            for f in file_list[:10]:
                report += f"- {f.name}\n"
            report += "\n"
        
        return report


class MetricsExporter:
    """Export metrics to various formats"""
    
    def __init__(self, output_dir: str = "./Surypus2"):
        self.output_dir = Path(output_dir)
    
    def to_prometheus(self) -> str:
        """Export to Prometheus format"""
        metrics_file = self.output_dir / "metrics.json"
        
        if not metrics_file.exists():
            return "# No metrics available\n"
        
        metrics = json.loads(metrics_file.read_text())
        
        lines = []
        
        # Pipeline metrics
        lines.append(f'pipeline_runtime_seconds {metrics.get("runtime_seconds", 0)}')
        lines.append(f'pipeline_total_files {metrics.get("total_files", 0)}')
        
        # AI metrics
        ai = metrics.get("ai", {})
        lines.append(f'ai_total_calls {ai.get("total_calls", 0)}')
        lines.append(f'ai_total_tokens {ai.get("total_tokens", 0)}')
        
        # Cache metrics
        cache = metrics.get("cache", {})
        lines.append(f'cache_hits {cache.get("hits", 0)}')
        lines.append(f'cache_misses {cache.get("misses", 0)}')
        
        return "\n".join(lines)
    
    def to_csv(self) -> str:
        """Export to CSV"""
        metrics_file = self.output_dir / "metrics.json"
        
        if not metrics_file.exists():
            return "metric,value\n"
        
        metrics = json.loads(metrics_file.read_text())
        
        lines = ["metric,value"]
        
        lines.append(f"runtime_seconds,{metrics.get('runtime_seconds', 0)}")
        lines.append(f"total_files,{metrics.get('total_files', 0)}")
        
        ai = metrics.get("ai", {})
        lines.append(f"ai_calls,{ai.get('total_calls', 0)}")
        lines.append(f"ai_tokens,{ai.get('total_tokens', 0)}")
        
        return "\n".join(lines)


# CLI
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Report generation")
    parser.add_argument("command", choices=["generate", "export"])
    parser.add_argument("--format", default="markdown", choices=["markdown", "html", "json"])
    parser.add_argument("--output", default="report", help="Output filename")
    
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
    if args.command == "generate":
        path = generator.save_report(args.output, args.format)
        print(f"Report saved: {path}")
    
    elif args.command == "export":
        exporter = MetricsExporter()
        
        if args.format == "prometheus":
            print(exporter.to_prometheus())
        elif args.format == "csv":
            print(exporter.to_csv())


if __name__ == "__main__":
    main()