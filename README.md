# AI Pipeline - C++ to Haskell/QML/Reports Converter

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Tests](https://img.shields.io/badge/tests-13%20%F0%9F%8C%85-success)
![Providers](https://img.shields.io/badge/providers-99%2B-orange)

Многофазный AI-конвейер для конвертации C++ кода в Haskell, QML и отчёты.

## 🚀 Быстрый старт

```bash
# Клонировать репозиторий
git clone <repo-url>
cd test2

# Установить зависимости
pip install -r requirements.txt

# Запустить pipeline
./run.sh --provider ollama --model gemma3:1b
```

## 📋 Возможности

### AI Провайдеры (99+)
- **Основные**: OpenAI, Anthropic, Google, Mistral
- **Open-source**: DeepSeek, Qwen, Llama, Cohere
- **Локальные**: Ollama, LMStudio, LocalAI, vLLM
- **Российские**: Yandex, Sber (GigaChat)
- **Китайские**: MiniMax, Moonshot, Baidu, ByteDance

### Pipeline Фазы
1. **Analysis** - Глубокий анализ кода (1000+ классов)
2. **Database** - Btrieve → PostgreSQL DDL
3. **Haskell** - C++ → Haskell конвертация
4. **QML** - Qt → QML 3 конвертация
5. **Reports** - Crystal → Jasper/Pentaho/pdf-slave

### Мониторинг
- Web UI dashboard (:8080)
- Prometheus metrics (:9090)
- JSON logging
- Health checks

## 📖 Использование

```bash
# Список провайдеров
./run.sh --list

# Тест провайдера
./run.sh --test ollama

# Web UI
./run.sh --web --port 8080

# Docker
docker-compose up -d

# Тесты
pytest tests/ -v
```

## 📁 Структура проекта

```
orchestration/          # 38 Python файлов
├── ai/                 # AI клиент и провайдеры
├── pipeline/           # Основной pipeline
├── cache/              # Кэширование
├── circuit_breaker/    # Отказоустойчивость
├── monitoring/         # Метрики
├── validators/         # Валидация
├── utils/              # Утилиты
├── api_server.py       # REST API
├── graphql_api.py      # GraphQL API
├── websocket_server.py # WebSocket
├── templates.py        # Шаблоны
├── analytics.py        # Аналитика
├── notifications.py    # Уведомления
└── scheduler.py        # Планировщик
```

## 📊 Результаты

| Метрика | Значение |
|---------|----------|
| Python файлов | 38 |
| Тесты | 13 ✅ |
| AI провайдеров | 99+ |
| Сгенерировано файлов | 53 |

## 🔧 Конфигурация

Через переменные окружения:
```bash
export DEFAULT_PROVIDER=ollama
export OLLAMA_MODEL=gemma3:1b
export LOG_FORMAT=json
export ENABLE_RLM=true
```

Или через `.pipeline.json`:
```json
{
  "default_provider": "ollama",
  "ollama_model": "gemma3:1b",
  "max_workers": 4,
  "log_format": "json"
}
```

## 📝 История коммитов

```
532e6f1 - feat: add tests, CI/CD, and documentation
33bd15b - feat: add core orchestration module
3478659 - chore: add .gitignore
```

## 🛠 Технологии

- **Python 3.11+** - Основной язык
- **asyncio** - Асинхронное программирование
- **aiohttp** - HTTP клиент
- **FastAPI** - REST API
- **Strawberry** - GraphQL
- **Prometheus** - Метрики
- **Docker** - Контейнеризация

## 📄 License

MIT License
