from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class ClaudeCodePlatform(Platform):
    """Claude Code CLI — writes to .mcp.json (project) or ~/.claude.json (user)."""

    name = "claude-code"
    display_name = "Claude Code"

    def is_available(self) -> bool:
        result = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True
        )
        return result.returncode == 0

    def install(self, projects_dir: Path, scope: str = "project", **kwargs: Any) -> None:
        entry = self.mcp_entry(projects_dir, extra_env=kwargs.get("extra_env"))

        if scope == "user":
            config_path = Path.home() / ".claude.json"
            self._merge_json_config(config_path, entry)
            print(
                f"\n[{self.display_name}] Registered 'precice-ai' at user scope.\n"
                f"  Restart Claude Code to pick up the change."
            )
        else:
            # Project scope — .mcp.json next to where the user ran the command.
            config_path = Path.cwd() / ".mcp.json"
            self._merge_json_config(config_path, entry)
            self._approve_project_server(Path.cwd())
            print(
                f"\n[{self.display_name}] Registered 'precice-ai' in {config_path}.\n"
                f"  Restart Claude Code in this directory and the server will be available."
            )

    def _approve_project_server(self, project_dir: Path) -> None:
        """Mark 'precice-ai' as an approved .mcp.json server for this project.

        Claude Code normally asks for interactive confirmation the first time
        it sees a new (or changed) project-scoped MCP server, via a trust
        prompt tracked per-project in ~/.claude.json. Since this installer is
        the trusted source adding the entry in the first place, pre-approve
        it here so the server loads without that extra manual step.
        """
        claude_config_path = Path.home() / ".claude.json"
        config = self._load_json_config(claude_config_path)

        project_key = str(project_dir)
        project_entry = config.setdefault("projects", {}).setdefault(project_key, {})

        enabled = project_entry.setdefault("enabledMcpjsonServers", [])
        if "precice-ai" not in enabled:
            enabled.append("precice-ai")

        disabled = project_entry.setdefault("disabledMcpjsonServers", [])
        if "precice-ai" in disabled:
            disabled.remove("precice-ai")

        claude_config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def can_launch(self) -> bool:
        return True

    def launch(self, workspace_dir: Path, **kwargs: Any) -> None:
        self._spawn(["claude"], cwd=workspace_dir)
