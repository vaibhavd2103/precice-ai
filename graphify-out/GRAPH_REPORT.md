# Graph Report - precice-ai  (2026-10-20)

## Corpus Check
- 64 files · ~120,365 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 983 nodes · 1403 edges · 80 communities (65 shown, 15 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 41 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f3c39ffd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]

## God Nodes (most connected - your core abstractions)
1. `Contributor Guide` - 25 edges
2. `Platform` - 22 edges
3. `Deduper` - 20 edges
4. `KnowledgeBaseService` - 20 edges
5. `KBFormatError` - 19 edges
6. `RawChunk` - 16 edges
7. `assemble_document()` - 16 edges
8. `clean_markdown()` - 16 edges
9. `VectorKnowledgeBase` - 16 edges
10. `What You Must Do When Invoked` - 16 edges

## Surprising Connections (you probably didn't know these)
- `CleaningTests` --uses--> `RawChunk`  [INFERRED]
  tests/test_kb_format.py → precice_ai/kb/chunking.py
- `ChunkingTests` --uses--> `RawChunk`  [INFERRED]
  tests/test_kb_format.py → precice_ai/kb/chunking.py
- `StoreAndValidationTests` --uses--> `RawChunk`  [INFERRED]
  tests/test_kb_format.py → precice_ai/kb/chunking.py
- `CleaningTests` --uses--> `Segment`  [INFERRED]
  tests/test_kb_format.py → precice_ai/kb/chunking.py
- `ChunkingTests` --uses--> `Segment`  [INFERRED]
  tests/test_kb_format.py → precice_ai/kb/chunking.py

