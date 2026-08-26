"""Shared embedding helper — the single source of truth for turning text into
vectors, used by both the KB build scripts (scripts/build_embeddings.py and
the two builders that reuse it) and the MCP server's query path
(precice_ai/core/knowledge_base.py).

EMBED_PROVIDER selects the backend (default "local"):
  - "local": sentence-transformers running on the caller's machine. No API
    key, no network call, no rate limits. EMBEDDING_MODEL (default
    BAAI/bge-m3) must stay an 8192-token model to match the chunker in
    scripts/build_embeddings.py — see the note next to MAX_CHUNK_BYTES there.
  - "api": an OpenAI-compatible endpoint (OpenRouter by default, Blablador
    via EMBEDDING_BASE_URL). Requires OPENROUTER_API_KEY or
    BLABLADOR_API_KEY. Kept as a fallback for accounts with credits.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

DEFAULT_PROVIDER = "local"
DEFAULT_MODEL = "BAAI/bge-m3"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def _provider() -> str:
    return os.environ.get("EMBED_PROVIDER", DEFAULT_PROVIDER)


def _resolve_model(model: str | None) -> str:
    return model or os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)


def _is_cached_locally(model_name: str) -> bool:
    """Best-effort check for an existing HF cache snapshot of `model_name`.

    Deliberately a plain filesystem check (the documented HF cache layout,
    ``<HF_HOME>/hub/models--org--name/snapshots/<rev>/``) rather than calling
    into huggingface_hub: importing that package bakes its HF_HUB_OFFLINE
    read into a module-level constant at import time, so the offline env var
    below has to be set *before* that first import to have any effect.
    """
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    snapshots_dir = hf_home / "hub" / f"models--{model_name.replace('/', '--')}" / "snapshots"
    if not snapshots_dir.is_dir():
        return False
    return any(rev_dir.is_dir() and any(rev_dir.iterdir()) for rev_dir in snapshots_dir.iterdir())


@lru_cache(maxsize=1)
def _local_model(model_name: str):
    # Already-downloaded models load straight from the local HF cache with
    # zero network calls. HF_HUB_OFFLINE has to be set before
    # sentence-transformers (and the huggingface_hub it pulls in) is first
    # imported in this process — it's read into a module-level constant at
    # import time, so setting it afterward (or only passing
    # local_files_only=True per-call) does not suppress every background
    # metadata lookup. Not cached yet (first run): leave it unset so the
    # model can download normally; it's cached from then on.
    cached = _is_cached_locally(model_name)
    if cached:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, local_files_only=cached)


def _embed_texts_local(texts: list[str], model_name: str) -> list[list[float]]:
    embedder = _local_model(model_name)
    vectors = embedder.encode(
        list(texts),
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [vec.tolist() for vec in vectors]


def _embed_texts_api(texts: list[str], model_name: str) -> list[list[float]]:
    from openai import OpenAI

    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("BLABLADOR_API_KEY")
    base_url = os.environ.get("EMBEDDING_BASE_URL", DEFAULT_BASE_URL)
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.embeddings.create(input=texts, model=model_name)
    ordered = sorted(resp.data, key=lambda x: x.index)
    return [d.embedding for d in ordered]


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Embed a batch of texts, preserving input order.

    Unit-length vectors in local mode, so downstream cosine similarity
    reduces to a plain dot product.
    """
    model_name = _resolve_model(model)
    if _provider() == "local":
        return _embed_texts_local(texts, model_name)
    return _embed_texts_api(texts, model_name)


def embed_query(text: str, model: str | None = None) -> list[float]:
    """Embed a single query string. bge-m3 needs no instruction prefix."""
    return embed_texts([text], model=model)[0]
