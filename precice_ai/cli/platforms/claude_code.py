from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class ClaudeCodePlatform(Platform):
    """Claude Code CLI — writes to .mcp.json (project) or ~/.claude/settings.json (user)."""

    name = "claude-code"
    display_name = "Claude Code"

    def is_available(self) -> bool:
        result = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True
        )
        return result.returncode == 0

    def install(self, projects_dir: Path, scope: str = "project", **kwargs: Any) -> None:
        entry = self.mcp_entry(projects_dir)

        if scope == "user":
            config_path = Path.home() / ".claude" / "settings.json"
            self._merge_json_config(config_path, entry)
            print(
                f"\n[{self.display_name}] Registered 'precice-ai' at user scope.\n"
                f"  Restart Claude Code to pick up the change."
            )
        else:
            # Project scope — .mcp.json next to where the user ran the command.
            config_path = Path.cwd() / ".mcp.json"
            self._merge_json_config(config_path, entry)
            print(
                f"\n[{self.display_name}] Registered 'precice-ai' in {config_path}.\n"
                f"  Open this directory in Claude Code and the server will be available."
            )
