from __future__ import annotations

import shlex


ALLOWED_COMMAND_PREFIXES = [
    "ls",
    "pwd",
    "cat",
    "find",
    "grep",
    "tail",
    "head",
    "precice-tools",
    "precice-cli",
    "python3",
    "./run.sh",
]


BLOCKED_PATTERNS = [
    "rm ",
    "rm -",
    "sudo",
    "chmod",
    "chown",
    "mkfs",
    "dd ",
    ":(){",
    "curl ",
    "wget ",
    "> /dev/",
    "shutdown",
    "reboot",
]


def is_command_safe(command: str) -> tuple[bool, str]:
    """Check whether a command is safe to execute.

    Returns:
        (True, "Allowed") if safe
        (False, reason) if unsafe
    """
    command = command.strip()

    if not command:
        return False, "Empty command is not allowed."

    lowered = command.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            return False, f"Command contains blocked pattern: {pattern}"

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return False, f"Invalid command syntax: {exc}"

    if not parts:
        return False, "Empty command is not allowed."

    executable = parts[0]

    if any(command.startswith(prefix) for prefix in ALLOWED_COMMAND_PREFIXES):
        return True, "Allowed"

    return False, f"Command executable is not allowed: {executable}"


def get_allowed_commands() -> list[str]:
    return ALLOWED_COMMAND_PREFIXES
