# preCICE AI MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for exploring and operating local preCICE simulation projects from any AI coding agent.

Exposes 17 tools covering project discovery, config inspection, command execution, log analysis, and a local knowledge base built from the preCICE docs and Discourse forum.

## Why this exists

Working with multi-physics coupling means jumping between project folders, XML configs, and log files constantly. This server gives AI assistants — Claude Code, Cursor, Codex, Windsurf, and others — a safe, stable tool layer so they can read, inspect, and operate preCICE projects without needing raw shell access.

---

## Installation

```bash
git clone https://github.com/vaibhavd2103/precice-ai
cd precice-ai
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

After installation, the `precice-ai` CLI is available in the venv.

---

## Platform setup

Register the MCP server with your AI coding platform:

```bash
precice-ai setup claude-code
precice-ai setup claude-desktop
precice-ai setup cursor
precice-ai setup codex
precice-ai setup windsurf
precice-ai setup generic   # prints the JSON snippet for manual use
```

Pass `--projects-dir` to point at a custom location (defaults to `./test-projects`):

```bash
precice-ai setup claude-code --projects-dir /path/to/my/precice-cases
```

### Check which platforms are detected

```bash
precice-ai list-platforms
```

### Claude Code

Writes the server entry to `.mcp.json` in the current directory (project scope, the default):

```bash
precice-ai setup claude-code
```

Or to `~/.claude/settings.json` (user scope, available in every project):

```bash
precice-ai setup claude-code --scope user
```

After setup, open the directory in Claude Code — the server is picked up automatically.

### Claude Desktop

```bash
precice-ai setup claude-desktop
```

Config file locations:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Restart Claude Desktop after running setup.

### Cursor

```bash
precice-ai setup cursor
```

Writes to `~/.cursor/mcp.json`. Reload the window after setup.

### Windsurf

```bash
precice-ai setup windsurf
```

Writes to `~/.codeium/windsurf/mcp_config.json`. Restart Windsurf after setup.

### OpenAI Codex

```bash
precice-ai setup codex
```

Writes to `~/.codex/mcp.json`.

### Manual / generic

```bash
precice-ai setup generic
```

Prints the JSON block to paste into any MCP-compatible config file:

```json
{
  "mcpServers": {
    "precice-ai": {
      "command": "python",
      "args": ["-m", "precice_ai.server"],
      "env": {
        "PRECICE_PROJECTS_DIR": "/absolute/path/to/your/projects"
      }
    }
  }
}
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `PRECICE_PROJECTS_DIR` | `./test-projects` | Directory scanned by `list_precice_projects` and all project tools. |
| `PRECICE_KB_STORE_DIR` | `~/.precice-ai/kb_store` | Where the knowledge base JSON is stored. |

The `setup` command automatically injects `PRECICE_PROJECTS_DIR` into the platform config.

### Knowledge base storage

The knowledge base is stored as a single JSON file **outside the repo** so it is never committed to git:

```
~/.precice-ai/kb_store/knowledge_base.json
```

Check its status at any time:

```bash
# Via terminal
ls -lh ~/.precice-ai/kb_store/

# Via MCP tool
kb_precice_status()
```

To store the KB in a custom location (e.g. inside the project), set `PRECICE_KB_STORE_DIR` in the platform config. For Claude Code, add it to `.mcp.json`:

```json
{
  "mcpServers": {
    "precice-ai": {
      "command": "python",
      "args": ["-m", "precice_ai.server"],
      "env": {
        "PRECICE_PROJECTS_DIR": "/path/to/your/projects",
        "PRECICE_KB_STORE_DIR": "/path/to/your/kb_store"
      }
    }
  }
}
```

---

## MCP tools reference

### Knowledge base

| Tool | Description |
|---|---|
| `kb_ingest_precice_data(docs_pages_limit, forum_topics_limit, timeout_seconds)` | Fetches preCICE docs and Discourse forum, stores results locally. |
| `kb_query_precice(question, top_k)` | BM25 search over the ingested knowledge base. Returns scored snippets with source URLs. |
| `kb_query_precice_live(question, top_k, max_age_hours)` | Same as above but auto-refreshes the KB if the cache is older than `max_age_hours`. |
| `kb_precice_status()` | Returns KB freshness timestamp and document count. |

**Typical first use:** `kb_query_precice_live` handles everything automatically — it ingests on first use and re-ingests when the cache is older than 1 hour. The KB is stored at `~/.precice-ai/kb_store/knowledge_base.json` (outside the repo, never committed to git).

### Project discovery

| Tool | Description |
|---|---|
| `list_precice_projects()` | Lists all directories under `PRECICE_PROJECTS_DIR`. |
| `inspect_project_structure(project_name, max_depth)` | Prints the folder tree for a project up to `max_depth` levels. |
| `find_precice_config(project_name)` | Finds all `precice-config.xml` files within a project. |

### Configuration

| Tool | Description |
|---|---|
| `inspect_precice_config(project_name)` | Returns the raw contents of `precice-config.xml`. |
| `summarize_precice_config(project_name)` | Extracts participants, meshes, data items, and coupling scheme tags from the XML. |
| `check_precice_config(project_name)` | Runs `precice-cli config check` (falls back to `precice-tools check`) and returns the output. |
| `backup_precice_config(project_name)` | Creates a timestamped backup of `precice-config.xml` in the same directory. |
| `visualize_precice_config(project_name)` | Runs `precice-cli config visualize` to generate a diagram (requires preCICE CLI). |

