"""Reading/writing the two KB stores and the ingestion manifest.

On-disk layout (all chunk records are the canonical schema, full text):

  kb-embeddings-<category>.npz
      embeddings  float32 (N, D)
      chunk_ids   str array (N,)   — same order as embeddings
      chunks      0-d str: JSON list of N chunk records
      meta        0-d str: JSON {schema_version, model, dim, count, category, built_at}
  kb-lexical.json  (local name: knowledge_base.json)
      {schema_version, updated_at, categories, count, chunks: [...]}
  kb-manifest.json
      {schema_version, built_at, model, dim, normalized, categories: {cat: stats}, totals}

The lexical file is always derived from the npz files, so both stores contain
exactly the same chunk records and chunk_ids by construction.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from precice_ai.kb.schema import CATEGORIES, REINGEST_HINT, SCHEMA_VERSION, Chunk, KBFormatError

MANIFEST_NAME = "kb-manifest.json"
LEXICAL_RELEASE_NAME = "kb-lexical.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def npz_name(category: str) -> str:
    return f"kb-embeddings-{category}.npz"


def write_local_meta(path: Path, signature: str = "local-rebuild") -> None:
    """Sidecar in the format release sync uses, so a fresh local rebuild is
    trusted for the normal freshness window instead of being re-downloaded."""
    path.parent.joinpath(f"{path.name}.meta.json").write_text(
        json.dumps({"remote_signature": signature, "checked_at": now_iso()}), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def embed_chunks(
    chunks: list[Chunk],
    *,
    api_key: str,
    base_url: str,
    model: str,
    batch_size: int = 16,
    max_batch_chars: int = 60_000,
):
    """Embed `chunk.embed_text` (title > section + text) for every chunk."""
    import numpy as np
    from openai import OpenAI, RateLimitError

    client = OpenAI(api_key=api_key, base_url=base_url)
    texts = [c.embed_text for c in chunks]
    batches: list[list[str]] = []
    cur: list[str] = []
    cur_chars = 0
    for t in texts:
        if cur and (len(cur) >= batch_size or cur_chars + len(t) > max_batch_chars):
            batches.append(cur)
            cur, cur_chars = [], 0
        cur.append(t)
        cur_chars += len(t)
    if cur:
        batches.append(cur)

    vectors: list[list[float]] = []
    for i, batch in enumerate(batches, 1):
        print(f"  batch {i}/{len(batches)} ({len(batch)} chunks)", file=sys.stderr)
        for attempt in range(4):
            try:
                resp = client.embeddings.create(input=batch, model=model)
                vectors.extend(d.embedding for d in sorted(resp.data, key=lambda x: x.index))
                break
            except RateLimitError:
                wait = 2 ** (attempt + 2)
                print(f"  rate limited, retrying in {wait}s…", file=sys.stderr)
                time.sleep(wait)
        else:
            raise RuntimeError("Embedding failed after 4 retries")
    return np.array(vectors, dtype=np.float32)


# ---------------------------------------------------------------------------
# Vector store (npz)
# ---------------------------------------------------------------------------


def write_vector_store(path: Path, category: str, chunks: list[Chunk], embeddings, model: str) -> None:
    import numpy as np

    if len(chunks) != embeddings.shape[0]:
        raise ValueError(f"{category}: {len(chunks)} chunks but {embeddings.shape[0]} embeddings")
    meta = {
        "schema_version": SCHEMA_VERSION,
        "model": model,
        "dim": int(embeddings.shape[1]),
        "count": len(chunks),
        "category": category,
        "built_at": now_iso(),
    }
    np.savez_compressed(
        path,
        embeddings=embeddings.astype(np.float32),
        chunk_ids=np.array([c.chunk_id for c in chunks]),
        chunks=np.array(json.dumps([c.to_dict() for c in chunks], ensure_ascii=False)),
        meta=np.array(json.dumps(meta)),
    )


def read_npz_meta(path: Path) -> dict | None:
    """The `meta` record of an npz, or None for a legacy (pre-schema) file."""
    import numpy as np

    with np.load(path, allow_pickle=False) as data:
        if "meta" not in data.files:
            return None
        return json.loads(data["meta"].item())


def check_npz_compat(path: Path, expected_model: str | None = None) -> str | None:
    """None if the npz is usable, otherwise a human-readable reason (with the
    re-ingest instruction) why it is not."""
    try:
        meta = read_npz_meta(path)
    except Exception as exc:
        return f"{path.name} could not be read ({exc}). {REINGEST_HINT}"
    if meta is None:
        return f"{path.name} uses the legacy pre-schema format. {REINGEST_HINT}"
    if meta.get("schema_version") != SCHEMA_VERSION:
        return (
            f"{path.name} has schema_version {meta.get('schema_version')} but this version of "
            f"precice-ai needs {SCHEMA_VERSION}. {REINGEST_HINT}"
        )
    if expected_model and meta.get("model") != expected_model:
        return (
            f"{path.name} was embedded with {meta.get('model')!r} but EMBEDDING_MODEL is "
            f"{expected_model!r}; the vectors are not comparable. Set EMBEDDING_MODEL to "
            f"{meta.get('model')!r} or re-ingest with the new model. {REINGEST_HINT}"
        )
    return None


def read_vector_store(path: Path, expected_model: str | None = None):
    """Return (embeddings float32 (N, D), chunk dicts, meta). Raises KBFormatError
    on schema/model mismatch."""
    import numpy as np

    problem = check_npz_compat(path, expected_model)
    if problem:
        raise KBFormatError(problem)
    with np.load(path, allow_pickle=False) as data:
        embeddings = data["embeddings"].astype(np.float32)
        chunks = json.loads(data["chunks"].item())
        ids = [str(i) for i in data["chunk_ids"]]
        meta = json.loads(data["meta"].item())
    if len(chunks) != embeddings.shape[0] or ids != [c["chunk_id"] for c in chunks]:
        raise KBFormatError(f"{path.name} is internally inconsistent (ids/embeddings mismatch). {REINGEST_HINT}")
    return embeddings, chunks, meta


# ---------------------------------------------------------------------------
# Lexical store + manifest
# ---------------------------------------------------------------------------


def category_stats(chunks: list[dict]) -> dict:
    docs: dict[str, int] = defaultdict(int)
    lens: list[int] = []
    for c in chunks:
        docs[c["doc_id"]] += 1
        lens.append(c["char_len"])
    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "avg_chars": round(statistics.fmean(lens), 1) if lens else 0,
        "median_chars": round(statistics.median(lens), 1) if lens else 0,
    }


def write_lexical_store(path: Path, chunks: list[dict], categories: list[str]) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "categories": categories,
        "count": len(chunks),
        "chunks": chunks,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def read_lexical_store(path: Path) -> dict:
    """Load the lexical store; raises KBFormatError on schema mismatch."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        found = payload.get("schema_version") if isinstance(payload, dict) else None
        raise KBFormatError(
            f"{path.name} has schema_version {found!r} (legacy or incompatible); "
            f"this version of precice-ai needs {SCHEMA_VERSION}. {REINGEST_HINT}"
        )
    return payload


