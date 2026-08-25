# preCICE AI MCP Server

A Model Context Protocol (MCP) server for exploring and operating local preCICE simulation projects from AI coding tools such as Codex, Claude Code, Cursor, Windsurf, and Claude Desktop.

This README is the end-user guide: install it, register it with your MCP client, and start using the tools. If you want the architecture, file-by-file walkthrough, local development notes, or contribution workflow, read [CONTRIBUTOR_GUIDE.md](CONTRIBUTOR_GUIDE.md).

## What It Does

- Exposes MCP tools for project discovery, config inspection, log reading, and safe command execution.
- Wraps selected `precice-cli` functionality for validation, initialization, and profiling tasks.
- Provides a semantic preCICE knowledge base backed by pre-built embeddings downloaded from GitHub Releases.
- Ships a `precice-ai` CLI that sets up supported MCP clients for you.

## Installation

### macOS / Linux

```bash
git clone https://github.com/vaibhavd2103/precice-ai
cd precice-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Windows PowerShell

```powershell
git clone https://github.com/vaibhavd2103/precice-ai
cd precice-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

### One-command bootstrap helper

If you want the repo to create a virtual environment and immediately run the bootstrap flow:

```bash
./install.sh auto --projects-dir /path/to/preCICE/cases
```

After installation, the `precice-ai` command is available inside the virtual environment.

## Quick Start

Register the server with a supported MCP client:

```bash
precice-ai bootstrap auto --projects-dir /path/to/preCICE/cases
```

If you want KB queries to work immediately, include an embedding API key:

```bash
precice-ai bootstrap codex \
  --projects-dir /path/to/preCICE/cases \
  --openrouter-api-key sk-or-...
```

This command:

- creates or updates `.env`
- injects runtime variables into the MCP client config
- registers `python -m precice_ai.server` as the MCP server command

List which supported clients are detected locally:

```bash
precice-ai list-platforms
```

## Supported Clients

- `auto`
- `claude-code`
- `claude-desktop`
- `codex`
- `cursor`
- `windsurf`
- `generic`

`generic` prints config snippets for manual installation instead of editing a specific client config automatically.

## Manual MCP Setup

If you do not want to use `precice-ai bootstrap`, configure your client manually.

Use the Python interpreter inside the virtual environment:

- macOS / Linux: `.venv/bin/python`
- Windows: `.venv\Scripts\python.exe`

Use this server command:

```text
-m precice_ai.server
```

### JSON-based clients

Use this structure for Claude Code project config, Claude Desktop, Cursor JSON config, Windsurf, or any other JSON-based MCP client:

```json
{
  "mcpServers": {
    "precice-ai": {
      "command": "/absolute/path/to/precice-ai/.venv/bin/python",
      "args": ["-m", "precice_ai.server"],
      "env": {
        "PRECICE_PROJECTS_DIR": "/absolute/path/to/preCICE/cases",
        "OPENROUTER_API_KEY": "sk-or-..."
      }
    }
  }
}
```

### Codex

Native CLI:

```bash
codex mcp add precice-ai \
  --env PRECICE_PROJECTS_DIR=/absolute/path/to/preCICE/cases \
  --env OPENROUTER_API_KEY=sk-or-... \
  -- /absolute/path/to/precice-ai/.venv/bin/python -m precice_ai.server
```

Direct `~/.codex/config.toml` form:

```toml
[mcp_servers."precice-ai"]
command = "/absolute/path/to/precice-ai/.venv/bin/python"
args = ["-m", "precice_ai.server"]

[mcp_servers."precice-ai".env]
PRECICE_PROJECTS_DIR = "/absolute/path/to/preCICE/cases"
OPENROUTER_API_KEY = "sk-or-..."
```

### Common config locations

- Claude Code project scope: `.mcp.json`
- Claude Code user scope: `~/.claude/settings.json`
- Claude Desktop macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Claude Desktop Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Claude Desktop Linux: `~/.config/Claude/claude_desktop_config.json`
- Cursor global scope: `~/.cursor/mcp.json`
- Windsurf: `~/.codeium/windsurf/mcp_config.json`
- Codex: `~/.codex/config.toml`

Restart or reload the client after editing its config.

## Environment Variables

Required for semantic KB queries:

- `OPENROUTER_API_KEY` or `BLABLADOR_API_KEY`

Common optional variables:

| Variable                 | Default                                       | Purpose                                                          |
| ------------------------ | --------------------------------------------- | ---------------------------------------------------------------- |
| `PRECICE_PROJECTS_DIR`   | `./test-projects` when running from repo root | Directory scanned by the project tools.                          |
| `PRECICE_KB_STORE_DIR`   | `~/.precice-ai/kb_store`                      | Local storage for downloaded KB assets.                          |
| `OPENROUTER_API_KEY`     | none                                          | Embedding API key when using OpenRouter.                         |
| `BLABLADOR_API_KEY`      | none                                          | Embedding API key when using Blablador.                          |
| `EMBEDDING_BASE_URL`     | `https://openrouter.ai/api/v1`                | OpenAI-compatible embeddings base URL.                           |
| `EMBEDDING_MODEL`        | `openai/text-embedding-3-small`               | Embedding model name.                                            |
| `PRECICE_AI_GITHUB_REPO` | `vaibhavd2103/precice-ai`                     | GitHub repo used for KB asset downloads.                         |
| `GITHUB_TOKEN`           | none                                          | Optional token for private release access or higher rate limits. |

