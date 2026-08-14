"""Build the 'forum' vector KB category from precice.discourse.group topics.

Unlike the Markdown-based categories, forum content is fetched live over
HTTP rather than checked out from git, so it has its own build script but
produces the same chunk schema (title, url, source, category, chunk_index,
text) and .npz layout as build_embeddings.py, so VectorKnowledgeBase can
merge it with the other categories transparently.

Usage:
    python scripts/build_forum_embeddings.py \
        --forum-url https://precice.discourse.group \
        --api-key $OPENROUTER_API_KEY \
        --output kb-embeddings-forum.npz
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
import numpy as np
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_embeddings import BASE_URL_DEFAULT, BATCH_SIZE_DEFAULT, MODEL_DEFAULT, _chunk, _embed_batch
from precice_ai.core.discourse_api import fetch_discourse_topic_documents

USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"

def _fetch_topics(forum_url: str, topics_limit: int | None, timeout_seconds: int) -> list[dict]:
    with httpx.Client(
        timeout=timeout_seconds,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        return [
            {"title": topic.title, "url": topic.url, "text": topic.text}
            for topic in fetch_discourse_topic_documents(
                client,
                forum_url,
                topics_limit=topics_limit,
            )
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forum-url", default="https://precice.discourse.group")
    parser.add_argument(
        "--topics-limit",
        type=int,
        default=0,
        help="Maximum number of topics to fetch; use 0 to fetch every visible topic.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--output", default="kb-embeddings-forum.npz")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
    args = parser.parse_args()

    topics_limit = args.topics_limit if args.topics_limit > 0 else None
    topics = _fetch_topics(args.forum_url, topics_limit, args.timeout_seconds)
    print(f"Fetched {len(topics)} forum topics", file=sys.stderr)

    all_chunks: list[dict[str, str | int]] = []
    for topic in topics:
        for i, chunk_text in enumerate(_chunk(topic["text"])):
            all_chunks.append(
                {
                    "title": topic["title"],
                    "url": topic["url"],
                    "source": "precice-forum",
                    "category": "forum",
                    "chunk_index": i,
                    "text": chunk_text,
                }
            )

    if not all_chunks:
        sys.exit("No forum chunks produced.")

    print(f"Total chunks to embed: {len(all_chunks)}", file=sys.stderr)

    client = OpenAI(api_key=args.api_key, base_url=args.base_url)
    texts = [c["text"] for c in all_chunks]  # type: ignore[index]
    all_embeddings: list[list[float]] = []
    total_batches = (len(texts) + args.batch_size - 1) // args.batch_size

    for batch_idx in range(total_batches):
        start = batch_idx * args.batch_size
        batch = texts[start : start + args.batch_size]
        print(f"  batch {batch_idx + 1}/{total_batches} ({len(batch)} chunks)", file=sys.stderr)
        all_embeddings.extend(_embed_batch(client, batch, args.model))

    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    chunks_json = json.dumps(all_chunks, ensure_ascii=False)

    np.savez_compressed(
        args.output,
        embeddings=embeddings_array,
        chunks=np.array(chunks_json),
    )

    size_mb = Path(args.output).stat().st_size / 1_048_576
    print(
        f"Saved {len(all_chunks)} chunks, embeddings shape {embeddings_array.shape} "
        f"→ {args.output} ({size_mb:.1f} MB)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
