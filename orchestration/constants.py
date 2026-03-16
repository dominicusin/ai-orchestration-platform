"""Constants and enumerations"""

from enum import Enum


class PipelinePhase(str, Enum):
    """Pipeline phases"""
    INIT = "init"
    ANALYSIS = "analysis"
    DATABASE = "database"
    HASKELL = "haskell"
    QML = "qml"
    REPORTS = "reports"
    COMPLETE = "complete"


class FileFormat(str, Enum):
    """File formats"""
    HASKELL = "hs"
    QML = "qml"
    JASPER = "jrxml"
    PENTAHO = "xaction"
    PDFSLAVE = "yaml"
    SQL = "sql"
    CPP = "cpp"
    HEADER = "h"


class AIProvider(str, Enum):
    """AI providers"""
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    GOOGLE = "google"


# Default values
DEFAULT_MAX_WORKERS = 4
DEFAULT_BATCH_SIZE = 10
DEFAULT_TIMEOUT = 300
DEFAULT_CACHE_TTL = 86400

# Limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PROMPT_TOKENS = 128000
MAX_RETRIES = 3

# Paths
DEFAULT_PROJECT_PATH = "./OpenPapyrus"
DEFAULT_OUTPUT_PATH = "./Surypus2"
DEFAULT_CACHE_DIR = "./cache"
DEFAULT_PROMPTS_DIR = "./prompts"

# API
DEFAULT_API_PORT = 8000
DEFAULT_WEB_PORT = 8080
DEFAULT_PROMETHEUS_PORT = 9090

# Version
__version__ = "4.0.0"
__author__ = "AI Pipeline Team"
