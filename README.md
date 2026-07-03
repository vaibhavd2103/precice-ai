# preCICE AI MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for exploring and operating local preCICE simulation projects from any AI coding agent.

Exposes 26 tools covering project discovery, config inspection, `precice-cli` wrapping (version, config check/format/doc/init, profiling), command execution, log analysis, and a semantic knowledge base built from the preCICE documentation using vector embeddings.

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
| `PRECICE_KB_STORE_DIR` | `~/.precice-ai/kb_store` | Where the vector KB archive is stored locally. |
| `OPENROUTER_API_KEY` | — | **Required for KB queries.** API key used to embed questions at query time. |
| `EMBEDDING_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible base URL for the embedding API. Override to switch providers (e.g. Blablador). |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | Embedding model name passed to the API. |
| `PRECICE_AI_GITHUB_REPO` | `vaibhavd2103/precice-ai` | GitHub repo from which `kb_ingest_precice_data` downloads the release asset. |
| `GITHUB_TOKEN` | — | Optional. Set if the release asset is in a private repo. |

The `setup` command automatically injects `PRECICE_PROJECTS_DIR` into the platform config. Add the embedding variables manually for KB query support:

```json
{
  "mcpServers": {
    "precice-ai": {
      "command": "python",
      "args": ["-m", "precice_ai.server"],
      "env": {
        "PRECICE_PROJECTS_DIR": "/path/to/your/projects",
        "OPENROUTER_API_KEY": "sk-or-..."
      }
    }
  }
}
```

### Knowledge base storage

The vector KB is stored as a compressed NumPy archive **outside the repo** so it is never committed to git:

```
~/.precice-ai/kb_store/kb-embeddings.npz
```

Check its status at any time:

```bash
# Via terminal
ls -lh ~/.precice-ai/kb_store/

# Via MCP tool
kb_precice_status()
```

---

## MCP tools reference

### Knowledge base

| Tool | Description |
|---|---|
| `kb_ingest_precice_data(github_token?)` | Downloads the latest pre-built embeddings archive from the GitHub Release (`kb-latest`). Run once to populate the local index. |
| `kb_query_precice(question, top_k)` | Semantic search over the local vector KB. Embeds the question and returns the top-k most similar doc chunks with source URLs and scores. |
| `kb_query_precice_live(question, top_k)` | Same as above but auto-downloads the archive if it is not yet present locally. Use this for all preCICE questions. |
| `kb_precice_status()` | Returns the local archive size, download timestamp, and chunk count. |

**Typical first use:** `kb_query_precice_live` handles everything — it downloads the archive on first use and runs semantic search. Requires `OPENROUTER_API_KEY` (or `BLABLADOR_API_KEY`) to embed the question at query time.

### Project discovery

| Tool | Description |
|---|---|
| `list_precice_projects()` | Lists all directories under `PRECICE_PROJECTS_DIR`. |
| `inspect_project_structure(project_name, max_depth)` | Prints the folder tree for a project up to `max_depth` levels. |
| `find_precice_config(project_name)` | Finds all `precice-config.xml` files within a project. |
| `run_command_in_project(project_name, command)` | Runs a command inside the project directory. Only allowlisted prefixes are permitted. |

Allowed command prefixes: `ls`, `pwd`, `cat`, `find`, `grep`, `tail`, `head`, `precice-tools`, `precice-cli`, `python3`, `./run.sh`

### Configuration

| Tool | Description |
|---|---|
| `inspect_precice_config(project_name)` | Returns the raw contents of `precice-config.xml`. |
| `summarize_precice_config(project_name)` | Extracts participants, meshes, data items, and coupling scheme tags from the XML. |
| `backup_precice_config(project_name)` | Creates a timestamped backup of `precice-config.xml` in the same directory. |

### precice-cli wrappers

These require `precice-cli` on `PATH` (`pip install precice`) and take an explicit `cwd`, not a `project_name`.

| Tool | Description |
|---|---|
| `precice_version()` | Shows the installed preCICE version via `precice-cli version`. |
| `precice_config_check(cwd, config_file)` | Validates a config file via `precice-cli config check`. |
| `precice_config_format(cwd, config_file)` | Formats a config file via `precice-cli config format`. |
| `precice_config_visualize(cwd, config_file, output_file)` | Generates a diagram via `precice-cli config visualize`. |
| `precice_config_doc(cwd, tag)` | Shows XML tag documentation via `precice-cli config doc`. |
| `precice_init(cwd, extra_args)` | Scaffolds a new preCICE config via `precice-cli init`. |
| `precice_profiling_analyze(cwd, data_dir, extra_args)` | Analyzes profiling output via `precice-cli profiling analyze`. |
| `precice_profiling_trace(cwd, data_dir, extra_args)` | Generates a trace visualization via `precice-cli profiling trace`. |
| `precice_profiling_export(cwd, data_dir, output_file, extra_args)` | Exports profiling data via `precice-cli profiling export`. |
| `precice_profiling_histogram(cwd, data_dir, extra_args)` | Generates a profiling histogram via `precice-cli profiling histogram`. |
| `precice_profiling_merge(cwd, data_dirs, output_dir, extra_args)` | Merges multiple profiling datasets via `precice-cli profiling merge`. |

### Logs

| Tool | Description |
|---|---|
| `list_project_logs(project_name)` | Lists all `*.log` and `*.txt` files in the project. |
| `read_project_logs(project_name, max_chars_per_file)` | Returns contents of all log files (truncated per file). |
| `read_latest_log(project_name, lines)` | Returns the last N lines of the most recently modified log file. |
| `analyze_precice_logs(project_name)` | Scans each log for error/warning/convergence/failure keywords and appends the last 30 lines. |

---

## Usage walkthrough

### 1. Download the knowledge base

```
kb_ingest_precice_data()
```

Downloads the pre-built vector embeddings archive from the GitHub Release. Run once; queries use the local cache until you explicitly refresh.

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
precice_config_check("/path/to/PRECICE_PROJECTS_DIR/partitioned-heat-conduction")
```

