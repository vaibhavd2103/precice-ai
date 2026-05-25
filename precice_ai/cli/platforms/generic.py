from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from precice_ai.cli.platforms.base import Platform


class GenericPlatform(Platform):
    """Print the MCP server JSON snippet for manual integration."""

    name = "generic"
    display_name = "Generic (manual)"

    def is_available(self) -> bool:
        return True

    def install(self, projects_dir: Path, **kwargs: Any) -> None:
        entry = self.mcp_entry(projects_dir)
        snippet = {"mcpServers": {"precice-ai": entry}}
        print(
            "\n[Generic] Add this block to your MCP client's config file:\n"
        )
        print(json.dumps(snippet, indent=2))
        print(
            "\nCommon config file locations:\n"
            f"  Claude Code (project):  .mcp.json\n"
            f"  Claude Code (user):     ~/.claude/settings.json\n"
            f"  Claude Desktop (macOS): ~/Library/Application Support/Claude/claude_desktop_config.json\n"
            f"  Cursor:                 ~/.cursor/mcp.json\n"
            f"  Windsurf:               ~/.codeium/windsurf/mcp_config.json\n"
            f"  Codex:                  ~/.codex/mcp.json\n"
        )
