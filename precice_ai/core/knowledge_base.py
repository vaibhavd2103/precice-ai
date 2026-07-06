from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import httpx
from lxml import html


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
FORUM_RECENT_URL = "https://precice.discourse.group/latest.json"
USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"


@dataclass
class KBDocument:
    source: str
    url: str
    title: str
    content: str
    updated_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "updated_at": self.updated_at,
        }


class KnowledgeBaseService:
    def __init__(self, kb_file: Path | None = None) -> None:
        self.kb_file = kb_file or _get_kb_dir() / "knowledge_base.json"
        self.kb_file.parent.mkdir(parents=True, exist_ok=True)

    def ingest_precice_sources(
        self,
        docs_pages_limit: int = 20,
        forum_topics_limit: int = 20,
        timeout_seconds: int = 20,
    ) -> dict[str, str | int]:
        docs_documents: list[KBDocument] = []
        forum_documents: list[KBDocument] = []
        docs_error = ""
        forum_error = ""

        with httpx.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            try:
                docs_documents = self._fetch_docs_documents(client, docs_pages_limit)
            except Exception as exc:
                docs_error = str(exc)

            try:
                forum_documents = self._fetch_forum_documents(client, forum_topics_limit)
            except Exception as exc:
                forum_error = str(exc)

        all_documents = docs_documents + forum_documents

        if not all_documents:
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

        payload = {
            "updated_at": _now_iso(),
            "count": len(all_documents),
            "documents": [doc.to_dict() for doc in all_documents],
        }
        self.kb_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        return {
            "status": "ok",
            "kb_file": str(self.kb_file),
            "documents_ingested": len(all_documents),
            "docs_pages": len(docs_documents),
            "forum_topics": len(forum_documents),
            "docs_error": docs_error,
            "forum_error": forum_error,
        }

    def query(self, question: str, top_k: int = 5) -> dict[str, object]:
        payload = self._read_kb()
        if not payload:
            return {
                "status": "error",
                "message": "Knowledge base is empty. Run ingestion first.",
            }

        documents = payload.get("documents", [])
        if not isinstance(documents, list) or not documents:
            return {
                "status": "error",
                "message": "Knowledge base has no documents. Run ingestion first.",
            }

        query_terms = _tokenize(question)
        if not query_terms:
            return {
                "status": "error",
                "message": "Query is empty after tokenization.",
            }

        scored = []
        for doc in documents:
            if not isinstance(doc, dict):
                continue
            text = f"{doc.get('title', '')}\n{doc.get('content', '')}"
            score = _bm25_like_score(query_terms, _tokenize(text))
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_docs = scored[:top_k]

        return {
            "status": "ok",
            "updated_at": payload.get("updated_at", "unknown"),
            "results": [
                {
                    "score": round(score, 4),
                    "source": doc.get("source", "unknown"),
                    "title": doc.get("title", ""),
                    "url": doc.get("url", ""),
                    "snippet": _snippet_for_terms(doc.get("content", ""), query_terms),
                }
                for score, doc in top_docs
            ],
        }

    def query_with_optional_live_refresh(
        self,
        question: str,
        top_k: int = 5,
        refresh_if_older_than_hours: int = 24,
    ) -> dict[str, object]:
        payload = self._read_kb()

        if self._is_stale(payload, refresh_if_older_than_hours):
            ingest_result = self.ingest_precice_sources(
                docs_pages_limit=10,
                forum_topics_limit=10,
            )
            ingest_status = ingest_result.get("status")
            # "ok" = fresh data written; "warning" = kept old data — both allow querying.
            # On hard failure with no existing KB, surface the error.
            if ingest_status == "error" and not self._read_kb():
                return {
                    "status": "error",
                    "message": (
                        "Could not fetch preCICE docs/forum and no cached KB exists. "
                        f"Details: {ingest_result.get('message', '')}"
                    ),
                }

        return self.query(question=question, top_k=top_k)

    def kb_status(self) -> dict[str, object]:
        payload = self._read_kb()
        if not payload:
            return {
                "status": "empty",
                "kb_file": str(self.kb_file),
                "message": "No ingested data yet.",
            }

        documents = payload.get("documents", [])
        return {
            "status": "ok",
            "kb_file": str(self.kb_file),
            "updated_at": payload.get("updated_at", "unknown"),
            "documents": len(documents) if isinstance(documents, list) else 0,
        }

    def _fetch_docs_documents(self, client: httpx.Client, pages_limit: int) -> list[KBDocument]:
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

        docs: list[KBDocument] = []
        for url in selected_urls:
            try:
                page = client.get(url)
                page.raise_for_status()
                doc = _extract_html_document(page.text, url=url, source="precice-docs")
                if doc.content.strip():
                    docs.append(doc)
            except Exception:
                continue

        return docs

    def _fetch_forum_documents(self, client: httpx.Client, topics_limit: int) -> list[KBDocument]:
        response = client.get(FORUM_RECENT_URL)
        response.raise_for_status()

        data = response.json()
        topic_list = data.get("topic_list", {})
        topics = topic_list.get("topics", [])

        docs: list[KBDocument] = []
        for topic in topics[:topics_limit]:
            slug = topic.get("slug")
            topic_id = topic.get("id")
            title = topic.get("title", "")
            last_posted_at = topic.get("last_posted_at") or _now_iso()

            if not slug or not topic_id:
                continue

            topic_url = f"https://precice.discourse.group/t/{slug}/{topic_id}.json"
            try:
                topic_response = client.get(topic_url)
                topic_response.raise_for_status()
                topic_data = topic_response.json()
                post_stream = topic_data.get("post_stream", {})
                posts = post_stream.get("posts", [])
                merged = "\n\n".join(
                    _strip_html(post.get("cooked", ""))
                    for post in posts
                    if isinstance(post, dict)
                )
                if merged.strip():
                    docs.append(
                        KBDocument(
                            source="precice-forum",
                            url=f"https://precice.discourse.group/t/{slug}/{topic_id}",
                            title=title,
                            content=merged,
                            updated_at=last_posted_at,
                        )
                    )
            except Exception:
                continue

        return docs

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
        updated_at = payload.get("updated_at")
        if not isinstance(updated_at, str):
            return True
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        return age_hours > max_age_hours