def finalize_store(
    directory: Path,
    *,
    lexical_name: str = LEXICAL_RELEASE_NAME,
    excluded_stats: dict | None = None,
) -> dict:
    """Derive the lexical store and the manifest from the npz files in
    `directory` (every category that is present). Returns the manifest."""
    all_chunks: list[dict] = []
    per_category: dict[str, dict] = {}
    models: set[str] = set()
    dims: set[int] = set()
    for category in CATEGORIES:
        path = directory / npz_name(category)
        if not path.exists():
            continue
        problem = check_npz_compat(path)
        if problem:
            raise KBFormatError(problem)
        _, chunks, meta = read_vector_store(path)
        models.add(meta["model"])
        dims.add(meta["dim"])
        per_category[category] = {**category_stats(chunks), "built_at": meta["built_at"]}
        all_chunks.extend(chunks)
    if len(models) > 1 or len(dims) > 1:
        raise KBFormatError(
            f"Categories were embedded with different models/dimensions ({sorted(models)}, {sorted(dims)}). "
            "Rebuild all categories with the same EMBEDDING_MODEL."
        )
    if not per_category:
        raise KBFormatError(f"No {npz_name('<category>')} files found in {directory}")

    write_lexical_store(directory / lexical_name, all_chunks, list(per_category))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "built_at": now_iso(),
        "model": next(iter(models)),
        "dim": next(iter(dims)),
        "categories": per_category,
        "totals": {
            "documents": sum(c["documents"] for c in per_category.values()),
            "chunks": len(all_chunks),
        },
    }
    if excluded_stats:
        manifest["ingestion"] = excluded_stats
    (directory / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def read_manifest(directory: Path) -> dict | None:
    path = directory / MANIFEST_NAME
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None
