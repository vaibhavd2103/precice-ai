from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


def _config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        import os
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    # Linux / other
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


class ClaudeDesktopPlatform(Platform):
    """Claude Desktop app."""

    name = "claude-desktop"
    display_name = "Claude Desktop"

    def is_available(self) -> bool:
        return _config_path().parent.exists()

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        config_path = _config_path()
        entry = self.mcp_entry(projects_dir)
        self._merge_json_config(config_path, entry)
        print(
            f"\n[{self.display_name}] Registered 'precice-ai' in:\n"
            f"  {config_path}\n"
            f"  Restart Claude Desktop to pick up the change."
        )
