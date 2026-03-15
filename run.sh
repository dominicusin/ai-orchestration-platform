#!/bin/bash
# Quick start script for AI Pipeline

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
PROJECT="./OpenPapyrus"
OUTPUT="./Surypus2"
PROVIDER=""
WEB_UI=false

show_help() {
    echo -e "${BLUE}AI Pipeline - C++ to Haskell/QML/Reports converter${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project PATH    Project path (default: ./OpenPapyrus)"
    echo "  -o, --output PATH     Output path (default: ./Surypus2)"
    echo "  --provider NAME       AI provider (ollama, groq, deepseek, mistral)"
    echo "  --model NAME          Ollama model (gemma3:1b, mistral:latest, ...)"
    echo "  --web                 Start web UI"
    echo "  --port NUM            Web UI port (default: 8080)"
    echo "  --list                List available providers"
    echo "  --test PROVIDER       Test specific provider"
    echo "  -v, --verbose         Verbose output"
    echo "  -h, --help            Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --provider ollama --model gemma3:1b"
    echo "  $0 --web --port 9000"
    echo "  $0 --list"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --model)
            export OLLAMA_MODEL="$2"
            shift 2
            ;;
        --web)
            WEB_UI=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --list)
            python -m orchestration.pipeline --list-providers
            exit 0
            ;;
        --test)
            python -m orchestration.pipeline --test "$2"
            exit 0
            ;;
        -v|--verbose)
            export LOG_LEVEL=DEBUG
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Activate venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start web UI or pipeline
if [ "$WEB_UI" = true ]; then
    PORT="${PORT:-8080}"
    echo -e "${GREEN}🌐 Starting Web UI on port $PORT...${NC}"
    python -m orchestration.pipeline --web --port "$PORT"
else
    echo -e "${GREEN}🚀 Starting AI Pipeline${NC}"
    echo "   Project: $PROJECT"
    echo "   Output:  $OUTPUT"
    [ -n "$PROVIDER" ] && echo "   Provider: $PROVIDER"
    
    CMD="python -m orchestration.pipeline --project-path '$PROJECT' --output-path '$OUTPUT'"
    [ -n "$PROVIDER" ] && CMD="$CMD --provider '$PROVIDER'"
    
    eval $CMD
fi
