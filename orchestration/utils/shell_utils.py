"""Shell utilities"""

import subprocess
from typing import Optional, List


def run_cmd(cmd: str, shell: bool = True, capture: bool = True) -> Optional[str]:
    """Run shell command"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture, text=True, timeout=30
        )
        return result.stdout if capture else None
    except Exception as e:
        return None


def run_bg(cmd: str):
    """Run command in background"""
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def which(program: str) -> Optional[str]:
    """Find program in PATH"""
    return run_cmd(f"which {program}")


def is_command_available(cmd: str) -> bool:
    """Check if command is available"""
    return which(cmd) is not None
