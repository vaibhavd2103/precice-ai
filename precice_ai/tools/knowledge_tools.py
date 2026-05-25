from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from precice_ai.core.knowledge_base import KnowledgeBaseService


kb_service = KnowledgeBaseService()


def register_knowledge_tools(mcp: FastMCP) -> None:
    """Register knowledge-base tools for preCICE docs/forum retrieval."""

    @mcp.tool()
    def kb_ingest_precice_data(
        docs_pages_limit: int = 20,
        forum_topics_limit: int = 20,
        timeout_seconds: int = 20,
    ) -> str:
        """Ingest preCICE docs + forum data into local KB storage."""
        try:
            result = kb_service.ingest_precice_sources(
                docs_pages_limit=docs_pages_limit,
                forum_topics_limit=forum_topics_limit,
                timeout_seconds=timeout_seconds,
            )
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice(question: str, top_k: int = 5) -> str:
        """Query local ingested KB for preCICE-related answers/snippets."""
        try:
            result = kb_service.query(question=question, top_k=top_k)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice_live(question: str, top_k: int = 5, max_age_hours: int = 24) -> str:
        """Query KB and auto-refresh from docs/forum if cache is stale."""
        try:
            result = kb_service.query_with_optional_live_refresh(
                question=question,
                top_k=top_k,
                refresh_if_older_than_hours=max_age_hours,
            )
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_precice_status() -> str:
        """Show KB freshness and document count."""
        try:
            result = kb_service.kb_status()
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)
