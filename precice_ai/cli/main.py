from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from precice_ai.cli.bootstrap import build_client_env, write_env_file
from precice_ai.cli.platforms import REGISTRY

# Same .env lookup as precice_ai/server.py, so OPENROUTER_API_KEY / GITHUB_TOKEN
# picked up by the MCP server are also available to these CLI debug commands.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

app = typer.Typer(
    name="precice-ai",
    help=(
        "preCICE AI MCP server manager.\n\n"
        "Install the MCP server into your preferred AI coding platform so it is\n"
        "automatically available in every session."
    ),
    add_completion=False,
)

kb_app = typer.Typer(
    name="kb",
    help=(
        "Inspect and debug the knowledge base directly — calls the same "
        "code the MCP tools use, without going through an LLM/MCP client."
    ),
)
app.add_typer(kb_app, name="kb")


def _configure_logging(verbose: bool) -> None:
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


def _detect_platform(launchable_only: bool = False) -> str | None:
    for key in ("claude-code", "codex", "cursor", "windsurf", "claude-desktop"):
        platform_cls = REGISTRY.get(key)
        if not platform_cls:
            continue
        instance = platform_cls()
        if not instance.is_available():
            continue
        if launchable_only and not instance.can_launch():
            continue
        return key
    return None


def _resolve_platform(platform: str, launchable_only: bool = False) -> str:
    key = platform.lower().replace("_", "-")
    if key == "auto":
        detected = _detect_platform(launchable_only=launchable_only)
        if detected is None:
            available = ", ".join(sorted(REGISTRY))
            typer.echo(
                "Could not auto-detect a supported MCP client. "
                f"Run `precice-ai list-platforms` or choose one manually: {available}",
                err=True,
            )
            raise typer.Exit(1)
        typer.echo(f"Auto-detected MCP client: {detected}")
        return detected
    return key


def _build_extra_env(
    openrouter_api_key: Optional[str],
    embedding_base_url: Optional[str],
    embedding_model: Optional[str],
    github_token: Optional[str],
) -> dict[str, str]:
    return build_client_env(
        openrouter_api_key=openrouter_api_key,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        github_token=github_token,
    )


