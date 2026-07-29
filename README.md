# preCICE AI MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for exploring and operating local preCICE simulation projects from any AI coding agent.

Exposes 17 tools covering project discovery, config inspection, command execution, log analysis, and a semantic knowledge base built from the preCICE documentation using vector embeddings.

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

The vector KB is stored as one compressed NumPy archive per category **outside the repo** so it is never committed to git:

```
~/.precice-ai/kb_store/kb-embeddings-about.npz
~/.precice-ai/kb_store/kb-embeddings-community.npz
~/.precice-ai/kb_store/kb-embeddings-documentation.npz
~/.precice-ai/kb_store/kb-embeddings-tutorials.npz
~/.precice-ai/kb_store/kb-embeddings-forum.npz
~/.precice-ai/kb_store/kb-embeddings-issues.npz
~/.precice-ai/kb_store/kb-embeddings-pulls.npz
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
kb_query_precice_live("how does implicit coupling work in preCICE?")
kb_query_precice_live("what adapters does preCICE support?")
```

Both calls embed the question via the configured embedding API and return the most semantically similar chunks from the preCICE documentation.

---

## Vector knowledge base

This is the retrieval system behind every `kb_query_*` / `kb_ingest_precice_data` / `kb_precice_status` tool. It is implemented by `VectorKnowledgeBase` in [`precice_ai/core/knowledge_base.py`](precice_ai/core/knowledge_base.py) and has two independent lifecycles: an **offline ingestion pipeline** (runs in GitHub Actions, produces embeddings) and an **online query path** (runs inside the MCP server process, in your editor/agent).

There is also a second, older code path — `KnowledgeBaseService` (BM25-style lexical scoring over live-scraped docs/forum pages, no embeddings). It still lives in `knowledge_base.py` and is instantiated in `knowledge_tools.py`, but **no MCP tool calls it today**; it's kept around for [`scripts/compare_kb_search.py`](scripts/compare_kb_search.py), which benchmarks lexical vs. vector retrieval quality. Everything below describes the vector path, which is what actually answers questions.

### When it runs

| Event | What happens |
|---|---|
| Weekly, Sunday 02:00 UTC | `kb-ingest.yml` runs automatically, rebuilding only categories whose sources changed. |
| `gh workflow run kb-ingest.yml` / Actions tab "Run workflow" | Same pipeline, triggered on demand. |
| First call to `kb_query_precice_live` in a fresh environment | The server downloads whichever categories aren't yet cached in `~/.precice-ai/kb_store/`, then queries. Subsequent calls in the same environment reuse the cache — no network round-trip beyond embedding the question. |
| `kb_ingest_precice_data(category?)` called explicitly | Forces a fresh download of one or all categories, overwriting the local cache. |
| `kb_query_precice(...)` (non-live) | Never downloads — errors out if the local cache is empty. Use this when you want to control ingestion timing explicitly. |

Ingestion (building the embeddings) and querying (using them) are fully decoupled: the MCP server never computes embeddings for documents, only for the question text at query time.

### How ingestion works (offline, GitHub Actions)

```
GitHub Action (weekly / manual)
  └── checkout precice/precice.github.io, precice/precice, precice/tutorials
        └── for each category (about, community, documentation, tutorials,
            forum, issues, pulls):
              ├── compute a signature and compare it to kb_state.json:
              │     • git categories   → latest commit SHA per {repo, path}
              │     • forum            → latest post timestamp across recent topics
              │     • issues / pulls   → updated_at of the most recently
              │                          updated GitHub issue / PR (sorted desc,
              │                          one API call, first page only)
              ├── skip the category entirely if the signature is unchanged
              └── if stale, build the category:
                    • about/community/documentation/tutorials: chunk every .md
                      file under the configured checkout path (~450 words per
                      chunk, 50-word overlap, frontmatter stripped, min 30
                      words/chunk to drop near-empty fragments)
                    • forum: fetch recent Discourse topics + all posts in each,
                      merge post bodies into one document per topic, then chunk
                    • issues/pulls: fetch up to 200 items via the GitHub REST
                      API (state=all, sorted by updated), merge each item's
                      body with up to 20 of its comments into one document,
                      then chunk
                    └── embed every chunk via the OpenAI-compatible embedding
                          API (OpenRouter by default)
                          └── save kb-embeddings-<category>.npz
                                → upload/replace just that asset on the
                                  GitHub Release (kb-latest); other categories'
                                  assets are left untouched
        └── commit updated kb_state.json back to the repo
```

