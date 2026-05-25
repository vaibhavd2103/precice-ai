from precice_ai.cli.platforms.claude_code import ClaudeCodePlatform
from precice_ai.cli.platforms.claude_desktop import ClaudeDesktopPlatform
from precice_ai.cli.platforms.codex import CodexPlatform
from precice_ai.cli.platforms.cursor import CursorPlatform
from precice_ai.cli.platforms.windsurf import WindsurfPlatform
from precice_ai.cli.platforms.generic import GenericPlatform

REGISTRY: dict[str, type] = {
    "claude-code": ClaudeCodePlatform,
    "claude-desktop": ClaudeDesktopPlatform,
    "codex": CodexPlatform,
    "cursor": CursorPlatform,
    "windsurf": WindsurfPlatform,
    "generic": GenericPlatform,
}

__all__ = ["REGISTRY"]
