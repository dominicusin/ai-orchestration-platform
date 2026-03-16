"""Data export utilities for various formats"""

import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class DataExporter:
    """Export data to various formats"""
    
    def __init__(self, output_dir: str = "./Surypus2"):
        self.output_dir = Path(output_dir)
    
    def export_metrics_json(self, output_path: str = None) -> str:
        """Export metrics to JSON"""
        metrics_file = self.output_dir / "metrics.json"
        
        if not metrics_file.exists():
            return "{}"
        
        if output_path:
            import shutil
            shutil.copy(metrics_file, output_path)
            return output_path
        
        return metrics_file.read_text()
    
    def export_metrics_csv(self, output_path: str = None) -> str:
        """Export metrics to CSV"""
        metrics_file = self.output_dir / "metrics.json"
        
        if not metrics_file.exists():
            return ""
        
        metrics = json.loads(metrics_file.read_text())
        
        output = output_path or str(self.output_dir / "metrics.csv")
        
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            
            # Flatten metrics
            writer.writerow(["runtime_seconds", metrics.get("runtime_seconds", 0)])
            writer.writerow(["total_files", metrics.get("total_files", 0)])
            
            ai = metrics.get("ai", {})
            writer.writerow(["ai_total_calls", ai.get("total_calls", 0)])
            writer.writerow(["ai_total_tokens", ai.get("total_tokens", 0)])
            
            cache = metrics.get("cache", {})
            writer.writerow(["cache_hits", cache.get("hits", 0)])
            writer.writerow(["cache_misses", cache.get("misses", 0)])
        
        return output
    
    def export_analysis_xml(self, output_path: str = None) -> str:
        """Export analysis to XML"""
        analysis_file = self.output_dir / "analysis.json"
        
        if not analysis_file.exists():
            return ""
        
        analysis = json.loads(analysis_file.read_text())
        
        root = ET.Element("analysis")
        
        # Summary
        summary = analysis.get("summary", {})
        summary_elem = ET.SubElement(root, "summary")
        
        for key, value in summary.items():
            child = ET.SubElement(summary_elem, key)
            child.text = str(value)
        
        # Classes
        classes_elem = ET.SubElement(root, "classes")
        
        for cls in analysis.get("classes", [])[:100]:
            cls_elem = ET.SubElement(classes_elem, "class")
            cls_elem.set("name", cls.get("name", ""))
            
            for key, value in cls.items():
                if key != "name":
                    child = ET.SubElement(cls_elem, key)
                    child.text = str(value)
        
        output = output_path or str(self.output_dir / "analysis.xml")
        
        tree = ET.ElementTree(root)
        tree.write(output, encoding="utf-8", xml_declaration=True)
        
        return output
    
    def export_schema_sql(self, output_path: str = None) -> str:
        """Export schema with metadata"""
        schema_file = self.output_dir / "schema.sql"
        
        if not schema_file.exists():
            return ""
        
        output = output_path or str(self.output_dir / "schema_with_meta.sql")
        
        # Read original schema
        schema = schema_file.read_text()
        
        # Add metadata comment
        metadata = f"""-- Generated: {datetime.now().isoformat()}
-- Source: {self.output_dir}

{schema}
"""
        
        Path(output).write_text(metadata)
        
        return output
    
    def export_all(self, formats: List[str] = None) -> Dict[str, str]:
        """Export in all formats"""
        if formats is None:
            formats = ["json", "csv", "xml"]
        
        results = {}
        
        if "json" in formats:
            try:
                results["json"] = self.export_metrics_json()
            except Exception:
                results["json"] = None
        
        if "csv" in formats:
            try:
                results["csv"] = self.export_metrics_csv()
            except Exception:
                results["csv"] = None
        
        if "xml" in formats:
            try:
                results["xml"] = self.export_analysis_xml()
            except Exception:
                results["xml"] = None
        
        return results


