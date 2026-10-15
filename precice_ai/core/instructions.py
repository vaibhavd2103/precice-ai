"""Steering text shared between the MCP server's own `instructions` field
(precice_ai/server.py) and the optional global CLAUDE.md/AGENTS.md snippet
written by `precice-ai bootstrap/setup --write-global-instructions` (see
precice_ai/cli/platforms). Kept in one place so both stay in sync.
"""

from __future__ import annotations

KB_DECISION_TREE = """For every preCICE question or task — what preCICE is, how it works,
configuration, errors, adapters, coupling schemes, or any comparison — use
these tools before answering from training data, even outside a preCICE
project directory:

1. Call kb_precice_status() first.
2. Query a fresh category with kb_query_precice(...); if the category is
   missing or stale, use kb_query_precice_live(...) instead.
3. For project configuration, use the discovery and inspection tools before
   making changes. Inspect precice-config.xml and back it up before
   modifying it.
4. For logs, list logs, read the latest one, then analyze it.

Do not answer from training data alone when a KB tool should be used."""

RUN_DECISION_TREE = """Whenever the user asks to check, set up or run a preCICE project or
tutorial, do this before starting anything:

1. Find the project directory (list_precice_projects(path) with the user's
   workspace if only a name was given).
2. Call precice_project_preflight(project_path). It checks the preCICE
   installation, validates precice-config.xml and checks the solver
   dependencies of every participant case.
3. If "ready" is false, do not run: report the problems, fix them with the
   user's consent, and call precice_project_preflight again.
4. Only when "ready" is true, start one case per participant concurrently
   using the returned run_command values, then read and analyze the logs."""

SERVER_INSTRUCTIONS = f"""preCICE AI: tools for preCICE simulation projects — config inspection, log
analysis, precice-cli wrapping, and a semantic/lexical knowledge base of
preCICE docs, tutorials, forum posts, and GitHub issues/pulls.

{KB_DECISION_TREE}

{RUN_DECISION_TREE}"""

GLOBAL_MARKDOWN_SNIPPET = f"""## preCICE AI MCP server

{KB_DECISION_TREE}

{RUN_DECISION_TREE}"""
