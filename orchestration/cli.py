"""Advanced CLI with Typer"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, List

# Try typer, fallback to argparse
try:
    import typer
    from typer import echo, secho, confirm
    from rich.console import Console
    from rich.table import Table
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    typer = None

console = Console()


class PipelineCLI:
    """CLI for AI Pipeline"""
    
    def __init__(self):
        self.app = typer.Typer(
            name="ai-pipeline",
            help="AI Pipeline - C++ to Haskell/QML/Reports converter",
            add_completion=False,
        )
        
        self._setup_commands()
    
    def _setup_commands(self):
        """Setup CLI commands"""
        
        @self.app.command()
        def run(
            project: str = typer.Argument("./OpenPapyrus", help="Project path"),
            output: str = typer.Option("./Surypus2", "-o", "--output", help="Output path"),
            provider: str = typer.Option(None, "-p", "--provider", help="AI provider"),
            model: str = typer.Option(None, "-m", "--model", help="Model name"),
            workers: int = typer.Option(4, "-w", "--workers", help="Max workers"),
            force: bool = typer.Option(False, "-f", "--force", help="Force reprocess"),
            log_format: str = typer.Option("text", "-l", "--log", help="Log format"),
        ):
            """Run pipeline"""
            echo(f"🚀 Starting pipeline: {project} → {output}")
            
            if provider:
                os.environ["DEFAULT_PROVIDER"] = provider
            if model:
                os.environ["OLLAMA_MODEL"] = model
            
            from orchestration.pipeline import run_pipeline
            run_pipeline(project, output, workers, log_format=log_format)
        
        @self.app.command()
        def web(
            host: str = typer.Option("0.0.0.0", "--host", help="Host"),
            port: int = typer.Option(8080, "--port", help="Port"),
        ):
            """Start web UI"""
            from orchestration.web_ui import start_server
            start_server(port)
        
        @self.app.command()
        def api(
            host: str = typer.Option("0.0.0.0", "--host", help="Host"),
            port: int = typer.Option(8000, "--port", help="Port"),
        ):
            """Start API server"""
            from orchestration.api_server import start_server
            start_server(host, port)
        
        @self.app.command()
        def test(
            provider: str = typer.Argument(..., help="Provider to test"),
        ):
            """Test provider"""
            echo(f"🧪 Testing {provider}...")
            
            async def run_test():
                from orchestration.ai.providers import get_provider_manager
                pm = get_provider_manager()
                p = pm.providers.get(provider)
                
                if not p:
                    secho(f"Provider {provider} not available", fg="red")
                    return
                
                result = await p.complete("Say 'test' in 3 words", max_tokens=20)
                
                if result:
                    secho(f"✅ Success: {result}", fg="green")
                else:
                    secho(f"❌ Failed", fg="red")
            
            asyncio.run(run_test())
        
        @self.app.command()
        def providers(
            search: str = typer.Option(None, "-s", "--search", help="Search providers"),
        ):
            """List providers"""
            from orchestration.ai.providers import OPENAI_COMPATIBLE_PROVIDERS
            
            table = Table(title="AI Providers")
            table.add_column("Name", style="cyan")
            table.add_column("Base URL", style="dim")
            table.add_column("Model")
            
            for name, config in sorted(OPENAI_COMPATIBLE_PROVIDERS.items()):
                if search and search.lower() not in name:
                    continue
                
                table.add_row(
                    name,
                    config.base_url[:40] + "..." if len(config.base_url) > 40 else config.base_url,
                    config.model,
                )
            
            console.print(table)
            console.print(f"\n✅ Total: {len(OPENAI_COMPATIBLE_PROVIDERS)} providers")
        
        @self.app.command()
        def status():
            """Show pipeline status"""
            import json
            
            base = Path("./Surypus2")
            if not base.exists():
                secho("No output directory found", fg="yellow")
                return
            
            # Count files
            hs = len(list(base.glob("src/*.hs")))
            qml = len(list(base.glob("qml/*.qml")))
            reports = len(list(base.glob("reports/**/*.jrxml")))
            
            table = Table(title="Pipeline Status")
            table.add_column("Type", style="cyan")
            table.add_column("Count", justify="right")
            
            table.add_row("Haskell", str(hs))
            table.add_row("QML", str(qml))
            table.add_row("Reports", str(reports))
            table.add_row("Total", str(hs + qml + reports))
            
            console.print(table)
            
            # Metrics
            metrics_file = base / "metrics.json"
            if metrics_file.exists():
                metrics = json.loads(metrics_file.read_text())
                console.print(f"\n⏱ Runtime: {metrics.get('runtime_seconds', 0):.1f}s")
        
        @self.app.command()
        def clean(
            confirm_delete: bool = typer.Option(True, "--yes", help="Confirm deletion"),
        ):
            """Clean output directory"""
            base = Path("./Surypus2")
            
            if not base.exists():
                return
            
            if confirm_delete:
                if not confirm("Delete all generated files?"):
                    return
            
            import shutil
            for item in base.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            secho("✅ Cleaned output directory", fg="green")
        
        @self.app.command()
        def cache(
            action: str = typer.Argument("show", help="show/clear"),
        ):
            """Manage cache"""
            cache_dir = Path("./Surypus2/.cache")
            
            if action == "clear":
                import shutil
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                secho("Cache cleared", fg="green")
            else:
                if cache_dir.exists():
                    files = list(cache_dir.rglob("*"))
                    secho(f"Cache: {len(files)} entries", fg="cyan")
                else:
                    secho("Cache: empty", fg="cyan")
        
        @self.app.command()
        def config(
            key: str = typer.Option(None, "-k", "--key", help="Config key"),
            value: str = typer.Option(None, "-v", "--value", help="Config value"),
            list_all: bool = typer.Option(False, "-l", "--list", help="List all"),
        ):
            """Manage configuration"""
            from orchestration.config import get_config
            
            config = get_config()
            
            if list_all:
                table = Table(title="Configuration")
                table.add_column("Key", style="cyan")
                table.add_column("Value")
                
                for k, v in config.to_dict().items():
                    table.add_row(k, str(v))
                
                console.print(table)
            
            elif key:
                if value:
                    setattr(config, key, value)
                    secho(f"Set {key} = {value}", fg="green")
                else:
                    current = getattr(config, key, None)
                    secho(f"{key} = {current}", fg="cyan")
        
        @self.app.command()
        def version():
            """Show version"""
            echo("AI Pipeline v1.0.0")
            echo("Python: " + sys.version.split()[0])


def main():
    """Main entry point"""
    if not TYPER_AVAILABLE:
        print("Typer not available, using basic CLI")
        print("Install with: pip install typer rich")
        return
    
    cli = PipelineCLI()
    cli.app()


if __name__ == "__main__":
    main()