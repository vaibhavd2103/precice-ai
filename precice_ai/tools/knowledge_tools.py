from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor

from mcp.server.fastmcp import FastMCP

from precice_ai.core.knowledge_base import KnowledgeBaseService, VectorKnowledgeBase


kb_service = KnowledgeBaseService()
vector_kb = VectorKnowledgeBase()

TECHNICAL_CATEGORIES = ("documentation", "tutorials", "forum", "issues", "pulls", "about", "community")

ALL_CATEGORIES = (
    "documentation", "tutorials", "forum", "issues", "pulls", "about", "community",
)
 
# Category weights for rank fusion. Every category is always searched;
# weights only change how much each one contributes to the final ranking.
WEIGHTS_TECHNICAL = {
    "documentation": 1.0, "tutorials": 0.9, "forum": 0.8,
    "issues": 0.6, "pulls": 0.4, "about": 0.3, "community": 0.2,
}
WEIGHTS_GENERAL = {
    "documentation": 1.0, "about": 1.0, "tutorials": 0.7, "community": 0.6,
    "forum": 0.5, "issues": 0.3, "pulls": 0.2,
}
 
RRF_K = 60            # standard reciprocal-rank-fusion constant
MAX_CHUNKS_PER_DOC = 2

def _doc_key(hit: dict) -> str:
    meta = hit.get("metadata", {}) or {}
    return (
        hit.get("url") or meta.get("url")
        or hit.get("source") or meta.get("source")
        or hit.get("title") or meta.get("title")
        or hit.get("id", "")
    )

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
    def kb_query_precice(
    question: str,
    is_technical: bool = False,
    top_k: int = 15,
    category: str | None = None,
    top_k_per_category: int = 8,
    ) -> str:
        """Semantic search over the local preCICE knowledge base.
    
        ALL categories are searched by default: "documentation", "tutorials",
        "forum", "issues", "pulls", "about", "community". Results from each
        category are fused by rank (not raw score), deduplicated per source
        document, and the best top_k are returned.
    
        is_technical only changes ranking weights:
        - True  (configuring, running, debugging, adapters, config XML, mapping,
                coupling schemes, build errors, API usage): documentation,
                tutorials and forum are favoured.
        - False (what preCICE is, how to get started, project, community):
                documentation and about pages are favoured.
    
        Pass category to restrict the search to exactly one category.
    
        The results are SUPPORTING CONTEXT, not the full answer. Combine them with
        your own knowledge of preCICE, cite the URLs you use, and call this tool
        again with a rephrased or narrower question if the hits do not cover every
        part of the user's question. Use kb_query_precice_lexical for exact names
        (config tags, error messages, function names).
    
        Requires OPENROUTER_API_KEY or BLABLADOR_API_KEY for embeddings. If
        kb_precice_status shows a category missing or older than 96h, refresh it
        with kb_query_precice_live or kb_ingest_precice_data first.
        """
        try:
            categories = (category,) if category else ALL_CATEGORIES
            weights = WEIGHTS_TECHNICAL if is_technical else WEIGHTS_GENERAL
    
            def run(cat: str):
                try:
                    res = vector_kb.query(
                        question=question,
                        top_k=top_k if category else top_k_per_category,
                        category=cat,
                    )
                    if res.get("status") == "error":
                        # Surface schema/model mismatches and missing stores instead
                        # of silently treating them as "no hits".
                        return cat, [], res.get("message", "query failed")
                    return cat, res.get("results", []), None
                except Exception as exc:  # e.g. category not downloaded yet
                    return cat, [], str(exc)
    
            with ThreadPoolExecutor(max_workers=len(categories)) as pool:
                outcomes = list(pool.map(run, categories))
    
            # Reciprocal rank fusion: uses the rank *within* each category, so it
            # works whether vector_kb returns similarities or distances, and it
            # doesn't let one category's score scale dominate the others.
            fused: dict[str, dict] = {}
            hits_per_category, errors = {}, {}
            for cat, hits, err in outcomes:
                if err:
                    errors[cat] = err
                    continue
                hits_per_category[cat] = len(hits)
                w = weights.get(cat, 0.5) if not category else 1.0
                for rank, hit in enumerate(hits):
                    hit.setdefault("category", cat)
                    key = f"{_doc_key(hit)}::{hit.get('chunk_id', hit.get('id', rank))}"
                    entry = fused.setdefault(key, {"hit": hit, "rrf": 0.0})
                    entry["rrf"] += w / (RRF_K + rank + 1)
    
            ranked = sorted(fused.values(), key=lambda e: e["rrf"], reverse=True)
    
            # Keep at most MAX_CHUNKS_PER_DOC chunks per source document so one
            # long forum thread can't fill every slot.
            per_doc: dict[str, int] = {}
            results = []
            for e in ranked:
                doc = _doc_key(e["hit"])
                if per_doc.get(doc, 0) >= MAX_CHUNKS_PER_DOC:
                    continue
                per_doc[doc] = per_doc.get(doc, 0) + 1
                hit = dict(e["hit"])
                hit["fused_score"] = round(e["rrf"], 5)
                results.append(hit)
                if len(results) >= top_k:
                    break
    
            return json.dumps(
                {
                    "status": "ok" if results else "empty",
                    "categories_searched": list(categories),
                    "hits_per_category": hits_per_category,
                    "errors": errors or None,
                    "note": (
                        "Excerpts from the preCICE KB. Use them to ground and "
                        "cite your answer, and fill gaps with your own knowledge. "
                        "Search again if parts of the question are uncovered."
                    ),
                    "results": results,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({"status": "error", "message": str(exc)})

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