## Communities (80 total, 15 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (51): CommandResult, precice_cli_available(), Outcome of one command. `error` is set when it never ran (blocked,     missing w, Text report returned to the agent by the command tools., Run an allowlisted command inside a working directory., Run a command safely inside a given working directory and report it as text., Run `precice-cli <args>`; the single entry point for every precice-cli call., run_command() (+43 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (49): code:bash ($(cat graphify-out/.graphify_python) -c "), code:block11 ([Agent tool call 1: files 1-15, subagent_type="general-purpo), code:bash (PROJECT_ROOT=$(cat graphify-out/.graphify_root)), code:block13 (You are a graphify extraction subagent. Read the files liste), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c ") (+41 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (40): _client(), configured_model(), embed_query(), embed_texts(), EmbeddingConfigError, Shared embedding helper — the single source of truth for turning text into vecto, Raised when no embedding API key is configured., Embed a batch of texts, preserving input order. (+32 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (48): 1. Introduction & Problem Statement, 4.1 Tool Integration Approaches, 4.2 Knowledge & Context Management Approaches, 4. Comparison Matrices, 5. Best Approach & Recommended Architecture, 6. Conclusion, 7. References, A Comparative Analysis for Thesis Research (+40 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (45): Claude Code project scope (`.mcp.json`), CLI Commands, code:bash (pipx install precice-ai), code:json ({), code:json ({), code:bash (codex mcp add precice-ai \), code:toml ([mcp_servers."precice-ai"]), code:bash (precice-ai bootstrap codex \) (+37 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (43): code:block10 (You are a graphify extraction subagent. Read the files liste), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (mkdir -p graphify-out), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c ") (+35 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (40): Advantages, Advantages, Advantages, Advantages, Advantages, Approach 1: MCP Server (Model Context Protocol), Approach 2: LangChain / LangGraph Agent with Custom Tools, Approach 3: Raw Function Calling (Anthropic / OpenAI API) (+32 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (36): description, exclude_patterns, sources, description, exclude_patterns, gitmodules_branch, gitmodules_repo, type (+28 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (34): code:block1 (/graphify                                             # full), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c ") (+26 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (34): code:block1 (/graphify                                             # full), code:bash (if [ ! -f graphify-out/.graphify_python ]; then), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c ") (+26 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (26): build_client_env(), write_env_file(), bootstrap(), _build_extra_env(), _configure_logging(), _detect_platform(), kb_ingest(), kb_query() (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (22): category_stats(), check_npz_compat(), embed_chunks(), finalize_store(), manifest_categories(), now_iso(), npz_name(), Reading/writing the two KB stores and the ingestion manifest.  On-disk layout (a (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.21
Nodes (17): build_forum_chunks(), build_github_chunks(), _drop_template_lines(), topics: DiscourseTopicDocument-like objects (title, url, posts, ...)., chunk_segments(), Deduper, Merge short consecutive segments into chunks (original order kept,     the first, Exact-duplicate filter across everything assembled in one category. (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (13): clean_forum_post(), clean_markdown(), html_to_markdown(), parse_frontmatter(), _protect(), Structure-preserving cleaning for KB ingestion.  Unlike the legacy `strip_markdo, Discourse raw post → cleaned markdown (also drops :emoji: shortcodes)., Convert a rendered HTML page into (title, markdown). Keeps headings,     paragra (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (15): _bm25_like_score(), _dedupe_keep_order(), _fetch_release_assets(), _freshness_details(), _load_asset_meta(), _meta_expired(), _meta_path(), _normalize_url() (+7 more)

### Community 15 - "Community 15"
Cohesion: 0.17
Nodes (16): category_config(), checkout(), checkout_all(), _git(), _log(), parse_gitmodules(), Discover and check out the repos behind the 'adapters' KB category.  The categor, Discover repos from .gitmodules, check them out into dest, and write     dest/ma (+8 more)

### Community 16 - "Community 16"
Cohesion: 0.16
Nodes (13): _Block, chunk_markdown(), _overlap_tail(), _parse_blocks(), Chunkers that turn cleaned Markdown / discussion segments into chunk bodies, and, Up to OVERLAP_CHARS from the end of the previous chunk's last prose     block, s, Heading-aware chunking of cleaned Markdown., Split an over-long fenced block on line boundaries, re-fencing each part. (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.21
Nodes (13): build_markdown_chunks(), _doc_title(), _file_url(), _is_included(), _log(), Build canonical `Chunk` records for every KB category.  One function per source, Checklist lines that recur across many descriptions are PR/issue     template bo, _template_checklist_lines() (+5 more)

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (9): build_embed_text(), is_excluded_path(), make_chunk_id(), Canonical chunk schema shared by the vector and lexical knowledge bases.  Every, Return a list of schema violations for one serialised chunk (empty = ok)., True for changelog entries, CHANGELOG/CONTRIBUTING/LICENSE files., validate_chunk_dict(), validate_chunks() (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.23
Nodes (15): category_signature(), content_tree_hash(), forum_signature(), github_activity_signature(), is_stale(), load_state(), main(), _parse_checkout_dirs() (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.23
Nodes (7): KnowledgeBaseService, Sync kb_file from the kb-latest Release's kb-lexical.json asset.          The re, Search-hit shape shared by the lexical and vector stores. `text` is the     full, _result_from_chunk(), _schema_error(), main(), Dev/fallback-only tool — NOT part of the primary kb-ingest.yml pipeline.  The pr

### Community 21 - "Community 21"
Cohesion: 0.16
Nodes (7): ABC, Platform, Return the standard MCP server config block for this package.          When ``po, Return ``path`` as a POSIX string relative to ``root``, or None if it     is not, Return True if this platform can be launched from the CLI., Launch the platform, opening the given workspace when supported., _relative_to()

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (13): code:text (precice-ai/), code:text (pyproject.toml), Contributor Guide, Environment Loading Model, Final Mental Model, Fresh-System Setup: End-To-End Contributor Path, Graphify And Codebase Navigation, High-Level Architecture (+5 more)

### Community 23 - "Community 23"
Cohesion: 0.33
Nodes (11): DiscoursePost, DiscourseTopicDocument, _fetch_categories(), fetch_discourse_topic_documents(), _fetch_topic_posts(), _get_json(), _iter_category_topics(), _normalize_api_url() (+3 more)

### Community 24 - "Community 24"
Cohesion: 0.20
Nodes (8): kb_status(), Show local vector + lexical KB file status (size, last check, chunk counts)., _asset_name(), _find_kb_sources_config(), Downloads pre-built per-category .npz embedding archives from a GitHub     Relea, Sync each category's .npz from the kb-latest Release.          The release is th, Fallback for when no GitHub Release asset exists yet for a category.          Ru, VectorKnowledgeBase

### Community 25 - "Community 25"
Cohesion: 0.24
Nodes (8): Sync the local KB (vector + lexical) from the kb-latest GitHub Release.      Sin, sync_kb_from_release(), get_env_file_path(), Return the .env file to load API keys and other settings from.      Resolved in, _bootstrap_kb(), main(), Convenience entry point for running the server from the repo root.  For producti, Sync the local KB from the kb-latest GitHub Release before serving.      Runs on

### Community 26 - "Community 26"
Cohesion: 0.31
Nodes (8): _fetch_comments(), fetch_github_items(), _fetch_items(), _headers(), is_bot_user(), Network fetchers for the GitHub issues/pulls categories., Human comments only (bots dropped), oldest first, up to comments_limit., Issues or PRs as plain dicts: number, title, url, state, labels, merged,     clo

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (3): ClaudeCodePlatform, Claude Code CLI — writes to .mcp.json (project) or ~/.claude.json (user)., Mark 'precice-ai' as an approved .mcp.json server for this project.          Cla

### Community 28 - "Community 28"
Cohesion: 0.20
Nodes (10): description, type, description, type, properties, data, from-patch, to-patch (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.22
Nodes (9): code:text (CLI command), code:text (client launches python -m precice_ai.server), code:text (run_command_in_project(project_name, command)), code:text (kb_precice_status()), Flow 1: `precice-ai bootstrap codex`, Flow 2: MCP server startup, Flow 3: project command execution, Flow 4: semantic KB query (+1 more)

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (8): 1. MCP clients, 2. The FastMCP server, 3. Local preCICE project directory, 4. Local knowledge cache: `~/.precice-ai/kb_store`, 5. `precice-cli` binary, 6. Offline build pipeline and GitHub Release assets, Following one request through the diagram, MCP Server Architecture In Detail

### Community 32 - "Community 32"
Cohesion: 0.25
Nodes (8): code:bash (git clone https://github.com/vaibhavd2103/precice-ai), code:bash (./install.sh auto --projects-dir /path/to/preCICE/cases), code:bash (precice-ai --help), Local Development Setup, Optional helper script, Prerequisites, Quick sanity checks, Recommended setup

### Community 35 - "Community 35"
Cohesion: 0.29
Nodes (6): Current Scope, graphify (optional), preCICE AI Agent Instructions, preCICE knowledge base, Safety Rules, Tool Usage Order

### Community 36 - "Community 36"
Cohesion: 0.29
Nodes (7): code:bash (python -m precice_ai.cli.main --help), KB queries fail, MCP client shows no server or no tools, `precice-ai` command not found, `precice-cli` wrapper tools fail, Project tools return no projects, Troubleshooting

### Community 37 - "Community 37"
Cohesion: 0.38
Nodes (3): _ends_mid_word(), True when `chunk` stops inside a word that the next chunk continues., StoreAndValidationTests

### Community 38 - "Community 38"
Cohesion: 0.53
Nodes (5): main(), _print_results(), Run lexical (BM25-like) and vector (embedding cosine-similarity) search against, _run_lexical(), _run_vector()

### Community 40 - "Community 40"
Cohesion: 0.33
Nodes (6): Canonical chunk format (`precice_ai/kb/`), `core/command_runner.py`, `core/knowledge_base.py`, Core Modules, `core/paths.py`, `core/safety.py`

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (6): code:text (~/.precice-ai/kb_store/), code:text (source repos / APIs), Knowledge Base Architecture, Offline build/publish phase, Online download/query phase, Why the KB store lives outside the repo

### Community 42 - "Community 42"
Cohesion: 0.33
Nodes (6): 1. Confusing `requirements.txt` with the real package definition, 2. Forgetting that the server is launched by the client, not by the CLI, 3. Testing only from the repo root, 4. Breaking the safety model while adding convenience, 5. Assuming the whole KB is fetched at query time, Common Contributor Pitfalls

### Community 43 - "Community 43"
Cohesion: 0.33
Nodes (6): Tool Modules, `tools/cli_tools.py`, `tools/config_tools.py`, `tools/knowledge_tools.py`, `tools/log_tools.py`, `tools/project_tools.py`

### Community 44 - "Community 44"
Cohesion: 0.33
Nodes (6): code:bash (precice-ai --help), Day-To-Day Development Workflow, When you change CLI behavior, When you change knowledge-base behavior, When you change MCP tools, When you change safety behavior

### Community 45 - "Community 45"
Cohesion: 0.33
Nodes (5): description, properties, required, title, type

### Community 46 - "Community 46"
Cohesion: 0.40
Nodes (4): enableAllProjectMcpServers, enabledMcpjsonServers, permissions, allow

### Community 48 - "Community 48"
Cohesion: 0.40
Nodes (5): Add a new CLI command, Add a new client installer, Add a new KB category, Add a new MCP tool, How To Extend The Project

### Community 49 - "Community 49"
Cohesion: 0.40
Nodes (5): code:bash (precice-ai --help), code:bash (precice-ai kb status), code:bash (precice-ai kb ingest), code:bash (precice-ai setup generic --projects-dir /absolute/path/to/ca), Validation And Testing Strategy

### Community 50 - "Community 50"
Cohesion: 0.40
Nodes (5): default, description, enum, type, data-type

### Community 51 - "Community 51"
Cohesion: 0.50
Nodes (5): items, optional, required, type, items

### Community 52 - "Community 52"
Cohesion: 0.40
Nodes (5): description, minItems, type, uniqueItems, exchanges

### Community 53 - "Community 53"
Cohesion: 0.40
Nodes (5): description, minItems, type, uniqueItems, participants

### Community 54 - "Community 54"
Cohesion: 0.50
Nodes (3): graphify (optional), preCICE knowledge base, Running a preCICE project

### Community 57 - "Community 57"
Cohesion: 0.50
Nodes (4): Embedding configuration, Environment Variables In Detail, GitHub integration, Project and KB paths

### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (4): code:json ({), `Platform` base class responsibilities, Platform Installers, Supported installers

### Community 59 - "Community 59"
Cohesion: 0.50
Nodes (4): 1. The package/CLI entry point, 2. The MCP server entry point, code:toml ([project.scripts]), The Two Entry Points

### Community 60 - "Community 60"
Cohesion: 0.50
Nodes (3): Emergency live crawl (docs site + forum) into the lexical store.          Produc, build_html_chunks(), pages: (url, raw_html). Used only by the emergency live-crawl fallback.

### Community 61 - "Community 61"
Cohesion: 0.50
Nodes (4): default, description, type, dimensionality

### Community 62 - "Community 62"
Cohesion: 0.50
Nodes (4): type, description, enum, type

### Community 66 - "Community 66"
Cohesion: 0.67
Nodes (3): description, type, name

### Community 67 - "Community 67"
Cohesion: 0.67
Nodes (3): description, type, from

### Community 68 - "Community 68"
Cohesion: 0.67
Nodes (3): solver, description, type

### Community 69 - "Community 69"
Cohesion: 0.67
Nodes (3): to, description, type

## Knowledge Gaps
- **335 isolated node(s):** `install.sh script`, `base_url`, `description`, `sources`, `exclude_patterns` (+330 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `KBFormatError` connect `Community 12` to `Community 2`, `Community 37`, `Community 11`, `Community 13`, `Community 14`, `Community 16`, `Community 18`, `Community 20`, `Community 24`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `KnowledgeBaseService` connect `Community 20` to `Community 0`, `Community 38`, `Community 10`, `Community 12`, `Community 14`, `Community 24`, `Community 25`, `Community 60`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `VectorKnowledgeBase` connect `Community 24` to `Community 0`, `Community 2`, `Community 38`, `Community 10`, `Community 12`, `Community 14`, `Community 25`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Platform` (e.g. with `CursorPlatform` and `ClaudeCodePlatform`) actually correct?**
  _`Platform` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Deduper` (e.g. with `Chunk` and `SchemaTests`) actually correct?**
  _`Deduper` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `KBFormatError` (e.g. with `KnowledgeBaseService` and `VectorKnowledgeBase`) actually correct?**
  _`KBFormatError` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `install.sh script`, `base_url`, `description` to the rest of the system?**
  _467 weakly-connected nodes found - possible documentation gaps or missing edges._