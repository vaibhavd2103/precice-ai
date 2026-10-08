"""Build canonical `Chunk` records for every KB category.

One function per source family; all of them funnel through
`chunking.assemble_document`, so ids, embed_text, near-empty filtering and
exact-dedup behave identically for every category.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from precice_ai.kb.chunking import (
    Deduper,
    RawChunk,
    Segment,
    assemble_document,
    chunk_markdown,
    chunk_segments,
)
from precice_ai.kb.cleaning import clean_forum_post, clean_markdown, html_to_markdown, parse_frontmatter
from precice_ai.kb.schema import Chunk, is_excluded_path, make_doc_id, normalize_url


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Git-backed Markdown (about, community, documentation, tutorials)
# ---------------------------------------------------------------------------


def _file_url(filepath: Path, source_dir: Path, source: dict, meta: dict) -> str:
    url_base = source["url_base"].rstrip("/")
    rel = filepath.relative_to(source_dir)
    if source["url_mode"] == "website":
        permalink = meta.get("permalink", "")
        if permalink:
            return url_base + ("" if permalink.startswith("/") else "/") + permalink
        return f"{url_base}/{rel.stem}.html"
    return f"{url_base}/{rel.as_posix()}"


def _doc_title(meta: dict, body: str, filepath: Path) -> str:
    if meta.get("title"):
        return meta["title"]
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    stem = filepath.stem
    if stem.lower() in ("readme", "index"):
        stem = filepath.parent.name or stem
    return stem.replace("-", " ").replace("_", " ").strip().title()


def build_markdown_chunks(category: str, sources: list[dict], stats: dict | None = None) -> list[Chunk]:
    stats = stats if stats is not None else {}
    dedup = Deduper()
    chunks: list[Chunk] = []
    seen_docs: set[str] = set()

    for source in sources:
        source_dir = Path(source["path"]).resolve()
        if not source_dir.exists():
            _log(f"  warning: source dir not found: {source_dir}")
            continue
        patterns = source.get("exclude_patterns", [])
        files = sorted(source_dir.rglob("*.md"))
        _log(f"[{source['label']}] {len(files)} markdown files in {source_dir}")

        for filepath in files:
            rel = filepath.relative_to(source_dir).as_posix()
            if is_excluded_path(rel) or any(p in rel for p in patterns):
                stats["excluded_files"] = stats.get("excluded_files", 0) + 1
                continue
            try:
                raw = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                _log(f"  skip {filepath}: {exc}")
                continue

            meta, body = parse_frontmatter(raw)
            url = _file_url(filepath, source_dir, source, meta)
            if is_excluded_path(url):
                stats["excluded_files"] = stats.get("excluded_files", 0) + 1
                continue
            doc_id = make_doc_id(normalize_url(url))
            if doc_id in seen_docs:
                stats["skipped_duplicate_url"] = stats.get("skipped_duplicate_url", 0) + 1
                continue

            cleaned = clean_markdown(body)
            title = _doc_title(meta, cleaned, filepath)
            doc_chunks = assemble_document(
                category=category,
                source=source["label"],
                url=url,
                title=title,
                raw_chunks=chunk_markdown(cleaned, title),
                dedup=dedup,
                created_at=meta.get("date") or None,
                updated_at=meta.get("last_updated") or None,
                doc_extra={"path": rel},
                stats=stats,
            )
            if doc_chunks:
                seen_docs.add(doc_id)
                chunks.extend(doc_chunks)
    return chunks


# ---------------------------------------------------------------------------
# Forum
# ---------------------------------------------------------------------------


def build_forum_chunks(topics: list, stats: dict | None = None) -> list[Chunk]:
    """topics: DiscourseTopicDocument-like objects (title, url, posts, ...)."""
    stats = stats if stats is not None else {}
    dedup = Deduper()
    chunks: list[Chunk] = []
    seen_docs: set[str] = set()

    for topic in topics:
        doc_id = make_doc_id(normalize_url(topic.url))
        if doc_id in seen_docs:
            continue
        segments = [
            Segment(
                f"Post {p.post_number}",
                clean_forum_post(p.raw),
                {"post_number": p.post_number, "is_accepted_solution": p.is_accepted_solution},
            )
            for p in sorted(topic.posts, key=lambda p: p.post_number)
        ]
        raw_chunks: list[RawChunk] = []
        for path, text, extras in chunk_segments(segments):
            numbers = [e["post_number"] for e in extras]
            raw_chunks.append(
                RawChunk(
                    path,
                    text,
                    {
                        "post_number": numbers[0],
                        "post_numbers": numbers,
                        "post_url": f"{normalize_url(topic.url)}/{numbers[0]}",
                        "is_accepted_solution": any(e["is_accepted_solution"] for e in extras),
                    },
                )
            )
        doc_chunks = assemble_document(
            category="forum",
            source="forum",
            url=topic.url,
            title=topic.title,
            raw_chunks=raw_chunks,
            dedup=dedup,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
            doc_extra={"reply_count": topic.reply_count, "tags": list(topic.tags)},
            stats=stats,
        )
        if doc_chunks:
            seen_docs.add(doc_id)
            chunks.extend(doc_chunks)
    return chunks


# ---------------------------------------------------------------------------
# GitHub issues / pulls
# ---------------------------------------------------------------------------


_CHECKLIST_RE = re.compile(r"^\s*[-*+]\s*\[[ xX]\]\s*(.*\S)\s*$")
_TEMPLATE_MIN_ITEMS = 5


def _template_checklist_lines(items: list[dict]) -> set[str]:
    """Checklist lines that recur across many descriptions are PR/issue
    template boilerplate ("I added a changelog file..."), not content."""
    counts: Counter[str] = Counter()
    for item in items:
        counts.update({m.group(1).lower() for line in item["body"].splitlines() if (m := _CHECKLIST_RE.match(line))})
    return {line for line, n in counts.items() if n >= _TEMPLATE_MIN_ITEMS}


def _drop_template_lines(body: str, template: set[str]) -> str:
    if not template:
        return body
    kept = [ln for ln in body.splitlines() if not ((m := _CHECKLIST_RE.match(ln)) and m.group(1).lower() in template)]
    return "\n".join(kept)


def build_github_chunks(kind: str, repo: str, items: list[dict], stats: dict | None = None) -> list[Chunk]:
    stats = stats if stats is not None else {}
    template = _template_checklist_lines(items)
    dedup = Deduper()
    chunks: list[Chunk] = []
    source = f"{kind}-{repo.split('/')[-1]}"

    for item in items:
        segments = [Segment("Description", clean_markdown(_drop_template_lines(item["body"], template)), {})]
        for i, c in enumerate(item["comments"], 1):
            segments.append(Segment(f"Comment {i}", clean_markdown(c["body"]), {}))
        raw_chunks = [RawChunk(path, text) for path, text, _ in chunk_segments(segments)]

        extra = {
            "number": item["number"],
            "state": item["state"],
            "labels": item["labels"],
            "closed_at": item["closed_at"],
        }
        if kind == "pulls":
            extra["merged"] = bool(item["merged"])
        chunks.extend(
            assemble_document(
                category=kind,
                source=source,
                url=item["url"],
                title=f"#{item['number']} {item['title']}",
                raw_chunks=raw_chunks,
                dedup=dedup,
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                doc_extra=extra,
                stats=stats,
            )
        )
    return chunks


# ---------------------------------------------------------------------------
# Live-crawl fallback (HTML pages)
# ---------------------------------------------------------------------------


def build_html_chunks(
    pages: list[tuple[str, str]], category: str, source: str, stats: dict | None = None
) -> list[Chunk]:
    """pages: (url, raw_html). Used only by the emergency live-crawl fallback."""
    stats = stats if stats is not None else {}
    dedup = Deduper()
    chunks: list[Chunk] = []
    for url, raw_html in pages:
        if is_excluded_path(url):
            continue
        title, markdown = html_to_markdown(raw_html)
        title = title or url
        chunks.extend(
            assemble_document(
                category=category,
                source=source,
                url=url,
                title=title,
                raw_chunks=chunk_markdown(markdown, title),
                dedup=dedup,
                stats=stats,
            )
        )
    return chunks
