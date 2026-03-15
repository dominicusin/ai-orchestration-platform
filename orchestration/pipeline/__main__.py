"""Entry point for running pipeline as: python -m orchestration.pipeline"""

import sys
import asyncio
import argparse
from pathlib import Path
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.pipeline import run_pipeline
from orchestration.ai.providers import OPENAI_COMPATIBLE_PROVIDERS, get_provider_manager


async def test_provider(provider_name: str, stream: bool = False):
    """Тестирование провайдера"""
    pm = get_provider_manager()
    provider = pm.providers.get(provider_name)
    
    if not provider:
        print(f"❌ Provider '{provider_name}' not available")
        print(f"\nДоступные провайдеры: {pm.list_available()}")
        return
    
    print(f"🧪 Testing {provider.config.name}...")
    
    if stream:
        print("📡 Streaming mode:")
        # Streaming not implemented yet
        result = await provider.complete("Count from 1 to 5", max_tokens=50)
        print(f"✅ {result}")
    else:
        result = await provider.complete(
            "Say 'Hello' in 3 words",
            max_tokens=50,
        )
        
        if result:
            print(f"✅ Response: {result[:200]}")
        else:
            print(f"❌ Failed")


def main():
    parser = argparse.ArgumentParser(
        description="AI Pipeline - C++ to Haskell/QML/Reports converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m orchestration.pipeline
  python -m orchestration.pipeline --project-path ./MyProject --output-path ./Out
  python -m orchestration.pipeline --list-providers
  python -m orchestration.pipeline --test ollama
  python -m orchestration.pipeline --provider deepseek --log-format json
        """
    )
    parser.add_argument("project", nargs="?", help="Project path (default: ./OpenPapyrus)")
    parser.add_argument("--output", "-o", default="./Surypus2", help="Output path")
    parser.add_argument("--workers", "-w", type=int, default=None, help="Max parallel workers")
    parser.add_argument("--force", "-f", action="store_true", help="Force reprocess all files")
    parser.add_argument("--log-format", "-l", default=None, choices=["text", "json"], help="Log format")
    parser.add_argument("--list-providers", action="store_true", help="List all supported AI providers")
    parser.add_argument("--provider", "-p", default=None, help="Use specific provider (ollama, groq, deepseek, mistral...)")
    parser.add_argument("--test", "-t", default=None, help="Test specific provider")
    parser.add_argument("--stream", "-s", action="store_true", help="Enable streaming output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--web", action="store_true", help="Start web UI")
    parser.add_argument("--port", type=int, default=8080, help="Web UI port")
    args = parser.parse_args()
    
    if args.verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    if args.list_providers:
        print("\n📋 Supported AI Providers (99+):\n")
        print(f"{'Provider':<20} {'Base URL':<50} {'Model':<30}")
        print("-" * 100)
        for name, config in sorted(OPENAI_COMPATIBLE_PROVIDERS.items()):
            print(f"{name:<20} {config.base_url[:48]:<50} {config.model:<30}")
        print(f"\n✅ Total: {len(OPENAI_COMPATIBLE_PROVIDERS)} providers")
        return
    
    if args.test:
        async def run_test():
            await test_provider(args.test, args.stream)
            pm = get_provider_manager()
            await pm.close_all()
        asyncio.run(run_test())
        sys.exit(0)

    if args.web:
        from orchestration.web_ui import start_server
        start_server(args.port)
        return
    
    if args.provider:
        os.environ["DEFAULT_PROVIDER"] = args.provider

    project_path = args.project or "./OpenPapyrus"
    
    print(f"🚀 Starting AI Pipeline")
    print(f"   Project: {project_path}")
    print(f"   Output:  {args.output}")
    if args.provider:
        print(f"   Provider: {args.provider}")
    print()

    run_pipeline(
        project_path,
        args.output,
        args.workers,
        log_format=args.log_format,
    )


if __name__ == "__main__":
    main()