Requires `precice-cli` on `PATH` (`pip install precice`).

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
kb_query_precice_live("how does implicit coupling work in preCICE?")
kb_query_precice_live("what adapters does preCICE support?")
```

Both calls embed the question via the configured embedding API and return the most semantically similar chunks from the preCICE documentation.

---

## Vector knowledge base

### How it works

```
GitHub Action (weekly / manual)
  └── checkout precice/precice.github.io
        └── walk content/ (docs, tutorials, community, about)
              └── chunk each .md file (~450 words, 50-word overlap)
                    └── embed chunks via OpenRouter API
                          └── save kb-embeddings.npz → publish as GitHub Release (kb-latest)

MCP tool: kb_query_precice_live(question)
  └── download kb-embeddings.npz from kb-latest release  (first use only)
        └── embed question via OpenRouter API
              └── cosine similarity search (NumPy, no server)
                    └── return top-k chunks with title, url, score, snippet
```

The embeddings archive (`kb-embeddings.npz`) is stored locally at `~/.precice-ai/kb_store/` and loaded into memory on first query. No vector database server is required.

### Controlling what gets indexed

Edit [`kb_sources.json`](kb_sources.json) at the repo root to control which folders are indexed and which files are skipped:

```json
{
  "include_subfolders": ["docs", "tutorials", "community", "about"],
  "exclude_patterns": ["docs/_index.md", "docs/docs-meta", "tutorials/_index.md"]
}
```

The GitHub Action reads this file on every run — no changes to the workflow or build script are needed.

### Refreshing the knowledge base

**Automatic:** The Action runs every Sunday at 02:00 UTC. Any merged doc changes are picked up automatically.

**Manual trigger (GitHub UI):**
Actions → "Build & Publish Knowledge Base Embeddings" → "Run workflow"

**Manual trigger (CLI):**
```bash
gh workflow run kb-ingest.yml --repo vaibhavd2103/precice-ai
```

After the Action completes, the next call to any `kb_query_*` tool will download the new archive automatically (on first query after deletion of the old local file), or force a re-download explicitly:

```bash
# Delete local cache to force re-download on next query
rm ~/.precice-ai/kb_store/kb-embeddings.npz
```

Or call `kb_ingest_precice_data()` from the MCP tool to re-download immediately.

### Switching embedding providers

To switch from OpenRouter to Blablador (or any OpenAI-compatible provider), set these env vars in your MCP config — no code changes required:

| Variable | OpenRouter | Blablador |
|---|---|---|
| `OPENROUTER_API_KEY` / `BLABLADOR_API_KEY` | `sk-or-...` | your Blablador key |
| `EMBEDDING_BASE_URL` | `https://openrouter.ai/api/v1` | `https://helmholtz-blablador.fz-juelich.de:8000/v1` |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | `alias-embeddings` |

