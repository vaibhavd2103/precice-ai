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


def get_project_path(project_name: str) -> Path:
    """Return the absolute path of a project, preventing path traversal."""
    projects_dir = get_projects_dir()
    project_path = (projects_dir / project_name).resolve()

    if not str(project_path).startswith(str(projects_dir.resolve())):
        raise ValueError(f"Invalid project path: {project_name}")

    return project_path


def get_precice_config_path(project_name: str) -> Path:
    return get_project_path(project_name) / "precice-config.xml"
