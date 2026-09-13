from __future__ import annotations

import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


def _relative_to(path: Path, root: Path) -> str | None:
    """Return ``path`` as a POSIX string relative to ``root``, or None if it
    is not inside ``root``. POSIX separators are used deliberately: they work
    on Windows too and keep the generated config stable across platforms.

    Uses ``os.path.abspath`` rather than ``Path.resolve`` so a venv whose
    ``bin/python`` is a symlink to the system interpreter still resolves to
    the repo-relative ``.venv/bin/python``, not the symlink target."""
    try:
        abs_path = Path(os.path.abspath(path))
        abs_root = Path(os.path.abspath(root))
        return abs_path.relative_to(abs_root).as_posix()
    except ValueError:
        return None


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

    def mcp_entry(
        self,
        projects_dir: Path,
        extra_env: dict[str, str] | None = None,
        portable_root: Path | None = None,
    ) -> dict[str, Any]:
        """Return the standard MCP server config block for this package.

        When ``portable_root`` is given (a directory the client launches the
        server from, i.e. cwd == that dir — currently only Claude Code's
        project-scoped ``.mcp.json``), any path that lives under it is written
        as a repo-relative path wrapped in a ``${VAR:-default}`` override so
        the file is not tied to one machine or user. Absolute paths (the venv
        outside the repo, a global install, a projects dir elsewhere) are kept
        verbatim.
        """
        command = sys.executable
        projects_value = str(projects_dir)

        if portable_root is not None:
            root = portable_root.resolve()
            rel_python = _relative_to(Path(sys.executable), root)
            if rel_python is not None:
                command = "${PRECICE_AI_PYTHON:-" + rel_python + "}"
            rel_projects = _relative_to(projects_dir, root)
            if rel_projects is not None:
                projects_value = "${PRECICE_PROJECTS_DIR:-" + rel_projects + "}"

        entry: dict[str, Any] = {
            "command": command,
            "args": ["-m", "precice_ai.server"],
        }
        # Only embed env var if it differs from the convention-based default.
        # Users running from the repo root won't need it; global installs will.
        env = {"PRECICE_PROJECTS_DIR": projects_value}
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
