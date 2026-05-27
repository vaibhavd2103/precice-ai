from __future__ import annotations

from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class CursorPlatform(Platform):
    """Cursor IDE — writes MCP server entry to ~/.cursor/mcp.json."""

    name = "cursor"
    display_name = "Cursor"

    def is_available(self) -> bool:
        return (Path.home() / ".cursor").is_dir()

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        config_path = Path.home() / ".cursor" / "mcp.json"
        entry = self.mcp_entry(projects_dir)
        self._merge_json_config(config_path, entry)
        print(
            f"\n[{self.display_name}] Registered 'precice-ai' in:\n"
            f"  {config_path}\n"
            f"  Reload Cursor (Cmd/Ctrl+Shift+P → Reload Window) to pick up the change."
        )
