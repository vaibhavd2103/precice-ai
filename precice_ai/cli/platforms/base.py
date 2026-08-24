from __future__ import annotations

import json
import subprocess
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

    def can_launch(self) -> bool:
        """Return True if this platform can be launched from the CLI."""
        return False

    def launch(self, workspace_dir: Path, **kwargs: Any) -> None:
        """Launch the platform, opening the given workspace when supported."""
        raise NotImplementedError(f"{self.display_name} does not support launch from this CLI.")

    def _spawn(self, args: list[str], cwd: Path) -> None:
        subprocess.Popen(args, cwd=str(cwd))

    def mcp_entry(self, projects_dir: Path, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
        """Return the standard MCP server config block for this package."""
        entry: dict[str, Any] = {
            "command": sys.executable,
            "args": ["-m", "precice_ai.server"],
        }
        # Only embed env var if it differs from the convention-based default.
        # Users running from the repo root won't need it; global installs will.
        env = {"PRECICE_PROJECTS_DIR": str(projects_dir)}
        if extra_env:
            env.update(extra_env)
        entry["env"] = env
        return entry

    def _load_json_config(self, config_path: Path) -> dict[str, Any]:
        """Read a JSON config, or {} if it doesn't exist yet.

        Raises instead of silently discarding the file's contents if it exists
        but fails to parse — this may be a large, otherwise-unrelated config
        file (e.g. ~/.claude.json), and clobbering it on a parse error would
        destroy state that has nothing to do with this installer.
        """
        if not config_path.exists():
            return {}
        text = config_path.read_text(encoding="utf-8")
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"{config_path} exists but isn't valid JSON ({exc}). "
                "Fix or remove it and re-run, so this doesn't overwrite the file."
            ) from exc

    def _merge_json_config(self, config_path: Path, entry: dict[str, Any]) -> None:
        """Read (or create) a JSON config, inject the mcpServers entry, write back."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = self._load_json_config(config_path)
        config.setdefault("mcpServers", {})["precice-ai"] = entry
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  Updated: {config_path}")
