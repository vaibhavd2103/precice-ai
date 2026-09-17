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

SERVER_INSTRUCTIONS = f"""preCICE AI: tools for preCICE simulation projects — config inspection, log
analysis, precice-cli wrapping, and a semantic/lexical knowledge base of
preCICE docs, tutorials, forum posts, and GitHub issues/pulls.

{KB_DECISION_TREE}"""

GLOBAL_MARKDOWN_SNIPPET = f"""## preCICE AI MCP server

{KB_DECISION_TREE}"""
