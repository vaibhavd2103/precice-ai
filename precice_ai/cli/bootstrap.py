from __future__ import annotations

from pathlib import Path


ENV_TEMPLATE = """# Copied from .env.example by `precice-ai bootstrap`
OPENROUTER_API_KEY={openrouter_api_key}
EMBEDDING_BASE_URL={embedding_base_url}
EMBEDDING_MODEL={embedding_model}
GITHUB_TOKEN={github_token}
"""


def build_client_env(
    openrouter_api_key: str | None,
    embedding_base_url: str | None,
    embedding_model: str | None,
    github_token: str | None,
) -> dict[str, str]:
    env: dict[str, str] = {}
    if openrouter_api_key:
        env["OPENROUTER_API_KEY"] = openrouter_api_key
    if embedding_base_url:
        env["EMBEDDING_BASE_URL"] = embedding_base_url
    if embedding_model:
        env["EMBEDDING_MODEL"] = embedding_model
    if github_token:
        env["GITHUB_TOKEN"] = github_token
    return env


def write_env_file(
    env_path: Path,
    openrouter_api_key: str | None,
    embedding_base_url: str,
    embedding_model: str,
    github_token: str | None,
    force: bool = False,
) -> Path:
    if env_path.exists() and not force:
        return env_path

    env_path.write_text(
        ENV_TEMPLATE.format(
            openrouter_api_key=openrouter_api_key or "",
            embedding_base_url=embedding_base_url,
            embedding_model=embedding_model,
            github_token=github_token or "",
        ),
        encoding="utf-8",
    )
    return env_path
