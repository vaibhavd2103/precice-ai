# Graph Report - precice-ai  (2026-05-24)

## Corpus Check
- 20 files · ~22,337 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 400 nodes · 428 edges · 26 communities (21 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b119693e`
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

## God Nodes (most connected - your core abstractions)
1. `What You Must Do When Invoked` - 16 edges
2. `/graphify` - 15 edges
3. `/graphify` - 14 edges
4. `What You Must Do When Invoked` - 14 edges
5. `KnowledgeBaseService` - 11 edges
6. `preCICE AI MCP Server` - 11 edges
7. `MCP Tools` - 10 edges
8. `preCICE-AI: Approaches, Alternatives & Best Strategy` - 10 edges
9. `get_project_path()` - 9 edges
10. `Part B - Semantic extraction (parallel subagents)` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Approach 1: MCP Server` --semantically_similar_to--> `MCP Server`  [INFERRED] [semantically similar]
  document.md → README.md
- `register_config_tools()` --calls--> `get_project_path()`  [EXTRACTED]
  tools/config_tools.py → core/paths.py
- `register_log_tools()` --calls--> `get_project_path()`  [EXTRACTED]
  tools/log_tools.py → core/paths.py
- `register_project_tools()` --calls--> `get_project_path()`  [EXTRACTED]
  tools/project_tools.py → core/paths.py
- `register_config_tools()` --calls--> `get_precice_config_path()`  [EXTRACTED]
  tools/config_tools.py → core/paths.py

## Hyperedges (group relationships)
- **New Project Tool Order** — tool_list_precice_projects, tool_inspect_project_structure, tool_find_precice_config, tool_inspect_precice_config, tool_summarize_precice_config, tool_check_precice_config [EXTRACTED 1.00]
- **Log Analysis Tool Order** — tool_list_project_logs, tool_read_latest_log, tool_analyze_precice_logs [EXTRACTED 1.00]
- **Graphify Navigation Command Set** — cmd_graphify_query, cmd_graphify_path, cmd_graphify_explain, file_graphify_out_graph_json [INFERRED 0.82]

## Communities (26 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (26): Run a command safely inside a given working directory.      The command is check, run_safe_command(), get_precice_config_path(), get_project_path(), Return the expected precice-config.xml path for a project., Return the absolute path of a project inside test-projects.      This also preve, get_allowed_commands(), is_command_safe() (+18 more)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (13): files, code, document, image, paper, video, graphifyignore_patterns, needs_graph (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.32
Nodes (8): Backup Required Before Config Changes, precice-config.xml, check_precice_config, find_precice_config, inspect_precice_config, inspect_project_structure, list_precice_projects, summarize_precice_config

### Community 3 - "Community 3"
Cohesion: 0.29
Nodes (7): Approach 2: LangChain/LangGraph, Approach 1: MCP Server, Approach 3: Raw Function Calling, Thesis Comparative Analysis, test-projects Directory, MCP Server, preCICE AI MCP Server

### Community 4 - "Community 4"
Cohesion: 0.38
Nodes (7): graphify explain, graphify path, graphify query, graphify update ., graphify Knowledge Graph Workflow, graphify-out/graph.json, graphify Skill

### Community 5 - "Community 5"
Cohesion: 0.33
Nodes (5): cSpell.ignoreWords, editor.fontFamily, editor.fontSize, editor.formatOnSave, workbench.colorTheme

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (36): code:bash (mkdir -p graphify-out), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash (LOCAL_PATH=$(graphify clone <github-url> [--branch <branch>]), code:bash (graphify export obsidian), code:bash (graphify export html  # auto-aggregates to community view if), code:bash (graphify export wiki), code:bash (graphify export neo4j), code:bash (graphify export neo4j --push bolt://localhost:7687 --user ne) (+28 more)

### Community 8 - "Community 8"
Cohesion: 0.67
Nodes (3): analyze_precice_logs, list_project_logs, read_latest_log

### Community 9 - "Community 9"
Cohesion: 0.67
Nodes (3): fastmcp Python Package, mcp Python Package, Pylint GitHub Actions Workflow

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (34): code:block1 (/graphify                                             # full), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c ") (+26 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (34): code:block1 (/graphify                                             # full), code:bash (if [ ! -f graphify-out/.graphify_python ]; then), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash (if [ ! -f graphify-out/.graphify_extract.json ]; then), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c ") (+26 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (32): Advantages, Advantages, Advantages, Advantages, Advantages, Approach A: Obsidian Vault + MCP Write-back, Approach B: Vector Database RAG Pipeline, Approach C: mem0 — Agent Memory Layer (+24 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (31): Advantages, Advantages, Advantages, Advantages, Approach 2: LangChain / LangGraph Agent with Custom Tools, Approach 3: Raw Function Calling (Anthropic / OpenAI API), Approach 4: Semantic Kernel (Microsoft), Approach 5: Fine-Tuned / Domain-Adapted LLM (+23 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (30): code:bash (mkdir -p graphify-out), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash (# Detect the correct Python interpreter (handles pipx, venv,), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c ") (+22 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (28): 1. Create and activate a Python environment, 2. Install dependencies, 3. Start the MCP server, `analyze_precice_logs(project_name: str) -> str`, code:text (.), code:bash (python3 -m venv .venv), code:bash (pip install mcp), code:bash (python3 server.py) (+20 more)

### Community 18 - "Community 18"
Cohesion: 0.20
Nodes (10): _bm25_like_score(), _dedupe_keep_order(), _extract_html_document(), KBDocument, KnowledgeBaseService, _normalize_url(), _now_iso(), _snippet_for_terms() (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (16): 1. Introduction & Problem Statement, 4.1 Tool Integration Approaches, 4.2 Knowledge & Context Management Approaches, 4. Comparison Matrices, 5. Best Approach & Recommended Architecture, 6. Conclusion, 7. References, A Comparative Analysis for Thesis Research (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (13): code:block10 (You are a graphify extraction subagent. Read the files liste), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:bash ($(cat .graphify_python) -c "), code:block8 (spawn_agent(agent_type="worker", message="Your task is to pe) (+5 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (13): code:bash ($(cat graphify-out/.graphify_python) -c "), code:block11 ([Agent tool call 1: files 1-15, subagent_type="general-purpo), code:bash (PROJECT_ROOT=$(cat graphify-out/.graphify_root)), code:block13 (You are a graphify extraction subagent. Read the files liste), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c "), code:bash ($(cat graphify-out/.graphify_python) -c ") (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.22
Nodes (9): Advantages, Approach 1: MCP Server (Model Context Protocol), Best Suited For, code:block1 (User: "Debug my heat-exchanger simulation"), code:python (from mcp.server.fastmcp import FastMCP), Disadvantages, How It Works, Implementation Snapshot (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): graphify, preCICE AI Agent Instructions, Safety Rules, Tool Usage Order

## Knowledge Gaps
- **219 isolated node(s):** `PreToolUse`, `cSpell.ignoreWords`, `editor.fontFamily`, `editor.fontSize`, `editor.formatOnSave` (+214 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `What You Must Do When Invoked` connect `Community 6` to `Community 21`, `Community 13`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `preCICE-AI: Approaches, Alternatives & Best Strategy` connect `Community 19` to `Community 14`, `Community 15`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `Part A — LLM Tool Integration Approaches` connect `Community 15` to `Community 19`, `Community 22`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **What connects `Return the absolute path of a project inside test-projects.      This also preve`, `Return the expected precice-config.xml path for a project.`, `Check whether a command is safe to execute.      Returns:         (True, "Allowe` to the rest of the system?**
  _233 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0907563025210084 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `Community 6` be split into smaller, more focused modules?**
  _Cohesion score 0.05555555555555555 - nodes in this community are weakly interconnected._