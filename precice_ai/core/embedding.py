"""Shared embedding helper — the single source of truth for turning text into
vectors, used by both the KB build scripts (scripts/build_embeddings.py and
the two builders that reuse it) and the MCP server's query path
(precice_ai/core/knowledge_base.py).

Embedding always goes through an OpenAI-compatible embeddings API. Provide
one of:

  - OPENROUTER_API_KEY  → https://openrouter.ai/api/v1 (default),
                          model "openai/text-embedding-3-small"
  - BLABLADOR_API_KEY   → https://helmholtz-blablador.fz-juelich.de:8000/v1

Override the endpoint with EMBEDDING_BASE_URL and the model with
EMBEDDING_MODEL. Build and query must use the *same* model or the stored
vectors and the query vector won't be comparable.
"""

from __future__ import annotations

import os

DEFAULT_MODEL = "openai/text-embedding-3-small"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
BLABLADOR_BASE_URL = "https://helmholtz-blablador.fz-juelich.de:8000/v1"


class EmbeddingConfigError(RuntimeError):
    """Raised when no embedding API key is configured."""


def _resolve_api_key() -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("BLABLADOR_API_KEY")
    if not api_key:
        raise EmbeddingConfigError(
            "No embedding API key set. Export OPENROUTER_API_KEY (OpenRouter) or "
            "BLABLADOR_API_KEY (Blablador) — semantic KB queries embed the question "
            "through an OpenAI-compatible embeddings API and cannot run without a key."
        )
    return api_key


def _resolve_base_url() -> str:
    explicit = os.environ.get("EMBEDDING_BASE_URL")
    if explicit:
        return explicit
    # Convenience: if only a Blablador key is present, point at Blablador.
    if os.environ.get("BLABLADOR_API_KEY") and not os.environ.get("OPENROUTER_API_KEY"):
        return BLABLADOR_BASE_URL
    return OPENROUTER_BASE_URL


def _resolve_model(model: str | None) -> str:
    return model or os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)


def _client():
    from openai import OpenAI

    return OpenAI(api_key=_resolve_api_key(), base_url=_resolve_base_url())


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Embed a batch of texts, preserving input order."""
    model_name = _resolve_model(model)
    client = _client()
    resp = client.embeddings.create(input=list(texts), model=model_name)
    ordered = sorted(resp.data, key=lambda x: x.index)
    return [d.embedding for d in ordered]


def embed_query(text: str, model: str | None = None) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text], model=model)[0]
