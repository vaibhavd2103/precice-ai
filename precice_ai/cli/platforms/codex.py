from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class CodexPlatform(Platform):
    """OpenAI Codex CLI — writes MCP server entry to ~/.codex/mcp.json."""

    name = "codex"
    display_name = "OpenAI Codex"

    def is_available(self) -> bool:
        return (Path.home() / ".codex").is_dir() or shutil.which("codex") is not None

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        config_path = Path.home() / ".codex" / "mcp.json"
        entry = self.mcp_entry(projects_dir, extra_env=kwargs.get("extra_env"))
        self._merge_json_config(config_path, entry)
        print(
            f"\n[{self.display_name}] Registered 'precice-ai' in:\n"
            f"  {config_path}\n"
            f"  Restart Codex for the change to take effect."
        )

    def can_launch(self) -> bool:
        return shutil.which("codex") is not None

    def launch(self, workspace_dir: Path, **kwargs: Any) -> None:
        self._spawn(["codex"], cwd=workspace_dir)