To use Blablador instead of OpenRouter:

```bash
precice-ai bootstrap codex \
  --projects-dir /path/to/preCICE/cases \
  --embedding-base-url https://helmholtz-blablador.fz-juelich.de:8000/v1 \
  --embedding-model alias-embeddings
```

Then set `BLABLADOR_API_KEY` in `.env` or in the client config.

## How To Use It

Once your MCP client sees the server, the main workflow is:

1. Ask the agent to list available preCICE projects.
2. Inspect the project structure and locate `precice-config.xml`.
3. Read or summarize the config.
4. Read logs or run safe read-only commands in the project.
5. Check KB freshness with `kb_precice_status()`, then use `kb_query_precice(...)` for fresh categories or `kb_query_precice_live(...)` to refresh stale/missing ones.

Typical tool calls:

```text
list_precice_projects()
inspect_project_structure("partitioned-heat-conduction")
find_precice_config("partitioned-heat-conduction")
inspect_precice_config("partitioned-heat-conduction")
summarize_precice_config("partitioned-heat-conduction")
read_latest_log("partitioned-heat-conduction")
analyze_precice_logs("partitioned-heat-conduction")
kb_precice_status()
# If the documentation category is fresh:
kb_query_precice("how does implicit coupling work in preCICE?", category="documentation")
# If the documentation category is missing or stale:
kb_query_precice_live("how does implicit coupling work in preCICE?", category="documentation")
```

Safe command execution is available through:

```text
run_command_in_project("partitioned-heat-conduction", "ls -la")
run_command_in_project("partitioned-heat-conduction", "cat run.sh")
```

Only allowlisted command prefixes are permitted.

## `precice-cli`-Backed Tools

Some MCP tools wrap `precice-cli`. Those tools require `precice-cli` to be installed separately and available on `PATH`.

Examples:

```text
precice_version()
precice_config_check("/absolute/path/to/project")
precice_config_visualize("/absolute/path/to/project")
precice_config_doc("/absolute/path/to/project", "participant")
precice_init(...)
precice_profiling_analyze("/absolute/path/to/project")
```

If `precice-cli` is missing, those tools return an install hint instead of crashing the server.

## CLI Commands

The Typer-based CLI exposes:

- `precice-ai setup <platform>`
- `precice-ai bootstrap [platform]`
- `precice-ai open [platform]`
- `precice-ai list-platforms`
- `precice-ai server`
- `precice-ai kb status`
- `precice-ai kb ingest`
- `precice-ai kb query`

Examples:

```bash
precice-ai --help
precice-ai list-platforms
precice-ai kb status
precice-ai kb ingest
precice-ai kb query "implicit coupling" --mode vector-live
precice-ai server
```

## Running The Server Manually

All of the following start the same MCP server:

```bash
precice-ai server
python -m precice_ai.server
python server.py
```

This is mostly useful for local debugging or manual client integration.

## Knowledge Base Storage

`precice-ai setup`/`bootstrap` automatically download the full knowledge base
(all 7 vector categories + the lexical index) the first time you run them, so
it's ready to query immediately. This is a best-effort step — it never fails
setup, even if GitHub is unreachable. Pass `--skip-kb-ingest` to skip it (e.g.
in CI or offline environments), and run `precice-ai kb ingest` manually later.

Vector KB assets are stored outside the repo by default:

```text
~/.precice-ai/kb_store/kb-embeddings-about.npz
~/.precice-ai/kb_store/kb-embeddings-community.npz
~/.precice-ai/kb_store/kb-embeddings-documentation.npz
~/.precice-ai/kb_store/kb-embeddings-tutorials.npz
~/.precice-ai/kb_store/kb-embeddings-forum.npz
~/.precice-ai/kb_store/kb-embeddings-issues.npz
~/.precice-ai/kb_store/kb-embeddings-pulls.npz
```

Check status:

```bash
precice-ai kb status
```

Or from MCP:

```text
kb_precice_status()
```

## Safety Notes

- `run_command_in_project` is intentionally restrictive and only allows approved command prefixes.
- The server blocks obviously destructive patterns such as `rm`, `sudo`, `curl`, `wget`, and shutdown commands.
- Log analysis is heuristic and meant to assist debugging, not replace solver-level validation.
- Document embeddings are prebuilt offline; only the query text is embedded at query time.

## Project Layout

For contributors, the deep walkthrough lives in [CONTRIBUTOR_GUIDE.md](CONTRIBUTOR_GUIDE.md). At a high level:

```text
precice_ai/
  cli/      # user-facing Typer CLI and platform installers
  core/     # path resolution, safety checks, command runner, KB logic
  tools/    # MCP tool registration modules
  utils/    # JSON schema and supporting assets
scripts/    # KB build and maintenance scripts
server.py   # convenience entry point for local dev
```

<!-- ## License

MIT -->
