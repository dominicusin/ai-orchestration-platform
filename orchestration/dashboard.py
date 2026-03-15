"""Rich CLI dashboard with progress bars and tables"""

import sys
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Try to use rich library, fallback to basic
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


console = Console()


class CLIDashboard:
    """Rich CLI dashboard"""
    
    def __init__(self):
        self.start_time = time.time()
        self.phases: Dict[str, Dict] = {}
        self.current_phase: Optional[str] = None
    
    def start(self, project: str, output: str):
        """Start dashboard"""
        console.clear()
        
        console.print(Panel(
            f"[bold cyan]🤖 AI Pipeline[/bold cyan]\n"
            f"Project: {project}\n"
            f"Output: {output}",
            title="🚀 Starting",
            border_style="cyan"
        ))
    
    def phase_start(self, phase: str, total: int = 0):
        """Start phase"""
        self.current_phase = phase
        self.phases[phase] = {
            "start": time.time(),
            "total": total,
            "done": 0,
            "status": "running"
        }
        
        console.print(f"\n[bold cyan]▶ {phase}[/bold cyan]")
    
    def phase_progress(self, phase: str, done: int, total: int):
        """Update phase progress"""
        if phase in self.phases:
            self.phases[phase]["done"] = done
            self.phases[phase]["total"] = total
    
    def phase_complete(self, phase: str, files: int = 0):
        """Complete phase"""
        duration = time.time() - self.phases[phase]["start"]
        self.phases[phase]["status"] = "complete"
        self.phases[phase]["files"] = files
        self.phases[phase]["duration"] = duration
        
        console.print(f"  ✅ {phase}: {files} files in {duration:.1f}s")
    
    def phase_error(self, phase: str, error: str):
        """Phase error"""
        self.phases[phase]["status"] = "error"
        self.phases[phase]["error"] = error
        
        console.print(f"  ❌ {phase}: {error}")
    
    def show_summary(self, stats: Dict[str, Any]):
        """Show summary table"""
        table = Table(title="📊 Pipeline Summary")
        
        table.add_column("Phase", style="cyan")
        table.add_column("Files", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Status", justify="center")
        
        for phase, data in self.phases.items():
            status = "✅" if data.get("status") == "complete" else "❌"
            duration = f"{data.get('duration', 0):.1f}s"
            files = str(data.get("files", 0))
            
            table.add_row(phase, files, duration, status)
        
        console.print("\n")
        console.print(table)
        
        # Stats
        total_time = time.time() - self.start_time
        console.print(f"\n[bold]Total time:[/bold] {total_time:.1f}s")
        
        if "ai" in stats:
            console.print(f"[bold]AI calls:[/bold] {stats['ai'].get('total_calls', 0)}")
            console.print(f"[bold]Tokens:[/bold] {stats['ai'].get('total_tokens', 0)}")
    
    def log(self, message: str, level: str = "info"):
        """Log message"""
        colors = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }
        color = colors.get(level, "white")
        console.print(f"[{color}]{message}[/{color}]")


class SimpleDashboard:
    """Simple dashboard without rich"""
    
    def __init__(self):
        self.start_time = time.time()
        self.phases = {}
    
    def start(self, project: str, output: str):
        print(f"\n🚀 AI Pipeline")
        print(f"   Project: {project}")
        print(f"   Output:  {output}\n")
    
    def phase_start(self, phase: str, total: int = 0):
        print(f"\n▶ {phase}")
        self.phases[phase] = {"start": time.time()}
    
    def phase_progress(self, phase: str, done: int, total: int):
        pct = 100 * done // total if total else 0
        print(f"  Progress: {done}/{total} ({pct}%)", end="\r")
    
    def phase_complete(self, phase: str, files: int = 0):
        duration = time.time() - self.phases[phase]["start"]
        print(f"\n  ✅ {phase}: {files} files in {duration:.1f}s")
    
    def phase_error(self, phase: str, error: str):
        print(f"\n  ❌ {phase}: {error}")
    
    def show_summary(self, stats: Dict[str, Any]):
        total_time = time.time() - self.start_time
        print(f"\n📊 Total time: {total_time:.1f}s")
    
    def log(self, message: str, level: str = "info"):
        prefix = {"info": "ℹ", "warning": "⚠", "error": "❌", "success": "✅"}
        print(f"{prefix.get(level, '•')} {message}")


def get_dashboard() -> CLIDashboard:
    """Get appropriate dashboard"""
    if RICH_AVAILABLE:
        return CLIDashboard()
    return SimpleDashboard()


# Demo
def demo():
    """Demo dashboard"""
    dashboard = get_dashboard()
    
    dashboard.start("./OpenPapyrus", "./Surypus2")
    
    phases = [
        ("Phase 1: Analysis", 100),
        ("Phase 2: Database", 50),
        ("Phase 3: Haskell", 18),
        ("Phase 4: QML", 20),
        ("Phase 5: Reports", 15),
    ]
    
    for phase, count in phases:
        dashboard.phase_start(phase, count)
        time.sleep(0.5)
        
        for i in range(count):
            dashboard.phase_progress(phase, i + 1, count)
            time.sleep(0.05)
        
        dashboard.phase_complete(phase, count)
    
    dashboard.show_summary({
        "ai": {"total_calls": 35, "total_tokens": 30000}
    })


if __name__ == "__main__":
    demo()