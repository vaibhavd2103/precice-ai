from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "test-projects"


def get_project_path(project_name: str) -> Path:
    """
    Return the absolute path of a project inside test-projects.

    This also prevents path traversal attacks like:
    ../../somewhere-else
    """
    project_path = (PROJECTS_DIR / project_name).resolve()

    if not str(project_path).startswith(str(PROJECTS_DIR.resolve())):
        raise ValueError(f"Invalid project path: {project_name}")

    return project_path


def get_precice_config_path(project_name: str) -> Path:
    """
    Return the expected precice-config.xml path for a project.
    """
    return get_project_path(project_name) / "precice-config.xml"