Each `.npz` archive holds two parallel arrays: `embeddings` (an `(N, D)` float32 matrix, one row per chunk) and `chunks` (a JSON-encoded list of `{title, url, source, category, chunk_index, text}` — row `i` of `chunks` describes row `i` of `embeddings`). Because categories are independent, editing only the tutorials pages re-embeds and re-uploads just `kb-embeddings-tutorials.npz`; opening a new GitHub issue only touches `kb-embeddings-issues.npz` on the next scheduled run.

If no release asset exists yet for a category (e.g. right after adding one), the MCP server falls back to building it locally on first use, using the same scripts the Action runs — this requires a source checkout next to the installed package and `OPENROUTER_API_KEY` set, and can take a while for large categories.

### How querying and chunk matching work (online, inside the MCP server)

```
kb_query_precice_live(question, top_k=5, category=None)
  ├── if the requested category (or all, if none given) isn't cached locally:
  │     download kb-embeddings-<category>.npz from the kb-latest release
  ├── lazy-load each requested category's .npz into memory
  │     (kept cached for the life of the server process)
  ├── embed the question via the configured embedding API
  │     → a single (D,) float32 vector, same model/dimensions as the chunks
  ├── concatenate the embedding matrices of every requested category into
  │     one (N_total, D) matrix — matching happens globally, not per-category
  ├── score every chunk by cosine similarity:
  │     score[i] = (emb[i] · q_vec) / (‖emb[i]‖ · ‖q_vec‖)
  ├── argsort descending, take the top_k indices
  └── return {score, title, url, source, category, snippet} per hit
        (snippet = the chunk's raw text, truncated to 400 chars)
```

This is brute-force cosine similarity over whatever is loaded in memory — no ANN index (FAISS/HNSW), no vector database, no reranking stage. At the current corpus size (a few thousand chunks per category) a full NumPy matrix-vector product is fast enough to run synchronously per query. Passing `category` restricts the matrix to one category before scoring; omitting it merges every downloaded category and ranks globally, so a very on-topic forum chunk can legitimately outrank a documentation chunk if it embeds closer to the question.

### Categories and sources

Edit [`kb_sources.json`](kb_sources.json) at the repo root to control which categories exist, which repos/folders (or APIs) feed each one, and which files are skipped:

```json
{
  "categories": {
    "about":         { "sources": [{ "repo": "precice/precice.github.io", "checkout_path": "content/about" }] },
    "community":     { "sources": [{ "repo": "precice/precice.github.io", "checkout_path": "content/community" }] },
    "documentation": { "sources": [
      { "repo": "precice/precice.github.io", "checkout_path": "content/docs" },
      { "repo": "precice/precice", "checkout_path": "docs", "branch": "develop" }
    ]},
    "tutorials": { "sources": [
      { "repo": "precice/precice.github.io", "checkout_path": "content/tutorials" },
      { "repo": "precice/tutorials", "checkout_path": "", "branch": "develop" }
    ]},
    "forum":  { "type": "discourse",     "forum_url": "https://precice.discourse.group" },
    "issues": { "type": "github_issues", "repo": "precice/precice" },
    "pulls":  { "type": "github_prs",    "repo": "precice/precice" }
  }
}
```

The GitHub Action reads this file on every run — no changes to the workflow or build scripts are needed to add a source to an existing category. Adding a brand-new category also requires: its name added to `CATEGORIES` in [`precice_ai/core/knowledge_base.py`](precice_ai/core/knowledge_base.py), a matching branch in `_build_category_locally` (for the local-build fallback), and either an entry in `GIT_CATEGORIES` in [`kb-ingest.yml`](.github/workflows/kb-ingest.yml) (git-checkout categories) or a dedicated build/signature step (API-fetched categories, following the `forum`/`issues`/`pulls` pattern).

`kb_state.json` (committed to the repo) tracks each category's last-processed signature so unchanged categories are skipped on the next run.

### Limitations

