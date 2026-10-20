from pathlib import Path

from mcp.server.fastmcp import FastMCP

from precice_ai.core.paths import get_project_path, iter_project_files
from precice_ai.core.command_runner import run_safe_command


def register_project_tools(mcp: FastMCP) -> None:
    """Register project-related MCP tools."""

    @mcp.tool()
    def list_precice_projects(path: str) -> list[str]:
        """List the preCICE projects (case directories) inside a directory.

        Args:
            path: Absolute path of the directory to scan, e.g. the user's
                current workspace. The server does not assume a default
                location, so always pass it.

        Returns the absolute path of every sub-directory. Pass one of them as
        project_path to the other project, config and log tools.
        """
        projects_dir = Path(path).expanduser().resolve()
        if not projects_dir.is_dir():
            raise ValueError(f"Not a directory: {projects_dir}")
        return sorted(
            str(project)
            for project in projects_dir.iterdir()
            if project.is_dir() and not project.name.startswith(".")
        )

    @mcp.tool()
    def inspect_project_structure(project_path: str, max_depth: int = 3) -> str:
        """Inspect the folder structure of a preCICE project.

        Args:
            project_path: Absolute path of the project directory, as returned by list_precice_projects.
            max_depth: Maximum folder depth to display.
        """
        project_dir = get_project_path(project_path)

        if not project_dir.exists():
            return f"Project not found: {project_path}"

        lines: list[str] = [f"Project structure for: {project_path}\n"]
        base_depth = len(project_dir.parts)

        for path in iter_project_files(project_dir):
            relative_depth = len(path.parts) - base_depth
            if relative_depth > max_depth:
                continue
            indent = "  " * (relative_depth - 1)
            suffix = "/" if path.is_dir() else ""
            lines.append(f"{indent}- {path.name}{suffix}")

        return "\n".join(lines)

    @mcp.tool()
    def find_precice_config(project_path: str) -> str:
        """Find all precice-config.xml files inside a project.

        Args:
            project_path: Absolute path of the project directory.
        """
        project_dir = get_project_path(project_path)

        if not project_dir.exists():
            return f"Project not found: {project_path}"

        config_files = iter_project_files(project_dir, "precice-config.xml")

        if not config_files:
            return f"No precice-config.xml found in project: {project_path}"

        result = ["Found preCICE config file(s):"]
        for config_file in config_files:
            result.append(f"- {config_file.relative_to(project_dir)}")

        return "\n".join(result)

    @mcp.tool()
    def run_command_in_project(project_path: str, command: str) -> str:
        """Run a safe command inside a preCICE project.

        Only allowlisted read/list/test commands are permitted.

        Args:
            project_path: Absolute path of the project directory.
            command: The command to run with the project directory as cwd.
        """
        project_dir = get_project_path(project_path)

        if not project_dir.exists():
            return f"Project not found: {project_path}"

        return run_safe_command(command=command, cwd=project_dir)
