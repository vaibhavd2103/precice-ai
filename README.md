# preCICE AI MCP Server

A lightweight Model Context Protocol (MCP) server for exploring and operating local preCICE tutorial projects from AI coding agents.

This project exposes a focused set of tools to:
- discover local preCICE projects,
- inspect coupling configuration,
- run controlled project commands, and
- read/analyze simulation log files.

## Why this exists

When working with multi-physics coupling workflows, most time is spent jumping between project folders, XML configs, and logs. This MCP server provides a stable tool layer so assistants like Codex can interact with preCICE projects safely and consistently.

## Features

- Local project discovery under `test-projects/`
- Direct read access to `precice-config.xml`
- Controlled command execution with allowlisted command prefixes
- Recursive log aggregation (`*.log`)
- Basic log diagnostics (error/warning/failure/convergence/iteration signals)

## MCP Tools

The server currently provides the following MCP tools:

### `kb_ingest_precice_data(docs_pages_limit=20, forum_topics_limit=20, timeout_seconds=20) -> str`
Fetches content from preCICE documentation and preCICE Discourse forum, then stores it in `kb_store/knowledge_base.json` for retrieval.

### `kb_query_precice(question: str, top_k=5) -> str`
Queries the locally ingested knowledge base and returns the top matching snippets with source URLs.

### `kb_query_precice_live(question: str, top_k=5, max_age_hours=24) -> str`
Auto-refreshes the knowledge base from docs/forum when stale, then runs the query.

### `kb_precice_status() -> str`
Returns KB status, freshness timestamp, and document count.

### `list_precice_projects() -> list[str]`
Lists all subdirectories under `test-projects/`.

### `inspect_precice_config(project_name: str) -> str`
Reads `test-projects/<project_name>/precice-config.xml`.

### `run_command_in_project(project_name: str, command: str) -> str`
Runs a command inside a project directory if it matches one of these allowed prefixes:
- `ls`
- `pwd`
- `cat`
- `precice-tools`
- `python3`
- `./run.sh`

Returns stdout, stderr, and return code.

### `read_project_logs(project_name: str) -> str`
Finds all `*.log` files under the project and returns their content (truncated per file).

### `analyze_precice_logs(project_name: str) -> str`
Per log file, reports simple diagnostics and appends the last 30 lines.

## Project Structure

```text
.
├── server.py
├── document.md
└── test-projects/
    └── <your-precice-cases>/
        ├── precice-config.xml
        └── ... (*.log, run scripts, solver files)
```

## Setup

### 1. Create and activate a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install mcp
```

If your project pins dependencies elsewhere, install from your lock/requirements file instead.

### 3. Start the MCP server

```bash
python3 server.py
```

## Using with Codex

Add this server to your MCP client configuration for Codex using your local absolute path:

```json
{
  "mcpServers": {
    "precice-ai": {
      "command": "python3",
      "args": ["/absolute/path/to/precice-ai/server.py"]
    }
  }
}
```

After connecting, Codex can call the tools listed above to inspect and operate your local preCICE tutorial projects.

## Using with Claude Code (Later)

Claude Code support can be added with the same server entry pattern once MCP server configuration is enabled in your Claude setup.

Recommended approach:
- Reuse the same Python environment and `server.py` command.
- Register this MCP server under a name like `precice-ai`.
- Validate by calling `list_precice_projects` first.

Add your Claude-specific configuration snippet here when you finalize that integration.

## Safety Notes

- `run_command_in_project` is allowlist-based but still executes via shell; keep your project workspace trusted.
- The command allowlist is prefix-based; tighten it further for production usage.
- Log parsing is heuristic and should not replace solver-level validation.

## Roadmap

- Stronger command validation (exact command parsing instead of simple prefix checks)
- Structured JSON diagnostics for logs
- Optional project metadata tool (participants, meshes, coupling scheme extraction)
- Claude Code configuration examples with tested snippets

## License

Add your preferred license (for example, MIT) in a `LICENSE` file.