@app.command()
def setup(
    platform: str = typer.Argument(
        ...,
        help=(
            "Platform to configure. "
            "Choices: auto, claude-code, claude-desktop, codex, cursor, windsurf, generic"
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
    openrouter_api_key: Optional[str] = typer.Option(
        None,
        "--openrouter-api-key",
        help="Also inject OPENROUTER_API_KEY into the MCP client config.",
    ),
    embedding_base_url: Optional[str] = typer.Option(
        None,
        "--embedding-base-url",
        help="Also inject EMBEDDING_BASE_URL into the MCP client config.",
    ),
    embedding_model: Optional[str] = typer.Option(
        None,
        "--embedding-model",
        help="Also inject EMBEDDING_MODEL into the MCP client config.",
    ),
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        help="Also inject GITHUB_TOKEN into the MCP client config.",
    ),
) -> None:
    """Register the precice-ai MCP server with a supported AI coding platform."""
    key = _resolve_platform(platform)
    platform_cls = REGISTRY.get(key)

    if platform_cls is None:
        available = ", ".join(sorted(REGISTRY))
        typer.echo(f"Unknown platform '{platform}'. Available: {available}", err=True)
        raise typer.Exit(1)

    resolved_projects_dir = projects_dir or (Path.cwd() / "test-projects")
    extra_env = _build_extra_env(
        openrouter_api_key=openrouter_api_key,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        github_token=github_token,
    )

    instance = platform_cls()
    instance.install(projects_dir=resolved_projects_dir, scope=scope, extra_env=extra_env)


@app.command()
def bootstrap(
    platform: str = typer.Argument(
        "auto",
        help=(
            "Platform to configure. "
            "Choices: auto, claude-code, claude-desktop, codex, cursor, windsurf, generic"
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
    openrouter_api_key: Optional[str] = typer.Option(
        None,
        "--openrouter-api-key",
        help="Write OPENROUTER_API_KEY to .env and inject it into the MCP client config.",
    ),
    embedding_base_url: str = typer.Option(
        "https://openrouter.ai/api/v1",
        "--embedding-base-url",
        help="Write EMBEDDING_BASE_URL to .env and inject it into the MCP client config.",
    ),
    embedding_model: str = typer.Option(
        "openai/text-embedding-3-small",
        "--embedding-model",
        help="Write EMBEDDING_MODEL to .env and inject it into the MCP client config.",
    ),
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        help="Write GITHUB_TOKEN to .env and inject it into the MCP client config.",
    ),
    env_file: Path = typer.Option(
        Path(".env"),
        "--env-file",
        help="Path to the .env file to create or update.",
        resolve_path=False,
    ),
    force_env: bool = typer.Option(
        False,
        "--force-env",
        help="Overwrite the env file if it already exists.",
    ),
) -> None:
    """Create .env values and register the MCP server with a supported client."""
    resolved_projects_dir = projects_dir or (Path.cwd() / "test-projects")
    resolved_platform = _resolve_platform(platform)
    resolved_env_file = env_file if env_file.is_absolute() else (Path.cwd() / env_file)

    write_env_file(
        env_path=resolved_env_file,
        openrouter_api_key=openrouter_api_key,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        github_token=github_token,
        force=force_env,
    )

    if force_env:
        typer.echo(f"Wrote environment file: {resolved_env_file}")
    elif resolved_env_file.exists():
        typer.echo(f"Environment file ready: {resolved_env_file}")

    extra_env = _build_extra_env(
        openrouter_api_key=openrouter_api_key,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        github_token=github_token,
    )

    platform_cls = REGISTRY.get(resolved_platform)
    if platform_cls is None:
        available = ", ".join(sorted(REGISTRY))
        typer.echo(f"Unknown platform '{platform}'. Available: {available}", err=True)
        raise typer.Exit(1)

    instance = platform_cls()
    instance.install(projects_dir=resolved_projects_dir, scope=scope, extra_env=extra_env)


@app.command()
def open(
    platform: str = typer.Argument(
        "auto",
        help=(
            "Platform to configure and launch. "
            "Choices: auto, claude-code, codex, cursor, windsurf"
        ),
    ),
    projects_dir: Optional[Path] = typer.Option(
        None,
        "--projects-dir",
        "-p",
        help=(
            "Project directory to expose to the MCP server. "
            "Defaults to the current working directory."
        ),
        resolve_path=True,
    ),
    scope: str = typer.Option(
        "project",
        "--scope",
        "-s",
        help="[claude-code only] Config scope: 'project' (.mcp.json) or 'user' (~/.claude/settings.json).",
    ),
    openrouter_api_key: Optional[str] = typer.Option(
        None,
        "--openrouter-api-key",
        help="Also inject OPENROUTER_API_KEY into the MCP client config.",
    ),
    embedding_base_url: Optional[str] = typer.Option(
        None,
        "--embedding-base-url",
        help="Also inject EMBEDDING_BASE_URL into the MCP client config.",
    ),
    embedding_model: Optional[str] = typer.Option(
        None,
        "--embedding-model",
        help="Also inject EMBEDDING_MODEL into the MCP client config.",
    ),
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        help="Also inject GITHUB_TOKEN into the MCP client config.",
    ),
) -> None:
    """Use the current folder as projects dir, register the MCP server, and launch the client."""
    resolved_platform = _resolve_platform(platform, launchable_only=True)
    resolved_projects_dir = (projects_dir or Path.cwd()).resolve()
    extra_env = _build_extra_env(
        openrouter_api_key=openrouter_api_key,
        embedding_base_url=embedding_base_url,
        embedding_model=embedding_model,
        github_token=github_token,
    )

    platform_cls = REGISTRY.get(resolved_platform)
    if platform_cls is None:
        available = ", ".join(sorted(REGISTRY))
        typer.echo(f"Unknown platform '{platform}'. Available: {available}", err=True)
        raise typer.Exit(1)

    instance = platform_cls()
    instance.install(projects_dir=resolved_projects_dir, scope=scope, extra_env=extra_env)
    typer.echo(f"Active preCICE projects directory: {resolved_projects_dir}")

    if not instance.can_launch():
        typer.echo(
            f"{instance.display_name} was configured, but launching it from `precice-ai open` "
            "is not supported on this machine."
        )
        raise typer.Exit(0)

    instance.launch(workspace_dir=resolved_projects_dir, scope=scope)
    typer.echo(f"Launched {instance.display_name} in: {resolved_projects_dir}")


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


@kb_app.command("status")
def kb_status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs (incl. HTTP requests)."),
) -> None:
    """Show local vector + lexical KB file status (size, last check, chunk counts)."""
    _configure_logging(verbose)
    from precice_ai.core.knowledge_base import KnowledgeBaseService, VectorKnowledgeBase

    result = {
        "vector": VectorKnowledgeBase().status(),
        "lexical": KnowledgeBaseService().kb_status(),
    }
    typer.echo(json.dumps(result, indent=2))


