```"""Streaming AI responses with real-time output"""

import asyncio
import os
from typing import AsyncIterator, Optional, Callable
import aiohttp
import logging

logger = logging.getLogger("orchestration.ai.streaming")


class StreamingAI:
    """Streaming AI client для real-time вывода"""
    
    def __init__(self, provider: str = "ollama", model: str = None):
        self.provider = provider
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma3:1b")
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    async def stream_complete(
        self, 
        prompt: str,
        chunk_callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """Stream ответ от AI"""
        
        if self.provider == "ollama":
            async for chunk in self._stream_ollama(prompt, chunk_callback):
                yield chunk
        else:
            # Fallback to regular completion
            yield await self._complete(prompt)
    
    async def _stream_ollama(
        self, 
        prompt: str,
        chunk_callback: Optional[Callable[[str], None]] = None
    ) -> AsyncIterator[str]:
        """Stream от Ollama"""
        url = f"{self.base_url}/api/generate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                },
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Ollama error: {resp.status}")
                    return
                
                async for line in resp.content:
                    if not line:
                        continue
                    
                    try:
                        data = line.decode().strip()
                        if not data:
                            continue
                        
                        import json
                        obj = json.loads(data)
                        text = obj.get("response", "")
                        
                        if text and chunk_callback:
                            chunk_callback(text)
                        
                        if text:
                            yield text
                            
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
    
    async def _complete(self, prompt: str) -> str:
        """Non-streaming fallback"""
        url = f"{self.base_url}/api/generate"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.ok:
                    data = await resp.json()
                    return data.get("response", "")
        return ""


class ProgressStreamer:
    """Streamer с progress bar"""
    
    def __init__(self):
        self.accumulated = ""
        self.last_update = 0
    
    def on_chunk(self, text: str, force: bool = False):
        """Обработка чанка с throttling"""
        import time
        self.accumulated += text
        
        now = time.time()
        if force or now - self.last_update > 0.1:
            # Update progress (throttled)
            self._show_progress(len(self.accumulated))
            self.last_update = now
    
    def _show_progress(self, chars: int):
        """Показать прогресс"""
        bar_width = 30
        filled = min(chars // 50, bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\r📝 Generating: [{bar}] {chars} chars", end="", flush=True)
    
    def finish(self):
        """Завершение стрима"""
        print(f"\r✅ Generated: {len(self.accumulated)} chars    ")
        self.accumulated = ""
    
    @property
    def result(self) -> str:
        return self.accumulated


async def demo_streaming():
    """Демонстрация streaming"""
    print("🧪 Testing streaming...\n")
    
    streamer = ProgressStreamer()
    ai = StreamingAI("ollama", "gemma3:1b")
    
    print("Prompt: 'Write a short Haskell function'\n")
    
    async for chunk in ai.stream_complete(
        "Write a short Haskell function that reverses a list",
        chunk_callback=lambda t: streamer.on_chunk(t)
    ):
        pass
    
    streamer.finish()
    print(f"\nResult length: {len(streamer.result)} chars")


if __name__ == "__main__":
    asyncio.run(demo_streaming())
```