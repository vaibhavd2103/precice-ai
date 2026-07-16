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
import re
import sys
from pathlib import Path

import httpx
import numpy as np
from openai import OpenAI

from build_embeddings import BASE_URL_DEFAULT, BATCH_SIZE_DEFAULT, MODEL_DEFAULT, _chunk, _embed_batch

USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value).replace("\n", " ").strip()


def _fetch_topics(forum_url: str, topics_limit: int, timeout_seconds: int) -> list[dict]:
    with httpx.Client(
        timeout=timeout_seconds,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        response = client.get(forum_url.rstrip("/") + "/latest.json")
        response.raise_for_status()
        topics = response.json().get("topic_list", {}).get("topics", [])[:topics_limit]

        docs: list[dict] = []
        for topic in topics:
            slug = topic.get("slug")
            topic_id = topic.get("id")
            title = topic.get("title", "")
            if not slug or not topic_id:
                continue

            topic_url = f"{forum_url.rstrip('/')}/t/{slug}/{topic_id}.json"
            try:
                topic_response = client.get(topic_url)
                topic_response.raise_for_status()
                posts = topic_response.json().get("post_stream", {}).get("posts", [])
                merged = "\n\n".join(
                    _strip_html(post.get("cooked", "")) for post in posts if isinstance(post, dict)
                )
                if merged.strip():
                    docs.append(
                        {
                            "title": title,
                            "url": f"{forum_url.rstrip('/')}/t/{slug}/{topic_id}",
                            "text": merged,
                        }
                    )
            except Exception as exc:
                print(f"  skip topic {topic_id}: {exc}", file=sys.stderr)
                continue

        return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forum-url", default="https://precice.discourse.group")
    parser.add_argument("--topics-limit", type=int, default=50)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--output", default="kb-embeddings-forum.npz")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
    args = parser.parse_args()

    topics = _fetch_topics(args.forum_url, args.topics_limit, args.timeout_seconds)
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
