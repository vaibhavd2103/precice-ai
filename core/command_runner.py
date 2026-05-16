from __future__ import annotations

import subprocess
from pathlib import Path

from core.safety import is_command_safe


def run_safe_command(
    command: str,
    cwd: Path,
    timeout: int = 60,
) -> str:
    """
    Run a command safely inside a given working directory.

    The command is checked before execution.
    """
    is_safe, reason = is_command_safe(command)

    if not is_safe:
        return f"Command blocked for safety: {command}\nReason: {reason}"

    if not cwd.exists():
        return f"Working directory does not exist: {cwd}"

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds: {command}"
    except Exception as exc:
        return f"Command failed to execute: {exc}"

    return f"""Command:
{command}

Working directory:
{cwd}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}

RETURN CODE:
{result.returncode}
"""