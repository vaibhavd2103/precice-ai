"""Run lexical (BM25-like) and vector (embedding cosine-similarity) search
against the preCICE knowledge base for the same question, side by side.

Intended for manual accuracy review: for each question you pass, it prints
(and optionally saves) the full top-k results from both retrieval methods
plus timing, so you can check against the actual preCICE docs whether the
right chunk was retrieved and by which method.

Usage:
    python scripts/compare_kb_search.py "How do I configure a nearest-neighbor mapping?"
    python scripts/compare_kb_search.py "..." --top-k 8 --save out.json
    python scripts/compare_kb_search.py "..." --include-vectors --save out.json
    python scripts/compare_kb_search.py "How do I configure a nearest-neighbor mapping?" --top-k 8 --include-vectors --save out.json

Requires OPENROUTER_API_KEY (or BLABLADOR_API_KEY) for the vector search leg
(question embedding), and a locally ingested lexical KB / downloaded vector
KB (falls back to auto-download for the vector KB if missing).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from precice_ai.core.knowledge_base import KnowledgeBaseService, VectorKnowledgeBase

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _run_lexical(kb: KnowledgeBaseService, question: str, top_k: int) -> dict[str, object]:
    start = time.perf_counter()
    result = kb.query(question=question, top_k=top_k)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    result["elapsed_ms"] = elapsed_ms
    return result


def _run_vector(
    kb: VectorKnowledgeBase, question: str, top_k: int, include_vectors: bool
) -> dict[str, object]:
    if not kb.is_available():
        token = os.environ.get("GITHUB_TOKEN")
        download = kb.download_from_release(github_token=token)
        if download.get("status") == "error":
            return download

    start = time.perf_counter()
    result = kb.query(question=question, top_k=top_k)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    result["elapsed_ms"] = elapsed_ms

    if result.get("status") == "ok":
        all_embeddings = list(kb._embeddings.values())
        all_chunks = [c for chunks in kb._chunks.values() for c in chunks]
        result["embedding_dim"] = int(all_embeddings[0].shape[1]) if all_embeddings else None
        result["chunks_indexed"] = len(all_chunks)
        if include_vectors:
            # Attach the raw embedding vector for each returned chunk so it can
            # be inspected/plotted offline. Matched back by (title, url) since
            # VectorKnowledgeBase.query() doesn't return chunk indices.
            for item in result.get("results", []):
                for cat, chunks in kb._chunks.items():
                    for idx, chunk in enumerate(chunks):
                        if chunk.get("title") == item["title"] and chunk.get("url") == item["url"]:
                            item["embedding"] = kb._embeddings[cat][idx].tolist()
                            break

    return result


def _print_results(label: str, result: dict[str, object]) -> None:
    print(f"\n{'=' * 80}\n{label}\n{'=' * 80}")
    if result.get("status") != "ok":
        print(f"  ERROR: {result.get('message')}")
        return

    print(f"  elapsed: {result.get('elapsed_ms')} ms")
    if "chunks_indexed" in result:
        print(f"  chunks indexed: {result.get('chunks_indexed')}  embedding_dim: {result.get('embedding_dim')}")

    for rank, item in enumerate(result.get("results", []), start=1):
        print(f"\n  [{rank}] score={item.get('score')}  source={item.get('source')}")
        print(f"      title: {item.get('title')}")
        print(f"      url:   {item.get('url')}")
        snippet = str(item.get("snippet", "")).replace("\n", " ")
        print(f"      snippet: {snippet[:300]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", help="Question to search for")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results per method (default: 5)")
    parser.add_argument("--save", type=Path, default=None, help="Save full JSON output to this file")
    parser.add_argument(
        "--include-vectors",
        action="store_true",
        help="Include raw embedding vectors for top-k vector results (large; use with --save)",
    )
    args = parser.parse_args()

    lexical_kb = KnowledgeBaseService()
    vector_kb = VectorKnowledgeBase()

    lexical_result = _run_lexical(lexical_kb, args.question, args.top_k)
    vector_result = _run_vector(vector_kb, args.question, args.top_k, args.include_vectors)

    _print_results("LEXICAL (BM25-like)", lexical_result)
    _print_results("VECTOR (embedding cosine-similarity)", vector_result)

    output = {
        "question": args.question,
        "top_k": args.top_k,
        "lexical": lexical_result,
        "vector": vector_result,
    }

    if args.save:
        args.save.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nSaved full results to {args.save}")


if __name__ == "__main__":
    main()
