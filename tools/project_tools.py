from pathlib import Path

from mcp.server.fastmcp import FastMCP

from core.paths import PROJECTS_DIR, get_project_path
from core.command_runner import run_safe_command


def register_project_tools(mcp: FastMCP) -> None:
    """
    Register project-related MCP tools.
    """

    @mcp.tool()
    def list_precice_projects() -> list[str]:
        """
        List available local preCICE tutorial projects.
        """
        if not PROJECTS_DIR.exists():
            return []

        return sorted(
            [
                project.name
                for project in PROJECTS_DIR.iterdir()
                if project.is_dir()
            ]
        )

    @mcp.tool()
    def inspect_project_structure(project_name: str, max_depth: int = 3) -> str:
        """
        Inspect the folder structure of a preCICE project.

        Args:
            project_name: Name of the project inside test-projects.
            max_depth: Maximum folder depth to display.
        """
        project_path = get_project_path(project_name)

        if not project_path.exists():
            return f"Project not found: {project_name}"

        lines: list[str] = [f"Project structure for: {project_name}\n"]

        base_depth = len(project_path.parts)

        for path in sorted(project_path.rglob("*")):
            relative_depth = len(path.parts) - base_depth

            if relative_depth > max_depth:
                continue

            indent = "  " * (relative_depth - 1)
            suffix = "/" if path.is_dir() else ""
            lines.append(f"{indent}- {path.name}{suffix}")

        return "\n".join(lines)

    @mcp.tool()
    def find_precice_config(project_name: str) -> str:
        """
        Find all precice-config.xml files inside a project.
        """
        project_path = get_project_path(project_name)

        if not project_path.exists():
            return f"Project not found: {project_name}"

        config_files = list(project_path.rglob("precice-config.xml"))

        if not config_files:
            return f"No precice-config.xml found in project: {project_name}"

        result = ["Found preCICE config file(s):"]

        for config_file in config_files:
            result.append(f"- {config_file.relative_to(project_path)}")

        return "\n".join(result)

    @mcp.tool()
    def run_command_in_project(project_name: str, command: str) -> str:
        """
        Run a safe command inside a preCICE project.

        Only whitelisted read/list/test commands are allowed.
        """
        project_path = get_project_path(project_name)

        if not project_path.exists():
            return f"Project not found: {project_name}"

        return run_safe_command(command=command, cwd=project_path)