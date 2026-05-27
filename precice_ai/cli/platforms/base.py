from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Platform(ABC):
    name: str
    display_name: str

    @abstractmethod
    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        """Write the MCP server entry into this platform's config file."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this platform appears to be installed."""
        ...

    def mcp_entry(self, projects_dir: Path) -> dict[str, Any]:
        """Return the standard MCP server config block for this package."""
        entry: dict[str, Any] = {
            "command": sys.executable,
            "args": ["-m", "precice_ai.server"],
        }
        # Only embed env var if it differs from the convention-based default.
        # Users running from the repo root won't need it; global installs will.
        entry["env"] = {"PRECICE_PROJECTS_DIR": str(projects_dir)}
        return entry

    def _merge_json_config(self, config_path: Path, entry: dict[str, Any]) -> None:
        """Read (or create) a JSON config, inject the mcpServers entry, write back."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config: dict[str, Any] = {}
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                config = {}

        config.setdefault("mcpServers", {})["precice-ai"] = entry
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  Updated: {config_path}")
