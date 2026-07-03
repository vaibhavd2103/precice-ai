# preCICE AI Agent Instructions

This project implements an MCP server for assisting users with local preCICE simulations.

## Safety Rules

- Do not run destructive shell commands.
- Do not delete project files.
- Always inspect `precice-config.xml` before modifying it.
- Always call `backup_precice_config(project_name)` before applying config changes.
- Prefer MCP tools over raw shell commands.
- `run_command_in_project`, and the project-discovery/config/log tools, are scoped to `PRECICE_PROJECTS_DIR` (`./test-projects` by default). The `precice-cli` wrapper tools (`precice_version`, `precice_config_check/format/doc/visualize`, `precice_init`, `precice_profiling_*`) take an explicit `cwd` argument instead and are **not** restricted to that directory — pass a `cwd` under the current project on purpose, don't rely on sandboxing.
- Explain simulation/configuration errors in simple language.

## preCICE knowledge base

**Always** call `kb_query_precice_live` before answering any question about preCICE — what it is, how it works, configuration, errors, adapters, coupling schemes, or any comparison. Do not answer from training data alone. The tool auto-ingests on first use and caches results for 1 hour; subsequent calls in the same session are instant.

---

## Tool Usage Order

For a new project:

1. `list_precice_projects`
2. `inspect_project_structure`
3. `find_precice_config`
4. `inspect_precice_config`
5. `summarize_precice_config`
6. `precice_config_check(cwd, config_file)` — requires `precice-cli` on `PATH` (`pip install precice`); `cwd` is the project directory, not `project_name`

Before editing a config: `backup_precice_config(project_name)`, then `precice_config_format`/`precice_config_doc` as needed.

For logs:

1. `list_project_logs`
2. `read_latest_log`
3. `analyze_precice_logs`

For profiling data: `precice_profiling_analyze` → `precice_profiling_histogram` / `precice_profiling_trace` for a single run; `precice_profiling_merge` first if combining multiple runs; `precice_profiling_export` to save results.

## Current Scope

The assistant supports:

- project discovery
- config inspection, summarization, formatting, and backup
- config validation and doc lookup via `precice-cli`
- config scaffolding (`precice_init`) and visualization
- profiling analysis, tracing, histograms, merging, and export via `precice-cli`
- log reading and analysis
- semantic search over the preCICE knowledge base
- sandboxed command execution inside a project directory

## graphify (optional)

A knowledge graph is available at `graphify-out/` if graphify is installed.

Rules (only apply when `graphify-out/graph.json` exists):
- For codebase questions, first run `graphify query "<question>"`. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

If `graphify-out/graph.json` does not exist, skip all graphify commands and navigate the codebase directly.
