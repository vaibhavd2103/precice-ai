from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class CodexPlatform(Platform):
    """OpenAI Codex CLI — manages MCP servers via `codex mcp` and ~/.codex/config.toml."""

    name = "codex"
    display_name = "OpenAI Codex"

    def is_available(self) -> bool:
        return shutil.which("codex") is not None

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        entry = self.mcp_entry(projects_dir, extra_env=kwargs.get("extra_env"))
        codex_bin = shutil.which("codex")
        if codex_bin is None:
            raise SystemExit(
                "Codex CLI is required for `precice-ai bootstrap codex`. "
                "Install Codex and retry, or add the server manually to ~/.codex/config.toml."
            )

        server_names = ("precice-ai", "precice_ai")
        for server_name in server_names:
            subprocess.run(
                [codex_bin, "mcp", "remove", server_name],
                capture_output=True,
                text=True,
                check=False,
            )

        command = [codex_bin, "mcp", "add", server_names[0]]
        for key, value in sorted(entry.get("env", {}).items()):
            command.extend(["--env", f"{key}={value}"])
        command.extend(["--", entry["command"], *entry.get("args", [])])

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as exc:
            details = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise SystemExit(f"Failed to register Codex MCP server via `codex mcp add`: {details}")

        config_path = Path.home() / ".codex" / "config.toml"
        print(
            f"\n[{self.display_name}] Registered 'precice-ai' via `codex mcp add`.\n"
            f"  Config: {config_path}\n"
            f"  Verify: codex mcp get precice-ai\n"
            f"  List:   codex mcp list\n"
            f"  Restart Codex for the change to take effect."
        )

    def can_launch(self) -> bool:
        return shutil.which("codex") is not None

    def launch(self, workspace_dir: Path, **kwargs: Any) -> None:
        self._spawn(["codex"], cwd=workspace_dir)
