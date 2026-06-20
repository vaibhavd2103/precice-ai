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
    ) -> str:
        """Download the latest pre-built vector KB embeddings from GitHub Releases.

        The embeddings are built from the preCICE documentation by a scheduled
        GitHub Action and published as a Release asset. Call this once (or
        whenever you want a fresher index) — subsequent queries will use the
        cached local file.

        Optionally pass github_token if the repository is private; otherwise
        the public release asset is downloaded without authentication.
        """
        token = github_token or os.environ.get("GITHUB_TOKEN")
        try:
            result = vector_kb.download_from_release(github_token=token)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice(question: str, top_k: int = 5) -> str:
        """Semantic search over the local preCICE vector KB.

        Embeds the question via the configured embedding API (set
        OPENROUTER_API_KEY and optionally EMBEDDING_BASE_URL / EMBEDDING_MODEL)
        and returns the top_k most similar document chunks.

        Run kb_ingest_precice_data first if the local index is not yet
        downloaded.
        """
        try:
            result = vector_kb.query(question=question, top_k=top_k)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_query_precice_live(question: str, top_k: int = 5) -> str:
        """Answer any question about preCICE using semantic search.

        Use this for ALL preCICE questions (configuration, adapters, coupling
        schemes, errors, etc.). Automatically downloads the vector KB on first
        use if it is not present locally, then runs cosine-similarity search.

        Requires OPENROUTER_API_KEY (or BLABLADOR_API_KEY) to be set so the
        question can be embedded at query time.
        """
        try:
            if not vector_kb.is_available():
                token = os.environ.get("GITHUB_TOKEN")
                dl = vector_kb.download_from_release(github_token=token)
                if dl.get("status") == "error":
                    return json.dumps(dl, indent=2)

            result = vector_kb.query(question=question, top_k=top_k)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)

    @mcp.tool()
    def kb_precice_status() -> str:
        """Show the status of the local vector KB (file size, download time, chunk count)."""
        try:
            result = vector_kb.status()
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)}, indent=2)
