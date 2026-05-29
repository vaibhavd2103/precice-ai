import shutil
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from precice_ai.core.command_runner import run_safe_command


def _check_precice_cli() -> str | None:
    if shutil.which("precice-cli") is None:
        return "precice-cli is not installed or not in PATH. Install it via: pip install precice"
    return None


def register_cli_tools(mcp: FastMCP) -> None:
    """Register MCP tools that wrap precice-cli commands."""

    @mcp.tool()
    def precice_version() -> str:
        """Show the installed version of preCICE via precice-cli version."""
        if err := _check_precice_cli():
            return err
        return run_safe_command(command="precice-cli version", cwd=Path.cwd())

    @mcp.tool()
    def precice_config_check(cwd: str, config_file: str = "precice-config.xml") -> str:
        """Validate a preCICE configuration file using precice-cli config check.

        Args:
            cwd: Absolute path to the directory containing the config file.
            config_file: Config filename or relative path (default: precice-config.xml).
        """
        if err := _check_precice_cli():
            return err
        return run_safe_command(
            command=f"precice-cli config check {config_file}",
            cwd=Path(cwd),
            timeout=60,
        )

    @mcp.tool()
    def precice_config_visualize(
        cwd: str,
        config_file: str = "precice-config.xml",
        output_file: str = "",
    ) -> str:
        """Generate a visualization of a preCICE configuration file via precice-cli config visualize.

        Args:
            cwd: Absolute path to the working directory.
            config_file: Config filename or relative path (default: precice-config.xml).
            output_file: Optional output file path for the visualization.
        """
        if err := _check_precice_cli():
            return err
        cmd = f"precice-cli config visualize {config_file}"
        if output_file:
            cmd += f" --output {output_file}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=60)

    @mcp.tool()
    def precice_config_format(cwd: str, config_file: str = "precice-config.xml") -> str:
        """Format a preCICE configuration file using precice-cli config format.

        Args:
            cwd: Absolute path to the working directory.
            config_file: Config filename or relative path (default: precice-config.xml).
        """
        if err := _check_precice_cli():
            return err
        return run_safe_command(
            command=f"precice-cli config format {config_file}",
            cwd=Path(cwd),
            timeout=60,
        )

    @mcp.tool()
    def precice_config_doc(cwd: str, tag: str = "") -> str:
        """Show documentation for preCICE configuration XML tags via precice-cli config doc.

        Args:
            cwd: Absolute path to the working directory.
            tag: Optional specific XML tag to get documentation for.
        """
        if err := _check_precice_cli():
            return err
        cmd = "precice-cli config doc"
        if tag:
            cmd += f" {tag}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=60)

    @mcp.tool()
    def precice_init(cwd: str, extra_args: str = "") -> str:
        """Generate a new preCICE configuration scaffold using precice-cli init.

        Args:
            cwd: Absolute path to the directory where config should be generated.
            extra_args: Optional additional arguments passed to precice-cli init.
        """
        if err := _check_precice_cli():
            return err
        cmd = "precice-cli init"
        if extra_args:
            cmd += f" {extra_args}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=120)

    @mcp.tool()
    def precice_profiling_analyze(
        cwd: str, data_dir: str = ".", extra_args: str = ""
    ) -> str:
        """Analyze preCICE profiling output using precice-cli profiling analyze.

        Args:
            cwd: Absolute path to the working directory.
            data_dir: Path to the directory containing profiling files (default: .).
            extra_args: Optional additional arguments.
        """
        if err := _check_precice_cli():
            return err
        cmd = f"precice-cli profiling analyze {data_dir}"
        if extra_args:
            cmd += f" {extra_args}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=120)

    @mcp.tool()
    def precice_profiling_trace(
        cwd: str, data_dir: str = ".", extra_args: str = ""
    ) -> str:
        """Generate a trace visualization from preCICE profiling data via precice-cli profiling trace.

        Args:
            cwd: Absolute path to the working directory.
            data_dir: Path to the directory containing profiling files.
            extra_args: Optional additional arguments.
        """
        if err := _check_precice_cli():
            return err
        cmd = f"precice-cli profiling trace {data_dir}"
        if extra_args:
            cmd += f" {extra_args}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=120)

    @mcp.tool()
    def precice_profiling_export(
        cwd: str,
        data_dir: str = ".",
        output_file: str = "",
        extra_args: str = "",
    ) -> str:
        """Export preCICE profiling data using precice-cli profiling export.

        Args:
            cwd: Absolute path to the working directory.
            data_dir: Path to the directory containing profiling files.
            output_file: Optional output file path.
            extra_args: Optional additional arguments.
        """
        if err := _check_precice_cli():
            return err
        cmd = f"precice-cli profiling export {data_dir}"
        if output_file:
            cmd += f" --output {output_file}"
        if extra_args:
            cmd += f" {extra_args}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=120)

    @mcp.tool()
    def precice_profiling_histogram(
        cwd: str, data_dir: str = ".", extra_args: str = ""
    ) -> str:
        """Generate a histogram from preCICE profiling data via precice-cli profiling histogram.

        Args:
            cwd: Absolute path to the working directory.
            data_dir: Path to the directory containing profiling files.
            extra_args: Optional additional arguments.
        """
        if err := _check_precice_cli():
            return err
        cmd = f"precice-cli profiling histogram {data_dir}"
        if extra_args:
            cmd += f" {extra_args}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=120)

    @mcp.tool()
    def precice_profiling_merge(
        cwd: str,
        data_dirs: str,
        output_dir: str = "",
        extra_args: str = "",
    ) -> str:
        """Merge multiple preCICE profiling datasets via precice-cli profiling merge.

        Args:
            cwd: Absolute path to the working directory.
            data_dirs: Space-separated list of profiling data directories to merge.
            output_dir: Optional output directory for merged data.
            extra_args: Optional additional arguments.
        """
        if err := _check_precice_cli():
            return err
        cmd = f"precice-cli profiling merge {data_dirs}"
        if output_dir:
            cmd += f" --output {output_dir}"
        if extra_args:
            cmd += f" {extra_args}"
        return run_safe_command(command=cmd, cwd=Path(cwd), timeout=120)
