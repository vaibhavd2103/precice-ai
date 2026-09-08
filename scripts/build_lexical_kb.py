"""Dev/fallback-only tool — NOT part of the primary kb-ingest.yml pipeline.

The primary lexical KB (kb-lexical.json) is now built by merging the
per-category chunk fragments emitted by build_embeddings.py,
build_forum_embeddings.py, and build_github_activity_embeddings.py (via
their --lexical-output flag), so it stays in exact parity with the vector
KB. This script instead wraps KnowledgeBaseService.ingest_precice_sources(),
the same live docs-crawl + discourse-forum-crawl the MCP server falls back
to when no release is reachable and there's no local cache at all. It's
useful for exercising that fallback path locally, but its coverage (docs +
forum only, HTML-crawled) is narrower than the primary pipeline.

CLI usage:
    python scripts/build_lexical_kb.py --output kb-lexical.json \
        --docs-pages-limit 200 --forum-topics-limit 0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precice_ai.core.knowledge_base import KnowledgeBaseService


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Path to write knowledge_base.json to")
    parser.add_argument("--docs-pages-limit", type=int, default=200)
    parser.add_argument(
        "--forum-topics-limit",
        type=int,
        default=0,
        help="Maximum number of forum topics to fetch; use 0 to fetch every visible topic.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    output_path = Path(args.output)
    service = KnowledgeBaseService(kb_file=output_path)
    forum_topics_limit = args.forum_topics_limit if args.forum_topics_limit > 0 else None
    result = service.ingest_precice_sources(
        docs_pages_limit=args.docs_pages_limit,
        forum_topics_limit=forum_topics_limit,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, indent=2))

    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
