from __future__ import annotations

import json
from typing import Any

from precice_ai.cli.platforms.base import Platform


class GenericPlatform(Platform):
    """Print the MCP server JSON snippet for manual integration."""

    name = "generic"
    display_name = "Generic (manual)"

    def is_available(self) -> bool:
        return True

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        entry = self.mcp_entry(projects_dir, extra_env=kwargs.get("extra_env"))
        snippet = {"mcpServers": {"precice-ai": entry}}
        codex_lines = [
            '[mcp_servers."precice-ai"]',
            f'command = {json.dumps(entry["command"])}',
            f'args = {json.dumps(entry["args"])}',
            "",
            '[mcp_servers."precice-ai".env]',
        ]
        for key, value in sorted(entry.get("env", {}).items()):
            codex_lines.append(f"{key} = {json.dumps(value)}")
        print(
            "\n[Generic] Add this block to your MCP client's config file:\n"
        )
        print(json.dumps(snippet, indent=2))
        print(
            "\nCodex uses TOML instead of JSON. Add this block to ~/.codex/config.toml:\n"
        )
        print("\n".join(codex_lines))
        print(
            "\nCommon config file locations:\n"
            f"  Claude Code (project):  .mcp.json\n"
            f"  Claude Code (user):     ~/.claude/settings.json\n"
            f"  Claude Desktop (macOS): ~/Library/Application Support/Claude/claude_desktop_config.json\n"
            f"  Cursor (project):       .cursor/mcp.json\n"
            f"  Cursor (global):        ~/.cursor/mcp.json\n"
            f"  Windsurf:               ~/.codeium/windsurf/mcp_config.json\n"
            f"  Codex:                  ~/.codex/config.toml\n"
        )
