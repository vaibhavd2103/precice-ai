"""Rebuild the vector and lexical KB stores from scratch in the canonical format.

    precice-ai kb rebuild                      # all categories, into the local kb_store
    python scripts/rebuild_kb.py --out-dir out --categories documentation forum
    python scripts/rebuild_kb.py --dry-run     # chunk + stats only, no embedding API calls

Writes kb-embeddings-<category>.npz for each category, then (unless
--no-finalize) derives the lexical store (knowledge_base.json) and
kb-manifest.json from those npz files and validates the result.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from precice_ai.kb import builder, store
from precice_ai.kb.fetch import fetch_github_items
from precice_ai.kb.schema import CATEGORIES, Chunk
from precice_ai.kb.sources import clone_category_sources, load_sources_config, render_sources

LEXICAL_LOCAL_NAME = "knowledge_base.json"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def collect_category_chunks(
    category: str,
    config: dict,
    *,
    checkout_map: dict[str, str] | None = None,
    forum_topics_limit: int | None = None,
    items_limit: int = 100_000,
    comments_limit: int = 100,
    github_token: str | None = None,
    stats: dict | None = None,
) -> list[Chunk]:
    cat_config = config["categories"].get(category)
    if cat_config is None:
        raise SystemExit(f"Unknown category: {category}")
    stats = stats if stats is not None else {}
    kind = cat_config.get("type")

    if kind == "discourse":
        import httpx

        from precice_ai.core.discourse_api import fetch_discourse_topic_documents

        with httpx.Client(
            timeout=30, headers={"User-Agent": "precice-ai-mcp/1.0 (+https://github.com/precice)"},
            follow_redirects=True,
        ) as client:
            topics = fetch_discourse_topic_documents(client, cat_config["forum_url"], topics_limit=forum_topics_limit)
        _log(f"Fetched {len(topics)} forum topics")
        return builder.build_forum_chunks(topics, stats)

    if kind in ("github_issues", "github_prs"):
        gh_kind = "issues" if kind == "github_issues" else "pulls"
        items = fetch_github_items(cat_config["repo"], gh_kind, items_limit, comments_limit, github_token)
        return builder.build_github_chunks(gh_kind, cat_config["repo"], items, stats)

    with tempfile.TemporaryDirectory(prefix="precice-kb-src-") as tmp:
        mapping = dict(checkout_map or {})
        missing = [s["repo"] for s in cat_config["sources"] if s["repo"] not in mapping]
        if missing:
            _log(f"[{category}] cloning {', '.join(sorted(set(missing)))}")
            mapping.update(clone_category_sources(config, category, Path(tmp)))
        sources = render_sources(config, category, mapping)
        return builder.build_markdown_chunks(category, sources, stats)


def rebuild(
    out_dir: Path,
    categories: list[str],
    *,
    config_path: Path | None = None,
    checkout_map: dict[str, str] | None = None,
    forum_topics_limit: int | None = None,
    items_limit: int = 100_000,
    comments_limit: int = 100,
    github_token: str | None = None,
    batch_size: int = 16,
    dry_run: bool = False,
    finalize: bool = True,
    lexical_name: str = LEXICAL_LOCAL_NAME,
) -> dict:
    from precice_ai.core.embedding import _resolve_api_key, _resolve_base_url, _resolve_model

    config = load_sources_config(config_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = _resolve_model(None)
    if not dry_run:
        api_key, base_url = _resolve_api_key(), _resolve_base_url()

    ingestion_stats: dict[str, dict] = {}
    for category in categories:
        _log(f"=== {category} ===")
        stats: dict = {}
        chunks = collect_category_chunks(
            category, config, checkout_map=checkout_map, forum_topics_limit=forum_topics_limit,
            items_limit=items_limit, comments_limit=comments_limit, github_token=github_token, stats=stats,
        )
        ingestion_stats[category] = stats
        if not chunks:
            raise SystemExit(f"No chunks produced for {category}.")
        summary = store.category_stats([c.to_dict() for c in chunks])
        _log(f"[{category}] {summary} dropped={stats}")
        if dry_run:
            continue
        embeddings = store.embed_chunks(chunks, api_key=api_key, base_url=base_url, model=model, batch_size=batch_size)
        npz_path = out_dir / store.npz_name(category)
        store.write_vector_store(npz_path, category, chunks, embeddings, model)
        store.write_local_meta(npz_path)

    if dry_run:
        return {"dry_run": True, "ingestion": ingestion_stats}
    if not finalize:
        return {"ingestion": ingestion_stats}

    manifest = store.finalize_store(out_dir, lexical_name=lexical_name, excluded_stats=ingestion_stats)
    store.write_local_meta(out_dir / lexical_name)
    from precice_ai.kb.validate import validate_directory

    report = validate_directory(out_dir, lexical_name=lexical_name)
    manifest["validation"] = {"ok": report["ok"], "errors": report["errors"][:20]}
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out-dir", type=Path, default=None, help="Default: the local kb_store directory.")
    p.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    p.add_argument("--config", type=Path, default=None, help="kb_sources.json (default: auto-detected).")
    p.add_argument("--checkout-dir", action="append", default=[], help="repo=local_dir; skips cloning that repo.")
    p.add_argument("--forum-topics-limit", type=int, default=0, help="0 = every topic.")
    p.add_argument("--items-limit", type=int, default=100_000)
    p.add_argument("--comments-limit", type=int, default=100)
    p.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--dry-run", action="store_true", help="Chunk and print stats; no embedding calls, nothing written.")
    p.add_argument("--no-finalize", action="store_true", help="Only write npz files (CI finalizes later).")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    checkout_map: dict[str, str] = {}
    for pair in args.checkout_dir:
        repo, _, local = pair.partition("=")
        if not repo or not local:
            raise SystemExit(f"Invalid --checkout-dir {pair!r} (expected repo=local_dir)")
        checkout_map[repo] = local

    from precice_ai.core.knowledge_base import _get_kb_dir

    result = rebuild(
        args.out_dir or _get_kb_dir(),
        args.categories,
        config_path=args.config,
        checkout_map=checkout_map,
        forum_topics_limit=args.forum_topics_limit or None,
        items_limit=args.items_limit,
        comments_limit=args.comments_limit,
        github_token=args.github_token,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        finalize=not args.no_finalize,
    )
    print(json.dumps(result, indent=2))
    if result.get("validation") and not result["validation"]["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
