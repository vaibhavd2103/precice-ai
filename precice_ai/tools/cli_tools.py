import json
from pathlib import Path

import jsonschema
import yaml
from mcp.server.fastmcp import FastMCP

from precice_ai.core.command_runner import PRECICE_CLI_MISSING, precice_cli_available, run_precice_cli
from precice_ai.core.paths import get_project_path
from precice_ai.core.preflight import preflight

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
    def precice_project_preflight(project_path: str) -> str:
        """Check that a preCICE project can run: dependencies, configuration and solvers.

        ALWAYS call this first when the user asks to check, validate, set up,
        run, start, launch or simulate a preCICE project or tutorial, and
        again after fixing anything it reports. Never start a participant
        (run.sh, a solver, or run_command_in_project) before this returns
        "ready": true.

        It verifies, without changing anything:
        - preCICE itself: precice-cli and the libprecice version;
        - the project: precice-config.xml exists and passes
          `precice-cli config check`;
        - each participant: which <participant>-<solver> case directories
          exist and whether that solver's executables / Python modules are
          installed.

        Returns JSON with "ready", a "problems" list, the per-participant
        cases with their "run_command", and "next_steps" to follow.

        Args:
            project_path: Absolute path of the project directory, as returned
                by list_precice_projects.
        """
        try:
            project_dir = get_project_path(project_path)
        except ValueError as exc:
            return str(exc)
        if not project_dir.is_dir():
            return f"Project not found: {project_path}"
        return json.dumps(preflight(project_dir), indent=2)

    @mcp.tool()
    def precice_version() -> str:
        """Show the installed version of preCICE via precice-cli version."""
        return run_precice_cli("version", cwd=Path.cwd()).format()

    @mcp.tool()
    def precice_config_check(cwd: str, config_file: str = "precice-config.xml") -> str:
        """Validate a preCICE configuration file using precice-cli config check.

        Args:
            cwd: Absolute path to the directory containing the config file.
            config_file: Config filename or relative path (default: precice-config.xml).
        """
        return run_precice_cli(f"config check {config_file}", cwd=Path(cwd), timeout=60).format()

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
        args = f"config visualize {config_file}"
        if output_file:
            args += f" --output {output_file}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=60).format()

    @mcp.tool()
    def precice_config_format(cwd: str, config_file: str = "precice-config.xml") -> str:
        """Format a preCICE configuration file using precice-cli config format.

        Args:
            cwd: Absolute path to the working directory.
            config_file: Config filename or relative path (default: precice-config.xml).
        """
        return run_precice_cli(f"config format {config_file}", cwd=Path(cwd), timeout=60).format()

    @mcp.tool()
    def precice_config_doc(cwd: str, tag: str = "") -> str:
        """Show documentation for preCICE configuration XML tags via precice-cli config doc.

        Args:
            cwd: Absolute path to the working directory.
            tag: Optional specific XML tag to get documentation for.
        """
        args = "config doc"
        if tag:
            args += f" {tag}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=60).format()

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
        if not precice_cli_available():
            return PRECICE_CLI_MISSING

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

        args = "init -f topology.yaml -o generated --validate-topology -v"
        return run_precice_cli(args, cwd=target_dir, timeout=120).format()

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
        args = f"profiling analyze {data_dir}"
        if extra_args:
            args += f" {extra_args}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=120).format()

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
        args = f"profiling trace {data_dir}"
        if extra_args:
            args += f" {extra_args}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=120).format()

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
        args = f"profiling export {data_dir}"
        if output_file:
            args += f" --output {output_file}"
        if extra_args:
            args += f" {extra_args}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=120).format()

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
        args = f"profiling histogram {data_dir}"
        if extra_args:
            args += f" {extra_args}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=120).format()

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
        args = f"profiling merge {data_dirs}"
        if output_dir:
            args += f" --output {output_dir}"
        if extra_args:
            args += f" {extra_args}"
        return run_precice_cli(args, cwd=Path(cwd), timeout=120).format()
