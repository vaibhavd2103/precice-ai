from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class WindsurfPlatform(Platform):
    """Windsurf (Codeium) — writes MCP config to ~/.codeium/windsurf/mcp_config.json."""

    name = "windsurf"
    display_name = "Windsurf"

    def is_available(self) -> bool:
        return (Path.home() / ".codeium" / "windsurf").is_dir() or shutil.which("windsurf") is not None

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        config_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
        entry = self.mcp_entry(projects_dir, extra_env=kwargs.get("extra_env"))
        self._merge_json_config(config_path, entry)
        print(
            f"\n[{self.display_name}] Registered 'precice-ai' in:\n"
            f"  {config_path}\n"
            f"  Restart Windsurf to pick up the change."
        )

    def can_launch(self) -> bool:
        return shutil.which("windsurf") is not None

    def launch(self, workspace_dir: Path, **kwargs: Any) -> None:
        self._spawn(["windsurf", "."], cwd=workspace_dir)
