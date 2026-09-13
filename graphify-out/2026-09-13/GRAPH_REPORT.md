# Graph Report - precice-ai  (2026-07-05)

## Corpus Check
- 40 files · ~30,477 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 757 nodes · 1181 edges · 67 communities (51 shown, 16 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f8b69a03`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Agent Architecture & Safety Rules|Agent Architecture & Safety Rules]]
- [[_COMMUNITY_KB Retrieval & Comparison Tools|KB Retrieval & Comparison Tools]]
- [[_COMMUNITY_Graphify Skill (.agents copy)|Graphify Skill (.agents copy)]]
- [[_COMMUNITY_MCP Platform Installers|MCP Platform Installers]]
- [[_COMMUNITY_README Setup Instructions|README Setup Instructions]]
- [[_COMMUNITY_Graphify Skill Codeblocks|Graphify Skill Codeblocks]]
- [[_COMMUNITY_Thesis LLM Architecture Approaches|Thesis: LLM Architecture Approaches]]
- [[_COMMUNITY_Graphify Skill (.claude copy)|Graphify Skill (.claude copy)]]
- [[_COMMUNITY_KB & Config Policy Rules|KB & Config Policy Rules]]
- [[_COMMUNITY_KB Sources Config|KB Sources Config]]
- [[_COMMUNITY_Thesis Document Sections|Thesis Document Sections]]
- [[_COMMUNITY_README Usage Walkthrough|README Usage Walkthrough]]
- [[_COMMUNITY_Graphify Detect Output|Graphify Detect Output]]
- [[_COMMUNITY_Embeddings Build Script|Embeddings Build Script]]
- [[_COMMUNITY_CLI Entry & Server Bootstrap|CLI Entry & Server Bootstrap]]
- [[_COMMUNITY_Claude Settings & Graphify Commands|Claude Settings & Graphify Commands]]
- [[_COMMUNITY_Command Safety Core|Command Safety Core]]
- [[_COMMUNITY_README Graphify Setup|README Graphify Setup]]
- [[_COMMUNITY_AGENTS.md Policy Sections|AGENTS.md Policy Sections]]
- [[_COMMUNITY_VSCode Settings|VSCode Settings]]
- [[_COMMUNITY_CLAUDE.md Graphify Section|CLAUDE.md Graphify Section]]
- [[_COMMUNITY_Claude Hooks Config|Claude Hooks Config]]
- [[_COMMUNITY_Claude Local Permissions|Claude Local Permissions]]
- [[_COMMUNITY_Log Analysis Tools|Log Analysis Tools]]
- [[_COMMUNITY_Dependencies & CI|Dependencies & CI]]
- [[_COMMUNITY_Claude Graphify Cross-ref|Claude Graphify Cross-ref]]
- [[_COMMUNITY_Core Package Init|Core Package Init]]
- [[_COMMUNITY_Thesis Fine-tuned LLM Approach|Thesis: Fine-tuned LLM Approach]]
- [[_COMMUNITY_MCP Tool Preference|MCP Tool Preference]]
- [[_COMMUNITY_Platform Base Rationale|Platform Base Rationale]]
- [[_COMMUNITY_Platform Base Rationale|Platform Base Rationale]]
- [[_COMMUNITY_CLI App Entrypoint|CLI App Entrypoint]]
- [[_COMMUNITY_Knowledge Tools KB Service|Knowledge Tools KB Service]]
- [[_COMMUNITY_README Overview|README Overview]]
- [[_COMMUNITY_README Env Vars|README Env Vars]]
- [[_COMMUNITY_Thesis Reference preCICE Paper|Thesis Reference: preCICE Paper]]
- [[_COMMUNITY_Thesis Reference Survey Paper|Thesis Reference: Survey Paper]]
- [[_COMMUNITY_Pylint CI Job|Pylint CI Job]]
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

## God Nodes (most connected - your core abstractions)
1. `Platform` - 24 edges
2. `run_safe_command` - 23 edges
3. `get_project_path` - 22 edges
4. `KnowledgeBaseService.query` - 22 edges
5. `preCICE AI MCP Server` - 21 edges
6. `VectorKnowledgeBase.query` - 21 edges
7. `code:bash ($(cat .graphify_python) -c ")` - 18 edges
8. `What You Must Do When Invoked` - 16 edges
9. `graphify path` - 16 edges
10. `README MCP Tools Reference` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Approach B: Vector Database RAG Pipeline` --semantically_similar_to--> `vector_kb (VectorKnowledgeBase instance)`  [INFERRED] [semantically similar]
  document.md → precice_ai/tools/knowledge_tools.py
- `Approach 1: MCP Server` --semantically_similar_to--> `MCP Server`  [INFERRED] [semantically similar]
  document.md → README.md
- `Approach D: GraphRAG / Knowledge Graph` --semantically_similar_to--> `graphify Skill`  [INFERRED] [semantically similar]
  document.md → .agents/skills/graphify/SKILL.md
- `PreToolUse Grep-to-Graphify Hook` --rationale_for--> `graphify Skill`  [INFERRED]
  .claude/settings.json → .agents/skills/graphify/SKILL.md
- `AGENTS.md Safety Rules` --rationale_for--> `run_command_in_project`  [INFERRED]
  AGENTS.md → precice_ai/tools/project_tools.py

## Hyperedges (group relationships)
- **Multi-platform MCP server installation pattern** — base_platform, cursor_cursorplatform, claude_code_claudecodeplatform, claude_desktop_claudedesktopplatform, windsurf_windsurfplatform, codex_codexplatform, generic_genericplatform, platforms_registry [EXTRACTED 1.00]
- **Dual lexical/vector KB build-and-query pipeline** — build_embeddings_main, knowledge_base_vectorknowledgebase, knowledge_base_knowledgebaseservice, compare_kb_search_main, kb_sources_config [INFERRED 0.85]
- **Safe shell command execution flow** — command_runner_run_safe_command, safety_is_command_safe, safety_allowed_command_prefixes, safety_blocked_patterns [EXTRACTED 1.00]
- **Config Tool Registration** — tools_config_tools_register_config_tools, tools_config_tools_inspect_precice_config, tools_config_tools_summarize_precice_config, tools_config_tools_backup_precice_config [EXTRACTED 1.00]
- **preCICE CLI Availability Precondition** — tools_cli_tools_check_precice_cli, tools_cli_tools_precice_version, tools_cli_tools_precice_config_check, tools_cli_tools_precice_config_visualize, tools_cli_tools_precice_config_format, tools_cli_tools_precice_config_doc, tools_cli_tools_precice_init, tools_cli_tools_precice_profiling_analyze, tools_cli_tools_precice_profiling_trace, tools_cli_tools_precice_profiling_export, tools_cli_tools_precice_profiling_histogram, tools_cli_tools_precice_profiling_merge [EXTRACTED 1.00]
- **Vector KB Build & Query Pipeline** — workflows_kb_ingest_build_kb_job, tools_knowledge_tools_kb_ingest_precice_data, tools_knowledge_tools_kb_query_precice_live, tools_knowledge_tools_vector_kb, readme_vector_kb_workflow [INFERRED 0.85]

## Communities (67 total, 16 thin omitted)

### Community 0 - "Agent Architecture & Safety Rules"
Cohesion: 0.06
Nodes (68): AGENTS.md Safety Rules, AGENTS.md Tool Usage Order, Approach 2: LangChain/LangGraph, Approach 1: MCP Server, Approach 3: Raw Function Calling, run_safe_command, Thesis Comparative Analysis, Run a command safely inside a given working directory. (+60 more)

### Community 1 - "KB Retrieval & Comparison Tools"
Cohesion: 0.07
Nodes (47): compare_kb_search main(), _print_results, _run_lexical, _run_vector, _asset_name(), _bm25_like_score(), _dedupe_keep_order(), _extract_html_document() (+39 more)

### Community 2 - "Graphify Skill (.agents copy)"
Cohesion: 0.10
Nodes (26): code:bash (mkdir -p graphify-out), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (# Detect the correct Python interpreter (handles pipx, venv,), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c ") (+18 more)

### Community 3 - "MCP Platform Installers"
Cohesion: 0.08
Nodes (34): ABC, Platform (abstract base class), Platform.mcp_entry, Platform._merge_json_config, ClaudeCodePlatform, ClaudeDesktopPlatform, _config_path, list_platforms() (+26 more)

### Community 4 - "README Setup Instructions"
Cohesion: 0.14
Nodes (18): 1. Create and activate a Python environment, 2. Install dependencies, 3. Start the MCP server, Check which platforms are detected, code:bash (precice-ai setup codex), code:bash (precice-ai setup generic), code:bash (precice-ai setup claude-code), code:bash (precice-ai setup claude-code --projects-dir /path/to/my/prec) (+10 more)

### Community 5 - "Graphify Skill Codeblocks"
Cohesion: 0.13
Nodes (15): code:bash (mkdir -p graphify-out), code:bash (graphify export obsidian), code:bash (graphify export html  # auto-aggregates to community view if), code:bash (graphify export neo4j), code:bash (graphify export neo4j --push bolt://localhost:7687 --user ne), code:bash (graphify benchmark), code:bash (# Detect the correct Python interpreter (handles uv tool, pi), code:bash (GRAPHIFY_WHISPER_MODEL=base  # or whatever --whisper-model t) (+7 more)

### Community 6 - "Thesis: LLM Architecture Approaches"
Cohesion: 0.23
Nodes (22): Approach E: Fine-Tuned Embeddings, Approach D: GraphRAG / Knowledge Graph, Approach 2: LangChain/LangGraph Agent, Approach C: mem0 Agent Memory Layer, Approach A: Obsidian Vault + MCP Write-back, Approach 3: Raw Function Calling (Anthropic/OpenAI API), Recommended Stack: MCP + ChromaDB RAG + Obsidian + mem0, From Local to Global: A Graph RAG Approach - Edge et al. (2024) (+14 more)

### Community 7 - "Graphify Skill (.claude copy)"
Cohesion: 0.06
Nodes (32): code:block1 (/graphify                                             # full), code:bash (if [ ! -f graphify-out/.graphify_python ]; then), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c ") (+24 more)

### Community 8 - "KB & Config Policy Rules"
Cohesion: 0.09
Nodes (24): preCICE Knowledge Base Query Policy (AGENTS.md), preCICE Knowledge Base Query Policy (root CLAUDE.md), Backup Required Before Config Changes, precice-config.xml, `analyze_precice_logs(project_name: str) -> str`, `inspect_precice_config(project_name: str) -> str`, `kb_ingest_precice_data(docs_pages_limit=20, forum_topics_limit=20, timeout_seconds=20) -> str`, `kb_precice_status() -> str` (+16 more)

### Community 9 - "KB Sources Config"
Cohesion: 0.05
Nodes (38): description, exclude_patterns, sources, base_url, categories, about, community, documentation (+30 more)

### Community 10 - "Thesis Document Sections"
Cohesion: 0.12
Nodes (16): 1. Introduction & Problem Statement, 4.1 Tool Integration Approaches, 4.2 Knowledge & Context Management Approaches, 4. Comparison Matrices, 5. Best Approach & Recommended Architecture, 6. Conclusion, 7. References, A Comparative Analysis for Thesis Research (+8 more)

### Community 11 - "README Usage Walkthrough"
Cohesion: 0.13
Nodes (15): 1. Download the knowledge base, 2. Discover your projects, 3. Inspect a project, 4. Validate the config, 5. Run safe commands, 6. Read and analyze logs, 7. Ask the knowledge base, code:block16 (kb_ingest_precice_data()) (+7 more)

### Community 12 - "Graphify Detect Output"
Cohesion: 0.14
Nodes (13): files, code, document, image, paper, video, graphifyignore_patterns, needs_graph (+5 more)

### Community 13 - "Embeddings Build Script"
Cohesion: 0.14
Nodes (25): _chunk, _collect_md_files, _embed_batch, _file_to_url, _load_config, build_embeddings main(), _parse_frontmatter, _strip_markdown (+17 more)

### Community 14 - "CLI Entry & Server Bootstrap"
Cohesion: 0.10
Nodes (16): Register the precice-ai MCP server with a supported AI coding platform., Start the preCICE AI MCP server (stdio transport)., server(), setup(), is_command_safe(), Check whether a command is safe to execute.      Returns:         (True, "Allowe, Return the list of allowed command prefixes., main() (+8 more)

### Community 15 - "Claude Settings & Graphify Commands"
Cohesion: 0.20
Nodes (11): .claude/settings.local.json Permission Allowlist, PreToolUse Grep-to-Graphify Hook, graphify Optional Codebase Graph Rule (AGENTS.md), graphify Optional Codebase Graph Rule (root CLAUDE.md), graphify explain, graphify query, graphify update ., graphify Knowledge Graph Workflow (+3 more)

### Community 16 - "Command Safety Core"
Cohesion: 0.16
Nodes (17): code:block1 (/graphify                                             # full), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (python3 -m graphify.watch INPUT_PATH --debounce 3), code:bash (graphify hook install    # install), code:bash (graphify claude install), code:bash (graphify claude uninstall  # remove the section), For --cluster-only (+9 more)

### Community 17 - "README Graphify Setup"
Cohesion: 0.18
Nodes (13): Codebase knowledge graph (optional), Codebase knowledge graph via the graphify skill (optional), code:block28 (detect files (code / docs / papers / images / video)), code:bash (# Ask a question about the codebase — BFS traversal for broa), code:bash (graphify update .        # incremental — re-extracts only ch), Configure your AI assistant to use the graph, How Claude Code picks it up automatically, How it's built (+5 more)

### Community 18 - "AGENTS.md Policy Sections"
Cohesion: 0.25
Nodes (7): Current Scope, graphify, graphify (optional), preCICE AI Agent Instructions, preCICE knowledge base, Safety Rules, Tool Usage Order

### Community 19 - "VSCode Settings"
Cohesion: 0.33
Nodes (5): cSpell.ignoreWords, editor.fontFamily, editor.fontSize, editor.formatOnSave, workbench.colorTheme

### Community 20 - "CLAUDE.md Graphify Section"
Cohesion: 0.50
Nodes (3): graphify, graphify (optional), preCICE knowledge base

### Community 23 - "Log Analysis Tools"
Cohesion: 0.67
Nodes (3): analyze_precice_logs, list_project_logs, read_latest_log

### Community 24 - "Dependencies & CI"
Cohesion: 0.67
Nodes (3): fastmcp Python Package, mcp Python Package, Pylint GitHub Actions Workflow

### Community 41 - "Community 41"
Cohesion: 0.17
Nodes (16): test-projects Directory, code:bash (git clone https://github.com/vaibhavd2103/precice-ai), code:block27 (precice_ai/), code:bash (# Via the CLI), code:bash (# Via the CLI), Features, Installation, License (+8 more)

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (13): category_signature(), forum_signature(), git_sha_for_path(), is_stale(), load_state(), main(), _parse_checkout_dirs(), Track per-category ingestion state so the KB workflow only rebuilds categories w (+5 more)

### Community 43 - "Community 43"
Cohesion: 0.17
Nodes (12): code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -m graphify save-result --question "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -m graphify save-result --question "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c ") (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (11): Advantages, Approach C: mem0 — Agent Memory Layer, Best Suited For, code:python (from mem0 import Memory), code:python (from mcp.server.fastmcp import FastMCP), code:python (import chromadb), Disadvantages, Implementation Snapshot (+3 more)

### Community 45 - "Community 45"
Cohesion: 0.22
Nodes (10): code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), For /graphify add, Part A - Structural extraction for code files, Part C - Merge AST + semantic into final extraction (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (10): Advantages, Advantages, Approach A: Obsidian Vault + MCP Write-back, Approach D: GraphRAG / Knowledge Graph, Best Suited For, Best Suited For, Disadvantages, Disadvantages (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (9): Advantages, Approach 2: LangChain / LangGraph Agent with Custom Tools, Best Suited For, code:block3 (User query), code:python (from langchain.tools import tool), Disadvantages, How It Works, Implementation Snapshot (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.25
Nodes (9): Advantages, Approach 5: Fine-Tuned / Domain-Adapted LLM, Best Suited For, code:block1 (User: "Debug my heat-exchanger simulation"), code:block7 (Data Collection:), Disadvantages, How It Works, How It Works (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.25
Nodes (8): code:block10 (You are a graphify extraction subagent. Read the files liste), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:block8 (spawn_agent(agent_type="worker", message="Your task is to pe), code:block9 (result = wait_agent(handle); close_agent(handle)   # repeat ), Part B - Semantic extraction (parallel subagents)

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (8): code:bash ($(cat graphify-out/.graphify_python) -c "), code:block11 ([Agent tool call 1: files 1-15, subagent_type="general-purpo), code:bash (PROJECT_ROOT=$(cat graphify-out/.graphify_root)), code:block13 (You are a graphify extraction subagent. Read the files liste), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), Part B - Semantic extraction (parallel subagents)

### Community 51 - "Community 51"
Cohesion: 0.29
Nodes (7): Advantages, Approach 3: Raw Function Calling (Anthropic / OpenAI API), Best Suited For, code:python (import anthropic), Disadvantages, How It Works, Overview

### Community 52 - "Community 52"
Cohesion: 0.29
Nodes (7): Advantages, Approach 4: Semantic Kernel (Microsoft), Best Suited For, code:python (import semantic_kernel as sk), Disadvantages, Implementation Snapshot, Overview

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (7): Advantages, Approach B: Vector Database RAG Pipeline, Best Suited For, code:block8 (Indexing (one-time):), Disadvantages, How It Works, Overview

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (7): code:json ({), code:json ({), code:block14 (~/.precice-ai/kb_store/kb-embeddings-about.npz), code:bash (# Via terminal), Controlling what gets indexed, Environment variables, Knowledge base storage

### Community 55 - "Community 55"
Cohesion: 0.29
Nodes (7): Command execution, Configuration, Knowledge base, Logs, MCP tools reference, precice-cli wrappers, Project discovery

### Community 56 - "Community 56"
Cohesion: 0.33
Nodes (6): code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), For --update (incremental re-extraction)

### Community 57 - "Community 57"
Cohesion: 0.33
Nodes (6): code:bash (graphify export wiki), code:bash (graphify export svg), code:bash (graphify export graphml), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 6b - Wiki (only if --wiki flag)

### Community 58 - "Community 58"
Cohesion: 0.40
Nodes (5): code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), Part A - Structural extraction for code files, Part C - Merge AST + semantic into final extraction, Step 3 - Extract entities and relationships

### Community 59 - "Community 59"
Cohesion: 0.40
Nodes (5): Advantages, Approach E: Fine-Tuned Embeddings, Best Suited For, Disadvantages, Overview

### Community 60 - "Community 60"
Cohesion: 0.50
Nodes (4): code:bash (LOCAL_PATH=$(graphify clone <github-url> [--branch <branch>]), code:bash (# Clone each repo, run the full pipeline on each, then merge), code:bash (graphify extract ./core/     # → ./core/graphify-out/graph.j), Step 0 - Clone GitHub repo(s) (only if a GitHub URL was given)

### Community 61 - "Community 61"
Cohesion: 0.67
Nodes (3): main(), Render the --sources-json argument for build_embeddings.py from kb_sources.json., render()

### Community 62 - "Community 62"
Cohesion: 0.67
Nodes (3): code:bash (python3 -m graphify.serve graphify-out/graph.json), code:json ({), Step 7d - MCP server (only if --mcp flag)

### Community 63 - "Community 63"
Cohesion: 0.67
Nodes (3): code:block4 (Corpus: X files · ~Y words), code:block7 (Corpus: X files · ~Y words), Step 2 - Detect files

### Community 64 - "Community 64"
Cohesion: 0.67
Nodes (3): code:bash (python3 -m graphify.serve graphify-out/graph.json), code:json ({), Step 7d - MCP server (only if --mcp flag)

### Community 65 - "Community 65"
Cohesion: 0.67
Nodes (3): code:bash ($(cat graphify-out/.graphify_python) -c "), code:block31 (Graph complete. Outputs in PATH_TO_DIR/graphify-out/), Step 9 - Save manifest, update cost tracker, clean up, and report

## Ambiguous Edges - Review These
- `KnowledgeBaseService.query` → `is_command_safe`  [AMBIGUOUS]
  precice_ai/core/knowledge_base.py · relation: conceptually_related_to
- `precice_config_check` → `AGENTS.md Tool Usage Order`  [AMBIGUOUS]
  AGENTS.md · relation: references
- `precice_config_check` → `README MCP Tools Reference`  [AMBIGUOUS]
  README.md · relation: references
- `precice_config_visualize` → `README MCP Tools Reference`  [AMBIGUOUS]
  README.md · relation: references

## Knowledge Gaps
- **279 isolated node(s):** `categories`, `base_url`, `description`, `sources`, `exclude_patterns` (+274 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `KnowledgeBaseService.query` and `is_command_safe`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `precice_config_check` and `AGENTS.md Tool Usage Order`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `precice_config_check` and `README MCP Tools Reference`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `precice_config_visualize` and `README MCP Tools Reference`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `preCICE AI MCP Server` connect `Community 41` to `Agent Architecture & Safety Rules`, `KB Retrieval & Comparison Tools`, `README Setup Instructions`, `KB & Config Policy Rules`, `README Usage Walkthrough`, `README Graphify Setup`, `Community 54`, `Community 55`?**
  _High betweenness centrality (0.284) - this node is a cross-community bridge._
- **Why does `graphify Skill` connect `Claude Settings & Graphify Commands` to `Command Safety Core`, `Thesis: LLM Architecture Approaches`?**
  _High betweenness centrality (0.282) - this node is a cross-community bridge._
- **Why does `Approach D: GraphRAG / Knowledge Graph` connect `Thesis: LLM Architecture Approaches` to `Claude Settings & Graphify Commands`?**
  _High betweenness centrality (0.282) - this node is a cross-community bridge._