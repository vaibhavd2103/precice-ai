from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
import httpx
from lxml import html

from precice_ai.core.discourse_api import fetch_discourse_topic_documents
from precice_ai.kb import store as kb_store
from precice_ai.kb.builder import build_forum_chunks, build_html_chunks
from precice_ai.kb.schema import CATEGORIES as SCHEMA_CATEGORIES
from precice_ai.kb.schema import REINGEST_HINT, SCHEMA_VERSION, KBFormatError


def _get_kb_dir() -> Path:
    """Return the KB store directory.

    Uses PRECICE_KB_STORE_DIR env var when set (required for global pip
    installs), otherwise defaults to ~/.precice-ai/kb_store so that the
    installed package never writes into the source tree.
    """
    env = os.environ.get("PRECICE_KB_STORE_DIR")
    if env:
        return Path(env).resolve()
    return Path.home() / ".precice-ai" / "kb_store"


DOCS_START_URL = "https://precice.org/"
USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"

# How often (in hours) a locally cached release asset is re-checked against
# GitHub before being trusted as-is. 96h (4 days) matches kb-ingest.yml's
# publish cadence, so this never checks more often than the source can change.
RELEASE_ASSET_MAX_AGE_HOURS = 96


# ---------------------------------------------------------------------------
# Release asset sync — shared "source of truth" logic for both the vector KB
# (per-category .npz files) and the lexical KB (kb-lexical.json), all
# published to the same kb-latest GitHub Release by kb-ingest.yml.
#
# For RELEASE_ASSET_MAX_AGE_HOURS after the last check, the local copy is
# trusted as-is — no network call at all. Once that window elapses, the
# asset is always re-downloaded (old file deleted first), since kb-ingest.yml
# rebuilds and republishes every category unconditionally on every one of
# its ~96h (4-day) runs — the KB is never allowed to go stale for longer than
# that, regardless of whether the underlying content actually changed. The
# remote digest is still fetched and compared, purely to distinguish
# "genuinely new content" from "same content, refreshed on schedule" in the
# returned action.
# ---------------------------------------------------------------------------


def _meta_path(local_path: Path) -> Path:
    return local_path.parent / f"{local_path.name}.meta.json"


def _load_asset_meta(local_path: Path) -> dict[str, str] | None:
    meta_file = _meta_path(local_path)
    if not meta_file.exists():
        return None
    try:
        data = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _save_asset_meta(local_path: Path, remote_signature: str) -> None:
    _meta_path(local_path).write_text(
        json.dumps({"remote_signature": remote_signature, "checked_at": _now_iso()}),
        encoding="utf-8",
    )


def _meta_expired(meta: dict[str, str], max_age_hours: int) -> bool:
    checked_at = meta.get("checked_at")
    if not isinstance(checked_at, str):
        return True
    try:
        dt = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    return age_hours > max_age_hours


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness_details(
    local_path: Path,
    *,
    max_age_hours: int = RELEASE_ASSET_MAX_AGE_HOURS,
    fallback_checked_at: str | None = None,
) -> dict[str, object]:
    """Return cache-freshness metadata for a local KB asset.

    Prefer the release-asset metadata timestamp when available because the
    96h trust window is defined in terms of the last successful freshness
    check. Fall back to a logical payload timestamp (for live-ingested
    lexical KBs) or the file mtime so agents still get a useful answer for
    locally built or legacy files that have no sidecar metadata yet.
    """
    if not local_path.exists():
        return {
            "present": False,
            "checked_at": None,
            "age_hours": None,
            "expires_at": None,
            "is_fresh": False,
            "freshness_source": "missing",
            "max_age_hours": max_age_hours,
        }

    meta = _load_asset_meta(local_path)
    checked_dt: datetime | None = None
    freshness_source = "unknown"

    if meta:
        checked_dt = _parse_iso_datetime(meta.get("checked_at"))
        if checked_dt is not None:
            freshness_source = "release_meta"

    if checked_dt is None:
        checked_dt = _parse_iso_datetime(fallback_checked_at)
        if checked_dt is not None:
            freshness_source = "payload_timestamp"

    if checked_dt is None:
        checked_dt = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
        freshness_source = "file_mtime"

    age_hours = (datetime.now(timezone.utc) - checked_dt).total_seconds() / 3600.0
    expires_at = checked_dt + timedelta(hours=max_age_hours)
    return {
        "present": True,
        "checked_at": checked_dt.isoformat().replace("+00:00", "Z"),
        "age_hours": round(age_hours, 2),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        "is_fresh": age_hours < max_age_hours,
        "freshness_source": freshness_source,
        "max_age_hours": max_age_hours,
    }


