from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import re

import httpx
from lxml import html


BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / "kb_store"
KB_FILE = KB_DIR / "knowledge_base.json"

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
    def __init__(self, kb_file: Path = KB_FILE) -> None:
        self.kb_file = kb_file
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
            ingest_result = self.ingest_precice_sources()
            if ingest_result.get("status") != "ok":
                return {
                    "status": "error",
                    "message": "Failed to refresh knowledge base before query.",
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
    # Remove HTML tags from Discourse "cooked" content.
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
