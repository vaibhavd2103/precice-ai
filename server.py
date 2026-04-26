from pathlib import Path
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("preCICE AI")

BASE_DIR = Path(__file__).parent
PROJECTS_DIR = BASE_DIR / "test-projects"


@mcp.tool()
def list_precice_projects() -> list[str]:
    """List available local preCICE tutorial projects."""
    if not PROJECTS_DIR.exists():
        return []
    return [p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()]


@mcp.tool()
def inspect_precice_config(project_name: str) -> str:
    """Read the precice-config.xml file of a project."""
    project_path = PROJECTS_DIR / project_name
    config_file = project_path / "precice-config.xml"

    if not config_file.exists():
        return f"No precice-config.xml found in {project_path}"

    return config_file.read_text()


@mcp.tool()
def run_command_in_project(project_name: str, command: str) -> str:
    """
    Run a safe command inside a preCICE project.
    For now, only allow read/list/test commands.
    """
    allowed_prefixes = [
        "ls",
        "pwd",
        "cat",
        "precice-tools",
        "python3",
        "./run.sh",
    ]

    if not any(command.startswith(prefix) for prefix in allowed_prefixes):
        return f"Command blocked for safety: {command}"

    project_path = PROJECTS_DIR / project_name

    if not project_path.exists():
        return f"Project not found: {project_name}"

    result = subprocess.run(
        command,
        cwd=project_path,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    return f"""
STDOUT:
{result.stdout}

STDERR:
{result.stderr}

RETURN CODE:
{result.returncode}
"""


@mcp.tool()
def read_project_logs(project_name: str) -> str:
    """Read log files from a preCICE tutorial project."""
    project_path = PROJECTS_DIR / project_name

    logs = []
    for file in project_path.rglob("*.log"):
        logs.append(f"\n--- {file.relative_to(project_path)} ---\n")
        logs.append(file.read_text(errors="ignore")[:5000])

    if not logs:
        return "No .log files found."

    return "\n".join(logs)


if __name__ == "__main__":
    mcp.run()