def _fetch_release_assets(
    repo: str, tag: str, github_token: str | None, timeout_seconds: int = 20
) -> dict[str, dict[str, str]]:
    """Map of asset name -> {digest, url} for a GitHub Release, via the API
    (metadata only — doesn't download asset bytes)."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    with httpx.Client(timeout=timeout_seconds, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()

    assets: dict[str, dict[str, str]] = {}
    for asset in data.get("assets", []):
        name = asset.get("name")
        if not name:
            continue
        # digest is a real content hash (sha256:...) when GitHub reports one;
        # updated_at is a reasonable fallback signal (assets are replaced via
        # --clobber, which bumps this even when digest isn't exposed).
        assets[name] = {
            "digest": asset.get("digest") or asset.get("updated_at") or "",
            "url": asset.get("browser_download_url", ""),
        }
    return assets


def sync_release_asset(
    *,
    local_path: Path,
    asset_name: str,
    repo: str,
    tag: str,
    github_token: str | None = None,
    max_age_hours: int = RELEASE_ASSET_MAX_AGE_HOURS,
    timeout_seconds: int = 180,
    force: bool = False,
) -> dict[str, object]:
    """Ensure local_path mirrors the named release asset, treating the
    release as the source of truth on a fixed refresh cadence.

    Within max_age_hours of the last check, the local copy is trusted as-is
    (no network call at all). Once that window elapses, the asset is always
    re-downloaded — the publish side (kb-ingest.yml) rebuilds and republishes
    unconditionally every cycle, so a fresh copy is pulled every time the
    window elapses regardless of whether the digest happens to match; the
    digest is only used to decide *whether the old file needs deleting first*,
    not whether to skip the download.

    force=True skips the trust window (used when the cached file has an
    incompatible schema, so waiting out the window would only keep serving
    unusable data).
    """
    local_path.parent.mkdir(parents=True, exist_ok=True)
    meta = _load_asset_meta(local_path)

    if not force and local_path.exists() and meta and not _meta_expired(meta, max_age_hours):
        return {"status": "ok", "action": "cached", "path": str(local_path)}

    try:
        assets = _fetch_release_assets(repo, tag, github_token)
    except Exception as exc:
        if local_path.exists():
            # Can't reach GitHub right now — keep serving what we already have.
            return {"status": "ok", "action": "cached_offline", "path": str(local_path), "message": str(exc)}
        return {"status": "error", "message": f"Failed to fetch release metadata: {exc}"}

    asset = assets.get(asset_name)
    if asset is None:
        if local_path.exists():
            return {"status": "ok", "action": "cached_missing_remote", "path": str(local_path)}
        return {"status": "error", "message": f"No asset named {asset_name!r} found in {repo}@{tag}"}

    remote_signature = asset["digest"]
    content_unchanged = bool(local_path.exists() and meta and meta.get("remote_signature") == remote_signature)

    headers: dict[str, str] = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    with httpx.Client(follow_redirects=True, timeout=timeout_seconds, headers=headers) as client:
        response = client.get(asset["url"])
        response.raise_for_status()
        content = response.content

    if local_path.exists():
        local_path.unlink()
    local_path.write_bytes(content)
    _save_asset_meta(local_path, remote_signature)
    return {
        "status": "ok",
        "action": "downloaded_unchanged_content" if content_unchanged else "downloaded",
        "path": str(local_path),
        "size_mb": round(len(content) / 1_048_576, 2),
    }


class KnowledgeBaseService:
    def __init__(self, kb_file: Path | None = None) -> None:
        self.kb_file = kb_file or _get_kb_dir() / "knowledge_base.json"
        self.kb_file.parent.mkdir(parents=True, exist_ok=True)

    def ingest_precice_sources(
        self,
        docs_pages_limit: int = 20,
        forum_topics_limit: int | None = None,
        timeout_seconds: int = 20,
    ) -> dict[str, str | int]:
        """Emergency live crawl (docs site + forum) into the lexical store.

        Produces the same canonical chunk records as the release pipeline
        (see precice_ai.kb.schema), but covers only the documentation and
        forum categories.
        """
        docs_pages: list[tuple[str, str]] = []
        forum_topics: list = []
        docs_error = ""
        forum_error = ""

        with httpx.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            try:
                docs_pages = self._fetch_docs_pages(client, docs_pages_limit)
            except Exception as exc:
                docs_error = str(exc)

            try:
                forum_topics = fetch_discourse_topic_documents(
                    client, "https://precice.discourse.group", topics_limit=forum_topics_limit
                )
            except Exception as exc:
                forum_error = str(exc)

        chunks = [
            c.to_dict()
            for c in (
                build_html_chunks(docs_pages, "documentation", "documentation-website")
                + build_forum_chunks(forum_topics)
            )
        ]

        if not chunks:
            previous = self._read_kb()
            if previous:
                return {
                    "status": "warning",
                    "message": "No new content fetched. Keeping previous KB data.",
                    "kb_file": str(self.kb_file),
                    "documents_ingested": 0,
                    "docs_pages": 0,
                    "forum_topics": 0,
                    "docs_error": docs_error,
                    "forum_error": forum_error,
                }

            return {
                "status": "error",
                "message": "Unable to fetch docs/forum content and no existing KB was found.",
                "kb_file": str(self.kb_file),
                "documents_ingested": 0,
                "docs_pages": 0,
                "forum_topics": 0,
                "docs_error": docs_error,
                "forum_error": forum_error,
            }

        categories = sorted({c["category"] for c in chunks})
        kb_store.write_lexical_store(self.kb_file, chunks, categories)

        return {
            "status": "ok",
            "kb_file": str(self.kb_file),
            "documents_ingested": len({c["doc_id"] for c in chunks}),
            "docs_pages": len({c["doc_id"] for c in chunks if c["category"] == "documentation"}),
            "forum_topics": len({c["doc_id"] for c in chunks if c["category"] == "forum"}),
            "docs_error": docs_error,
            "forum_error": forum_error,
        }

    def query(self, question: str, top_k: int = 5, category: str | None = None) -> dict[str, object]:
        payload = self._read_kb()
        if not payload:
            return {
                "status": "error",
                "message": "Knowledge base is empty. Run ingestion first.",
            }

        schema_error = self._schema_error(payload)
        if schema_error:
            return {"status": "error", "message": schema_error}

        chunks = payload.get("chunks", [])
        if not isinstance(chunks, list) or not chunks:
            return {
                "status": "error",
                "message": "Knowledge base has no chunks. Run ingestion first.",
            }

        if category:
            chunks = [c for c in chunks if isinstance(c, dict) and c.get("category") == category]
            if not chunks:
                return {
                    "status": "error",
                    "message": f"No lexical chunks found for category '{category}'.",
                }

        query_terms = _tokenize(question)
        if not query_terms:
            return {
                "status": "error",
                "message": "Query is empty after tokenization.",
            }

        scored = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            text = f"{chunk.get('title', '')}\n{' '.join(chunk.get('section_path', []))}\n{chunk.get('text', '')}"
            score = _bm25_like_score(query_terms, _tokenize(text))
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_chunks = scored[:top_k]

        return {
            "status": "ok",
            "updated_at": payload.get("updated_at", "unknown"),
            "results": [_result_from_chunk(chunk, round(score, 4)) for score, chunk in top_chunks],
        }

    def sync_from_release(self, github_token: str | None = None) -> dict[str, object]:
        """Sync kb_file from the kb-latest Release's kb-lexical.json asset.

        The release is the source of truth: the local copy is trusted as-is
        for RELEASE_ASSET_MAX_AGE_HOURS (every 4 days, matching
        kb-ingest.yml's publish cadence — kb-ingest.yml republishes every
        category unconditionally on every run, so once that window elapses
        the asset is always re-downloaded, old file deleted first). A cached
        file with an incompatible schema is re-downloaded immediately instead
        of waiting out the window. Falls back to a hard error if there's no
        asset and no cached file, letting the caller decide whether to fall
        back to a live crawl.
        """
        repo = os.environ.get("PRECICE_AI_GITHUB_REPO", _DEFAULT_GITHUB_REPO)
        cached = self._read_kb()
        return sync_release_asset(
            local_path=self.kb_file,
            asset_name="kb-lexical.json",
            repo=repo,
            tag=_RELEASE_TAG,
            github_token=github_token,
            force=bool(cached) and self._schema_error(cached) is not None,
        )

    def query_with_optional_live_refresh(
        self,
        question: str,
        top_k: int = 5,
        category: str | None = None,
        github_token: str | None = None,
        refresh_if_older_than_hours: int = 24,
    ) -> dict[str, object]:
        sync_result = self.sync_from_release(github_token=github_token)

        if sync_result.get("status") == "error":
            # No release asset reachable and nothing cached locally — fall
            # back to the live docs/forum crawl as a last resort.
            payload = self._read_kb()
            if self._is_stale(payload, refresh_if_older_than_hours):
                ingest_result = self.ingest_precice_sources(
                    docs_pages_limit=10,
                    forum_topics_limit=None,
                )
                ingest_status = ingest_result.get("status")
                # "ok" = fresh data written; "warning" = kept old data — both allow querying.
                # On hard failure with no existing KB, surface the error.
                if ingest_status == "error" and not self._read_kb():
                    return {
                        "status": "error",
                        "message": (
                            "Could not sync the lexical KB release, fetch docs/forum live, "
                            f"or find a cached KB. Sync error: {sync_result.get('message', '')}; "
                            f"live fetch error: {ingest_result.get('message', '')}"
                        ),
                    }

        return self.query(question=question, top_k=top_k, category=category)

    def kb_status(self) -> dict[str, object]:
        payload = self._read_kb()
        freshness = _freshness_details(
            self.kb_file,
            fallback_checked_at=payload.get("updated_at") if isinstance(payload, dict) else None,
        )
        if not payload:
            return {
                "status": "empty",
                "kb_file": str(self.kb_file),
                "message": "No ingested data yet.",
                **freshness,
            }

        chunks = payload.get("chunks", [])
        schema_error = self._schema_error(payload)
        return {
            "status": "incompatible" if schema_error else "ok",
            "kb_file": str(self.kb_file),
            "updated_at": payload.get("updated_at", "unknown"),
            "schema_version": payload.get("schema_version"),
            "chunks": len(chunks) if isinstance(chunks, list) else 0,
            **({"message": schema_error} if schema_error else {}),
            **freshness,
        }

    @staticmethod
    def _schema_error(payload: dict[str, object]) -> str | None:
        if payload.get("schema_version") == SCHEMA_VERSION:
            return None
        return (
            f"The lexical KB has schema_version {payload.get('schema_version')!r} (legacy or "
            f"incompatible); this version of precice-ai needs {SCHEMA_VERSION}. {REINGEST_HINT}"
        )

    def _fetch_docs_pages(self, client: httpx.Client, pages_limit: int) -> list[tuple[str, str]]:
        response = client.get(DOCS_START_URL)
        response.raise_for_status()

        tree = html.fromstring(response.text)
        links = tree.xpath("//a[@href]/@href")

        candidates: list[str] = []
        for link in links:
            normalized = _normalize_url(DOCS_START_URL, link)
            if not normalized:
                continue
            if not normalized.startswith(DOCS_START_URL):
                continue
            if any(x in normalized for x in ["#", "?", "mailto:", "/tag/", "/search"]):
                continue
            candidates.append(normalized)

        unique_urls = _dedupe_keep_order(candidates)
        selected_urls = unique_urls[:pages_limit]

        pages: list[tuple[str, str]] = []
        for url in selected_urls:
            try:
                page = client.get(url)
                page.raise_for_status()
                pages.append((url, page.text))
            except Exception:
                continue
        return pages

    def _read_kb(self) -> dict[str, object] | None:
        if not self.kb_file.exists():
            return None
        try:
            data = json.loads(self.kb_file.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _is_stale(self, payload: dict[str, object] | None, max_age_hours: int) -> bool:
        if not payload:
            return True
        if self._schema_error(payload):
            return True
        updated_at = payload.get("updated_at")
        if not isinstance(updated_at, str):
            return True
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        return age_hours > max_age_hours


def _result_from_chunk(chunk: dict, score: float) -> dict[str, object]:
    """Search-hit shape shared by the lexical and vector stores. `text` is the
    full chunk (never truncated); ids let callers expand to neighbouring chunks
    (doc_id + chunk_index) or merge hits from both stores (chunk_id)."""
    return {
        "score": score,
        "chunk_id": chunk.get("chunk_id", ""),
        "doc_id": chunk.get("doc_id", ""),
        "chunk_index": chunk.get("chunk_index", 0),
        "chunk_count": chunk.get("chunk_count", 1),
        "title": chunk.get("title", ""),
        "section_path": chunk.get("section_path", []),
        "url": chunk.get("url", ""),
        "source": chunk.get("source", ""),
        "category": chunk.get("category", ""),
        "updated_at": chunk.get("updated_at"),
        "extra": chunk.get("extra", {}),
        "text": chunk.get("text", ""),
    }


def _normalize_url(base: str, href: str) -> str | None:
    if href.startswith("javascript:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return base.rstrip("/") + href
    return base.rstrip("/") + "/" + href


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]{2,}", text.lower())


def _bm25_like_score(query_terms: list[str], doc_terms: list[str]) -> float:
    if not query_terms or not doc_terms:
        return 0.0
    doc_len = len(doc_terms)
    if doc_len == 0:
        return 0.0
    tf: dict[str, int] = {}
    for term in doc_terms:
        tf[term] = tf.get(term, 0) + 1
    score = 0.0
    for term in query_terms:
        freq = tf.get(term, 0)
        if freq == 0:
            continue
        score += (freq / (freq + 1.2 * (0.25 + 0.75 * (doc_len / 1000.0)))) * (1.0 + math.log1p(freq))
    return score


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


_now_iso = kb_store.now_iso


# ---------------------------------------------------------------------------
# Vector knowledge base (semantic search via pre-built embeddings)
# ---------------------------------------------------------------------------

_RELEASE_TAG = "kb-latest"
_DEFAULT_GITHUB_REPO = "vaibhavd2103/precice-ai"

# Must match the category keys in kb_sources.json and the asset names the
# kb-ingest.yml workflow uploads (kb-embeddings-<category>.npz), one per
# category, so a changed category can be re-fetched without touching the rest.
CATEGORIES = list(SCHEMA_CATEGORIES)


def _asset_name(category: str) -> str:
    return f"kb-embeddings-{category}.npz"


def _find_kb_sources_config() -> Path | None:
    env = os.environ.get("PRECICE_AI_KB_SOURCES")
    if env:
        candidate = Path(env)
        return candidate if candidate.exists() else None
    candidate = Path(__file__).resolve().parents[2] / "kb_sources.json"
    return candidate if candidate.exists() else None


class VectorKnowledgeBase:
    """Downloads pre-built per-category .npz embedding archives from a GitHub
    Release and answers semantic queries by cosine-similarity search (pure
    NumPy, no server). Each category can be refreshed independently."""

    def __init__(self, store_dir: Path | None = None) -> None:
        self._dir = store_dir or _get_kb_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._npz_files = {cat: self._dir / _asset_name(cat) for cat in CATEGORIES}
        # In-memory cache — populated lazily per category on first query
        self._embeddings: dict[str, object] = {}   # category -> np.ndarray (N, D)
        self._chunks: dict[str, list[dict[str, str | int]]] = {}

    # ------------------------------------------------------------------
    # Ingest: download release assets, one per category
    # ------------------------------------------------------------------

    def download_from_release(
        self, github_token: str | None = None, category: str | None = None
    ) -> dict[str, object]:
        """Sync each category's .npz from the kb-latest Release.

        The release is the source of truth: each category's local file is
        trusted for RELEASE_ASSET_MAX_AGE_HOURS (every 4 days) after the
        last check, then always re-downloaded (old file deleted first) once
        that window elapses, since kb-ingest.yml republishes every category
        unconditionally on every run. If no asset exists yet for a category
        and there's no local copy either, falls back to building it locally.
        """
        categories = [category] if category else CATEGORIES
        repo = os.environ.get("PRECICE_AI_GITHUB_REPO", _DEFAULT_GITHUB_REPO)

        per_category: dict[str, object] = {}
        any_ok = False
        for cat in categories:
            local = self._npz_files[cat]
            # A cached file in an older schema is useless: skip the trust
            # window and fetch the release copy right away.
            stale_schema = local.exists() and kb_store.check_npz_compat(local) is not None
            result = sync_release_asset(
                local_path=local,
                asset_name=_asset_name(cat),
                repo=repo,
                tag=_RELEASE_TAG,
                github_token=github_token,
                force=stale_schema,
            )
            if result.get("status") == "error":
                # No release asset published yet and nothing cached locally —
                # build this category locally instead of failing outright.
                result = self._build_category_locally(cat)
            elif str(result.get("action", "")).startswith("downloaded"):
                # File on disk was replaced (fresh 96h cycle, or genuinely
                # changed content) — drop the in-memory cache so the next
                # query reloads from the fresh file.
                self._embeddings.pop(cat, None)
                self._chunks.pop(cat, None)

            if result.get("status") == "ok" and local.exists():
                problem = kb_store.check_npz_compat(local)
                if problem:
                    result = {
                        "status": "error",
                        "message": (
                            f"{problem} The published kb-latest release still holds assets in the "
                            "old format — run the kb-ingest.yml workflow to republish them, or "
                            "rebuild locally with `precice-ai kb rebuild`."
                        ),
                    }

            per_category[cat] = result
            if result.get("status") == "ok":
                any_ok = True

        # The manifest is advisory (freshness/counts); never fail a sync over it.
        manifest_result = sync_release_asset(
            local_path=self._dir / kb_store.MANIFEST_NAME,
            asset_name=kb_store.MANIFEST_NAME,
            repo=repo,
            tag=_RELEASE_TAG,
            github_token=github_token,
        )

        return {
            "status": "ok" if any_ok else "error",
            "categories": per_category,
            "manifest": manifest_result,
        }

    def _build_category_locally(self, category: str) -> dict[str, object]:
        """Fallback for when no GitHub Release asset exists yet for a category.

        Runs the same canonical build the kb-ingest.yml workflow uses
        (precice_ai.kb.rebuild) for just this category and saves the npz into
        the local kb_store. Needs kb_sources.json (shipped in the source
        checkout) and an embedding API key; otherwise degrades to an
        explanatory error.
        """
        config_path = _find_kb_sources_config()
        if not config_path:
            return {
                "status": "error",
                "message": (
                    f"No GitHub Release asset found for category '{category}' and kb_sources.json "
                    "is not available to build it on the fly. Either wait for the scheduled "
                    "kb-ingest.yml Action to publish a release, trigger it manually "
                    "(`gh workflow run kb-ingest.yml`), or run this MCP server from a full clone "
                    "of the precice-ai repo."
                ),
            }
        if not (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("BLABLADOR_API_KEY")):
            return {
                "status": "error",
                "message": (
                    f"No GitHub Release asset found for category '{category}'. A local build "
                    "was attempted but neither OPENROUTER_API_KEY nor BLABLADOR_API_KEY is set — "
                    "embedding requires an OpenAI-compatible API key."
                ),
            }

        from precice_ai.kb.rebuild import rebuild

        output_path = self._npz_files[category]
        try:
            rebuild(
                self._dir,
                [category],
                config_path=config_path,
                github_token=os.environ.get("GITHUB_TOKEN"),
                finalize=False,
            )
        except (Exception, SystemExit) as exc:
            return {"status": "error", "message": f"Local build for '{category}' failed: {exc}"}

        kb_store.write_local_meta(output_path)
        self._embeddings.pop(category, None)
        self._chunks.pop(category, None)
        return {
            "status": "ok",
            "npz_file": str(output_path),
            "size_mb": round(output_path.stat().st_size / 1_048_576, 2),
            "built_locally": True,
        }

    def is_available(self, category: str | None = None) -> bool:
        if category:
            return self._npz_files[category].exists()
        return any(f.exists() for f in self._npz_files.values())

    def status(self) -> dict[str, object]:
        from precice_ai.core.embedding import configured_model

        manifest = kb_store.read_manifest(self._dir)
        categories: dict[str, object] = {}
        for cat, npz_file in self._npz_files.items():
            freshness = _freshness_details(
                npz_file,
                fallback_checked_at=(manifest or {}).get("categories", {}).get(cat, {}).get("built_at"),
            )
            if not npz_file.exists():
                categories[cat] = {
                    "status": "empty",
                    "message": "No embeddings downloaded yet.",
                    **freshness,
                }
                continue
            mtime = datetime.fromtimestamp(npz_file.stat().st_mtime, tz=timezone.utc)
            size_mb = npz_file.stat().st_size / 1_048_576
            loaded = cat in self._chunks
            problem = kb_store.check_npz_compat(npz_file, configured_model())
            try:
                meta = kb_store.read_npz_meta(npz_file) or {}
            except Exception:
                meta = {}
            categories[cat] = {
                "status": "incompatible" if problem else "ok",
                **({"message": problem} if problem else {}),
                "npz_file": str(npz_file),
                "size_mb": round(size_mb, 2),
                "downloaded_at": mtime.isoformat().replace("+00:00", "Z"),
                "schema_version": meta.get("schema_version"),
                "embedding_model": meta.get("model"),
                "chunks": meta.get("count"),
                "chunks_in_memory": len(self._chunks[cat]) if loaded else None,
                **freshness,
            }

        summary = (
            {
                "schema_version": manifest.get("schema_version"),
                "built_at": manifest.get("built_at"),
                "model": manifest.get("model"),
                "dim": manifest.get("dim"),
                "totals": manifest.get("totals"),
            }
            if manifest
            else None
        )
        if not any(npz_file.exists() for npz_file in self._npz_files.values()):
            return {"status": "empty", "message": "No embeddings downloaded yet.", "categories": categories}
        return {"status": "ok", "manifest": summary, "categories": categories}

    # ------------------------------------------------------------------
    # Query: embed question → cosine similarity, merged across categories
    # ------------------------------------------------------------------

    def query(self, question: str, top_k: int = 5, category: str | None = None) -> dict[str, object]:
        try:
            import numpy as np
        except ImportError:
            return {"status": "error", "message": "numpy is required: pip install numpy"}

        from precice_ai.core.embedding import configured_model, embed_query

        categories = [category] if category else CATEGORIES
        available = [cat for cat in categories if self._npz_files[cat].exists()]
        if not available:
            return {
                "status": "error",
                "message": "Vector KB not available. Run kb_ingest_precice_data first.",
            }

        # Lazy-load embeddings for any category not yet cached in memory. The
        # schema version and embedding model are verified here, so a stale or
        # mismatched store fails loudly instead of returning bad results.
        model = configured_model()
        for cat in available:
            if cat not in self._embeddings or cat not in self._chunks:
                try:
                    embeddings, chunks, _ = kb_store.read_vector_store(self._npz_files[cat], expected_model=model)
                except KBFormatError as exc:
                    return {"status": "error", "message": str(exc)}
                except Exception as exc:
                    return {"status": "error", "message": f"Failed to load embeddings for {cat}: {exc}"}
                self._embeddings[cat] = embeddings
                self._chunks[cat] = chunks

        # Embed the query through the OpenAI-compatible embeddings API
        # (OPENROUTER_API_KEY / BLABLADOR_API_KEY, optional EMBEDDING_BASE_URL
        # / EMBEDDING_MODEL). Must use the same model the .npz was built with.
        try:
            q_vec = np.array(embed_query(question), dtype=np.float32)
        except Exception as exc:
            return {"status": "error", "message": f"Embedding error: {exc}"}

        q_norm = float(np.linalg.norm(q_vec))
        if q_norm == 0:
            return {"status": "error", "message": "Query embedding is a zero vector."}

        # Merge embeddings/chunks across all requested categories, then rank globally
        emb = np.concatenate([self._embeddings[cat] for cat in available], axis=0)
        chunks: list[dict] = []
        for cat in available:
            chunks.extend(self._chunks[cat])

        if emb.shape[1] != q_vec.shape[0]:
            return {
                "status": "error",
                "message": (
                    f"Embedding dimension mismatch: stored vectors are {emb.shape[1]}-dim "
                    f"but the query embedding is {q_vec.shape[0]}-dim. {REINGEST_HINT}"
                ),
            }

        norms = np.linalg.norm(emb, axis=1)
        scores = (emb @ q_vec) / (norms * q_norm + 1e-9)
        top_idx = list(map(int, np.argsort(scores)[::-1][:top_k]))

        return {
            "status": "ok",
            "results": [_result_from_chunk(chunks[i], round(float(scores[i]), 4)) for i in top_idx],
        }


def sync_kb_from_release(
    *,
    category: str | None = None,
    github_token: str | None = None,
    skip_lexical: bool = False,
    skip_vector: bool = False,
) -> dict[str, object]:
    """Sync the local KB (vector + lexical) from the kb-latest GitHub Release.

    Single source of truth for KB ingestion — used by the `kb ingest` CLI
    command, the automatic first-run download in `setup`/`bootstrap`, and
    the MCP server's own startup bootstrap (see `precice_ai/server.py`).
    Cheap to call repeatedly: `sync_release_asset` trusts a cached asset
    as-is for RELEASE_ASSET_MAX_AGE_HOURS, so a fresh local KB means no
    network call at all.
    """
    token = github_token or os.environ.get("GITHUB_TOKEN")
    result: dict[str, object] = {}
    if not skip_vector:
        result["vector"] = VectorKnowledgeBase().download_from_release(github_token=token, category=category)
    if not skip_lexical:
        result["lexical"] = KnowledgeBaseService().sync_from_release(github_token=token)
    return result
