from __future__ import annotations

import os
from pathlib import Path


def get_projects_dir() -> Path:
    """Return the preCICE projects directory.

    Resolved from PRECICE_PROJECTS_DIR env var when set (required for global
    pip installs), otherwise falls back to test-projects/ in the current
    working directory (works when running from the repo root).
    """
    env = os.environ.get("PRECICE_PROJECTS_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd() / "test-projects"


def get_project_path(project_path: str) -> Path:
    """Return the absolute path of a project directory.

    Agents pass the project directory itself, so an absolute path (or one
    starting with ~) is used as given. A bare project name is still resolved
    inside the projects directory, preventing path traversal out of it.
    """
    candidate = Path(project_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()

    projects_dir = get_projects_dir().resolve()
    resolved = (projects_dir / candidate).resolve()

    if not resolved.is_relative_to(projects_dir):
        raise ValueError(f"Invalid project path: {project_path}")

    return resolved


def get_precice_config_path(project_path: str) -> Path:
    return get_project_path(project_path) / "precice-config.xml"


def get_env_file_path() -> Path:
    """Return the .env file to load API keys and other settings from.

    Resolved in order:
    - PRECICE_AI_ENV_FILE env var, if set (explicit override)
    - ./.env in the current working directory, if it already exists (keeps
      the git-clone + `pip install -e .` dev workflow working unchanged)
    - ~/.precice-ai/.env otherwise (stable per-user default for a real
      pip/pipx install, alongside PRECICE_KB_STORE_DIR's ~/.precice-ai home)
    """
    env = os.environ.get("PRECICE_AI_ENV_FILE")
    if env:
        return Path(env).resolve()

    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env

    return Path.home() / ".precice-ai" / ".env"
