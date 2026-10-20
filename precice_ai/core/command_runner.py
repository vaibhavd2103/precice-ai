from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from precice_ai.core.safety import is_command_safe

PRECICE_CLI_MISSING = "precice-cli is not installed or not in PATH. Install it via: pip install precice"


@dataclass
class CommandResult:
    """Outcome of one command. `error` is set when it never ran (blocked,
    missing working directory, timeout, ...); otherwise `returncode` is."""

    command: str
    cwd: Path
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        return self.error or (self.stdout + self.stderr).strip()

    def format(self) -> str:
        """Text report returned to the agent by the command tools."""
        if self.error:
            return self.error
        return f"""Command:
{self.command}

Working directory:
{self.cwd}

STDOUT:
{self.stdout}

STDERR:
{self.stderr}

RETURN CODE:
{self.returncode}
"""


def run_command(command: str, cwd: Path, timeout: int = 60) -> CommandResult:
    """Run an allowlisted command inside a working directory."""
    result = CommandResult(command=command, cwd=cwd)

    is_safe, reason = is_command_safe(command)
    if not is_safe:
        result.error = f"Command blocked for safety: {command}\nReason: {reason}"
        return result

    if not cwd.exists():
        result.error = f"Working directory does not exist: {cwd}"
        return result

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        result.error = f"Command timed out after {timeout} seconds: {command}"
        return result
    except Exception as exc:
        result.error = f"Command failed to execute: {exc}"
        return result

    result.returncode = completed.returncode
    result.stdout = completed.stdout
    result.stderr = completed.stderr
    return result


def run_safe_command(command: str, cwd: Path, timeout: int = 60) -> str:
    """Run a command safely inside a given working directory and report it as text."""
    return run_command(command, cwd, timeout).format()


def precice_cli_available() -> bool:
    return shutil.which("precice-cli") is not None


def run_precice_cli(args: str, cwd: Path, timeout: int = 60) -> CommandResult:
    """Run `precice-cli <args>`; the single entry point for every precice-cli call."""
    command = f"precice-cli {args}"
    if not precice_cli_available():
        return CommandResult(command=command, cwd=cwd, error=PRECICE_CLI_MISSING)
    return run_command(command, cwd, timeout)