Also update `OPENROUTER_API_KEY` → `BLABLADOR_API_KEY` in the `OPENROUTER_API_KEY` GitHub Secret when rebuilding the index with Blablador.

### Required GitHub secret

Add this secret in **Settings → Secrets and variables → Actions → New repository secret** before running the Action:

| Secret | Value |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key from openrouter.ai/keys |

---

## Project structure

```
precice_ai/
├── server.py               # FastMCP server entry point
├── core/
│   ├── paths.py            # Project path resolution (env-var aware)
│   ├── safety.py           # Command allowlist and block patterns
│   ├── command_runner.py   # Safe subprocess execution
│   └── knowledge_base.py   # VectorKnowledgeBase (download, cosine search)
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
scripts/
└── build_embeddings.py     # Chunks docs, calls embedding API, saves .npz
.github/workflows/
└── kb-ingest.yml           # Scheduled Action: build embeddings → GitHub Release
kb_sources.json             # Controls which doc folders/files get indexed
server.py                   # Convenience shim for python server.py (local dev)
pyproject.toml              # Package definition and CLI entry points
```

---

## Codebase knowledge graph via the graphify skill (optional)

This repo ships a pre-built knowledge graph in `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`, `graph.html`), generated by the [graphify](https://github.com/Graphify-app/Graphify) Claude Code skill (`.claude/skills/graphify/SKILL.md`, triggered by `/graphify`). It gives an AI assistant a fast, structured map of this codebase instead of grepping raw files every time.

### How it's built

`/graphify` turns the repo into a graph in two extraction passes that run in parallel, then clusters and reports on the result:

```
detect files (code / docs / papers / images / video)
  ├── structural extraction: deterministic AST pass over .py files (free, no LLM)
  └── semantic extraction: files chunked (~20-25 each) and handed to parallel
        general-purpose subagents, which pull entities/relationships an AST
        can't see (call intent, shared data, design rationale)
        → merge AST + semantic nodes/edges, dedup by id
              → community detection (clustering) + god-node / surprising-connection analysis
                    → graph.json (GraphRAG-ready) + GRAPH_REPORT.md (plain-language audit) + graph.html (interactive)
```

Every edge is tagged `EXTRACTED` (explicit in source, e.g. an import or call), `INFERRED` (reasonable inference, with a confidence score), or `AMBIGUOUS` (uncertain, flagged rather than dropped) — the audit trail is never hidden.

### Querying it

```bash
# Ask a question about the codebase — BFS traversal for broad context
graphify query "how does the knowledge base ingestion work?"

# Find the relationship between two modules — shortest path
graphify path "KnowledgeBaseService" "kb_query_precice"

# Plain-language explanation of one node and its connections
graphify explain "VectorKnowledgeBase"
```

### Keeping it current

```bash
graphify update .        # incremental — re-extracts only changed files
```

Code-only changes skip the LLM subagent pass entirely (AST-only, no API cost); doc/image changes trigger the full semantic re-extraction.

### How Claude Code picks it up automatically

Both `/home/vaibhav/.claude/CLAUDE.md` (user-level) and this repo's `CLAUDE.md`/`.claude/CLAUDE.md` register the trigger: typing `/graphify` invokes the skill directly, and — per the rules in this repo's `CLAUDE.md` — whenever `graphify-out/graph.json` already exists, codebase questions are answered with `graphify query "<question>"` before falling back to reading files, and `graphify update .` runs after code edits to keep the graph in sync.

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
- The vector KB archive is stored locally at `~/.precice-ai/kb_store/kb-embeddings.npz`. At query time, the question text is sent to the configured embedding API (OpenRouter or Blablador) to produce a vector — no document content leaves your machine.

---

## License

MIT — see `LICENSE`.
