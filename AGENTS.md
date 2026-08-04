# preCICE AI Agent Instructions

This project implements an MCP server for assisting users with local preCICE simulations.

## Safety Rules

- Do not run destructive shell commands.
- Do not delete project files.
- Always inspect `precice-config.xml` before modifying it.
- Always create a backup before applying config changes.
- Prefer MCP tools over raw shell commands.
- Explain simulation/configuration errors in simple language.

## preCICE knowledge base

Before answering any question about preCICE — what it is, how it works, configuration, errors, adapters, coupling schemes, or comparisons — first inspect the local KB state in `.precice-ai/kb_store` with `kb_precice_status()`.

Use this decision rule for the relevant KB category:

- If the category is present and `is_fresh` is true (less than 48 hours old), answer with `kb_query_precice`.
- If the category is missing, freshness is unknown, or it is 48 hours old or older, answer with `kb_query_precice_live` so the category is refreshed first and then queried.
- If a separate refresh step is needed, use `kb_ingest_precice_data` for that category before answering.
- Do not answer preCICE KB questions from model memory alone when a KB tool should be used.

---

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

## graphify (optional)

A knowledge graph is available at `graphify-out/` if graphify is installed.

Rules (only apply when `graphify-out/graph.json` exists):

- For codebase questions, first run `graphify query "<question>"`. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

If `graphify-out/graph.json` does not exist, skip all graphify commands and navigate the codebase directly.
