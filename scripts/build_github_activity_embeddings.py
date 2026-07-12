"""Build the 'issues' or 'pulls' vector KB category from a GitHub repo's
Issues or Pull Requests, via the REST API.

Like the forum category, this content is fetched live over HTTP rather than
checked out from git, so it has its own build script but produces the same
chunk schema (title, url, source, category, chunk_index, text) and .npz
layout as build_embeddings.py, so VectorKnowledgeBase can merge it with the
other categories transparently.

Each issue/PR's title, body, and comments are merged into one document
before chunking, so a resolved bug report or a merged PR's discussion reads
as a single unit of context.

Usage:
    python scripts/build_github_activity_embeddings.py \
        --repo precice/precice --kind issues \
        --api-key $OPENROUTER_API_KEY \
        --github-token $GITHUB_TOKEN \
        --output kb-embeddings-issues.npz
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
import numpy as np
from openai import OpenAI

from build_embeddings import BASE_URL_DEFAULT, BATCH_SIZE_DEFAULT, MODEL_DEFAULT, _chunk, _embed_batch

USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"
API_ROOT = "https://api.github.com"


def _headers(github_token: str | None) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _list_endpoint(repo: str, kind: str) -> str:
    return f"{API_ROOT}/repos/{repo}/pulls" if kind == "pulls" else f"{API_ROOT}/repos/{repo}/issues"


def _fetch_items(
    client: httpx.Client, repo: str, kind: str, items_limit: int
) -> list[dict]:
    endpoint = _list_endpoint(repo, kind)
    items: list[dict] = []
    page = 1
    while len(items) < items_limit:
        response = client.get(
            endpoint,
            params={
                "state": "all",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        for entry in batch:
            # The issues endpoint also returns PRs; skip them when building
            # the "issues" category since "pulls" covers that content instead.
            if kind == "issues" and "pull_request" in entry:
                continue
            items.append(entry)
            if len(items) >= items_limit:
                break
        page += 1
    return items


def _fetch_comments(client: httpx.Client, repo: str, number: int, comments_limit: int) -> str:
    try:
        response = client.get(
            f"{API_ROOT}/repos/{repo}/issues/{number}/comments",
            params={"per_page": comments_limit},
        )
        response.raise_for_status()
        comments = response.json()
    except Exception as exc:
        print(f"  skip comments for #{number}: {exc}", file=sys.stderr)
        return ""
    return "\n\n".join(c.get("body", "") or "" for c in comments if isinstance(c, dict))


def _fetch_documents(
    repo: str,
    kind: str,
    items_limit: int,
    comments_limit: int,
    github_token: str | None,
    timeout_seconds: int,
) -> list[dict]:
    source = "precice-github-issues" if kind == "issues" else "precice-github-prs"
    with httpx.Client(timeout=timeout_seconds, headers=_headers(github_token), follow_redirects=True) as client:
        items = _fetch_items(client, repo, kind, items_limit)
        print(f"Fetched {len(items)} {kind} from {repo}", file=sys.stderr)

        docs: list[dict] = []
        for item in items:
            number = item.get("number")
            title = item.get("title", "")
            body = item.get("body") or ""
            url = item.get("html_url", "")
            if not number or not url:
                continue

            comments_text = _fetch_comments(client, repo, number, comments_limit)
            merged = "\n\n".join(part for part in (body, comments_text) if part.strip())
            if not merged.strip():
                continue

            docs.append({"title": f"#{number} {title}", "url": url, "text": merged, "source": source})

        return docs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name, e.g. precice/precice")
    parser.add_argument("--kind", required=True, choices=["issues", "pulls"])
    parser.add_argument("--items-limit", type=int, default=200)
    parser.add_argument("--comments-limit", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--github-token", default=None, help="Raises the GitHub API rate limit")
    parser.add_argument("--api-key", required=True, help="OpenRouter / Blablador API key")
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--output", default=None)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT)
    args = parser.parse_args()

    output = args.output or f"kb-embeddings-{args.kind}.npz"

    documents = _fetch_documents(
        repo=args.repo,
        kind=args.kind,
        items_limit=args.items_limit,
        comments_limit=args.comments_limit,
        github_token=args.github_token,
        timeout_seconds=args.timeout_seconds,
    )

    all_chunks: list[dict[str, str | int]] = []
    for doc in documents:
        for i, chunk_text in enumerate(_chunk(doc["text"])):
            all_chunks.append(
                {
                    "title": doc["title"],
                    "url": doc["url"],
                    "source": doc["source"],
                    "category": args.kind,
                    "chunk_index": i,
                    "text": chunk_text,
                }
            )

    if not all_chunks:
        sys.exit(f"No {args.kind} chunks produced.")

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
        output,
        embeddings=embeddings_array,
        chunks=np.array(chunks_json),
    )

    size_mb = Path(output).stat().st_size / 1_048_576
    print(
        f"Saved {len(all_chunks)} chunks, embeddings shape {embeddings_array.shape} "
        f"→ {output} ({size_mb:.1f} MB)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
