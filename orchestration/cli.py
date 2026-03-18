"""CLI for DAG execution"""

import asyncio
import sys
import logging
import click
from typing import List

logger = logging.getLogger("orchestration.cli")


@click.group()
def cli():
    """DAG Execution CLI"""
    pass


@cli.command()
@click.argument("items", nargs=-1)
@click.option("--stages", "-s", multiple=True, help="Processing stages")
@click.option("--workers", "-w", default=4, help="Number of workers")
def run(items: tuple, stages: tuple, workers: int):
    """Run DAG pipeline"""
    click.echo(f"Running DAG with {len(items)} items, {workers} workers")
    
    # Build and execute
    from orchestration.graph_engine import execute_pipeline
    
    items_list = list(items)
    stage_funcs = [lambda x: x for _ in stages]
    
    async def main():
        results = await execute_pipeline(items_list, stage_funcs, workers)
        click.echo(f"Completed: {len(results)} tasks")
    
    asyncio.run(main())


@cli.command()
@click.argument("items", nargs=-1)
def visualize(items: tuple):
    """Visualize DAG structure"""
    from orchestration.graph_recursive import RecursiveDAG
    
    dag = RecursiveDAG()
    items_list = list(items) if items else list(range(100))
    
    # Build sample DAG
    def decompose(items):
        n = len(items)
        if n <= 10:
            return {"atomic": items}
        return {"a": items[:n//2], "b": items[n//2:]}
    
    dag.build_from_decomposition(
        task_id="root",
        task_name="root",
        items=items_list,
        decompose_func=decompose,
        get_handler=lambda i: lambda: i,
        get_capability=lambda i: None,
    )
    
    click.echo(dag.visualize())


@cli.command()
@click.option("--host", default="localhost", help="Host")
@click.option("--port", default=8080, help="Port")
def serve(host: str, port: int):
    """Start web UI"""
    from orchestration.web_ui import start_ui
    click.echo(f"Starting UI at http://{host}:{port}")
    start_ui(host, port)


@cli.command()
def status():
    """Show execution status"""
    from orchestration.graph_monitor import get_monitor
    
    m = get_monitor()
    summary = m.get_summary()
    
    click.echo("=== Execution Status ===")
    click.echo(f"Total: {summary['total_tasks']}")
    click.echo(f"Completed: {summary['completed']}")
    click.echo(f"Failed: {summary['failed']}")
    click.echo(f"Success Rate: {summary['success_rate']:.1%}")
    click.echo(f"Duration: {summary['total_duration']:.2f}s")


if __name__ == "__main__":
    cli()
