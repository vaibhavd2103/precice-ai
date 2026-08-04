# Contributor Guide

This guide is for people who want to understand, modify, debug, or extend `precice-ai`. It combines the detailed operational material that used to live in the README with repo-specific architecture notes, local development workflow, and the main code paths you will touch while contributing.

If you only want to install and use the project, go back to [README.md](README.md).

## What This Project Is

`precice-ai` is a Python package that exposes a preCICE-focused MCP server plus a Typer CLI that installs that server into supported AI clients.

There are two main user-facing surfaces:

1. The `precice-ai` CLI.
2. The `precice_ai.server` MCP server process.

The project is designed so that an AI client starts the server as a subprocess over stdio, and the server exposes tools for:

- discovering local preCICE projects
- inspecting and backing up config files
- reading and summarizing logs
- running a tightly restricted set of shell commands
- querying a pre-built semantic knowledge base
- wrapping selected `precice-cli` commands

## Read This Guide In Order

If you are new to the repo, this reading order is the fastest path:

1. `pyproject.toml`
2. `precice_ai/cli/main.py`
3. `precice_ai/cli/platforms/base.py`
4. `precice_ai/server.py`
5. `precice_ai/tools/__init__.py`
6. `precice_ai/tools/project_tools.py`
7. `precice_ai/tools/config_tools.py`
8. `precice_ai/tools/log_tools.py`
9. `precice_ai/tools/knowledge_tools.py`
10. `precice_ai/tools/cli_tools.py`
11. `precice_ai/core/paths.py`
12. `precice_ai/core/safety.py`
13. `precice_ai/core/command_runner.py`
14. `precice_ai/core/knowledge_base.py`

After that, read the scripts in `scripts/` if you plan to touch the KB ingestion pipeline.

## Repository Map

```text
precice-ai/
├── README.md                    # end-user install and usage overview
├── CONTRIBUTOR_GUIDE.md         # this file
├── pyproject.toml               # package metadata, dependencies, CLI entry points
├── requirements.txt             # flat dependency list, not the authoritative install path
├── install.sh                   # helper: create venv, install editable package, bootstrap client
├── server.py                    # repo-root convenience launcher
├── kb_sources.json              # category/source config for the knowledge base
├── kb_state.json                # last-processed signatures for KB rebuild workflows
├── document.md                  # design/thesis-style background material
├── graphify-out/                # checked-in graph artifacts for codebase navigation
├── scripts/                     # KB build, rendering, comparison, and maintenance helpers
└── precice_ai/
    ├── __init__.py
    ├── server.py                # FastMCP server entry point
    ├── core/
    │   ├── paths.py             # project and config path resolution
    │   ├── safety.py            # shell command allowlist and blocklist
    │   ├── command_runner.py    # guarded subprocess execution
    │   └── knowledge_base.py    # lexical KB and vector KB implementation
    ├── tools/
    │   ├── __init__.py          # registers all MCP tool groups
    │   ├── project_tools.py     # project discovery and safe in-project commands
    │   ├── config_tools.py      # config file read, summary, backup
    │   ├── log_tools.py         # log listing, reading, heuristic analysis
    │   ├── knowledge_tools.py   # KB ingest/query/status MCP tools
    │   └── cli_tools.py         # wrappers around external precice-cli commands
    ├── cli/
    │   ├── __init__.py
    │   ├── main.py              # Typer CLI entry point
    │   ├── bootstrap.py         # .env writing and env dict assembly
    │   └── platforms/
    │       ├── __init__.py      # platform registry
    │       ├── base.py          # shared platform abstraction
    │       ├── claude_code.py
    │       ├── claude_desktop.py
    │       ├── codex.py
    │       ├── cursor.py
    │       ├── generic.py
    │       └── windsurf.py
    └── utils/
        └── topology_schema.json # schema used by precice_init
```

## The Two Entry Points

### 1. The package/CLI entry point

`pyproject.toml` is the authoritative package definition. It tells Python packaging tools:

- how to build the project
- which dependencies to install
- which Python versions are supported
- which console scripts to create

The important part is:

```toml
[project.scripts]
precice-ai = "precice_ai.cli.main:app"
precice-ai-server = "precice_ai.server:main"
```

That means:

- running `precice-ai ...` starts the Typer app in `precice_ai/cli/main.py`
- running `precice-ai-server` starts the MCP server `main()` in `precice_ai/server.py`

### 2. The MCP server entry point

`precice_ai/server.py` does three things:

1. loads `.env` from the repo root
2. creates `FastMCP("preCICE AI")`
3. registers all tool groups and starts the stdio server

In other words, the CLI installs the server, but the server is what your MCP client actually runs during a session.

## High-Level Architecture

The core wiring looks like this:

```text
pyproject.toml
  -> console script: precice-ai
  -> precice_ai.cli.main
     -> platform registry
     -> platform installer writes MCP client config
     -> client launches python -m precice_ai.server
        -> FastMCP instance
        -> register_all_tools()
           -> project_tools
           -> config_tools
           -> log_tools
           -> knowledge_tools
           -> cli_tools
              -> core helpers
                 -> paths
                 -> safety
                 -> command_runner
                 -> knowledge_base
```

The CLI and the server are separate on purpose:

- the CLI configures a client once
- the server then runs repeatedly in that client over stdio

## Local Development Setup

### Prerequisites

- Python 3.10 or newer
- `git`
- optionally `precice-cli` if you want to exercise the preCICE wrapper tools
- optionally a supported MCP client such as Codex, Claude Code, Cursor, or Windsurf
- optionally an embedding API key for KB queries

### Recommended setup