def _normalize_url(base: str, href: str) -> str | None:
    if href.startswith("javascript:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return base.rstrip("/") + href
    return base.rstrip("/") + "/" + href


def _extract_html_document(raw_html: str, url: str, source: str) -> KBDocument:
    tree = html.fromstring(raw_html)
    title_candidates = tree.xpath("//title/text()")
    title = title_candidates[0].strip() if title_candidates else url

    paragraphs = tree.xpath("//p//text()")
    headings = tree.xpath("//h1//text() | //h2//text() | //h3//text()")

    pieces = [x.strip() for x in headings + paragraphs if x.strip()]
    content = "\n".join(pieces)

    return KBDocument(
        source=source,
        url=url,
        title=title,
        content=content,
        updated_at=_now_iso(),
    )


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value).replace("\n", " ").strip()


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


def _snippet_for_terms(content: str, terms: list[str], size: int = 320) -> str:
    lowered = content.lower()
    for term in terms:
        idx = lowered.find(term)
        if idx >= 0:
            start = max(0, idx - size // 3)
            end = min(len(content), start + size)
            return content[start:end].strip()
    return content[:size].strip()


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Vector knowledge base (semantic search via pre-built embeddings)
# ---------------------------------------------------------------------------

_RELEASE_TAG = "kb-latest"
_DEFAULT_GITHUB_REPO = "vaibhavd2103/precice-ai"
_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "openai/text-embedding-3-small"

# Must match the category keys in kb_sources.json and the asset names the
# kb-ingest.yml workflow uploads (kb-embeddings-<category>.npz), one per
# category, so a changed category can be re-fetched without touching the rest.
CATEGORIES = ["about", "community", "documentation", "tutorials", "forum"]


def _asset_name(category: str) -> str:
    return f"kb-embeddings-{category}.npz"


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
        categories = [category] if category else CATEGORIES
        repo = os.environ.get("PRECICE_AI_GITHUB_REPO", _DEFAULT_GITHUB_REPO)
        headers: dict[str, str] = {}
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        per_category: dict[str, object] = {}
        any_ok = False
        with httpx.Client(follow_redirects=True, timeout=180, headers=headers) as client:
            for cat in categories:
                asset_url = (
                    f"https://github.com/{repo}/releases/download/{_RELEASE_TAG}/{_asset_name(cat)}"
                )
                try:
                    response = client.get(asset_url)
                    response.raise_for_status()
                    self._npz_files[cat].write_bytes(response.content)
                except httpx.HTTPStatusError as exc:
                    per_category[cat] = {
                        "status": "error",
                        "message": f"Failed to download release asset ({exc.response.status_code}): {asset_url}",
                    }
                    continue
                except Exception as exc:
                    per_category[cat] = {"status": "error", "message": str(exc)}
                    continue

                # Invalidate in-memory cache so next query reloads from fresh file
                self._embeddings.pop(cat, None)
                self._chunks.pop(cat, None)
                any_ok = True
                size_mb = self._npz_files[cat].stat().st_size / 1_048_576
                per_category[cat] = {
                    "status": "ok",
                    "npz_file": str(self._npz_files[cat]),
                    "size_mb": round(size_mb, 2),
                }

        return {
            "status": "ok" if any_ok else "error",
            "categories": per_category,
        }

    def is_available(self, category: str | None = None) -> bool:
        if category:
            return self._npz_files[category].exists()
        return any(f.exists() for f in self._npz_files.values())

    def status(self) -> dict[str, object]:
        categories: dict[str, object] = {}
        for cat, npz_file in self._npz_files.items():
            if not npz_file.exists():
                categories[cat] = {"status": "empty", "message": "No embeddings downloaded yet."}
                continue
            mtime = datetime.fromtimestamp(npz_file.stat().st_mtime, tz=timezone.utc)
            size_mb = npz_file.stat().st_size / 1_048_576
            loaded = cat in self._chunks
            categories[cat] = {
                "status": "ok",
                "npz_file": str(npz_file),
                "size_mb": round(size_mb, 2),
                "downloaded_at": mtime.isoformat().replace("+00:00", "Z"),
                "chunks_in_memory": len(self._chunks[cat]) if loaded else None,
            }

        if not any(npz_file.exists() for npz_file in self._npz_files.values()):
            return {"status": "empty", "message": "No embeddings downloaded yet.", "categories": categories}
        return {"status": "ok", "categories": categories}

    # ------------------------------------------------------------------
    # Query: embed question → cosine similarity, merged across categories
    # ------------------------------------------------------------------

    def query(self, question: str, top_k: int = 5, category: str | None = None) -> dict[str, object]:
        try:
            import numpy as np
        except ImportError:
            return {"status": "error", "message": "numpy is required: pip install numpy"}

        try:
            from openai import OpenAI
        except ImportError:
            return {"status": "error", "message": "openai is required: pip install openai"}

        categories = [category] if category else CATEGORIES
        available = [cat for cat in categories if self._npz_files[cat].exists()]
        if not available:
            return {
                "status": "error",
                "message": "Vector KB not available. Run kb_ingest_precice_data first.",
            }

        # Lazy-load embeddings for any category not yet cached in memory
        for cat in available:
            if cat not in self._embeddings or cat not in self._chunks:
                try:
                    data = np.load(self._npz_files[cat], allow_pickle=True)
                    self._embeddings[cat] = data["embeddings"].astype(np.float32)
                    self._chunks[cat] = json.loads(data["chunks"].item())
                except Exception as exc:
                    return {"status": "error", "message": f"Failed to load embeddings for {cat}: {exc}"}

        # Embed the query
        api_key = (
            os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("BLABLADOR_API_KEY")
        )
        if not api_key:
            return {
                "status": "error",
                "message": "Set OPENROUTER_API_KEY (or BLABLADOR_API_KEY) env var for query embedding.",
            }

        base_url = os.environ.get("EMBEDDING_BASE_URL", _DEFAULT_BASE_URL)
        model = os.environ.get("EMBEDDING_MODEL", _DEFAULT_MODEL)

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            resp = client.embeddings.create(input=question, model=model)
            q_vec = np.array(resp.data[0].embedding, dtype=np.float32)
        except Exception as exc:
            return {"status": "error", "message": f"Embedding API error: {exc}"}

        q_norm = float(np.linalg.norm(q_vec))
        if q_norm == 0:
            return {"status": "error", "message": "Query embedding is a zero vector."}

        # Merge embeddings/chunks across all requested categories, then rank globally
        emb = np.concatenate([self._embeddings[cat] for cat in available], axis=0)
        chunks: list[dict[str, str | int]] = []
        for cat in available:
            chunks.extend(self._chunks[cat])

        norms = np.linalg.norm(emb, axis=1)
        scores = (emb @ q_vec) / (norms * q_norm + 1e-9)
        top_idx = list(map(int, np.argsort(scores)[::-1][:top_k]))

        results = []
        for i in top_idx:
            chunk = chunks[i]
            results.append(
                {
                    "score": round(float(scores[i]), 4),
                    "title": chunk.get("title", ""),
                    "url": chunk.get("url", ""),
                    "source": chunk.get("source", "precice-docs"),
                    "category": chunk.get("category", ""),
                    "snippet": str(chunk.get("text", ""))[:400],
                }
            )

        return {"status": "ok", "results": results}
