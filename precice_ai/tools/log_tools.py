from pathlib import Path

from mcp.server.fastmcp import FastMCP

from precice_ai.core.paths import get_project_path, iter_project_files


LOG_EXTENSIONS = ["*.log", "*.txt"]


def register_log_tools(mcp: FastMCP) -> None:
    """Register log-related MCP tools."""

    @mcp.tool()
    def list_project_logs(project_path: str) -> str:
        """List available log files in a preCICE project.

        project_path is the absolute path of the project directory.
        """
        project_dir = get_project_path(project_path)
        if not project_dir.exists():
            return f"Project not found: {project_path}"

        log_files = _find_log_files(project_dir)
        if not log_files:
            return "No log files found."

        lines = ["Log files found:"]
        for log_file in log_files:
            lines.append(f"- {log_file.relative_to(project_dir)}")
        return "\n".join(lines)

    @mcp.tool()
    def read_project_logs(project_path: str, max_chars_per_file: int = 5000) -> str:
        """Read log files from a preCICE tutorial project.

        project_path is the absolute path of the project directory.
        """
        project_dir = get_project_path(project_path)
        if not project_dir.exists():
            return f"Project not found: {project_path}"

        log_files = _find_log_files(project_dir)
        if not log_files:
            return "No log files found."

        logs: list[str] = []
        for log_file in log_files:
            logs.append(f"\n--- {log_file.relative_to(project_dir)} ---\n")
            logs.append(log_file.read_text(errors="ignore")[:max_chars_per_file])
        return "\n".join(logs)

    @mcp.tool()
    def read_latest_log(project_path: str, lines: int = 80) -> str:
        """Read the latest modified log file from a project.

        project_path is the absolute path of the project directory.
        """
        project_dir = get_project_path(project_path)
        if not project_dir.exists():
            return f"Project not found: {project_path}"

        log_files = _find_log_files(project_dir)
        if not log_files:
            return "No log files found."

        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        content = latest_log.read_text(errors="ignore")

        return f"""Latest log file:
{latest_log.relative_to(project_dir)}

Last {lines} lines:
{chr(10).join(content.splitlines()[-lines:])}
"""

    @mcp.tool()
    def analyze_precice_logs(project_path: str) -> str:
        """Analyze preCICE log files and detect common success/failure patterns.

        project_path is the absolute path of the project directory.
        """
        project_dir = get_project_path(project_path)
        if not project_dir.exists():
            return f"Project not found: {project_path}"

        log_files = _find_log_files(project_dir)
        if not log_files:
            return "No log files found."

        report: list[str] = []
        for log_file in log_files:
            content = log_file.read_text(errors="ignore")
            lower_content = content.lower()
            report.append(f"\n--- Log file: {log_file.relative_to(project_dir)} ---")

            if "error" in lower_content:
                report.append("❌ Error detected in log.")
            elif "warning" in lower_content:
                report.append("⚠️ Warning detected in log.")
            else:
                report.append("✅ No obvious errors or warnings found.")

            if "iteration" in lower_content:
                report.append("Coupling iterations detected.")
            if "converged" in lower_content:
                report.append("✅ Convergence information found.")
            if "failed" in lower_content:
                report.append("❌ Failure keyword found.")
            if "exiting" in lower_content or "finished" in lower_content:
                report.append("Simulation appears to have reached an exit/finish state.")

            report.append("\nLast 30 lines:")
            report.append("\n".join(content.splitlines()[-30:]))

        return "\n".join(report)


def _find_log_files(project_dir: Path) -> list[Path]:
    log_files: list[Path] = []
    for pattern in LOG_EXTENSIONS:
        log_files.extend(iter_project_files(project_dir, pattern))
    return sorted(set(log_files))
