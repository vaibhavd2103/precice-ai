# Graph Report - .  (2026-07-03)

## Corpus Check
- 39 files · ~27,657 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 551 nodes · 819 edges · 41 communities (26 shown, 15 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.76)
- Token cost: 0 input · 208,225 output

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

## God Nodes (most connected - your core abstractions)
1. `run_safe_command` - 23 edges
2. `get_project_path` - 22 edges
3. `KnowledgeBaseService.query` - 22 edges
4. `preCICE AI MCP Server` - 21 edges
5. `VectorKnowledgeBase.query` - 21 edges
6. `code:bash ($(cat .graphify_python) -c ")` - 18 edges
7. `Platform` - 16 edges
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

## Communities (41 total, 15 thin omitted)

### Community 0 - "Agent Architecture & Safety Rules"
Cohesion: 0.06
Nodes (62): AGENTS.md Safety Rules, AGENTS.md Tool Usage Order, Approach 2: LangChain/LangGraph, Approach 1: MCP Server, Approach 3: Raw Function Calling, run_safe_command, Thesis Comparative Analysis, Run a command safely inside a given working directory. (+54 more)

### Community 1 - "KB Retrieval & Comparison Tools"
Cohesion: 0.08
Nodes (34): compare_kb_search main(), _print_results, _run_lexical, _run_vector, _dedupe_keep_order(), _get_kb_dir(), KBDocument, _normalize_url() (+26 more)

