"""Build a vector KB category from one or more Markdown source trees.

Chunks every Markdown file under each configured source directory, embeds
chunks via an OpenAI-compatible API (OpenRouter by default, Blablador
later), and saves the result as a compressed NumPy archive (.npz) tagged
with a category, ready to be uploaded as a GitHub Release asset.

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

CHUNK_WORDS = 450
OVERLAP_WORDS = 50
MIN_CHUNK_WORDS = 30
BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
MODEL_DEFAULT = "openai/text-embedding-3-small"
BATCH_SIZE_DEFAULT = 64


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
    body = text[end + 4:].lstrip("\n")
    meta: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("\"'")
    return meta, body


def _strip_markdown(text: str) -> str:
    """Best-effort markdown → plain text."""
    text = re.sub(r"```[\s\S]*?```", " ", text)          # code blocks
    text = re.sub(r"`[^`]+`", " ", text)                  # inline code
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)          # images
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text) # links → text
    text = re.sub(r"#{1,6}\s+", "", text)                  # headings
    text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)  # bold/italic
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)  # bullets
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)  # numbered
    text = re.sub(r"\|[^\n]+\|", " ", text)               # tables
    return text


def _chunk(text: str) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + CHUNK_WORDS]
        if len(chunk_words) >= MIN_CHUNK_WORDS:
            chunks.append(" ".join(chunk_words))
        i += CHUNK_WORDS - OVERLAP_WORDS
    return chunks


def _file_to_url(filepath: Path, source_dir: Path, source: dict) -> str:
    url_base = source["url_base"].rstrip("/")
    rel = filepath.relative_to(source_dir)

    if source["url_mode"] == "website":
        meta, _ = _parse_frontmatter(filepath.read_text(encoding="utf-8", errors="replace"))
        permalink = meta.get("permalink", "")
        if permalink:
            return url_base + ("" if permalink.startswith("/") else "/") + permalink
        # content/docs/configuration-overview.md → /configuration-overview.html
        return f"{url_base}/{rel.stem}.html"

    # github mode: link straight to the file in the repo, on its configured branch
    return f"{url_base}/{rel.as_posix()}"


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
    parser.add_argument("--category", required=True, help="Category tag stored with every chunk")
    parser.add_argument(
        "--sources-json",
        required=True,
        help="JSON list of {label, path, url_mode, url_base, exclude_patterns}",
    )
    parser.add_argument("--api-key", required=True, help="OpenRouter / Blablador API key")
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT, help="OpenAI-compatible base URL")
    parser.add_argument("--model", default=MODEL_DEFAULT, help="Embedding model name")
    parser.add_argument("--output", default="kb-embeddings.npz", help="Output .npz path")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
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
        print(f"[{source['label']}] {len(md_files)} markdown files in {source_dir}", file=sys.stderr)

        for filepath in md_files:
            try:
                raw = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                print(f"  skip {filepath}: {exc}", file=sys.stderr)
                continue

            meta, body = _parse_frontmatter(raw)
            title = meta.get("title") or filepath.stem.replace("-", " ").title()
            url = _file_to_url(filepath, source_dir, source)
            plain = _strip_markdown(body)

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
