# preCICE AI Agent Instructions

This project implements an MCP server for assisting users with local preCICE simulations.

## Safety Rules

- Do not run destructive shell commands.
- Do not delete project files.
- Always inspect `precice-config.xml` before modifying it.
- Always create a backup before applying config changes.
- Prefer MCP tools over raw shell commands.
- Only run commands inside `test-projects/`.
- Explain simulation/configuration errors in simple language.

## Tool Usage Order

For a new project:

1. `list_precice_projects`
2. `inspect_project_structure`
3. `find_precice_config`
4. `inspect_precice_config`
5. `summarize_precice_config`
6. `check_precice_config`

For logs:

1. `list_project_logs`
2. `read_latest_log`
3. `analyze_precice_logs`

<!-- ## Current Scope

The assistant supports:

- project discovery
- config inspection
- config checking
- config backup
- basic log reading
- basic log analysis

Future scope:

- simulation execution
- result analysis
- documentation search
- Discourse/forum search -->

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
