"""Pre-run checks for a preCICE project: is preCICE installed, is the
configuration valid, and are the solvers of each participant case available.

Read-only: nothing is installed, built or started here. The result tells the
agent whether the case can be run and what is missing if it cannot.

To support another solver, add one entry to SOLVERS.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from precice_ai.core.command_runner import PRECICE_CLI_MISSING, run_command, run_precice_cli
from precice_ai.core.config_xml import parse_precice_config
from precice_ai.core.paths import iter_project_files

_BUILD_FIRST = "The solver executable must be built first (see the case README)."

# What a participant case needs, keyed by the solver token in its directory
# name (the preCICE tutorials convention: <participant>-<solver>, e.g.
# fluid-openfoam). "executables" must be on PATH, "python_modules" must be
# importable by the python3 on PATH, "note" is passed on to the agent.
# Solvers not listed are reported as "unknown" so the agent checks run.sh
# itself instead of assuming.
SOLVERS: dict[str, dict[str, object]] = {
    "openfoam": {
        "executables": ["blockMesh"],
        "note": "Also needs the OpenFOAM-preCICE adapter (libpreciceAdapterFunctionObject.so) built for this OpenFOAM version.",
    },
    "calculix": {"executables": ["ccx_preCICE"]},
    "su2": {"executables": ["SU2_CFD"]},
    "codeaster": {"executables": ["as_run"]},
    "fenics": {"executables": ["python3"], "python_modules": ["fenics", "fenicsprecice"]},
    "fenicsx": {"executables": ["python3"], "python_modules": ["dolfinx", "fenicsxprecice"]},
    "nutils": {"executables": ["python3"]},
    "python": {"executables": ["python3"]},
    "fmi": {"executables": ["python3"]},
    "dealii": {"executables": ["cmake", "make"], "note": _BUILD_FIRST},
    "dumux": {"executables": ["cmake", "make"], "note": _BUILD_FIRST},
    "dune": {"executables": ["cmake", "make"], "note": _BUILD_FIRST},
    "cpp": {"executables": ["cmake", "make"], "note": _BUILD_FIRST},
    "fortran": {"executables": ["cmake", "make", "gfortran"], "note": _BUILD_FIRST},
    "rust": {"executables": ["cargo"]},
    "matlab": {"executables": ["matlab"]},
}


def check_precice_installation() -> dict[str, object]:
    """Report the precice-cli and preCICE library versions found on this machine."""
    result = run_precice_cli("version", cwd=Path.cwd())
    if result.error:
        return {"precice_cli": None, "libprecice": None, "problems": [result.error]}

    # Lines look like "libprecice : 3.4.1;<build info>".
    versions = {
        name.strip(): value.strip().split(";")[0]
        for name, _, value in (line.partition(":") for line in result.stdout.splitlines())
        if value
    }
    problems = []
    if not versions.get("libprecice"):
        problems.append(
            "The preCICE library (libprecice) was not found. Install it first: "
            "https://precice.org/installation-overview.html"
        )
    return {
        "precice_cli": versions.get("precice-cli", "installed"),
        "libprecice": versions.get("libprecice"),
        "problems": problems,
    }


def check_config(project_dir: Path) -> dict[str, object]:
    """Locate precice-config.xml, validate it and extract the participant names."""
    config_files = iter_project_files(project_dir, "precice-config.xml")
    if not config_files:
        return {"file": None, "valid": False, "participants": [], "problems": ["No precice-config.xml found in the project."]}

    config_file = config_files[0]
    participants: list[str] = []
    problems: list[str] = []

    try:
        root = parse_precice_config(config_file)
    except ValueError as exc:
        problems.append(f"Could not parse {config_file.name}: {exc}")
    else:
        participants = [
            element.attrib["name"]
            for element in root.iter("participant")
            if element.getparent() is root and "name" in element.attrib
        ]

    check = run_precice_cli(f"config check {config_file.name}", cwd=config_file.parent)
    if check.error == PRECICE_CLI_MISSING:
        valid = None  # already reported by check_precice_installation
    else:
        valid = check.ok
        if not valid:
            problems.append(f"precice-cli config check failed:\n{check.output}")

    return {"file": str(config_file), "valid": valid, "participants": participants, "problems": problems}


def _python_module_available(module: str, cwd: Path) -> bool:
    probe = f"import importlib.util as u, sys; sys.exit(u.find_spec('{module}') is None)"
    return run_command(f'python3 -c "{probe}"', cwd=cwd).ok


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _solver_of(case_name: str) -> str | None:
    return next((token for token in case_name.lower().split("-")[1:] if token in SOLVERS), None)


def check_case(case_dir: Path) -> dict[str, object]:
    """Check whether the solver behind one participant case directory is available."""
    solver = _solver_of(case_dir.name)
    missing: list[str] = []
    notes: list[str] = []

    if solver is None:
        notes.append("Solver not recognised from the directory name; read run.sh to see what it needs.")
    else:
        requirements = SOLVERS[solver]
        python_modules = list(requirements.get("python_modules", []))  # type: ignore[call-overload]

        run_script = (case_dir / "run.sh").read_text(errors="ignore")
        if "pip install" in run_script and "PRECICE_TUTORIALS_NO_VENV" not in os.environ:
            notes.append("run.sh creates its own .venv and pip-installs its requirements (needs network access).")
            python_modules += ["venv", "ensurepip"]
        if "note" in requirements:
            notes.append(str(requirements["note"]))

        missing += [
            f"executable: {executable}"
            for executable in requirements.get("executables", [])  # type: ignore[attr-defined]
            if shutil.which(executable) is None
        ]
        if shutil.which("python3"):
            missing += [
                f"python module: {module}"
                for module in python_modules
                if not _python_module_available(module, case_dir)
            ]

    if solver is None:
        status = "unknown"
    else:
        status = "missing" if missing else "ok"
    return {
        "case": case_dir.name,
        "solver": solver,
        "status": status,
        "missing": missing,
        "notes": notes,
        "run_command": f"cd {case_dir} && ./run.sh",
    }


def _group_by_participant(
    participant_names: list[str], cases: list[dict[str, object]]
) -> tuple[dict[str, list[dict[str, object]]], list[dict[str, object]]]:
    """Assign each case to the participant its directory is named after.

    Names are compared without case and separators (Fluid1DLeft matches
    fluid1d-left-nutils). Cases matching no participant are returned separately.
    """
    grouped: dict[str, list[dict[str, object]]] = {name: [] for name in participant_names}
    other: list[dict[str, object]] = []
    for case in cases:
        case_key = _normalize(str(case["case"]))
        owners = [name for name in grouped if case_key.startswith(_normalize(name))]
        if owners:
            grouped[max(owners, key=len)].append(case)
        else:
            other.append(case)
    return grouped, other


def preflight(project_dir: Path) -> dict[str, object]:
    """Run every pre-run check for a project and say whether it can be started."""
    installation = check_precice_installation()
    config = check_config(project_dir)
    cases = [
        check_case(case_dir)
        for case_dir in sorted(project_dir.iterdir())
        if case_dir.is_dir() and (case_dir / "run.sh").is_file()
    ]
    participants, other_cases = _group_by_participant(config["participants"], cases)  # type: ignore[arg-type]

    problems: list[str] = [*installation.pop("problems"), *config.pop("problems")]  # type: ignore[misc]
    warnings: list[str] = []
    if not cases:
        problems.append("No participant case directories with a run.sh were found.")

    for name, options in participants.items():
        if options and not any(option["status"] == "ok" for option in options):
            listed = "; ".join(
                f"{option['case']} ({', '.join(option['missing']) or 'check run.sh manually'})"  # type: ignore[arg-type]
                for option in options
            )
            problems.append(f"Participant '{name}': no case is ready to run. {listed}")

    # Directory names do not always follow the participant names, so an
    # unmatched participant only blocks the run when too few usable cases are left.
    unmatched = [name for name, options in participants.items() if not options]
    if unmatched:
        message = (
            f"Could not match participant(s) {', '.join(unmatched)} to a case directory by name; "
            "choose their cases from other_cases (the project README says which is which)."
        )
        usable = [case for case in other_cases if case["status"] == "ok"]
        if len(usable) < len(unmatched):
            problems.append(message + " Not enough of those cases are ready to run.")
        else:
            warnings.append(message)

    ready = not problems
    if ready:
        next_steps = [
            "Pick one case with status 'ok' per participant.",
            "Start all participants at the same time, each with its run_command in its own shell/background process; they wait for each other.",
            "When they finish (or hang), call read_latest_log / analyze_precice_logs on the project.",
        ]
    else:
        next_steps = [
            "Do not start the simulation yet.",
            "Report the problems to the user and resolve them (ask before installing anything).",
            "Call precice_project_preflight again and only run once ready is true.",
        ]

    return {
        "project": str(project_dir),
        "ready": ready,
        "problems": problems,
        "warnings": warnings,
        "precice": installation,
        "config": config,
        "participants": participants,
        "other_cases": other_cases,
        "next_steps": next_steps,
    }