### Community 2 - "Graphify Skill (.agents copy)"
Cohesion: 0.06
Nodes (44): code:block1 (/graphify                                             # full), code:bash (mkdir -p graphify-out), code:bash (# Detect the correct Python interpreter (handles pipx, venv,), code:bash (python3 -m graphify.serve graphify-out/graph.json), code:json ({), code:bash ($(cat .graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat .graphify_python) -m graphify save-result --question ") (+36 more)

### Community 3 - "MCP Platform Installers"
Cohesion: 0.08
Nodes (23): ABC, Platform (abstract base class), Platform.mcp_entry, Platform._merge_json_config, ClaudeCodePlatform, ClaudeDesktopPlatform, _config_path, list_platforms() (+15 more)

### Community 4 - "README Setup Instructions"
Cohesion: 0.05
Nodes (43): test-projects Directory, 1. Create and activate a Python environment, 2. Install dependencies, 3. Start the MCP server, Check which platforms are detected, Claude Code, code:bash (git clone https://github.com/vaibhavd2103/precice-ai), code:bash (precice-ai setup codex) (+35 more)

### Community 5 - "Graphify Skill Codeblocks"
Cohesion: 0.06
Nodes (40): code:block10 (You are a graphify extraction subagent. Read the files liste), code:block27 (Graph complete. Outputs in PATH_TO_DIR/graphify-out/), code:block4 (Corpus: X files · ~Y words), code:block11 ([Agent tool call 1: files 1-15, subagent_type="general-purpo), code:bash (PROJECT_ROOT=$(cat graphify-out/.graphify_root)), code:bash (mkdir -p graphify-out), code:bash (LOCAL_PATH=$(graphify clone <github-url> [--branch <branch>]), code:bash (graphify export obsidian) (+32 more)

### Community 6 - "Thesis: LLM Architecture Approaches"
Cohesion: 0.13
Nodes (35): Approach E: Fine-Tuned Embeddings, Approach D: GraphRAG / Knowledge Graph, Approach 2: LangChain/LangGraph Agent, Approach C: mem0 Agent Memory Layer, Approach A: Obsidian Vault + MCP Write-back, Approach 3: Raw Function Calling (Anthropic/OpenAI API), Recommended Stack: MCP + ChromaDB RAG + Obsidian + mem0, From Local to Global: A Graph RAG Approach - Edge et al. (2024) (+27 more)

### Community 7 - "Graphify Skill (.claude copy)"
Cohesion: 0.08
Nodes (25): code:block1 (/graphify                                             # full), code:bash (if [ ! -f graphify-out/.graphify_python ]; then), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash (graphify cluster-only .), code:bash (graphify query "QUESTION"), code:bash ($(cat graphify-out/.graphify_python) -m graphify save-result), code:bash (graphify path "NODE_A" "NODE_B"), code:bash (graphify explain "NODE_NAME") (+17 more)

### Community 8 - "KB & Config Policy Rules"
Cohesion: 0.09
Nodes (24): preCICE Knowledge Base Query Policy (AGENTS.md), preCICE Knowledge Base Query Policy (root CLAUDE.md), Backup Required Before Config Changes, precice-config.xml, `analyze_precice_logs(project_name: str) -> str`, `inspect_precice_config(project_name: str) -> str`, `kb_ingest_precice_data(docs_pages_limit=20, forum_topics_limit=20, timeout_seconds=20) -> str`, `kb_precice_status() -> str` (+16 more)

### Community 9 - "KB Sources Config"
Cohesion: 0.11
Nodes (17): base_url, docs_dir, exclude_patterns, include_subfolders, notes, about, community, docs/adapters (+9 more)

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
Cohesion: 0.30
Nodes (13): _chunk, _collect_md_files, _embed_batch, _file_to_url, _load_config, build_embeddings main(), _parse_frontmatter, _strip_markdown (+5 more)

### Community 14 - "CLI Entry & Server Bootstrap"
Cohesion: 0.18
Nodes (9): Register the precice-ai MCP server with a supported AI coding platform., Start the preCICE AI MCP server (stdio transport)., server(), setup(), main(), mcp FastMCP instance, Convenience entry point for running the server from the repo root.  For producti, server.py main() entry point (+1 more)

### Community 15 - "Claude Settings & Graphify Commands"
Cohesion: 0.20
Nodes (11): .claude/settings.local.json Permission Allowlist, PreToolUse Grep-to-Graphify Hook, graphify Optional Codebase Graph Rule (AGENTS.md), graphify Optional Codebase Graph Rule (root CLAUDE.md), graphify explain, graphify query, graphify update ., graphify Knowledge Graph Workflow (+3 more)

### Community 16 - "Command Safety Core"
Cohesion: 0.24
Nodes (6): Check whether a command is safe to execute.      Returns:         (True, "Allowe, Return the list of allowed command prefixes., ALLOWED_COMMAND_PREFIXES, BLOCKED_PATTERNS, get_allowed_commands, is_command_safe

### Community 17 - "README Graphify Setup"
Cohesion: 0.22
Nodes (9): Codebase knowledge graph (optional), code:bash (pip install graphify-cli   # or follow the graphify README f), code:bash (# Ask a question about the codebase), code:bash (graphify update .), code:block31 (When graphify-out/graph.json exists, run `graphify query "<q), Configure your AI assistant to use the graph, Install graphify, Keep the graph current after code changes (+1 more)

### Community 18 - "AGENTS.md Policy Sections"
Cohesion: 0.29
Nodes (6): graphify, graphify (optional), preCICE AI Agent Instructions, preCICE knowledge base, Safety Rules, Tool Usage Order

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
- **184 isolated node(s):** `repo`, `sparse_checkout_paths`, `docs_dir`, `include_subfolders`, `exclude_patterns` (+179 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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
- **Why does `preCICE AI MCP Server` connect `README Setup Instructions` to `KB & Config Policy Rules`, `README Graphify Setup`, `README Usage Walkthrough`, `KB Retrieval & Comparison Tools`?**
  _High betweenness centrality (0.305) - this node is a cross-community bridge._
- **Why does `graphify Skill` connect `Claude Settings & Graphify Commands` to `Graphify Skill (.agents copy)`, `Thesis: LLM Architecture Approaches`?**
  _High betweenness centrality (0.284) - this node is a cross-community bridge._
- **Why does `Approach D: GraphRAG / Knowledge Graph` connect `Thesis: LLM Architecture Approaches` to `Claude Settings & Graphify Commands`?**
  _High betweenness centrality (0.283) - this node is a cross-community bridge._