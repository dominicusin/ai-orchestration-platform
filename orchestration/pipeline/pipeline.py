"""
Многофазный AI-конвейер конвертации C++ → Haskell (v4)
Модульная архитектура с async AI, circuit breaker, и мониторингом.
"""

import asyncio
import json
import logging
import os
import re
import signal
import sys
import time
from pathlib import Path

# Модули проекта
from ..ai.client import AIConfig, AsyncAIClient
from ..cache.cache import CachePolicy, FileCache
from ..monitoring.metrics import create_metrics, create_tracer
from ..utils.logging_utils import LogFormat, setup_logging
from ..validators.validators import (
    get_haskell_validator,
    get_qml_validator,
    get_sql_validator,
)

logger = logging.getLogger("orchestration.pipeline")

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

CONFIG = {
    # Параметры
    "max_workers": int(os.getenv("MAX_WORKERS", "4")),
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "batch_size": int(os.getenv("BATCH_SIZE", "5")),

    # Валидация
    "validate_with_ghc": os.getenv("VALIDATE_WITH_GHC", "true").lower() == "true",
    "use_hlint": os.getenv("USE_HLINT", "true").lower() == "true",
    "use_pgformat": os.getenv("USE_PGFORMAT", "true").lower() == "true",

    # Кэш
    "cache_policy": os.getenv("CACHE_POLICY", "cache_first"),
    "max_memory_cache": int(os.getenv("MAX_MEMORY_CACHE", "1000")),

    # Мониторинг
    "enable_prometheus": os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true",
    "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),

    # Логирование
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "log_file": os.getenv("LOG_FILE", "pipeline.log"),
    "log_format": os.getenv("LOG_FORMAT", "json"),
}

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

PROMPTS = {
    "cpp_to_haskell": """Ты - эксперт по конвертации C++ в Haskell.
Конвертируй следующий C++ код в чистый Haskell.

ВАЖНЫЕ ПРАВИЛА:
1. Используй Haskell 2010, без расширений
2. Типы C++ → Haskell:
   - int → Int, float → Double, double → Double
   - bool → Bool, char → Char
   - std::string → Text
   - std::vector<a> → [a]
   - std::map<k,v> → Map k v
   - std::shared_ptr<a> → Maybe a
   - nullptr → Nothing
   - class → data type с record синтаксисом
   - public/private → не используй (Haskell все публичное)
   - virtual → не нужно (полиморфизм через type classes)
   - void → ()
   - * (указатель) → Maybe или IO

3. Функции-члены класса → standalone функции

Верни ТОЛЬКО Haskell код, без пояснений.

```cpp
{code}
```

Haskell:""",
    "sql_ddl": """Ты - эксперт по PostgreSQL.
Конвертируй C++ структуру в PostgreSQL DDL.

ПРАВИЛА:
1. Используй snake_case для имен таблиц и колонок
2. Типы: int → INTEGER, long → BIGINT, float → REAL, double → DOUBLE PRECISION
3. Добавь PRIMARY KEY, NOT NULL где логично

Верни ТОЛЬКО SQL.

{struct_info}

SQL:""",
    "qml_convert": """Ты - эксперт по Qt → QML.
Конвертируй Qt C++ код в чистый QML 3 (Qt Quick).

МАППИНГ:
- QPushButton → Button from QtQuick.Controls
- QLineEdit → TextField from QtQuick.Controls
- QLabel → Text from QtQuick
- QCheckBox → CheckBox from QtQuick.Controls
- QRadioButton → RadioButton from QtQuick.Controls
- QComboBox → ComboBox from QtQuick.Controls
- QTextEdit/PlainTextEdit → TextArea from QtQuick.Controls
- QListWidget → ListView with ListModel
- QTableWidget → TableView with TableModel
- QSlider → Slider from QtQuick.Controls
- QProgressBar → ProgressBar from QtQuick.Controls

СВОЙСТВА:
- setText("x") → text: "x"
- setVisible(true) → visible: true
- setEnabled(false) → enabled: false
- setPlaceholderText("x") → placeholderText: "x"
- setChecked(true) → checked: true
- setCurrentIndex(i) → currentIndex: i
- setCurrentText("x") → currentText: "x"

Верни ТОЛЬКО валидный QML код (без markdown блоков!).

```cpp
{code}
```

QML:""",
    "report_convert": """Ты - эксперт по конвертации отчётов.
Конвертируй Crystal Reports в JasperReports (JRXML), Pentaho (xaction), pdf-slave (YAML).

Верни ТОЛЬКО валидный JSON (без markdown блоков!) с ключами jasper, pentaho, pdfslave.

Пример формата:
```json
{{"jasper": "<?xml version='1.0'?><jasperReport...>", "pentaho": "<?xml version='1.0'?><action-sequence...>", "pdfslave": "report_name: test\\nfields: [...]"}}
```

Исходный код:
```cpp
{code}
```

JSON:""",
}


