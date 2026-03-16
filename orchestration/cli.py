"""CLI with advanced features and subcommands"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, List

# Try imports, provide fallbacks
try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    typer = None
    Console = None
    Table = None


if TYPER_AVAILABLE:
    console = Console()
    app = typer.Typer(help="AI Pipeline - C++ to Haskell/QML/Reports")

    # ============================================================================
    # STATUS COMMAND
    # ============================================================================

    @app.command()
    def status(
        output: str = typer.Option("Surypus2", "-o", "--output", help="Output directory"),
        verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    ):
        """Show pipeline status"""
        from orchestration.config import get_config
        
        config = get_config()
        base = Path(output)
        
        if not base.exists():
            console.print(f"[yellow]No output directory: {output}[/yellow]")
            return
        
        # Count files
        hs = len(list(base.glob("src/*.hs")))
        qml = len(list(base.glob("qml/*.qml")))
        jasper = len(list(base.glob("reports/jasper/*.jrxml")))
        pentaho = len(list(base.glob("reports/pentaho/*.xaction")))
        pdfslave = len(list(base.glob("reports/pdfslave/*.yaml")))
        
        table = Table(title="Pipeline Status")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        table.add_row("Haskell", str(hs))
        table.add_row("QML", str(qml))
        table.add_row("Jasper Reports", str(jasper))
        table.add_row("Pentaho", str(pentaho))
        table.add_row("PDF-Slave", str(pdfslave))
        table.add_row("[bold]Total[/bold]", str(hs + qml + jasper + pentaho + pdfslave))
        
        console.print(table)
        
        # State file
        state_file = base / ".pipeline_state.json"
        if state_file.exists():
            import json
            state = json.loads(state_file.read_text())
            
            if verbose:
                console.print("\n[bold]Pipeline State:[/bold]")
                for phase, done in state.items():
                    status_icon = "✅" if done else "⬜"
                    console.print(f"  {status_icon} {phase}")
        
        # Metrics
        metrics_file = base / "metrics.json"
        if metrics_file.exists():
            import json
            metrics = json.loads(metrics_file.read_text())
            
            console.print(f"\n⏱ Runtime: {metrics.get('runtime_seconds', 0):.1f}s")
            
            if verbose:
                ai = metrics.get("ai", {})
                console.print(f"🤖 AI Calls: {ai.get('total_calls', 0)}")
                console.print(f"📝 AI Tokens: {ai.get('total_tokens', 0)}")


    # ============================================================================
    # RUN COMMAND
    # ============================================================================

    @app.command()
    def run(
        project: str = typer.Argument("OpenPapyrus", help="Project path"),
        output: str = typer.Option("Surypus2", "-o", "--output", help="Output path"),
        provider: str = typer.Option(None, "-p", "--provider", help="AI provider"),
        model: str = typer.Option(None, "-m", "--model", help="Model name"),
        workers: int = typer.Option(4, "-w", "--workers", help="Max workers"),
        force: bool = typer.Option(False, "-f", "--force", help="Force reprocess"),
        log_format: str = typer.Option("text", "-l", "--log", help="Log format"),
        phase: str = typer.Option(None, "--phase", help="Run specific phase (1-5)"),
    ):
        """Run the conversion pipeline"""
        from orchestration.pipeline import run_pipeline
        
        if provider:
            os.environ["DEFAULT_PROVIDER"] = provider
        if model:
            os.environ["OLLAMA_MODEL"] = model
        
        console.print(f"🚀 Starting pipeline: {project} → {output}")
        
        run_pipeline(
            project,
            output,
            workers,
            log_format=log_format,
        )


    # ============================================================================
    # PROVIDERS COMMAND
    # ============================================================================

    @app.command()
    def providers(
        search: Optional[str] = typer.Option(None, "-s", "--search", help="Search providers"),
        available_only: bool = typer.Option(False, "-a", "--available", help="Show only available"),
    ):
        """List available AI providers"""
        from orchestration.ai.providers import OPENAI_COMPATIBLE_PROVIDERS, get_provider_manager
        
        pm = get_provider_manager()
        
        table = Table(title="AI Providers")
        table.add_column("Name", style="cyan")
        table.add_column("Base URL", style="dim")
        table.add_column("Model", style="green")
        table.add_column("Status", style="yellow")
        
        for name, config in sorted(OPENAI_COMPATIBLE_PROVIDERS.items()):
            if search and search.lower() not in name.lower():
                continue
            
            is_available = name in pm.providers
            
            if available_only and not is_available:
                continue
            
            status = "✅" if is_available else "❌"
            
            table.add_row(
                name,
                config.base_url[:45] + "..." if len(config.base_url) > 45 else config.base_url,
                config.model,
                status,
            )
        
        console.print(table)


    # ============================================================================
    # TEST COMMAND
    # ============================================================================

    @app.command()
    def test(
        provider: str = typer.Argument(..., help="Provider to test"),
        prompt: str = typer.Option("Say 'test' in 3 words", "-p", "--prompt", help="Test prompt"),
    ):
        """Test an AI provider"""
        console.print(f"🧪 Testing {provider}...")
        
        async def run_test():
            from orchestration.ai.client import AsyncAIClient, AIConfig
            
            config = AIConfig(
                default_provider=provider,
                timeout=60,
            )
            
            client = AsyncAIClient(config)
            
            try:
                result = await client.call(prompt, "general", 100)
                
                if result:
                    console.print(f"[green]✅ Success:[/green] {result}")
                else:
                    console.print("[red]❌ Failed: No response[/red]")
                    
            except Exception as e:
                console.print(f"[red]❌ Error:[/red] {e}")
            finally:
                await client.close()
        
        asyncio.run(run_test())


    # ============================================================================
    # CACHE COMMAND
    # ============================================================================

    @app.command()
    def cache(
        action: str = typer.Argument("show", help="show/clear/stats"),
        output: str = typer.Option("Surypus2", "-o", "--output", help="Output directory"),
    ):
        """Manage cache"""
        cache_dir = Path(output) / ".cache"
        
        if action == "clear":
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
            console.print("[green]Cache cleared[/green]")
            
        elif action == "stats":
            if not cache_dir.exists():
                console.print("[yellow]Cache is empty[/yellow]")
                return
            
            files = list(cache_dir.rglob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            console.print(f"Entries: {len(files)}")
            console.print(f"Size: {total_size / 1024:.1f} KB")
            
        else:  # show
            if cache_dir.exists():
                files = list(cache_dir.rglob("*"))
                console.print(f"Cache: {len(files)} entries")
            else:
                console.print("Cache: empty")


    # ============================================================================
    # CLEAN COMMAND
    # ============================================================================

    @app.command()
    def clean(
        output: str = typer.Option("Surypus2", "-o", "--output", help="Output directory"),
        confirm: bool = typer.Option(True, "--yes", help="Confirm deletion"),
    ):
        """Clean output directory"""
        base = Path(output)
        
        if not base.exists():
            return
        
        if not confirm:
            if not typer.confirm(f"Delete all generated files in {output}?"):
                return
        
        import shutil
        for item in base.iterdir():
            if item.name.startswith("."):
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        
        console.print(f"[green]✅ Cleaned {output}[/green]")


    # ============================================================================
    # CONFIG COMMAND
    # ============================================================================

    @app.command()
    def config_cmd(
        key: Optional[str] = typer.Option(None, "-k", "--key", help="Config key"),
        value: Optional[str] = typer.Option(None, "-v", "--value", help="Config value"),
        list_all: bool = typer.Option(False, "-l", "--list", help="List all"),
        save: Optional[str] = typer.Option(None, "-s", "--save", help="Save to file"),
    ):
        """Manage configuration"""
        from orchestration.config import ConfigManager, get_config
        
        config = get_config()
        
        if list_all:
            table = Table(title="Configuration")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            
            for k, v in config.to_dict().items():
                table.add_row(k, str(v))
            
            console.print(table)
        
        elif key:
            if value:
                if hasattr(config, key):
                    setattr(config, key, value)
                    console.print(f"[green]Set {key} = {value}[/green]")
                else:
                    console.print(f"[red]Unknown key: {key}[/red]")
            else:
                current = getattr(config, key, None)
                console.print(f"{key} = {current}")
        
        if save:
            manager = ConfigManager()
            manager.save(save)
            console.print(f"[green]Saved to {save}[/green]")


    # ============================================================================
    # WEB COMMAND
    # ============================================================================

    @app.command()
    def web(
        host: str = typer.Option("0.0.0.0", "--host", help="Host"),
        port: int = typer.Option(8080, "--port", help="Port"),
    ):
        """Start web UI"""
        console.print(f"🌐 Starting web UI on http://{host}:{port}")
        
        from orchestration.web_ui import start_server
        start_server(port)


    # ============================================================================
    # API COMMAND
    # ============================================================================

    @app.command()
    def api(
        host: str = typer.Option("0.0.0.0", "--host", help="Host"),
        port: int = typer.Option(8000, "--port", help="Port"),
    ):
        """Start API server"""
        console.print(f"🌐 Starting API on http://{host}:{port}")
        console.print(f"   Docs: http://{host}:{port}/docs")
        
        from orchestration.api_server import start_server
        start_server(host, port)


    # ============================================================================
    # VERSION COMMAND
    # ============================================================================

    @app.command()
    def version():
        """Show version"""
        from orchestration import __version__
        console.print(f"AI Pipeline v{__version__}")

    # ============================================================================
    # MAIN
    # ============================================================================

    def main():
        app()

else:
    # Fallback CLI
    def main():
        print("Typer not available. Install with: pip install typer rich")
        print("\nAvailable commands (basic):")
        print("  python -m orchestration.pipeline --help")
        print("  python -m orchestration.web_ui")
        print("  python -m orchestration.api_server")