"""Prompts for LLM interactions"""

from typing import Dict, List


SYSTEM_PROMPT = """You are a DAG execution assistant.
You help execute tasks in a directed acyclic graph.
Tasks are executed in topological order.
Each task may have dependencies that must complete first."""


TASK_DECOMPOSITION_PROMPT = """Decompose the following task into subtasks.
Each subtask should be atomic and executable by a specific agent.

Task: {task_description}

Return a JSON list of subtasks with:
- name: subtask name
- description: what it does
- capability: required agent capability (file_read, llm_call, code_execute, etc.)"""


VALIDATION_PROMPT = """Validate the following task configuration.
Check for:
- Circular dependencies
- Missing handlers
- Invalid capabilities
- Resource constraints

Task config: {task_config}

Return validation result as JSON."""


RESULT_AGGREGATION_PROMPT = """Aggregate results from subtasks.
Each subtask result is provided below.
Combine them into a final result.

Subtask results:
{subtask_results}

Aggregation rule: {aggregation_rule}"""


ERROR_HANDLING_PROMPT = """An error occurred during task execution.
Analyze the error and suggest:
1. Root cause
2. Recovery action
3. Whether to retry

Error: {error}
Task: {task}

Return as JSON with keys: analysis, recovery, retry"""


def get_prompt(name: str, **kwargs) -> str:
    """Get prompt by name with interpolation"""
    prompts = {
        "system": SYSTEM_PROMPT,
        "decomposition": TASK_DECOMPOSITION_PROMPT,
        "validation": VALIDATION_PROMPT,
        "aggregation": RESULT_AGGREGATION_PROMPT,
        "error": ERROR_HANDLING_PROMPT,
    }
    
    template = prompts.get(name, "")
    return template.format(**kwargs)