# Graph Report - /home/vaibhav/precice-ai-workspace/precice-ai  (2026-05-24)

## Corpus Check
- Corpus is ~21,036 words - fits in a single context window. You may not need a graph.

## Summary
- 74 nodes · 85 edges · 12 communities (9 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_get_precice_config_path()|get_precice_config_path()]]
- [[_COMMUNITY_.graphify_detect.json|.graphify_detect.json]]
- [[_COMMUNITY_Backup Required Before Config Ch|Backup Required Before Config Ch]]
- [[_COMMUNITY_Approach 2 LangChainLangGraph|Approach 2: LangChain/LangGraph]]
- [[_COMMUNITY_graphify explain|graphify explain]]
- [[_COMMUNITY_cSpell.ignoreWords|cSpell.ignoreWords]]
- [[_COMMUNITY_command_runner.py|command_runner.py]]
- [[_COMMUNITY_hooks|hooks]]
- [[_COMMUNITY_analyze_precice_logs|analyze_precice_logs]]
- [[_COMMUNITY_fastmcp Python Package|fastmcp Python Package]]
- [[_COMMUNITY_Prefer MCP Tools Over Raw Shell|Prefer MCP Tools Over Raw Shell ]]

## God Nodes (most connected - your core abstractions)
1. `get_project_path()` - 8 edges
2. `files` - 6 edges
3. `run_safe_command()` - 6 edges
4. `register_config_tools()` - 6 edges
5. `register_project_tools()` - 5 edges
6. `register_all_tools()` - 5 edges
7. `graphify Knowledge Graph Workflow` - 5 edges
8. `get_precice_config_path()` - 4 edges
9. `register_log_tools()` - 4 edges
10. `precice-config.xml` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Approach 1: MCP Server` --semantically_similar_to--> `MCP Server`  [INFERRED] [semantically similar]
  document.md → README.md
- `register_config_tools()` --calls--> `run_safe_command()`  [EXTRACTED]
  tools/config_tools.py → core/command_runner.py
- `register_project_tools()` --calls--> `run_safe_command()`  [EXTRACTED]
  tools/project_tools.py → core/command_runner.py
- `register_config_tools()` --calls--> `get_project_path()`  [EXTRACTED]
  tools/config_tools.py → core/paths.py
- `register_log_tools()` --calls--> `get_project_path()`  [EXTRACTED]
  tools/log_tools.py → core/paths.py

## Hyperedges (group relationships)
- **New Project Tool Order** — tool_list_precice_projects, tool_inspect_project_structure, tool_find_precice_config, tool_inspect_precice_config, tool_summarize_precice_config, tool_check_precice_config [EXTRACTED 1.00]
- **Log Analysis Tool Order** — tool_list_project_logs, tool_read_latest_log, tool_analyze_precice_logs [EXTRACTED 1.00]
- **Graphify Navigation Command Set** — cmd_graphify_query, cmd_graphify_path, cmd_graphify_explain, file_graphify_out_graph_json [INFERRED 0.82]

## Communities (12 total, 3 thin omitted)

### Community 0 - "get_precice_config_path()"
Cohesion: 0.27
Nodes (6): get_precice_config_path(), get_project_path(), register_config_tools(), register_all_tools(), register_log_tools(), register_project_tools()

### Community 1 - ".graphify_detect.json"
Cohesion: 0.14
Nodes (13): files, code, document, image, paper, video, graphifyignore_patterns, needs_graph (+5 more)

### Community 2 - "Backup Required Before Config Ch"
Cohesion: 0.32
Nodes (8): Backup Required Before Config Changes, precice-config.xml, check_precice_config, find_precice_config, inspect_precice_config, inspect_project_structure, list_precice_projects, summarize_precice_config

### Community 3 - "Approach 2: LangChain/LangGraph"
Cohesion: 0.29
Nodes (7): Approach 2: LangChain/LangGraph, Approach 1: MCP Server, Approach 3: Raw Function Calling, Thesis Comparative Analysis, test-projects Directory, MCP Server, preCICE AI MCP Server

### Community 4 - "graphify explain"
Cohesion: 0.38
Nodes (7): graphify explain, graphify path, graphify query, graphify update ., graphify Knowledge Graph Workflow, graphify-out/graph.json, graphify Skill

### Community 5 - "cSpell.ignoreWords"
Cohesion: 0.33
Nodes (5): cSpell.ignoreWords, editor.fontFamily, editor.fontSize, editor.formatOnSave, workbench.colorTheme

### Community 8 - "analyze_precice_logs"
Cohesion: 0.67
Nodes (3): analyze_precice_logs, list_project_logs, read_latest_log

### Community 9 - "fastmcp Python Package"
Cohesion: 0.67
Nodes (3): fastmcp Python Package, mcp Python Package, Pylint GitHub Actions Workflow

## Knowledge Gaps
- **31 isolated node(s):** `code`, `document`, `paper`, `image`, `video` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_safe_command()` connect `command_runner.py` to `get_precice_config_path()`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `code`, `document`, `paper` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.graphify_detect.json` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._