class ReportExporter:
    """Export comprehensive reports"""
    
    def __init__(self, output_dir: str = "./Surypus2"):
        self.output_dir = Path(output_dir)
    
    def generate_html_report(self, output_path: str = None) -> str:
        """Generate HTML report"""
        # Collect data
        data = {
            "generated_at": datetime.now().isoformat(),
            "metrics": self._load_json("metrics.json"),
            "analysis": self._load_json("analysis.json"),
            "state": self._load_json(".pipeline_state.json"),
        }
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Pipeline Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 15px 25px;
            background: #f0f0f0;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Pipeline Report</h1>
        <p>Generated: {data['generated_at']}</p>
    </div>
    
    <div class="card">
        <h2>📊 Summary</h2>
        <div class="metrics">
            {self._format_metrics(data.get('metrics', {}))}
        </div>
    </div>
    
    <div class="card">
        <h2>📁 Files</h2>
        <table>
            <tr><th>Type</th><th>Count</th></tr>
            {self._format_file_counts()}
        </table>
    </div>
    
    <div class="card">
        <h2>🔄 Pipeline State</h2>
        <table>
            <tr><th>Phase</th><th>Status</th></tr>
            {self._format_state(data.get('state', {}))}
        </table>
    </div>
    
    <div class="card">
        <h2>📈 Analysis</h2>
        {self._format_analysis(data.get('analysis', {}))}
    </div>
</body>
</html>"""
        
        output = output_path or str(self.output_dir / "report.html")
        Path(output).write_text(html)
        
        return output
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON file"""
        path = self.output_dir / filename
        if path.exists():
            return json.loads(path.read_text())
        return {}
    
    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics"""
        runtime = metrics.get("runtime_seconds", 0)
        ai = metrics.get("ai", {})
        cache = metrics.get("cache", {})
        
        return f"""
            <div class="metric">
                <div class="metric-value">{runtime:.1f}s</div>
                <div class="metric-label">Runtime</div>
            </div>
            <div class="metric">
                <div class="metric-value">{ai.get('total_calls', 0)}</div>
                <div class="metric-label">AI Calls</div>
            </div>
            <div class="metric">
                <div class="metric-value">{ai.get('total_tokens', 0):,}</div>
                <div class="metric-label">Tokens</div>
            </div>
            <div class="metric">
                <div class="metric-value">{cache.get('hit_rate', 0):.1%}</div>
                <div class="metric-label">Cache Hit Rate</div>
            </div>
        """
    
    def _format_file_counts(self) -> str:
        """Format file counts"""
        counts = {
            "Haskell": len(list(self.output_dir.glob("src/*.hs"))),
            "QML": len(list(self.output_dir.glob("qml/*.qml"))),
            "Jasper": len(list(self.output_dir.glob("reports/jasper/*.jrxml"))),
            "Pentaho": len(list(self.output_dir.glob("reports/pentaho/*.xaction"))),
            "PDF-Slave": len(list(self.output_dir.glob("reports/pdfslave/*.yaml"))),
        }
        
        return "\n".join(
            f"<tr><td>{fmt}</td><td>{cnt}</td></tr>"
            for fmt, cnt in counts.items()
        )
    
    def _format_state(self, state: Dict) -> str:
        """Format pipeline state"""
        phases = {
            "phase1_done": "Analysis",
            "phase2_done": "Database",
            "phase3_done": "Haskell",
            "phase4_done": "QML",
            "phase5_done": "Reports",
        }
        
        rows = []
        for key, name in phases.items():
            done = state.get(key, False)
            status = "✅" if done else "⬜"
            rows.append(f"<tr><td>{name}</td><td>{status}</td></tr>")
        
        return "\n".join(rows)
    
    def _format_analysis(self, analysis: Dict) -> str:
        """Format analysis summary"""
        summary = analysis.get("summary", {})
        
        if not summary:
            return "<p>No analysis data available</p>"
        
        return f"""
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Classes</td><td>{summary.get('total_classes', 0)}</td></tr>
            <tr><td>Structs</td><td>{summary.get('total_structs', 0)}</td></tr>
            <tr><td>Btrieve Files</td><td>{summary.get('total_btrieve', 0)}</td></tr>
            <tr><td>SQL Queries</td><td>{summary.get('total_sql_queries', 0)}</td></tr>
            <tr><td>Reports</td><td>{summary.get('total_reports', 0)}</td></tr>
            <tr><td>Qt Widgets</td><td>{summary.get('total_widgets', 0)}</td></tr>
        </table>
        """