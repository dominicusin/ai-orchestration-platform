#!/bin/bash
# AI Pipeline completion

_pipeline_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    opts="
        --help
        --project-path
        --output-path
        --workers
        --force
        --log-format
        --list-providers
        --provider
        --test
        --stream
        --verbose
        --web
        --port
        ollama
        groq
        deepseek
        mistral
        anthropic
        google
        gemma3:1b
        mistral:latest
        qwen3:32b
        deepseek-coder:6.7b
    "
    
    # Options that need values
    if [[ "${prev}" == "--project-path" || "${prev}" == "-o" || "${prev}" == "--output" ]]; then
        COMPREPLY=( $(compgen -d -- "${cur}") )
        return 0
    fi
    
    if [[ "${prev}" == "--provider" || "${prev}" == "-p" ]]; then
        COMPREPLY=( $(compgen -W "ollama groq deepseek mistral anthropic google cerebras hyperbolic" -- "${cur}") )
        return 0
    fi
    
    if [[ "${prev}" == "--test" || "${prev}" == "-t" ]]; then
        COMPREPLY=( $(compgen -W "ollama groq deepseek mistral" -- "${cur}") )
        return 0
    fi
    
    COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
    return 0
}

complete -F _pipeline_completion python
complete -F _pipeline_completion python3