### Command execution

| Tool | Description |
|---|---|
| `run_command_in_project(project_name, command)` | Runs a command inside the project directory. Only allowlisted prefixes are permitted. |

Allowed command prefixes: `ls`, `pwd`, `cat`, `find`, `grep`, `tail`, `head`, `precice-tools`, `precice-cli`, `python3`, `./run.sh`

### Logs

| Tool | Description |
|---|---|
| `list_project_logs(project_name)` | Lists all `*.log` and `*.txt` files in the project. |
| `read_project_logs(project_name, max_chars_per_file)` | Returns contents of all log files (truncated per file). |
| `read_latest_log(project_name, lines)` | Returns the last N lines of the most recently modified log file. |
| `analyze_precice_logs(project_name)` | Scans each log for error/warning/convergence/failure keywords and appends the last 30 lines. |

---

## Usage walkthrough

### 1. Ingest the preCICE knowledge base

```
kb_ingest_precice_data()
```

Fetches up to 20 docs pages and 20 forum topics and stores them locally. Run once; subsequent queries use the cache.

### 2. Discover your projects

```
list_precice_projects()
```

Returns the names of all case directories under `PRECICE_PROJECTS_DIR`.

### 3. Inspect a project

```
inspect_project_structure("partitioned-heat-conduction")
summarize_precice_config("partitioned-heat-conduction")
```

### 4. Validate the config

```
check_precice_config("partitioned-heat-conduction")
```

### 5. Run safe commands

```
run_command_in_project("partitioned-heat-conduction", "ls -la")
run_command_in_project("partitioned-heat-conduction", "cat run.sh")
```

### 6. Read and analyze logs

```
read_latest_log("partitioned-heat-conduction")
analyze_precice_logs("partitioned-heat-conduction")
```

### 7. Ask the knowledge base

```
kb_query_precice("how does implicit coupling work in preCICE?")
kb_query_precice_live("what is the waveform relaxation method?")
```

---

## Project structure

```
precice_ai/
├── server.py               # FastMCP server entry point
├── core/
│   ├── paths.py            # Project path resolution (env-var aware)
│   ├── safety.py           # Command allowlist and block patterns
│   ├── command_runner.py   # Safe subprocess execution
│   └── knowledge_base.py   # KB ingestion and BM25 query engine
├── tools/
│   ├── project_tools.py    # list, inspect, find, run_command
│   ├── config_tools.py     # inspect, summarize, check, backup, visualize
│   ├── log_tools.py        # list, read, read_latest, analyze
│   └── knowledge_tools.py  # kb_ingest, kb_query, kb_query_live, kb_status
└── cli/
    ├── main.py             # precice-ai CLI (setup / list-platforms / server)
    └── platforms/          # Per-platform config writers
        ├── claude_code.py
        ├── claude_desktop.py
        ├── codex.py
        ├── cursor.py
        ├── windsurf.py
        └── generic.py
server.py                   # Convenience shim for python server.py (local dev)
pyproject.toml              # Package definition and CLI entry points
```

---

## Codebase knowledge graph (optional)

This repo ships a pre-built knowledge graph in `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`). If you have [graphify](https://github.com/Graphify-app/Graphify) installed you can query it directly from your terminal or let your AI assistant use it for faster codebase navigation.

### Install graphify

```bash
pip install graphify-cli   # or follow the graphify README for your platform
```

### Query the graph

```bash
# Ask a question about the codebase
graphify query "how does the knowledge base ingestion work?"

# Find the relationship between two modules
graphify path "KnowledgeBaseService" "kb_query_precice"

# Deep-dive on a concept
graphify explain "BM25 scoring"
```

### Keep the graph current after code changes

```bash
graphify update .
```

This re-indexes only changed files (AST-only pass, no API cost).

### Configure your AI assistant to use the graph

For Claude Code, add this to `.claude/CLAUDE.md` in the project root (already present in this repo):

```
When graphify-out/graph.json exists, run `graphify query "<question>"` before
browsing source files. Use `graphify path "<A>" "<B>"` for relationships and
`graphify explain "<concept>"` for focused concepts.
```

Graphify is entirely optional — the MCP server and CLI work without it.

---

## Starting the server manually

```bash
# Via the CLI
precice-ai server

# Via Python module
python -m precice_ai.server

# From the repo root (local dev)
python server.py
```

---

## Safety notes

- `run_command_in_project` executes via shell with a prefix allowlist. Commands not matching an allowed prefix are rejected before execution.
- The command allowlist blocks patterns like `rm`, `sudo`, `curl`, `wget`, and fork bombs. Tighten it further in [precice_ai/core/safety.py](precice_ai/core/safety.py).
- Log parsing is heuristic (keyword search). It does not replace solver-level validation.
- The knowledge base is stored locally at `~/.precice-ai/kb_store/`. No data leaves your machine except when ingesting from `precice.org` and `precice.discourse.group`.

---

## License

MIT — see `LICENSE`.
