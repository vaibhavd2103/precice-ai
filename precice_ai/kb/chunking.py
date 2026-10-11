"""Chunkers that turn cleaned Markdown / discussion segments into chunk bodies,
and `assemble_document`, which turns those into canonical `Chunk` records
(ids, embed_text, exclusion of near-empty chunks, exact-duplicate removal).

Rules (see docs in schema.py):
  * Markdown is split on H1-H3 headings; the heading hierarchy becomes
    `section_path`. H4+ stay inline.
  * Target ~800-1500 chars per chunk with ~150 chars of overlap between chunks
    of the same section.
  * Fenced code blocks (and therefore XML config snippets) are atomic. Only a
    block above HARD_MAX_CHARS (an embedding-model safety limit) is split, on
    line boundaries, and each part is re-fenced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from precice_ai.kb.schema import (
    MIN_CHUNK_CHARS,
    SCHEMA_VERSION,
    Chunk,
    build_embed_text,
    make_chunk_id,
    make_doc_id,
    normalize_url,
    text_fingerprint,
)

TARGET_MIN_CHARS = 800
TARGET_MAX_CHARS = 1500
OVERLAP_CHARS = 150
# Embedding models cap input at ~8k tokens; 6000 chars stays safely below that
# even for token-dense text such as logs.
HARD_MAX_CHARS = 6000
# A tiny chunk may swallow a following block up to this size rather than be
# emitted on its own.
SMALL_CHUNK_CHARS = 300
SMALL_CHUNK_MAX_COMBINED = 3000

_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t#]*$")


@dataclass
class _Block:
    kind: str  # "text" | "code" | "heading"
    text: str
    level: int = 0


@dataclass
class RawChunk:
    section_path: list[str]
    text: str
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Markdown → blocks
# ---------------------------------------------------------------------------


def _split_code_block(text: str) -> list[str]:
    """Split an over-long fenced block on line boundaries, re-fencing each part."""
    if len(text) <= HARD_MAX_CHARS:
        return [text]
    lines = text.split("\n")
    opener = lines[0]
    has_closer = len(lines) > 1 and _FENCE_RE.match(lines[-1]) is not None
    closer = lines[-1] if has_closer else _FENCE_RE.match(opener).group(1)  # type: ignore[union-attr]
    body = lines[1:-1] if has_closer else lines[1:]
    parts: list[str] = []
    cur: list[str] = []
    size = len(opener) + len(closer) + 2
    for line in body:
        # A single over-long line is cut hard; there is nothing better to do.
        while len(line) > HARD_MAX_CHARS - size:
            cut = HARD_MAX_CHARS - size - 1
            if cur:
                parts.append("\n".join([opener, *cur, closer]))
                cur, size = [], len(opener) + len(closer) + 2
            parts.append("\n".join([opener, line[:cut], closer]))
            line = line[cut:]
        if cur and size + len(line) + 1 > HARD_MAX_CHARS:
            parts.append("\n".join([opener, *cur, closer]))
            cur, size = [], len(opener) + len(closer) + 2
        cur.append(line)
        size += len(line) + 1
    if cur:
        parts.append("\n".join([opener, *cur, closer]))
    return parts


def _split_text_block(text: str, limit: int = TARGET_MAX_CHARS) -> list[str]:
    """Split an over-long prose/list/table block on lines, then sentences, then words."""
    if len(text) <= limit:
        return [text]
    pieces: list[str] = []
    for line in text.split("\n"):
        if len(line) <= limit:
            pieces.append(line)
            continue
        for sent in re.split(r"(?<=[.!?])\s+", line):
            if len(sent) <= limit:
                pieces.append(sent)
                continue
            words, cur = sent.split(" "), ""
            for w in words:
                if cur and len(cur) + 1 + len(w) > limit:
                    pieces.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}" if cur else w
                while len(cur) > limit:  # one giant token (URL, hash): cut hard
                    pieces.append(cur[:limit])
                    cur = cur[limit:]
            if cur:
                pieces.append(cur)
    out: list[str] = []
    cur = ""
    for p in pieces:
        joiner = "\n" if "\n" in text else " "
        if cur and len(cur) + len(joiner) + len(p) > limit:
            out.append(cur)
            cur = p
        else:
            cur = f"{cur}{joiner}{p}" if cur else p
    if cur:
        out.append(cur)
    return out


def _parse_blocks(markdown: str) -> list[_Block]:
    blocks: list[_Block] = []
    para: list[str] = []
    code: list[str] = []
    fence: str | None = None

    def flush_para() -> None:
        if para:
            blocks.append(_Block("text", "\n".join(para)))
            para.clear()

    for line in markdown.split("\n"):
        if fence is not None:
            code.append(line)
            m = _FENCE_RE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                blocks.append(_Block("code", "\n".join(code)))
                code, fence = [], None
            continue
        m = _FENCE_RE.match(line)
        if m:
            flush_para()
            fence = m.group(1)
            code = [line]
            continue
        h = _HEADING_RE.match(line)
        if h and len(h.group(1)) <= 3:
            flush_para()
            blocks.append(_Block("heading", h.group(2).strip(), len(h.group(1))))
            continue
        if not line.strip():
            flush_para()
            continue
        para.append(line)
    if fence is not None:  # unterminated fence: keep what we have, closed
        blocks.append(_Block("code", "\n".join([*code, fence])))
    flush_para()
    return blocks


# ---------------------------------------------------------------------------
# Markdown chunker
# ---------------------------------------------------------------------------


def _overlap_tail(prev_blocks: list[_Block]) -> str:
    """Up to OVERLAP_CHARS from the end of the previous chunk's last prose
    block, starting at a word boundary. Never taken from a code block."""
    if not prev_blocks or prev_blocks[-1].kind != "text":
        return ""
    text = prev_blocks[-1].text
    if len(text) <= OVERLAP_CHARS:
        return text
    tail = text[-OVERLAP_CHARS:]
    cut = re.search(r"\s", tail)
    return tail[cut.end():] if cut else ""


def chunk_markdown(markdown: str, title: str = "") -> list[RawChunk]:
    """Heading-aware chunking of cleaned Markdown."""
    norm_title = re.sub(r"\W+", " ", title).strip().lower()
    stack: dict[int, str] = {}

    def current_path() -> list[str]:
        path = [stack[k] for k in sorted(stack)]
        if path and re.sub(r"\W+", " ", path[0]).strip().lower() == norm_title:
            path = path[1:]
        return path

    chunks: list[RawChunk] = []
    cur: list[_Block] = []
    cur_len = 0
    cur_path: list[str] = []
    own_len = 0  # chars in `cur` that are not overlap

    def render(blocks: list[_Block]) -> str:
        return "\n\n".join(b.text for b in blocks)

    def flush(next_path: list[str], keep_overlap: bool) -> None:
        nonlocal cur, cur_len, cur_path, own_len
        if not cur:
            return
        chunks.append(RawChunk(list(cur_path), render(cur), {"_own": own_len}))
        tail = _overlap_tail(cur) if keep_overlap else ""
        cur = [_Block("text", tail)] if tail else []
        cur_len = len(tail)
        own_len = 0
        cur_path = next_path

    for block in _parse_blocks(markdown):
        if block.kind == "heading":
            for lvl in [k for k in stack if k >= block.level]:
                del stack[lvl]
            stack[block.level] = block.text
            if cur and own_len == 0:
                cur, cur_len = [], 0  # only overlap from the previous section: drop it
                cur_path = current_path()
            elif cur and own_len >= TARGET_MIN_CHARS:
                flush(current_path(), keep_overlap=False)
                cur, cur_len, own_len = [], 0, 0
            elif cur:
                # Section too small to stand alone: keep it inline in this chunk.
                line = "#" * block.level + " " + block.text
                cur.append(_Block("text", line))
                cur_len += len(line) + 2
                own_len += len(line) + 2
            else:
                cur_path = current_path()
            continue

        if not cur:
            cur_path = current_path()
        pieces = _split_code_block(block.text) if block.kind == "code" else _split_text_block(block.text)
        for piece in pieces:
            sep = 2 if cur else 0
            fits = cur_len + sep + len(piece) <= TARGET_MAX_CHARS or (
                own_len < SMALL_CHUNK_CHARS and cur_len + sep + len(piece) <= SMALL_CHUNK_MAX_COMBINED
            )
            if cur and not fits:
                if own_len == 0:
                    cur, cur_len = [], 0  # overlap alone never forms a chunk
                else:
                    flush(cur_path, keep_overlap=True)
                sep = 2 if cur else 0
            cur.append(_Block(block.kind, piece))
            cur_len += sep + len(piece)
            own_len += sep + len(piece)

    if cur and own_len > 0:
        chunks.append(RawChunk(list(cur_path), render(cur), {"_own": own_len}))

    # A short final remainder joins the previous chunk instead of standing alone.
    merged: list[RawChunk] = []
    for ch in chunks:
        if (
            merged
            and ch.extra["_own"] < MIN_CHUNK_CHARS
            and ch.section_path == merged[-1].section_path
            and len(merged[-1].text) + ch.extra["_own"] + 2 <= HARD_MAX_CHARS
        ):
            own_text = ch.text[len(ch.text) - ch.extra["_own"]:] if ch.extra["_own"] else ""
            merged[-1].text += "\n\n" + own_text.strip()
            continue
        merged.append(ch)
    for ch in merged:
        ch.extra.pop("_own", None)
    return merged


# ---------------------------------------------------------------------------
# Discussion segments (forum posts, issue/PR body + comments)
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    label: str  # e.g. "Post 3", "Description", "Comment 2"
    text: str  # already cleaned
    extra: dict = field(default_factory=dict)


def chunk_segments(segments: list[Segment]) -> list[tuple[list[str], str, list[dict]]]:
    """Merge short consecutive segments into chunks (original order kept,
    the first segment — the opening question/description — leads). Segments
    longer than the target are split with `chunk_markdown`.

    Returns (section_path, text, [extra of every segment merged into it]).
    """
    out: list[tuple[list[str], str, list[dict]]] = []
    buf: list[str] = []
    buf_extras: list[dict] = []
    buf_label = ""
    buf_len = 0

    def flush() -> None:
        nonlocal buf, buf_extras, buf_len
        if buf:
            out.append(([buf_label], "\n\n".join(buf), list(buf_extras)))
        buf, buf_extras, buf_len = [], [], 0

    for seg in segments:
        body = seg.text.strip()
        if not body:
            continue
        text = f"[{seg.label}]\n{body}"
        if len(text) > TARGET_MAX_CHARS:
            flush()
            for i, part in enumerate(chunk_markdown(body)):
                out.append(([seg.label], f"[{seg.label}]\n{part.text}" if i == 0 else part.text, [seg.extra]))
            continue
        if buf and buf_len + 2 + len(text) > TARGET_MAX_CHARS:
            flush()
        if not buf:
            buf_label = seg.label
        buf.append(text)
        buf_extras.append(seg.extra)
        buf_len += len(text) + (2 if buf_len else 0)
        if buf_len >= TARGET_MIN_CHARS:
            flush()
    flush()
    return out


# ---------------------------------------------------------------------------
# Assembly into canonical records
# ---------------------------------------------------------------------------


class Deduper:
    """Exact-duplicate filter across everything assembled in one category."""

    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.dropped = 0

    def is_duplicate(self, text: str) -> bool:
        fp = text_fingerprint(text)
        if fp in self.seen:
            self.dropped += 1
            return True
        self.seen.add(fp)
        return False


def assemble_document(
    *,
    category: str,
    source: str,
    url: str,
    title: str,
    raw_chunks: list[RawChunk],
    dedup: Deduper,
    created_at: str | None = None,
    updated_at: str | None = None,
    doc_extra: dict | None = None,
    stats: dict | None = None,
) -> list[Chunk]:
    """Drop near-empty and duplicate chunks, then number what is left so
    `chunk_index` is contiguous 0..chunk_count-1 and ids are deterministic."""
    canonical = normalize_url(url)
    doc_id = make_doc_id(canonical)
    kept: list[RawChunk] = []
    for rc in raw_chunks:
        text = rc.text.strip()
        if len(text) < MIN_CHUNK_CHARS:
            if stats is not None:
                stats["dropped_short"] = stats.get("dropped_short", 0) + 1
            continue
        if dedup.is_duplicate(text):
            if stats is not None:
                stats["dropped_duplicate"] = stats.get("dropped_duplicate", 0) + 1
            continue
        rc.text = text
        kept.append(rc)

    chunks: list[Chunk] = []
    for i, rc in enumerate(kept):
        chunks.append(
            Chunk(
                chunk_id=make_chunk_id(doc_id, i),
                doc_id=doc_id,
                url=canonical,
                title=title,
                section_path=list(rc.section_path),
                category=category,
                source=source,
                chunk_index=i,
                chunk_count=len(kept),
                text=rc.text,
                embed_text=build_embed_text(title, rc.section_path, rc.text),
                char_len=len(rc.text),
                created_at=created_at,
                updated_at=updated_at,
                extra={**(doc_extra or {}), **rc.extra},
                schema_version=SCHEMA_VERSION,
            )
        )
    return chunks
