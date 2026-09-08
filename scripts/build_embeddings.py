"""Build a vector KB category from one or more Markdown source trees.

Chunks every Markdown file under each configured source directory, embeds
chunks via an OpenAI-compatible API (OpenRouter by default, Blablador via
--base-url), and saves the result as a compressed NumPy archive (.npz)
tagged with a category, ready to be uploaded as a GitHub Release asset.

Sources are passed as a JSON list, each entry:
    {"label": str, "path": str, "url_mode": "website" | "github",
     "url_base": str, "exclude_patterns": [str, ...]}

"website" mode builds precice.org URLs from frontmatter permalinks (or the
file's relative path). "github" mode builds GitHub blob URLs by joining
url_base with the file's path relative to its source directory.

Usage:
    python scripts/build_embeddings.py \
        --category documentation \
        --sources-json "$(python scripts/render_sources_json.py --config kb_sources.json --category documentation --checkout-dir precice/precice.github.io=precice-docs)" \
        --api-key $OPENROUTER_API_KEY \
        --output kb-embeddings-documentation.npz
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from openai import OpenAI, RateLimitError

from precice_ai.core.text_cleaning import strip_markdown

CHUNK_WORDS = 450
OVERLAP_WORDS = 50
MIN_CHUNK_WORDS = 30
# Keep a safety margin below the embedding model's 8192-token limit.  A byte
# cap is deliberately used instead of a model-specific tokenizer: this script
# also targets OpenAI-compatible providers with different tokenizers, and a
# UTF-8 token cannot contain fewer than one byte.
#
MAX_CHUNK_BYTES = 7_000
BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "openai/text-embedding-3-small"
# 64 chunks x ~450 words each pushed some batches to ~43.6k prompt tokens,
# which exceeds OpenRouter's per-request prompt-token cap for accounts
# without a funded/verified balance (observed ceiling ~21k tokens; see
# "Prompt tokens limit exceeded" / 402 errors). 16 keeps every batch at
# roughly half that ceiling with headroom for larger-than-average chunks,
# regardless of account tier. Override with --batch-size on a funded account
# that wants fewer, larger requests.
BATCH_SIZE_DEFAULT = 16


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (meta, body) stripping YAML frontmatter."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("\"'")
    return meta, body


def _chunk(text: str) -> list[str]:
    """Split text into bounded chunks suitable for embedding APIs.

    Word counts alone are not enough here: GitHub issues and pasted logs can
    contain very long words (URLs, stack traces, minified code), causing a
    nominally small chunk to exceed the provider's token limit.
    """
    words = text.split()
    chunks: list[str] = []
    i = 0
    while i < len(words):
        chunk_words: list[str] = []
        chunk_bytes = 0
        j = i

        while j < len(words) and len(chunk_words) < CHUNK_WORDS:
            word = words[j]
            word_bytes = len(word.encode("utf-8"))

            # A single oversized word must be split independently.  This is
            # uncommon, but is the exact case that a word-count-only chunker
            # cannot protect against.
            if word_bytes > MAX_CHUNK_BYTES:
                if chunk_words:
                    break
                chunks.extend(_split_utf8(word, MAX_CHUNK_BYTES))
                j += 1
                break

            added_bytes = word_bytes + (1 if chunk_words else 0)
            if chunk_words and chunk_bytes + added_bytes > MAX_CHUNK_BYTES:
                break
            chunk_words.append(word)
            chunk_bytes += added_bytes
            j += 1

        if chunk_words:
            chunks.append(" ".join(chunk_words))
            next_i = j
        else:
            next_i = i

        if next_i >= len(words):
            break
        # Retain the existing word overlap, while guaranteeing progress when
        # the byte limit (rather than CHUNK_WORDS) ended the chunk.
        i = max(i + 1, next_i - OVERLAP_WORDS)
    return chunks


def _split_utf8(text: str, max_bytes: int) -> list[str]:
    """Split a string at character boundaries without exceeding max_bytes."""
    pieces: list[str] = []
    current: list[str] = []
    current_bytes = 0
    for char in text:
        char_bytes = len(char.encode("utf-8"))
        if current and current_bytes + char_bytes > max_bytes:
            pieces.append("".join(current))
            current = []
            current_bytes = 0
        current.append(char)
        current_bytes += char_bytes
    if current:
        pieces.append("".join(current))
    return pieces


def _file_to_url(filepath: Path, source_dir: Path, source: dict) -> str:
    url_base = source["url_base"].rstrip("/")
    rel = filepath.relative_to(source_dir)

    if source["url_mode"] == "website":
        meta, _ = _parse_frontmatter(
            filepath.read_text(encoding="utf-8", errors="replace")
        )
        permalink = meta.get("permalink", "")
        if permalink:
            return url_base + ("" if permalink.startswith("/") else "/") + permalink
        # content/docs/configuration-overview.md → /configuration-overview.html
        return f"{url_base}/{rel.stem}.html"

    # github mode: link straight to the file in the repo, on its configured branch
    return f"{url_base}/{rel.as_posix()}"


# ---------------------------------------------------------------------------
# Lexical fragment (chunks-only, no embeddings) — shared by all three build
# scripts so the lexical KB and the vector KB are derived from the exact same
# chunk list, guaranteeing parity instead of relying on two separate crawls.
# ---------------------------------------------------------------------------


def write_chunk_fragment(chunks: list[dict], category: str, output_path: str) -> None:
    Path(output_path).write_text(
        json.dumps(
            {"category": category, "count": len(chunks), "chunks": chunks},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


def _embed_batch(
    client: OpenAI,
    texts: list[str],
    model: str,
    retry: int = 3,
) -> list[list[float]]:
    for attempt in range(retry):
        try:
            response = client.embeddings.create(input=texts, model=model)
            ordered = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in ordered]
        except RateLimitError:
            wait = 2 ** (attempt + 2)
            print(f"  rate limited, retrying in {wait}s…", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Embedding failed after {retry} retries")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _collect_md_files(source_dir: Path, exclude_patterns: list[str]) -> list[Path]:
    if not source_dir.exists():
        print(f"  warning: source dir not found: {source_dir}", file=sys.stderr)
        return []

    files = sorted(source_dir.rglob("*.md"))
    if exclude_patterns:

        def _is_excluded(p: Path) -> bool:
            rel = str(p.relative_to(source_dir))
            return any(pat in rel for pat in exclude_patterns)

        files = [f for f in files if not _is_excluded(f)]
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--category", required=True, help="Category tag stored with every chunk"
    )
    parser.add_argument(
        "--sources-json",
        required=True,
        help="JSON list of {label, path, url_mode, url_base, exclude_patterns}",
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="OpenRouter / Blablador API key",
    )
    parser.add_argument(
        "--base-url", default=BASE_URL_DEFAULT, help="OpenAI-compatible base URL"
    )
    parser.add_argument(
        "--model",
        default=MODEL_DEFAULT,
        help="Embedding model name",
    )
    parser.add_argument(
        "--output", default="kb-embeddings.npz", help="Output .npz path"
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
    parser.add_argument(
        "--lexical-output",
        default=None,
        help="If given, also write the chunk list (no embeddings) to this path for the lexical KB.",
    )
    args = parser.parse_args()

    sources = json.loads(args.sources_json)
    if not sources:
        sys.exit("--sources-json is empty")

    client = OpenAI(api_key=args.api_key, base_url=args.base_url)

    all_chunks: list[dict[str, str | int]] = []
    for source in sources:
        source_dir = Path(source["path"]).resolve()
        exclude_patterns = source.get("exclude_patterns", [])
        md_files = _collect_md_files(source_dir, exclude_patterns)
        print(
            f"[{source['label']}] {len(md_files)} markdown files in {source_dir}",
            file=sys.stderr,
        )

        for filepath in md_files:
            try:
                raw = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                print(f"  skip {filepath}: {exc}", file=sys.stderr)
                continue

            meta, body = _parse_frontmatter(raw)
            title = meta.get("title") or filepath.stem.replace("-", " ").title()
            url = _file_to_url(filepath, source_dir, source)
            plain = strip_markdown(body)

            for i, chunk_text in enumerate(_chunk(plain)):
                all_chunks.append(
                    {
                        "title": title,
                        "url": url,
                        "source": source["label"],
                        "category": args.category,
                        "chunk_index": i,
                        "text": chunk_text,
                    }
                )

    if not all_chunks:
        sys.exit("No chunks produced — check --sources-json paths.")

    if args.lexical_output:
        write_chunk_fragment(all_chunks, args.category, args.lexical_output)

    print(f"Total chunks to embed: {len(all_chunks)}", file=sys.stderr)

    texts = [c["text"] for c in all_chunks]  # type: ignore[index]
    all_embeddings: list[list[float]] = []
    total_batches = (len(texts) + args.batch_size - 1) // args.batch_size

    for batch_idx in range(total_batches):
        start = batch_idx * args.batch_size
        batch = texts[start : start + args.batch_size]
        print(
            f"  batch {batch_idx + 1}/{total_batches} ({len(batch)} chunks)",
            file=sys.stderr,
        )
        embeddings = _embed_batch(client, batch, args.model)
        all_embeddings.extend(embeddings)

    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    chunks_json = json.dumps(all_chunks, ensure_ascii=False)

    np.savez_compressed(
        args.output,
        embeddings=embeddings_array,
        chunks=np.array(chunks_json),  # 0-d object array, read back with .item()
    )

    size_mb = Path(args.output).stat().st_size / 1_048_576
    print(
        f"Saved {len(all_chunks)} chunks, embeddings shape {embeddings_array.shape} "
        f"→ {args.output} ({size_mb:.1f} MB)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