- **Query-time freshness ceiling.** Once a category is downloaded locally it is used indefinitely — the MCP server never checks whether a newer release exists. Freshness is bounded by whenever you last called `kb_ingest_precice_data` (or deleted the cache), not by how recently the Action ran.
- **No reranking or cross-encoder pass.** Retrieval is pure cosine similarity over independently-embedded chunks; it has no notion of query-document interaction beyond the embedding space, so subtly-worded or multi-hop questions can retrieve topically-related-but-wrong chunks.
- **Chunk-boundary fragmentation.** Long documents (a big config reference page, a long issue thread) are split into ~450-word windows with only 50 words of overlap. An answer that spans two chunks may not fully appear in either one, and `top_k` results can duplicate content across overlapping chunks from the same document.
- **Global top-k merge across categories.** Without an explicit `category`, ranking is entirely score-driven — there's no per-category quota, so a category with many near-duplicate chunks (e.g. `forum`) can crowd out a category with fewer but more authoritative chunks (e.g. `documentation`).
- **`issues`/`pulls` are lossy summaries of long threads.** Only the first 20 comments per issue/PR are embedded and each item is capped at 200 most-recently-updated items per category per rebuild; very active or very old discussions may be truncated or missing entirely.
- **Model lock-in per corpus.** All chunks in a category must share one embedding model/dimensionality. Changing `EMBEDDING_MODEL` requires rebuilding every category from scratch — old and new embeddings can't be mixed in one `.npz`.
- **No in-place incremental updates.** A "stale" category is rebuilt wholesale (every source file re-chunked and re-embedded), not diffed — there's no per-chunk change detection, so a one-line doc edit re-embeds the entire category.
- **Requires live network + API key at query time.** `kb_query_precice`/`kb_query_precice_live` need `OPENROUTER_API_KEY` (or `BLABLADOR_API_KEY`) to embed the question; if unset, or if the embedding API is unreachable, the tool returns an error rather than falling back to lexical search.
- **GitHub API rate limits bound `issues`/`pulls` ingestion.** Unauthenticated requests are capped at 60/hour; the Action passes `GITHUB_TOKEN` to raise this to 5,000/hour, but a manual local rebuild without a token can hit the limit on large repos.
- **Snippets are truncated, not summarized.** The `snippet` field in results is the raw chunk text cut to 400 characters — it can end mid-sentence and isn't re-ranked for relevance within the chunk.
- **No access control.** Everything ingested is assumed public (precice.org, the public GitHub repos, the public forum); there's no mechanism to scope or redact content per user/query.

### Refreshing the knowledge base

**Automatic:** The Action runs every Sunday at 02:00 UTC and only rebuilds categories whose sources changed since the last run.

**Manual trigger (GitHub UI):**
Actions → "Build & Publish Knowledge Base Embeddings" → "Run workflow"

**Manual trigger (CLI):**
```bash
gh workflow run kb-ingest.yml --repo vaibhavd2103/precice-ai
```

After the Action completes, the next call to any `kb_query_*` tool downloads any category not yet cached locally. To force a re-download of everything (or just one category):

```bash
# Delete local cache to force re-download on next query
rm ~/.precice-ai/kb_store/kb-embeddings-*.npz

# Or just one category
rm ~/.precice-ai/kb_store/kb-embeddings-tutorials.npz
```

Or call `kb_ingest_precice_data()` (optionally with `category="tutorials"`) from the MCP tool to re-download immediately.

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
├── build_embeddings.py                  # Chunks a category's Markdown sources, embeds, saves .npz
├── build_forum_embeddings.py            # Same, for the forum category (fetched via Discourse API)
├── build_github_activity_embeddings.py  # Same, for the issues/pulls categories (fetched via GitHub REST API)
├── render_sources_json.py               # Resolves a category's kb_sources.json entries to local checkout paths
└── kb_state.py                          # Computes/compares per-category signatures (git SHA / forum timestamp / GitHub updated_at)
.github/workflows/
└── kb-ingest.yml           # Scheduled Action: rebuild only changed categories → GitHub Release
kb_sources.json             # Defines categories and which repos/folders feed each one
kb_state.json               # Per-category last-processed signature (committed, updated by the Action)
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
- The vector KB archives are stored locally at `~/.precice-ai/kb_store/kb-embeddings-<category>.npz`. At query time, the question text is sent to the configured embedding API (OpenRouter or Blablador) to produce a vector — no document content leaves your machine.

---

## License

MIT — see `LICENSE`.
