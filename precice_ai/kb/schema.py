"""Canonical chunk schema shared by the vector and lexical knowledge bases.

Every ingestion path (git-backed Markdown, Discourse forum, GitHub
issues/pulls, live-crawl fallback) produces `Chunk` records, and both stores
(`kb-embeddings-<category>.npz` and `kb-lexical.json`) carry the very same
records keyed by `chunk_id`. Retrieval relies on that: neighbour expansion
uses `doc_id` + `chunk_index`, dedup uses `doc_id`, and hybrid fusion merges
vector/lexical hits by `chunk_id`.

Bump SCHEMA_VERSION whenever a field is added/removed/changes meaning, or the
chunking/cleaning rules change in a way that alters chunk boundaries.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field, fields
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA_VERSION = 1

CATEGORIES = ("about", "community", "documentation", "tutorials", "forum", "issues", "pulls")

MIN_CHUNK_CHARS = 150

# ---------------------------------------------------------------------------
# Exclusions (applied at ingestion, not only at query time)
# ---------------------------------------------------------------------------

# Matched against the lower-cased path of a source file *or* a URL.
_EXCLUDED_DIR_RE = re.compile(r"(^|/)changelog-entries(/|$)")
_EXCLUDED_STEM_RE = re.compile(
    r"(^|/)(changelog|contributing|licen[cs]e|copying)([-_.][^/]*)?(\.(md|markdown|txt|rst|html))?$"
)


def is_excluded_path(path_or_url: str) -> bool:
    """True for changelog entries, CHANGELOG/CONTRIBUTING/LICENSE files."""
    p = urlsplit(path_or_url).path if "://" in path_or_url else path_or_url
    p = p.replace("\\", "/").lower().rstrip("/")
    return bool(_EXCLUDED_DIR_RE.search(p) or _EXCLUDED_STEM_RE.search(p))


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------

_TRACKING_PARAMS = {
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src", "source", "igshid",
    "_ga", "_gl", "yclid", "msclkid",
}
_HOST_ALIASES = {"www.precice.org": "precice.org", "precice.github.io": "precice.org"}


def normalize_url(url: str) -> str:
    """Canonical URL: https, lower-case host, no tracking params, no fragment,
    no trailing slash, no trailing index.html."""
    url = url.strip()
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return url.rstrip("/")
    scheme = "https" if parts.scheme in ("http", "https") else parts.scheme
    host = parts.netloc.lower()
    if host.endswith(":443") or host.endswith(":80"):
        host = host.rsplit(":", 1)[0]
    host = _HOST_ALIASES.get(host, host)
    path = re.sub(r"/{2,}", "/", parts.path)
    path = re.sub(r"/index\.html?$", "", path)
    path = path.rstrip("/")
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_PARAMS
        ]
    )
    return urlunsplit((scheme, host, path, query, ""))


def make_doc_id(canonical_url: str) -> str:
    return hashlib.sha1(canonical_url.encode("utf-8")).hexdigest()[:16]


def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    return f"{doc_id}#{chunk_index}"


def build_embed_text(title: str, section_path: list[str], text: str) -> str:
    header = " > ".join([title, *section_path]) if title or section_path else ""
    return f"{header}\n\n{text}" if header else text


def text_fingerprint(text: str) -> str:
    """Hash of whitespace/case-normalised text, for exact-duplicate detection."""
    norm = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Chunk record
# ---------------------------------------------------------------------------


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    url: str
    title: str
    section_path: list[str]
    category: str
    source: str
    chunk_index: int
    chunk_count: int
    text: str
    embed_text: str
    char_len: int
    created_at: str | None = None
    updated_at: str | None = None
    extra: dict = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})


_REQUIRED_TYPES: dict[str, type | tuple[type, ...]] = {
    "chunk_id": str, "doc_id": str, "url": str, "title": str, "section_path": list,
    "category": str, "source": str, "chunk_index": int, "chunk_count": int,
    "text": str, "embed_text": str, "char_len": int, "extra": dict, "schema_version": int,
}


def validate_chunk_dict(d: dict) -> list[str]:
    """Return a list of schema violations for one serialised chunk (empty = ok)."""
    errors: list[str] = []
    for key, typ in _REQUIRED_TYPES.items():
        if key not in d:
            errors.append(f"missing field {key!r}")
        elif not isinstance(d[key], typ) or (typ is int and isinstance(d[key], bool)):
            errors.append(f"field {key!r} has type {type(d[key]).__name__}, expected {typ}")
    if errors:
        return errors
    if not d["text"].strip():
        errors.append("empty text")
    if not d["url"].strip():
        errors.append("empty url")
    if d["category"] not in CATEGORIES:
        errors.append(f"unknown category {d['category']!r}")
    if d["chunk_id"] != make_chunk_id(d["doc_id"], d["chunk_index"]):
        errors.append("chunk_id != f'{doc_id}#{chunk_index}'")
    if not (0 <= d["chunk_index"] < d["chunk_count"]):
        errors.append("chunk_index outside 0..chunk_count-1")
    if d["char_len"] != len(d["text"]):
        errors.append("char_len != len(text)")
    if d["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version {d['schema_version']} != {SCHEMA_VERSION}")
    if not all(isinstance(s, str) for s in d["section_path"]):
        errors.append("section_path must be a list of strings")
    return errors


class KBFormatError(RuntimeError):
    """Raised when a local KB store was built with an incompatible schema or
    embedding model. The message always tells the user how to re-ingest."""


REINGEST_HINT = (
    "Re-ingest the knowledge base: run `precice-ai kb ingest` to pull the rebuilt "
    "release assets, or `precice-ai kb rebuild` to rebuild both stores locally."
)
