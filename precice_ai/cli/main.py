from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from precice_ai.cli.platforms import REGISTRY

app = typer.Typer(
    name="precice-ai",
    help=(
        "preCICE AI MCP server manager.\n\n"
        "Install the MCP server into your preferred AI coding platform so it is\n"
        "automatically available in every session."
    ),
    add_completion=False,
)


@app.command()
def setup(
    platform: str = typer.Argument(
        ...,
        help=(
            "Platform to configure. "
            "Choices: claude-code, claude-desktop, codex, cursor, windsurf, generic"
        ),
    ),
    projects_dir: Optional[Path] = typer.Option(
        None,
        "--projects-dir",
        "-p",
        help=(
            "Absolute path to the directory that contains your preCICE projects. "
            "Defaults to ./test-projects relative to the current working directory."
        ),
        resolve_path=True,
    ),
    scope: str = typer.Option(
        "project",
        "--scope",
        "-s",
        help="[claude-code only] Config scope: 'project' (.mcp.json) or 'user' (~/.claude/settings.json).",
    ),
) -> None:
    """Register the precice-ai MCP server with a supported AI coding platform."""
    key = platform.lower().replace("_", "-")
    platform_cls = REGISTRY.get(key)

    if platform_cls is None:
        available = ", ".join(sorted(REGISTRY))
        typer.echo(f"Unknown platform '{platform}'. Available: {available}", err=True)
        raise typer.Exit(1)

    resolved_projects_dir = projects_dir or (Path.cwd() / "test-projects")

    instance = platform_cls()
    instance.install(projects_dir=resolved_projects_dir, scope=scope)


@app.command(name="list-platforms")
def list_platforms() -> None:
    """List all supported platforms and whether they appear to be installed."""
    typer.echo("Supported platforms:\n")
    for key, cls in sorted(REGISTRY.items()):
        instance = cls()
        available = "✓ detected" if instance.is_available() else "  not detected"
        typer.echo(f"  {key:<20} {available}  ({instance.display_name})")
    typer.echo()


@app.command()
def server() -> None:
    """Start the preCICE AI MCP server (stdio transport)."""
    from precice_ai.server import main
    main()


if __name__ == "__main__":
    app()
