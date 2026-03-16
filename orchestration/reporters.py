"""Pipeline reporters for various outputs"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("orchestration.reporters")


class Reporter:
    """Base reporter"""
    
    def report(self, data: Dict):
        """Report data"""
        raise NotImplementedError


class JSONReporter(Reporter):
    """JSON reporter"""
    
    def __init__(self, output_file: str = None):
        self.output_file = output_file
    
    def report(self, data: Dict):
        """Report as JSON"""
        json_data = json.dumps(data, indent=2)
        
        if self.output_file:
            Path(self.output_file).write_text(json_data)
        
        return json_data


class TextReporter(Reporter):
    """Text reporter"""
    
    def report(self, data: Dict):
        """Report as text"""
        lines = []
        
        lines.append("=" * 50)
        lines.append("Pipeline Report")
        lines.append("=" * 50)
        
        if "status" in data:
            lines.append(f"Status: {data['status']}")
        
        if "duration" in data:
            lines.append(f"Duration: {data['duration']:.2f}s")
        
        if "files" in data:
            lines.append(f"Files: {data['files']}")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)


class MarkdownReporter(Reporter):
    """Markdown reporter"""
    
    def report(self, data: Dict):
        """Report as markdown"""
        md = []
        
        md.append("# Pipeline Report")
        md.append("")
        md.append(f"**Generated:** {datetime.now().isoformat()}")
        md.append("")
        
        if "status" in data:
            md.append(f"**Status:** {data['status']}")
        
        if "duration" in data:
            md.append(f"**Duration:** {data['duration']:.2f}s")
        
        if "phases" in data:
            md.append("## Phases")
            md.append("")
            md.append("| Phase | Status |")
            md.append("|-------|--------|")
            
            for phase in data["phases"]:
                md.append(f"| {phase['name']} | {phase['status']} |")
        
        return "\n".join(md)


class ReporterFactory:
    """Create reporters"""
    
    @staticmethod
    def create(format: str, **kwargs) -> Reporter:
        """Create reporter by format"""
        if format == "json":
            return JSONReporter(**kwargs)
        elif format == "text":
            return TextReporter()
        elif format == "markdown":
            return MarkdownReporter()
        
        raise ValueError(f"Unknown format: {format}")