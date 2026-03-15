# AI Pipeline - Documentation

## Quick Start

```bash
# Run pipeline
python -m orchestration.pipeline --project-path ./OpenPapyrus --output-path ./Surypus2 --log-format json

# List available providers
python -m orchestration.pipeline --list-providers

# Test specific provider
python -m orchestration.pipeline --test ollama
```

## Environment Variables

### AI Providers
| Variable | Description |
|----------|-------------|
| `DEFAULT_PROVIDER` | Force specific provider |
| `OLLAMA_MODEL` | Ollama model (default: gemma3:1b) |
| `GROQ_API_KEY` | Groq API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `MISTRAL_API_KEY` | Mistral AI key |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) key |

### RLM Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_RLM` | false | Enable Recursive LM |
| `RLM_MAX_DEPTH` | 2 | Max recursion depth |
| `RLM_USE_INFINIRETRI` | false | Use InfiniRetri |
| `RLM_INFINIRETRI_THRESHOLD` | 100000 | Tokens threshold |

### Pipeline Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_POLICY` | memory | Cache strategy |
| `MAX_WORKERS` | 4 | Parallel workers |
| `ENABLE_PROMETHEUS` | true | Metrics endpoint |
| `LOG_FORMAT` | text | json or text |

## Supported Providers (99+)

### Major
- OpenAI (GPT-4o, o1)
- Anthropic (Claude 3.5)
- Google (Gemini 2.0)
- Mistral (Large, Codestral)

### Open-Source
- DeepSeek (Chat, Coder)
- Qwen (Turbo, Plus)
- Llama 3.3 (Groq, Cerebras, Together)
- Cohere (Command R+)

### Local
- Ollama (localhost:11434)
- LMStudio (localhost:1234)
- LocalAI (localhost:8080)
- vLLM (localhost:8000)

### Russian
- Yandex Cloud
- Sber (GigaChat)
- YandexGPT

### Chinese
- MiniMax
- Moonshot (Kimi)
- Baidu (Ernie)
- ByteDance (Doubao)
- Zhipu (GLM)

## Architecture

```
orchestration/
├── ai/              # AI clients & providers
│   ├── client.py    # Async AI with fallback
│   ├── providers.py # 99+ provider support
│   └── rlm_wrapper.py # RLM-Toolkit
├── pipeline/        # Main pipeline
│   ├── pipeline.py  # 5-phase conversion
│   └── __main__.py  # CLI entry
├── cache/           # Incremental caching
├── circuit_breaker/ # Fault tolerance
├── validators/      # Code validation
├── monitoring/      # Prometheus metrics
└── utils/           # Logging
```

## Phases

1. **Analysis** - Deep code analysis
2. **Database** - Btrieve → PostgreSQL
3. **Haskell** - C++ → Haskell
4. **QML** - Qt → QML
5. **Reports** - Crystal → Jasper/Pentaho/pdf-slave

## API Usage

```python
from orchestration.ai.client import AsyncAIClient, AIConfig
from orchestration.ai.providers import get_provider_manager

# Direct client
client = AsyncAIClient(AIConfig.from_env())
result = await client.call("Convert to Haskell", "haskell")

# Universal provider
pm = get_provider_manager()
provider = pm.providers.get("deepseek")
result = await provider.complete("Your prompt")
```