```bash
git clone https://github.com/vaibhavd2103/precice-ai
cd precice-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Why `pip install -e .` matters:

- it installs dependencies from `pyproject.toml`
- it creates the `precice-ai` and `precice-ai-server` console scripts
- it keeps the package editable, so source changes are reflected immediately

Do not rely on `pip install -r requirements.txt` alone for normal development. That file is only a flat dependency list and does not define console scripts.

### Optional helper script

`install.sh` automates the venv creation and editable install:

```bash
./install.sh auto --projects-dir /path/to/preCICE/cases
```

Under the hood it:

1. creates `.venv`
2. upgrades `pip`
3. runs `pip install -e .`
4. calls `precice-ai bootstrap "$@"`

### Quick sanity checks

After setup:

```bash
precice-ai --help
precice-ai list-platforms
precice-ai kb status
python -m precice_ai.server
```

`python -m precice_ai.server` will start the stdio MCP server and wait for a client. That is expected. Use Ctrl+C to stop it if you launched it manually for a quick smoke test.

## Fresh-System Setup: End-To-End Contributor Path

If you are onboarding onto a clean machine and want a full working dev environment:

1. Install Python 3.10+ and `git`.
2. Clone the repo.
3. Create and activate the virtual environment.
4. Run `pip install -e .`.
5. Run `precice-ai list-platforms` to see which clients are available locally.
6. Decide what directory will contain your local preCICE cases.
7. Run `precice-ai bootstrap <client> --projects-dir /path/to/cases`.
8. If you want semantic KB queries, provide `--openrouter-api-key ...` or configure Blablador variables.
9. Restart the target client.
10. In the client, call `list_precice_projects()`, then `kb_precice_status()`, then use `kb_query_precice("what is preCICE?", category="about")` if that category is fresh or `kb_query_precice_live("what is preCICE?", category="about")` if it is missing or stale.

If you do not have a client installed yet, you can still develop the code locally by:

- running `precice-ai kb ...` commands directly
- running `python -m precice_ai.server`
- manually inspecting JSON snippets from `precice-ai setup generic`

## Day-To-Day Development Workflow

### When you change CLI behavior

Touch these files first:

- `precice_ai/cli/main.py`
- `precice_ai/cli/bootstrap.py`
- `precice_ai/cli/platforms/base.py`
- one or more files in `precice_ai/cli/platforms/`

Then validate:

```bash
precice-ai --help
precice-ai list-platforms
precice-ai setup generic --projects-dir /tmp/example
```

### When you change MCP tools

Touch these files first:

- `precice_ai/tools/*.py`
- optionally `precice_ai/core/*.py`

Then validate by:

- starting the server manually
- using the CLI `kb` subcommands where applicable
- using a real MCP client if the behavior depends on client-launched environment variables

### When you change safety behavior

Touch:

- `precice_ai/core/safety.py`
- possibly `precice_ai/core/command_runner.py`

Be extra careful here. The project’s safety posture depends on this allowlist and blocklist remaining intentionally narrow.

### When you change knowledge-base behavior

Touch:

- `precice_ai/core/knowledge_base.py`
- `precice_ai/tools/knowledge_tools.py`
- scripts in `scripts/`
- maybe `kb_sources.json`
- maybe `kb_state.json`

Validate both:

- direct CLI access via `precice-ai kb ...`
- the MCP tools that wrap the same internals

## The Typer CLI: How It Works

`precice_ai/cli/main.py` is the main CLI application.

It defines:

- the root `app = typer.Typer(...)`
- the `kb_app = typer.Typer(...)` subcommand group
- commands such as `setup`, `bootstrap`, `open`, `list-platforms`, and `server`
- KB debug commands such as `kb status`, `kb ingest`, and `kb query`

Why Typer is a good fit here:

- type hints become CLI argument parsing rules
- `Path` parameters become path-aware options
- default values, help text, and validation are easy to keep close to the function definitions
- `typer.echo()` and `typer.Exit()` keep the CLI ergonomics clean

The CLI does not implement the server logic itself. It is mostly an installer, launcher, and debug surface.

## Platform Installers

The platform-specific files under `precice_ai/cli/platforms/` all inherit from the abstract `Platform` base class.

### `Platform` base class responsibilities

`precice_ai/cli/platforms/base.py` provides:

- `install(...)` and `is_available()` as required abstract methods
- optional `can_launch()` and `launch(...)`
- `_spawn(...)` for detached client launching
- `mcp_entry(...)` for generating a standard server config block
- `_merge_json_config(...)` for JSON-based clients

The key abstraction is `mcp_entry(...)`. It builds the canonical server launch entry:

```json
{
  "command": "<current python executable>",
  "args": ["-m", "precice_ai.server"],
  "env": {
    "PRECICE_PROJECTS_DIR": "..."
  }
}
```

That means every installer points clients back at the exact Python interpreter that installed the package.

### Supported installers

- `claude_code.py`
- `claude_desktop.py`
- `cursor.py`
- `windsurf.py`
- `codex.py`
- `generic.py`

The differences are mostly:

- how availability is detected
- where the client config lives
- whether the config file is JSON or TOML
- whether the client can be launched from the CLI after setup

`generic.py` is useful during development because it prints the expected MCP config instead of modifying a client config file directly.

## Environment Loading Model

Both the CLI and the server explicitly load `.env` from the repo root.

This is important because many MCP clients launch the server with a minimal environment and do not source shell startup files.

The practical outcome is:

- `precice-ai kb ...` can see the same API keys as the server
- `python -m precice_ai.server` can pick up `.env` values without manual export
- already-set environment variables still win, because `load_dotenv(...)` does not override them by default

## Core Modules

### `core/paths.py`

This module answers one deceptively important question: where are the projects?

Behavior:

- if `PRECICE_PROJECTS_DIR` is set, use it
- otherwise default to `Path.cwd() / "test-projects"`

It also provides `get_project_path(project_name)` and prevents path traversal by verifying that the resolved path still stays inside the configured projects directory.

### `core/safety.py`

This is the command safety policy.

It defines:

- `ALLOWED_COMMAND_PREFIXES`
- `BLOCKED_PATTERNS`
- `is_command_safe(command)`

Right now the allowed prefixes are intentionally narrow and mostly read-only:

- `ls`
- `pwd`
- `cat`
- `find`
- `grep`
- `tail`
- `head`
- `precice-tools`
- `precice-cli`
- `python3`
- `./run.sh`

And it blocks obvious dangerous patterns such as:

- `rm`
- `sudo`
- `chmod`
- `curl`
- `wget`
- `shutdown`
- `reboot`

Because `run_safe_command(...)` eventually executes with `shell=True`, this module is security-critical.

### `core/command_runner.py`

This is the execution shim used by multiple tools.

It:

1. checks the command through `is_command_safe(...)`
2. verifies the working directory exists
3. runs the command with a timeout
4. returns stdout, stderr, and return code as plain text

This is intentionally simple and transparent, which makes it easier to reason about in an MCP setting.

### `core/knowledge_base.py`

This is the largest and most complex module in the repo.

It contains two KB implementations:

1. `KnowledgeBaseService`
2. `VectorKnowledgeBase`

The important distinction is:

- `KnowledgeBaseService` is the older lexical path
- `VectorKnowledgeBase` is the semantic embeddings-based path that powers the main KB experience

The lexical path still matters because:

- the CLI still exposes lexical mode
- it provides a fallback or comparison baseline
- scripts such as `scripts/compare_kb_search.py` depend on it

## Tool Modules

All MCP tools are registered through `precice_ai/tools/__init__.py`, which calls:

- `register_project_tools`
- `register_config_tools`
- `register_log_tools`
- `register_knowledge_tools`
- `register_cli_tools`

### `tools/project_tools.py`

This module exposes:

- `list_precice_projects()`
- `inspect_project_structure(project_name, max_depth=3)`
- `find_precice_config(project_name)`
- `run_command_in_project(project_name, command)`

It is the main bridge between an AI agent and the local preCICE case directory.

### `tools/config_tools.py`

This module exposes:

- `inspect_precice_config(project_name)`
- `summarize_precice_config(project_name)`
- `backup_precice_config(project_name)`

It deliberately stays conservative:

- raw reading
- lightweight XML parsing
- explicit backups before edits

If you later add config mutation tools, keep the existing safety expectations in mind.

### `tools/log_tools.py`

This module exposes:

- `list_project_logs(project_name)`
- `read_project_logs(project_name, max_chars_per_file=5000)`
- `read_latest_log(project_name, lines=80)`
- `analyze_precice_logs(project_name)`

The log analysis is heuristic. It scans for terms like `error`, `warning`, `iteration`, `converged`, `failed`, `exiting`, and `finished`, then appends the tail of the log for context.

### `tools/knowledge_tools.py`

This module exposes:

- `kb_ingest_precice_data(...)`
- `kb_query_precice(...)`
- `kb_query_precice_live(...)`
- `kb_query_precice_lexical(...)`
- `kb_precice_status()`

There are two important runtime objects created at import time:

- `kb_service = KnowledgeBaseService()`
- `vector_kb = VectorKnowledgeBase()`

That keeps the objects reusable for the life of the server process.

### `tools/cli_tools.py`

This module wraps external `precice-cli` commands and exposes them through MCP.

Examples include:

- `precice_version()`
- `precice_config_check(...)`
- `precice_config_visualize(...)`
- `precice_config_format(...)`
- `precice_config_doc(...)`
- `precice_init(...)`
- profiling helpers such as `precice_profiling_analyze(...)`

There are two especially important details here:

1. `_check_precice_cli()` guards access and returns a friendly error if `precice-cli` is not installed.
2. `precice_init(...)` validates topology input against `precice_ai/utils/topology_schema.json` before writing files and invoking `precice-cli init`.

## Knowledge Base Architecture

The KB has two distinct phases:

1. offline build/publish
2. online download/query

### Offline build/publish phase

This is handled outside the normal MCP session flow by scripts and GitHub Actions.

At a high level:

```text
source repos / APIs
  -> chunk content
  -> embed chunks
  -> save kb-embeddings-<category>.npz
  -> publish to GitHub Release
```

Categories are configured in `kb_sources.json`, including:

- `about`
- `community`
- `documentation`
- `tutorials`
- `forum`
- `issues`
- `pulls`

The main helper scripts are:

- `scripts/build_embeddings.py`
- `scripts/build_forum_embeddings.py`
- `scripts/build_github_activity_embeddings.py`
- `scripts/render_sources_json.py`
- `scripts/kb_state.py`
- `scripts/compare_kb_search.py`

`kb_state.json` stores change signatures so rebuild workflows can skip categories whose sources did not change.

### Online download/query phase

This is what happens inside the installed server:

1. `kb_precice_status(...)` reports whether the relevant category is present and fresh enough to trust locally.
2. `kb_query_precice(...)` uses the local vector KB directly when that category is fresh.
3. `kb_query_precice_live(...)` refreshes missing or stale release assets in `~/.precice-ai/kb_store/` before querying.
4. `VectorKnowledgeBase` lazy-loads the relevant `.npz` files.
5. it embeds the user’s question using the configured embedding provider
6. it computes cosine similarity against the stored chunk embeddings
7. it returns the best-matching chunks with metadata and snippets

Important design note:

- document embeddings are precomputed offline
- only the question text is embedded at query time

### Why the KB store lives outside the repo

By default, KB assets go into:

```text
~/.precice-ai/kb_store/
```

That prevents:

- accidental git commits of large binary assets
- the installed package writing back into the source tree
- confusion between checked-in source and runtime cache

Override with `PRECICE_KB_STORE_DIR` when needed.

## Important Runtime Flows

### Flow 1: `precice-ai bootstrap codex`

```text
CLI command
  -> precice_ai.cli.main.bootstrap(...)
  -> write .env if requested
  -> resolve platform through REGISTRY
  -> build env dict
  -> platform.install(...)
  -> codex mcp add precice-ai -- <python> -m precice_ai.server
```

### Flow 2: MCP server startup

```text
client launches python -m precice_ai.server
  -> load .env
  -> create FastMCP("preCICE AI")
  -> register_all_tools(mcp)
  -> mcp.run()
```

### Flow 3: project command execution

```text
run_command_in_project(project_name, command)
  -> get_project_path(project_name)
  -> run_safe_command(command, cwd=project_path)
  -> is_command_safe(command)
  -> subprocess.run(...)
  -> formatted text result
```

### Flow 4: semantic KB query

```text
kb_precice_status()
  -> if category fresh: kb_query_precice(question, category=...)
     -> VectorKnowledgeBase.query(...)
  -> else: kb_query_precice_live(question, category=...)
     -> VectorKnowledgeBase.download_from_release(...)
     -> VectorKnowledgeBase.query(...)
  -> embed question
  -> cosine similarity against stored chunk vectors
  -> return top-k results
```

## How To Extend The Project

### Add a new CLI command

1. Add a function in `precice_ai/cli/main.py`.
2. Decorate it with `@app.command()` or `@kb_app.command(...)`.
3. Use Typer types and help text.
4. Test with `precice-ai --help` and the command itself.

### Add a new MCP tool

1. Pick the right tool module under `precice_ai/tools/`.
2. Define a function inside that module’s `register_*_tools(mcp)` function.
3. Decorate it with `@mcp.tool()`.
4. Reuse helpers from `precice_ai/core/` rather than duplicating logic.
5. Restart the server and test through a client or direct MCP workflow.

### Add a new client installer

1. Create a new file in `precice_ai/cli/platforms/`.
2. Subclass `Platform`.
3. Implement `is_available()` and `install(...)`.
4. Optionally implement `can_launch()` and `launch(...)`.
5. Register it in `precice_ai/cli/platforms/__init__.py`.
6. Update the README and this guide.

### Add a new KB category

1. Add the source definition to `kb_sources.json`.
2. Update `precice_ai/core/knowledge_base.py` so the category is recognized.
3. Update any local fallback logic for building that category.
4. Update the build workflow if it needs special handling.
5. Regenerate or publish the release assets.

## Graphify And Codebase Navigation

This repo includes checked-in graph artifacts under `graphify-out/`.

That gives contributors and AI agents:

- a prebuilt graph of code and documentation relationships
- a `GRAPH_REPORT.md` summary
- the ability to query the graph if `graphify` is installed locally

This is optional. The source code remains the ground truth.

## Environment Variables In Detail

### Project and KB paths

- `PRECICE_PROJECTS_DIR`
- `PRECICE_KB_STORE_DIR`

### Embedding provider configuration

- `OPENROUTER_API_KEY`
- `BLABLADOR_API_KEY`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`

### GitHub integration

- `PRECICE_AI_GITHUB_REPO`
- `GITHUB_TOKEN`

The CLI bootstrap flow can inject several of these into a client config automatically, but both the CLI and the server also support reading them from `.env`.

## Validation And Testing Strategy

At the moment, this repo does not ship a large automated test suite. Validation is mostly manual and workflow-based.

That means contributors should be disciplined about smoke tests after changes.

Recommended checks:

```bash
precice-ai --help
precice-ai list-platforms
precice-ai setup generic --projects-dir /tmp/example
precice-ai kb status
precice-ai kb query "implicit coupling" --mode lexical
python -m precice_ai.server
```

If you changed `precice-cli` wrappers and have `precice-cli` installed:

```bash
precice-ai kb status
python -m precice_ai.cli.main server
```

If you changed the KB code and have API credentials:

```bash
precice-ai kb ingest
precice-ai kb query "how does implicit coupling work?" --mode vector-live
```

If you changed platform installers, validate against at least one real client and one dry-run style path such as:

```bash
precice-ai setup generic --projects-dir /absolute/path/to/cases
```

## Common Contributor Pitfalls

### 1. Confusing `requirements.txt` with the real package definition

Use `pyproject.toml` as the source of truth.

### 2. Forgetting that the server is launched by the client, not by the CLI

The CLI configures installation. The actual interactive behavior comes from `precice_ai.server`.

### 3. Testing only from the repo root

A lot of path behavior changes depending on:

- whether `PRECICE_PROJECTS_DIR` is set
- whether the server is run from the repo root
- whether the package is run from an editable install or through a client

### 4. Breaking the safety model while adding convenience

Be very conservative when expanding allowed commands or introducing write-capable flows.

### 5. Assuming KB queries are fully offline

The vector documents are cached locally, but the user’s question still has to be embedded at query time unless you are using the lexical path.

## Troubleshooting

### `precice-ai` command not found

Usually means:

- the virtual environment is not activated
- the package was not installed with `pip install -e .`

Fallback:

```bash
python -m precice_ai.cli.main --help
```

### MCP client shows no server or no tools

Check:

- the client config path is correct
- the client was restarted or reloaded
- the configured Python interpreter still exists
- the server command is `-m precice_ai.server`

### KB queries fail

Check:

- embedding API key is present
- `EMBEDDING_BASE_URL` and `EMBEDDING_MODEL` are valid
- network access to the embedding provider works
- the local KB store is writable

### Project tools return no projects

Check:

- `PRECICE_PROJECTS_DIR` points at the right folder
- that folder contains subdirectories representing projects
- if running manually from the repo root, whether you expected the fallback `./test-projects`

### `precice-cli` wrapper tools fail

Check:

- `precice-cli` is installed
- it is on `PATH`
- the config path you passed is correct

## Suggested First Contributions

If you are looking for a safe way to learn the codebase:

- improve CLI help text or docs for a confusing command
- tighten or clarify error messages returned by tools
- add a missing validation or path check
- improve the generic/manual setup output
- add manual smoke-test notes for a new workflow
- document a real client setup that you verified yourself

## Final Mental Model

If you remember only one thing, remember this:

`precice-ai` is a packaging and integration layer around a FastMCP server.

The CLI exists to install and debug that server.

The server exists to expose safe, preCICE-aware tools.

Most contributions become straightforward once you know which side of that boundary you are changing.
