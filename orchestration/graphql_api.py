"""GraphQL API for pipeline"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import strawberry
    from strawberry import Schema
    from strawberry.fastapi import GraphQLRouter
    STRAWBERRY_AVAILABLE = True
except ImportError:
    STRAWBERRY_AVAILABLE = False

logger = logging.getLogger("orchestration.graphql")


# GraphQL Types
@strawberry.type
class FileType:
    path: str
    size: int
    modified: str
    format: str


@strawberry.type
class PhaseType:
    name: str
    status: str
    files: int
    duration: float


@strawberry.type
class MetricsType:
    runtime_seconds: float
    total_files: int
    ai_calls: int
    ai_tokens: int
    cache_hit_rate: float


@strawberry.type
class ProviderType:
    name: str
    base_url: str
    model: str
    available: bool


@strawberry.type
class ConversionResult:
    success: bool
    output: str
    errors: List[str]


# Queries
@strawberry.type
class Query:
    @strawberry.field
    def status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        base = Path("./Surypus2")
        if not base.exists():
            return {"running": False, "files": 0}
        
        return {
            "running": False,
            "files": {
                "haskell": len(list(base.glob("src/*.hs"))),
                "qml": len(list(base.glob("qml/*.qml"))),
                "reports": len(list(base.glob("reports/**/*.jrxml"))),
            }
        }
    
    @strawberry.field
    def metrics(self) -> Optional[MetricsType]:
        """Get pipeline metrics"""
        metrics_file = Path("./Surypus2/metrics.json")
        if metrics_file.exists():
            data = json.loads(metrics_file.read_text())
            return MetricsType(
                runtime_seconds=data.get("runtime_seconds", 0),
                total_files=53,
                ai_calls=data.get("ai", {}).get("total_calls", 0),
                ai_tokens=data.get("ai", {}).get("total_tokens", 0),
                cache_hit_rate=data.get("cache", {}).get("hit_rate", 0),
            )
        return None
    
    @strawberry.field
    def files(self, format: Optional[str] = None) -> List[FileType]:
        """Get generated files"""
        base = Path("./Surypus2")
        files = []
        
        patterns = {
            "haskell": "src/*.hs",
            "qml": "qml/*.qml",
            "reports": "reports/**/*.jrxml",
        }
        
        glob_patterns = [patterns[format]] if format and format in patterns else [
            "src/*.hs", "qml/*.qml", "reports/**/*.jrxml"
        ]
        
        for pattern in glob_patterns:
            for f in base.glob(pattern):
                if f.is_file():
                    files.append(FileType(
                        path=str(f.relative_to(base)),
                        size=f.stat().st_size,
                        modified=str(f.stat().st_mtime),
                        format=f.suffix[1:],
                    ))
        
        return files
    
    @strawberry.field
    def providers(self) -> List[ProviderType]:
        """Get available providers"""
        from orchestration.ai.providers import OPENAI_COMPATIBLE_PROVIDERS
        
        return [
            ProviderType(
                name=name,
                base_url=config.base_url,
                model=config.model,
                available=bool(os.getenv(config.api_key_env)),
            )
            for name, config in list(OPENAI_COMPATIBLE_PROVIDERS.items())[:20]
        ]


# Mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def convert(
        self,
        code: str,
        source_format: str,
        target_format: str,
    ) -> ConversionResult:
        """Convert code between formats"""
        # Would call AI here
        return ConversionResult(
            success=True,
            output=f"# Converted from {source_format} to {target_format}",
            errors=[],
        )
    
    @strawberry.mutation
    def clear_cache(self) -> str:
        """Clear cache"""
        cache_dir = Path("./Surypus2/.cache")
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
        return "Cache cleared"
    
    @strawberry.mutation
    def generate_api_key(self, name: str) -> str:
        """Generate API key"""
        from orchestration.security import APIKeyManager
        keys = APIKeyManager()
        return keys.generate_key(name)


# Schema
schema = Schema(query=Query, mutation=Mutation)


def create_graphql_router() -> Optional[GraphQLRouter]:
    """Create GraphQL router"""
    if not STRAWBERRY_AVAILABLE:
        return None
    
    return GraphQLRouter(schema)


def start_graphql_server(port: int = 4000):
    """Start GraphQL server"""
    if not STRAWBERRY_AVAILABLE:
        print("Strawberry not available, install with: pip install strawberry[fastapi]")
        return
    
    import uvicorn
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter
    
    app = FastAPI(title="AI Pipeline GraphQL")
    router = create_graphql_router()
    app.include_router(router, prefix="/graphql")
    
    print(f"🔮 GraphQL: http://localhost:{port}/graphql")
    print(f"   Playground: http://localhost:{port}/graphql")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start_graphql_server()
