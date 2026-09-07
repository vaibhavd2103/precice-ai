from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from precice_ai.core.knowledge_base import KnowledgeBaseService, VectorKnowledgeBase


kb_service = KnowledgeBaseService()
vector_kb = VectorKnowledgeBase()


def register_knowledge_tools(mcp: FastMCP) -> None:
    """Register knowledge-base tools for preCICE docs/forum retrieval."""

    @mcp.tool()
    def kb_ingest_precice_data(
        github_token: str | None = None,
        category: str | None = None,
    ) -> str:
        """Sync the local KB (vector + lexical) from GitHub Releases.

        The vector embeddings are built per category (about, community,
        documentation, tutorials, forum, issues, pulls) and the lexical
        (keyword) index is built from the same per-category chunk extraction
        (guaranteeing coverage parity between the two), both by a scheduled
        GitHub Action (kb-ingest.yml) that runs every 4 days and always
        rebuilds and republishes every category, regardless of whether the
        underlying content changed. This tool treats that release as the
        source of truth: each asset is trusted locally for up to 96h after
        the last check (no network call within that window), then always
        re-downloaded (replacing the old local copy) once the window
        elapses — so the KB is never more than ~96h stale. Call this once
        (or whenever you want to force a freshness check) — subsequent
        queries use the cached local files.

        Pass category to refresh just one vector category (e.g. "issues")
        instead of all of them; the lexical snapshot is always checked too.
        Agents should use this refresh path when kb_precice_status shows the
        relevant category is missing or at least 96h old.
        Optionally pass github_token if the repository is private; otherwise
        the public release assets are downloaded without authentication.
        """
        token = github_token or os.environ.get("GITHUB_TOKEN")
        try:
            vector_result = vector_kb.download_from_release(github_token=token, category=category)
            lexical_result = kb_service.sync_from_release(github_token=token)
            return json.dumps(
                {
                    "status": vector_result.get("status"),
                    "vector": vector_result,
                    "lexical": lexical_result,
                },
                indent=2,
            )
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice(question: str, top_k: int = 5, category: str | None = None) -> str:
        """Semantic search over the local preCICE vector KB.

        Embeds the question locally with sentence-transformers by default
        (EMBED_PROVIDER=local, EMBEDDING_MODEL=BAAI/bge-m3 — no API key, no
        network call) and returns the top_k most similar document chunks.
        Set EMBED_PROVIDER=api (with OPENROUTER_API_KEY/BLABLADOR_API_KEY and
        optionally EMBEDDING_BASE_URL / EMBEDDING_MODEL) to embed via an
        OpenAI-compatible API instead.

        Pass category ("about", "community", "documentation", "tutorials",
        "forum", "issues", or "pulls") to restrict the search to that category
        only; omit it to search across every downloaded category.

        Preferred when kb_precice_status shows the relevant local category is
        present and fresh (checked less than 96h ago). If the category is
        missing or stale, refresh it first with kb_query_precice_live or
        kb_ingest_precice_data.
        """
        try:
            result = vector_kb.query(question=question, top_k=top_k, category=category)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice_live(question: str, top_k: int = 5, category: str | None = None) -> str:
        """Answer any question about preCICE using semantic search.

        Use this when the relevant local KB category is missing, its
        freshness is unknown, or kb_precice_status shows it is at least 96h
        old. This refreshes the requested category from the published vector
        KB release first, then runs cosine-similarity search so the answer
        comes from updated local data. It is not the default for categories
        that are already present and fresh.

        Pass category ("about", "community", "documentation", "tutorials",
        "forum", "issues", or "pulls") to restrict the search to that category
        only.
        
        If answer not found in "issues" or "pulls" categories, then search in "forum" because it
        contains the most up-to-date information about preCICE, including discussions, bug reports, and user experiences.
        """
        try:
            token = os.environ.get("GITHUB_TOKEN")
            dl = vector_kb.download_from_release(github_token=token, category=category)
            if dl.get("status") == "error":
                return json.dumps(dl, indent=2)

            result = vector_kb.query(question=question, top_k=top_k, category=category)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice_lexical(question: str, top_k: int = 5, category: str | None = None) -> str:
        """Keyword (BM25-style) search over the local preCICE lexical KB.

        Useful as a fast, no-embedding-API-key-required complement to the
        semantic search tools, or for exact-term lookups (error strings,
        config keys). The lexical KB is chunk-based and covers the same
        categories as the vector KB (about, community, documentation,
        tutorials, forum, issues, pulls) — pass category to restrict the
        search to one of them, omit it to search everything. The published
        lexical KB release (kb-lexical.json) is the source of truth: the
        local copy is trusted for up to 96h after the last check, then
        always re-downloaded fresh once that window elapses, falling back
        to a live docs/forum crawl only if the release is unreachable and
        there's no local cache at all.
        """
        try:
            result = kb_service.query_with_optional_live_refresh(
                question=question, top_k=top_k, category=category
            )
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_precice_status() -> str:
        """Show local KB status and freshness for agent tool selection.

        Use this before choosing between kb_query_precice and
        kb_query_precice_live. The result includes per-category presence,
        checked_at, age_hours, and is_fresh (<96h) for the vector KB plus
        the lexical KB status.
        """
        try:
            result = {
                "vector": vector_kb.status(),
                "lexical": kb_service.kb_status(),
            }
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)
