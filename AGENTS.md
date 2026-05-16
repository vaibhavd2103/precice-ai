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

## Current Scope

<!-- The assistant supports:

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