# ============================================================================
# FALLBACK TEMPLATES
# ============================================================================

FALLBACK_TEMPLATES = {
    "haskell": """module {name} where

import Data.Text (Text)
import Data.Maybe (Maybe(..))

data {name} = {name}
    {{ {fields} }}
    deriving (Show, Eq)

{name} :: {name}
{name} = {name} {{ {defaults} }}
""",
    "sql": """-- {name}
CREATE TABLE IF NOT EXISTS {table_name} (
    id SERIAL PRIMARY KEY,
    {columns}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""",
}


# ============================================================================
# PIPELINE
# ============================================================================

class ConversionPipeline:
    """
    Многофазный конвейер конвертации v4

    Особенности:
    - Async AI клиент с circuit breaker
    - Инкрементальная обработка
    - Structured logging
    - Prometheus metrics
    - OpenTelemetry tracing (опционально)
    """

    def __init__(
        self,
        project_path: str,
        output_path: str,
        max_workers: int = None,
        log_format: str = None,
    ):
        self.project_path = Path(project_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers or CONFIG["max_workers"]

        # Логирование
        format_type = LogFormat.JSON if (log_format or CONFIG["log_format"]) == "json" else LogFormat.TEXT
        self._logger = setup_logging(
            name="orchestration",
            log_file=str(self.output_path / "pipeline.log"),
            log_level=CONFIG["log_level"],
            format_type=format_type,
            context={"project": str(project_path)},
        )

        # AI клиент (async)
        self.ai = AsyncAIClient(AIConfig.from_env())

        # RLM для длинных контекстов (опционально)
        self.rlm = None
        if os.getenv("ENABLE_RLM", "false").lower() == "true":
            from orchestration.ai.rlm_wrapper import RLMWrapper
            self.rlm = RLMWrapper(self.ai)
            if not self.rlm.initialize():
                self.rlm = None

        # Кэш
        cache_policy = CachePolicy[CONFIG["cache_policy"].upper().replace("_", "_")]
        self.cache = FileCache(
            self.output_path / ".cache",
            policy=cache_policy,
            max_memory_entries=CONFIG["max_memory_cache"],
        )

        # Валидаторы
        self.haskell_validator = get_haskell_validator()
        self.sql_validator = get_sql_validator()
        self.qml_validator = get_qml_validator()

        # Метрики и tracing
        self.metrics = create_metrics(CONFIG["enable_prometheus"])
        self.tracer = create_tracer()

        # State для resume
        self.state_file = self.output_path / ".pipeline_state.json"
        self.state = self._load_state()

        # Graceful shutdown
        self._shutdown_requested = False
        self._setup_signal_handlers()

        logger.info(f"Pipeline initialized: {project_path} -> {output_path}")

    def _setup_signal_handlers(self):
        """Настройка обработки сигналов"""
        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.warning(f"Received signal {sig_name}, saving state...")
            self._shutdown_requested = True
            self._save_state()
            logger.info("State saved. Exiting.")
            sys.exit(0)

        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except (ValueError, OSError) as e:
            logger.warning(f"Failed to setup signal handlers: {e}")

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except json.JSONDecodeError as e:
                logger.warning(f"Error loading state: {e}")
        return {
            "phase1_done": False,
            "phase2_done": False,
            "phase3_done": False,
            "phase4_done": False,
            "phase5_done": False,
            "last_class_idx": 0,
        }

    def _save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def _bar(self, current: int, total: int, name: str = ""):
        if total == 0:
            return
        pct = (current / total) * 100
        filled = int(15 * current / total)
        bar = "█" * filled + "░" * (15 - filled)
        sys.stdout.write(f"\r[{name}] {bar} {pct:5.1f}%")
        sys.stdout.flush()

    # ==========================================================================
    # ФАЗА 1: Анализ
    # ==========================================================================
    async def phase1_analyze(self, force: bool = False) -> dict:
        """Подробный анализ заголовочных файлов"""
        phase_start = time.time()
        logger.info("📊 Phase 1: Deep analysis")

        out_file = self.output_path / "analysis.json"

        if not force and out_file.exists() and self.state.get("phase1_done"):
            analysis = json.loads(out_file.read_text())
            logger.info(f"   Loaded from cache: {len(analysis.get('classes', []))} classes")
            return analysis

        src_dir = self.project_path / "Src"
        logger.info("   Scanning files...")

        all_classes = {}
        all_structs = {}
        all_includes = {}
        all_functions = {}
        sql_queries = []
        reports = []
        widgets = []
        btrieve_files = []

        for ext in ["*.h", "*.hpp", "*.cpp"]:
            for f in src_dir.rglob(ext):
                if not f.is_file():
                    continue

                if self._shutdown_requested:
                    break

                try:
                    content = f.read_text(errors="ignore")
                    rel = str(f.relative_to(self.project_path))

                    # Includes
                    includes = re.findall(r'#include\s+[<"]([^>"]+)[>"]', content)
                    if includes:
                        all_includes[rel] = includes

                    # SQL queries
                    queries = self._extract_sql_queries(content)
                    if queries:
                        sql_queries.extend([{"file": rel, "query": q} for q in queries])

                    # Classes
                    for m in re.finditer(
                        r"class\s+(\w+)\s*[:{]\s*public\s+(\w+)", content
                    ):
                        cls_name = m.group(1)
                        parent = m.group(2)
                        class_body = content[m.start() : m.start() + 8000]
                        methods = re.findall(
                            r"(virtual\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)",
                            class_body,
                        )
                        deps = self._extract_dependencies(class_body)

                        all_classes[cls_name] = {
                            "name": cls_name,
                            "file": rel,
                            "type": "BUSINESS",
                            "parent": parent,
                            "methods": [{"ret": m[1], "name": m[2], "params": m[3]}
                                        for m in methods[:30]],
                            "dependencies": deps[:20],
                            "includes": includes[:10],
                        }

                    # Simple classes
                    for m in re.finditer(r"class\s+(\w+)\s*[:{]", content):
                        cls_name = m.group(1)
                        if cls_name not in all_classes:
                            all_classes[cls_name] = {
                                "name": cls_name,
                                "file": rel,
                                "type": "CLASS",
                                "parent": None,
                                "methods": [],
                                "dependencies": [],
                                "includes": includes[:10],
                            }

                    # Structs
                    for m in re.finditer(
                        r"struct\s+(\w+)\s*\{([^}]{5,2000})\}", content
                    ):
                        name = m.group(1)
                        body = m.group(2)
                        fields = re.findall(r"(\w+(?:\*|\&)?)\s+(\w+)\s*;", body)
                        is_btrieve = any(x in body.lower() for x in ["char", "int", "float"])

                        all_structs[name] = {
                            "name": name,
                            "file": rel,
                            "type": "DATA",
                            "fields": [{"type": t.strip(), "name": n.strip()}
                                      for t, n in fields[:30]],
                            "is_btrieve": is_btrieve,
                            "includes": includes[:10],
                        }

                        if is_btrieve:
                            btrieve_files.append(all_structs[name])

                    # Functions
                    for m in re.finditer(
                        r"(?:void|int|bool|float|double|string|auto)\s+(\w+)\s*\([^)]*\)",
                        content,
                    ):
                        fn_name = m.group(1)
                        if fn_name not in ["if", "for", "while", "switch", "return"]:
                            all_functions[fn_name] = {"name": fn_name, "file": rel, "type": "FUNCTION"}

                    # Qt widgets
                    qt_patterns = [
                        (r"class\s+(\w+)\s*:\s*public\s+QWidget", "QWidget"),
                        (r"class\s+(\w+)\s*:\s*public\s+QMainWindow", "QMainWindow"),
                    ]
                    for pattern, widget_type in qt_patterns:
                        if re.search(pattern, content):
                            widgets.append({
                                "name": Path(rel).stem,
                                "file": rel,
                                "widget_type": widget_type,
                                "includes": includes[:10],
                            })
                            break

                    # Reports
                    if re.search(r"CrystalReport|\.rpt|CRPE", content, re.I):
                        reports.append({"name": Path(rel).stem, "file": rel, "includes": includes[:10]})

                except Exception as e:
                    logger.debug(f"Error analyzing {f}: {e}")

        analysis = {
            "summary": {
                "total_files": len(all_includes),
                "total_classes": len(all_classes),
                "total_structs": len(all_structs),
                "total_btrieve": len(btrieve_files),
                "total_reports": len(reports),
                "total_widgets": len(widgets),
                "total_sql_queries": len(sql_queries),
            },
            "classes": list(all_classes.values())[:1000],
            "structs": list(all_structs.values())[:500],
            "functions": list(all_functions.values())[:500],
            "btrieve_files": btrieve_files[:300],
            "reports": reports[:50],
            "qt_widgets": widgets[:100],
            "includes_map": dict(list(all_includes.items())[:200]),
            "sql_queries": sql_queries[:100],
        }

        out_file.write_text(json.dumps(analysis, ensure_ascii=False, indent=2))

        logger.info(f"   Found: {len(all_classes)} classes, {len(btrieve_files)} btrieve, {len(sql_queries)} SQL")

        self.state["phase1_done"] = True
        self._save_state()

        self.metrics.record_phase("phase1_analyze", time.time() - phase_start)
        return analysis

    # ==========================================================================
    # ФАЗА 2: PostgreSQL
    # ==========================================================================
    async def phase2_database(self, analysis: dict):
        """Конвертация Btrieve → PostgreSQL"""
        phase_start = time.time()
        logger.info("\n🗄️ Phase 2: Btrieve → PostgreSQL")

        schema_file = self.output_path / "schema.sql"

        if schema_file.exists() and schema_file.stat().st_size > 500 and self.state.get("phase2_done"):
            logger.info("   schema.sql already exists")
            self.metrics.record_phase("phase2_database", time.time() - phase_start)
            return

        tables = analysis.get("btrieve_files", [])[:50]

        # Batch prompts
        batch_size = CONFIG["batch_size"]
        batched_prompts = []
        for i in range(0, len(tables), batch_size):
            batch = tables[i:i + batch_size]
            prompt = "Конвертируй ВСЕ структуры в PostgreSQL DDL.\n\n"
            for bt in batch:
                prompt += f"Таблица: {bt['name']}, Поля: {json.dumps(bt.get('fields', []))}\n"

            batched_prompts.append({
                "prompt": prompt,
                "operation": "sql",
                "tables": [b["name"] for b in batch],
            })

        logger.info(f"   Processing {len(batched_prompts)} batches...")

        results = await self.ai.call_batch(batched_prompts, "sql")

        sql_parts = []
        for r in results:
            if r.get("result"):
                cleaned = re.sub(r"```sql\n?", "", r["result"])
                cleaned = re.sub(r"```\n?", "", cleaned)
                sql_parts.append(cleaned)

        schema_file.write_text("\n\n".join(sql_parts))

        # Validate
        content = schema_file.read_text()
        validation = self.sql_validator.validate(content)
        if validation.valid:
            logger.info(f"   ✅ {len(sql_parts)} tables, SQL valid")
        else:
            logger.warning(f"   ⚠️ SQL validation issues: {validation.errors[:3]}")

        self.state["phase2_done"] = True
        self._save_state()
        self.metrics.record_phase("phase2_database", time.time() - phase_start)

    # ==========================================================================
    # ФАЗА 3: Haskell
    # ==========================================================================
    async def phase3_haskell(self, analysis: dict):
        """Конвертация C++ → Haskell"""
        phase_start = time.time()
        logger.info("\n⚙️ Phase 3: C++ → Haskell")

        hs_dir = self.output_path / "src"
        hs_dir.mkdir(parents=True, exist_ok=True)

        classes = analysis.get("classes", [])[:10]
        start_idx = self.state.get("last_class_idx", 0)

        for idx, cls in enumerate(classes[start_idx:], start=start_idx):
            if self._shutdown_requested:
                break

            self._bar(idx + 1 - start_idx, len(classes) - start_idx, "Haskell")

            source_path = cls["file"]
            cpp_path = self.project_path / source_path.replace(".h", ".cpp").replace(".hpp", ".cpp")
            content = ""

            for p in [cpp_path, self.project_path / source_path]:
                if p.exists():
                    try:
                        content = p.read_text(errors="ignore")[:3000]
                        break
                    except Exception:
                        pass

            if not content:
                continue

            # Check cache
            cached = self.cache.get(source_path, "haskell", content)
            if cached:
                (hs_dir / f"{cls['name']}.hs").write_text(cached)
                self.metrics.record_cache_hit()
                continue

            self.metrics.record_cache_miss()

            # AI call - используем RLM для больших файлов если включено
            prompt = PROMPTS["cpp_to_haskell"].format(code=content)

            # RLM для контекстов > 2000 символов (если включено)
            if self.rlm and len(content) > 2000:
                try:
                    rlm_result = await self.rlm.run_async(content, "Convert this C++ to Haskell")
                    result = rlm_result.answer
                except Exception as e:
                    logger.warning(f"RLM failed for {cls['name']}: {e}, using regular AI")
                    result = await self.ai.call(prompt, "haskell", 4096)
            else:
                result = await self.ai.call(prompt, "haskell", 4096)

            if result:
                result = re.sub(r"```haskell\n?", "", result)
                result = re.sub(r"```\n?", "", result)

                # Validate
                validation = self.haskell_validator.validate(result)
                if validation.valid:
                    self.cache.set(source_path, "haskell", content, result)
                    (hs_dir / f"{cls['name']}.hs").write_text(result)
                else:
                    logger.warning(f"Validation failed for {cls['name']}, using fallback")
                    fallback = self._fallback_haskell(cls)
                    (hs_dir / f"{cls['name']}.hs").write_text(fallback)
            else:
                fallback = self._fallback_haskell(cls)
                (hs_dir / f"{cls['name']}.hs").write_text(fallback)

        hs_count = len(list(hs_dir.glob("*.hs")))
        self.state["phase3_done"] = True
        self.state["last_class_idx"] = len(classes)
        self._save_state()

        sys.stdout.write("\n")
        logger.info(f"   ✅ {hs_count} Haskell files")

        self.metrics.record_phase("phase3_haskell", time.time() - phase_start)

    # ==========================================================================
    # ФАЗА 4: QML
    # ==========================================================================
    async def phase4_qml(self, analysis: dict):
        """Конвертация Qt → QML"""
        phase_start = time.time()
        logger.info("\n🖥️ Phase 4: Qt → QML")

        qml_dir = self.output_path / "qml"
        qml_dir.mkdir(parents=True, exist_ok=True)

        widgets = analysis.get("qt_widgets", [])[:20]

        if not widgets:
            logger.info("   No Qt widgets to convert")
            self.state["phase4_done"] = True
            self._save_state()
            self.metrics.record_phase("phase4_qml", time.time() - phase_start)
            return

        for w in widgets:
            if self._shutdown_requested:
                break

            src = self.project_path / w["file"]
            if not src.exists():
                continue

            try:
                content = src.read_text(errors="ignore")[:2000]
            except Exception:
                continue

            prompt = PROMPTS["qml_convert"].format(code=content)

            # RLM для больших файлов
            if self.rlm and len(content) > 1500:
                try:
                    rlm_result = await self.rlm.run_async(content, "Convert this Qt C++ to QML")
                    result = rlm_result.answer
                except Exception as e:
                    logger.warning(f"RLM failed for {w['name']}: {e}")
                    result = await self.ai.call(prompt, "qml", 2048)
            else:
                result = await self.ai.call(prompt, "qml", 2048)

            if result:
                result = re.sub(r"```qml\n?", "", result)
                result = re.sub(r"```\n?", "", result)
                (qml_dir / f"{w['name']}.qml").write_text(result)

        qml_count = len(list(qml_dir.glob("*.qml")))
        self.state["phase4_done"] = True
        self._save_state()

        logger.info(f"   ✅ {qml_count} QML files")
        self.metrics.record_phase("phase4_qml", time.time() - phase_start)

    # ==========================================================================
    # ФАЗА 5: Reports
    # ==========================================================================
    async def phase5_reports(self, analysis: dict):
        """Конвертация Crystal Reports"""
        phase_start = time.time()
        logger.info("\n📄 Phase 5: Crystal → Jasper/Pentaho/pdf-slave")

        dirs = {
            "jasper": self.output_path / "reports" / "jasper",
            "pentaho": self.output_path / "reports" / "pentaho",
            "pdfslave": self.output_path / "reports" / "pdfslave",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        reports = analysis.get("reports", [])[:15]

        for rpt in reports:
            if self._shutdown_requested:
                break

            src = self.project_path / rpt["file"]
            if not src.exists():
                continue

            try:
                content = src.read_text(errors="ignore")[:1500]
            except Exception:
                continue

            prompt = PROMPTS["report_convert"].format(code=content)

            # RLM для больших файлов
            if self.rlm and len(content) > 1200:
                try:
                    rlm_result = await self.rlm.run_async(content, "Convert this report to Jasper/Pentaho/pdf-slave format")
                    result = rlm_result.answer
                except Exception as e:
                    logger.warning(f"RLM failed for {rpt['name']}: {e}")
                    result = await self.ai.call(prompt, "analysis", 4096)
            else:
                result = await self.ai.call(prompt, "analysis", 4096)

            if result:
                try:
                    # Агрессивная очистка JSON
                    cleaned = result.strip()
                    # Убираем markdown
                    cleaned = re.sub(r"^```json\s*", "", cleaned)
                    cleaned = re.sub(r"^```\s*", "", cleaned)
                    cleaned = re.sub(r"\s*```$", "", cleaned)
                    # Убираем управляющие символы
                    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
                    # Пробуем распарсить
                    data = json.loads(cleaned)
                    (dirs["jasper"] / f"{rpt['name']}.jrxml").write_text(data.get("jasper", ""))
                    (dirs["pentaho"] / f"{rpt['name']}.xaction").write_text(data.get("pentaho", ""))
                    (dirs["pdfslave"] / f"{rpt['name']}.yaml").write_text(data.get("pdfslave", ""))
                except json.JSONDecodeError:
                    # Пробуем найти JSON в ответе через regex
                    try:
                        # Ищем { ... } блок
                        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result, re.DOTALL)
                        if match:
                            data = json.loads(match.group())
                            (dirs["jasper"] / f"{rpt['name']}.jrxml").write_text(data.get("jasper", ""))
                            (dirs["pentaho"] / f"{rpt['name']}.xaction").write_text(data.get("pentaho", ""))
                            (dirs["pdfslave"] / f"{rpt['name']}.yaml").write_text(data.get("pdfslave", ""))
                            continue
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON parse error for {rpt['name']}: {e}")

        self.state["phase5_done"] = True
        self._save_state()

        logger.info(f"   ✅ {len(reports)} reports")
        self.metrics.record_phase("phase5_reports", time.time() - phase_start)

    # ==========================================================================
    # Helpers
    # ==========================================================================
    def _extract_sql_queries(self, content: str) -> list[str]:
        patterns = [
            r'SQLExecDirect\([^,]+,\s*"([^"]+)"',
            r'execute\([^,]*\s*,\s*"([^"]+)"',
            r'cbExec\([^,]+,\s*"([^"]+)"',
        ]
        queries = []
        for pattern in patterns:
            queries.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(queries))

    def _extract_dependencies(self, content: str) -> list[str]:
        deps = []
        deps.extend(re.findall(r"\b(\w+)\s+(\w+)\s*;", content))
        deps.extend(re.findall(r"\b(\w+)\s*->\s*(\w+)\s*\(", content))
        deps.extend(re.findall(r"\b(\w+)\s*\.(\w+)\s*\(", content))
        return list({d[0] for d in deps if d[0] != "this"})

    def _fallback_haskell(self, cls: dict) -> str:
        name = cls.get("name", "Unknown")
        fields = cls.get("fields", [])

        if isinstance(fields, list) and fields:
            field_strs = [f"{f.get('name', 'field')} :: {f.get('type', 'Int')}" for f in fields[:10]]
            defaults = [f.get("name", "field") for f in fields[:5]]
        else:
            field_strs = ["field1 :: Int"]
            defaults = ["0"]

        return FALLBACK_TEMPLATES["haskell"].format(
            name=name, fields=", ".join(field_strs), defaults=", ".join(defaults)
        )

    def _generate_cabal(self):
        """Генерация project.cabal"""
        cabal = """cabal-version: 3.0
name:          converted-project
version:       0.1.0.0
build-type:    Simple

executable converted-project
  main-is:          Main.hs
  hs-source-dirs:   src
  default-language: Haskell2010
  ghc-options:      -Wall
  build-depends:
      base >= 4.14 && < 5
    , text >= 2.0
    , containers >= 0.6
    , time >= 1.9
"""
        (self.output_path / "project.cabal").write_text(cabal)
        logger.info("   ✅ project.cabal created")

    # ==========================================================================
    # ЗАПУСК
    # ==========================================================================
    async def run(self, force: bool = False):
        total_start = time.time()

        logger.info("🚀 AI Pipeline C++ → Haskell (v4)")
        logger.info(f"   Project: {self.project_path}")
        logger.info(f"   Output: {self.output_path}")
        logger.info(f"   Workers: {self.max_workers}")

        try:
            analysis = await self.phase1_analyze(force=force)

            if not self._shutdown_requested:
                await self.phase2_database(analysis)

            if not self._shutdown_requested:
                await self.phase3_haskell(analysis)

            if not self._shutdown_requested:
                await self.phase4_qml(analysis)

            if not self._shutdown_requested:
                await self.phase5_reports(analysis)

            if not self._shutdown_requested:
                self._generate_cabal()

            # Stats
            total_duration = time.time() - total_start
            self.metrics.record_phase("total", total_duration)

            logger.info("\n📊 AI Statistics:")
            status = self.ai.get_status()
            for provider, data in status["metrics"]["by_provider"].items():
                logger.info(f"   {provider}: {data['calls']} calls, {data.get('total_tokens', 0)} tokens")

            # Cache stats
            cache_stats = self.cache.get_stats()
            logger.info(f"\n💾 Cache: {cache_stats['hits']} hits, {cache_stats['misses']} misses, {cache_stats['hit_rate']:.1%}")

            # Export metrics
            self.metrics.export_json(str(self.output_path / "metrics.json"))

            logger.info(f"\n✅ Pipeline completed in {total_duration:.1f}s")

        except KeyboardInterrupt:
            logger.warning("\n⚠️ Interrupted, state saved")
            self._save_state()
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self._save_state()
        finally:
            await self.ai.close()
            self.metrics.close()


def run_pipeline(project_path: str, output_path: str, max_workers: int = None, **kwargs):
    """Синхронный запуск pipeline"""
    pipeline = ConversionPipeline(project_path, output_path, max_workers, **kwargs)
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-path", default="/home/domini/src/petr/test2/OpenPapyrus")
    parser.add_argument("--output-path", default="/home/domini/src/petr/test2/Surypus2")
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--log-format", default=None, choices=["text", "json"])
    args = parser.parse_args()

    run_pipeline(
        args.project_path,
        args.output_path,
        args.workers,
        log_format=args.log_format,
    )