@kb_app.command("ingest")
def kb_ingest(
    category: Optional[str] = typer.Option(
        None, "--category", "-c",
        help="Only sync this vector category (about, community, documentation, tutorials, forum, issues, pulls).",
    ),
    github_token: Optional[str] = typer.Option(
        None, "--github-token", help="Defaults to $GITHUB_TOKEN if unset (only needed for a private repo)."
    ),
    skip_lexical: bool = typer.Option(False, "--skip-lexical", help="Only sync the vector KB."),
    skip_vector: bool = typer.Option(False, "--skip-vector", help="Only sync the lexical KB."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs (incl. HTTP requests)."),
) -> None:
    """Sync the local KB from the kb-latest GitHub Release (same as kb_ingest_precice_data).

    Trusts the local copy for up to 48h since the last check (no network
    call); past that, always re-downloads. Use --verbose to see exactly
    which HTTP calls are made and why a given asset was (or wasn't) refetched.
    """
    _configure_logging(verbose)
    from precice_ai.core.knowledge_base import KnowledgeBaseService, VectorKnowledgeBase

    token = github_token or os.environ.get("GITHUB_TOKEN")
    result: dict[str, object] = {}
    if not skip_vector:
        result["vector"] = VectorKnowledgeBase().download_from_release(github_token=token, category=category)
    if not skip_lexical:
        result["lexical"] = KnowledgeBaseService().sync_from_release(github_token=token)
    typer.echo(json.dumps(result, indent=2))


@kb_app.command("query")
def kb_query(
    question: str = typer.Argument(..., help="Question to search for."),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Restrict vector modes to one category; omit to search all downloaded ones."
    ),
    mode: str = typer.Option(
        "vector-live", "--mode", "-m",
        help="vector-live (auto-sync + semantic search, same as kb_query_precice_live) | "
             "vector (semantic search, local cache only, no sync) | "
             "lexical (keyword/BM25 search, same as kb_query_precice_lexical).",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs (incl. HTTP requests)."),
) -> None:
    """Query the local KB directly, exactly like the MCP tools would, printing raw JSON results."""
    _configure_logging(verbose)
    from precice_ai.core.knowledge_base import KnowledgeBaseService, VectorKnowledgeBase

    if mode == "lexical":
        result = KnowledgeBaseService().query_with_optional_live_refresh(question=question, top_k=top_k)
    elif mode == "vector":
        result = VectorKnowledgeBase().query(question=question, top_k=top_k, category=category)
    elif mode == "vector-live":
        vkb = VectorKnowledgeBase()
        token = os.environ.get("GITHUB_TOKEN")
        dl = vkb.download_from_release(github_token=token, category=category)
        if dl.get("status") == "error":
            typer.echo(json.dumps(dl, indent=2))
            raise typer.Exit(1)
        result = vkb.query(question=question, top_k=top_k, category=category)
    else:
        typer.echo(f"Unknown mode {mode!r}. Choose vector-live | vector | lexical.", err=True)
        raise typer.Exit(1)

    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()
