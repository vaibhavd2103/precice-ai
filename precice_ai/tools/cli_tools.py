import json
import shutil
from pathlib import Path

import jsonschema
import yaml
from mcp.server.fastmcp import FastMCP

from precice_ai.core.command_runner import run_safe_command
from precice_ai.core.paths import get_project_path

TOPOLOGY_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "utils" / "topology_schema.json"

# The installed precice-case-generate still requires an explicit
# coupling-scheme key to be present, even though topology_schema.json no
# longer requires it (those values are meant to be inferred/defaulted).
# Inject these defaults so generation doesn't crash on that version lag.
DEFAULT_COUPLING_SCHEME = {
    "max-time": 1.0,
    "time-window-size": 0.01,
    "max-iterations": 50,
    "coupling": "parallel",
}


def _check_precice_cli() -> str | None:
    if shutil.which("precice-cli") is None:
        return "precice-cli is not installed or not in PATH. Install it via: pip install precice"
    return None


def _load_topology_schema() -> dict:
    return json.loads(TOPOLOGY_SCHEMA_PATH.read_text())


def _validate_topology(topology: dict) -> list[str]:
    """Validate a topology dict against topology_schema.json.

    Returns a list of human-readable error messages (empty if valid).
    """
    schema = _load_topology_schema()
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(topology), key=lambda e: list(e.path))
    return [
        f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors
    ]


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
    def precice_init(
        project_name: str,
        participants: list[dict],
        exchanges: list[dict],
        coupling_scheme: dict | None = None,
        output_dir: str = "",
    ) -> str:
        """Create a new preCICE case from topology details and run precice-cli init.

        Validates participants/exchanges/coupling_scheme against
        precice_ai/utils/topology_schema.json. If required details are
        missing or invalid, no files are written or executed -- instead a
        list of validation errors is returned. Ask the user for the missing
        details and call this tool again with the complete topology.

        Once validation passes, writes topology.yaml to
        test-projects/<project_name> (or output_dir if given), then runs
        `precice-cli init` against it with --validate-topology.

        Args:
            project_name: Case name; determines the default test-projects/<project_name> location.
            participants: List of dicts per topology_schema.json, e.g.
                {"name": "Fluid", "solver": "OpenFOAM", "dimensionality": 3}.
            exchanges: List of dicts per topology_schema.json, e.g.
                {"from": "Fluid", "from-patch": "interface", "to": "Solid",
                 "to-patch": "interface", "data": "Force", "data-type": "vector",
                 "type": "strong"}.
            coupling_scheme: Optional dict with max-time, time-window-size,
                max-iterations, coupling ("parallel"/"serial"). Defaults are
                applied for any keys omitted.
            output_dir: Optional absolute path overriding the test-projects default.
        """
        if err := _check_precice_cli():
            return err

        topology = {"participants": participants, "exchanges": exchanges}
        errors = _validate_topology(topology)
        if errors:
            return (
                "Topology is incomplete or invalid. Please provide the following "
                "before the project can be created:\n"
                + "\n".join(f"- {e}" for e in errors)
            )

        full_topology = {
            "coupling-scheme": {**DEFAULT_COUPLING_SCHEME, **(coupling_scheme or {})},
            "participants": participants,
            "exchanges": exchanges,
        }

        try:
            target_dir = (
                Path(output_dir).resolve() if output_dir else get_project_path(project_name)
            )
        except ValueError as exc:
            return str(exc)

        target_dir.mkdir(parents=True, exist_ok=True)
        topology_path = target_dir / "topology.yaml"
        topology_path.write_text(yaml.dump(full_topology, sort_keys=False))

        cmd = "precice-cli init -f topology.yaml -o generated --validate-topology -v"
        return run_safe_command(command=cmd, cwd=target_dir, timeout=120)

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
