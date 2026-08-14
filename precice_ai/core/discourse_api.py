from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx


JSON_ACCEPT_HEADER = {"Accept": "application/json"}


@dataclass
class DiscourseTopicDocument:
    title: str
    url: str
    text: str
    updated_at: str


def fetch_discourse_topic_documents(
    client: httpx.Client,
    forum_url: str,
    topics_limit: int | None = None,
) -> list[DiscourseTopicDocument]:
    base_url = forum_url.rstrip("/") + "/"
    categories = _fetch_categories(client, base_url)

    documents: list[DiscourseTopicDocument] = []
    seen_topic_ids: set[int] = set()
    remaining = topics_limit if topics_limit and topics_limit > 0 else None

    for category in categories:
        try:
            for topic in _iter_category_topics(client, base_url, category):
                topic_id = topic.get("id")
                slug = topic.get("slug")
                title = topic.get("title", "")
                last_posted_at = topic.get("last_posted_at") or _now_iso()

                if not isinstance(topic_id, int) or not isinstance(slug, str) or not slug:
                    continue
                if topic_id in seen_topic_ids:
                    continue

                try:
                    merged = _fetch_topic_text(client, base_url, topic_id=topic_id)
                except Exception:
                    continue
                if not merged:
                    continue

                documents.append(
                    DiscourseTopicDocument(
                        title=title,
                        url=urljoin(base_url, f"t/{slug}/{topic_id}"),
                        text=merged,
                        updated_at=last_posted_at,
                    )
                )
                seen_topic_ids.add(topic_id)

                if remaining is not None:
                    remaining -= 1
                    if remaining <= 0:
                        return documents
        except Exception:
            continue

    return documents


def _fetch_categories(client: httpx.Client, base_url: str) -> list[dict]:
    response = client.get(
        urljoin(base_url, "categories.json"),
        params={"include_subcategories": "true"},
        headers=JSON_ACCEPT_HEADER,
    )
    response.raise_for_status()

    data = response.json()
    category_list = data.get("category_list", {})
    categories = category_list.get("categories", [])
    if not isinstance(categories, list):
        return []

    seen_category_ids: set[int] = set()
    result: list[dict] = []
    for category in categories:
        if not isinstance(category, dict):
            continue
        category_id = category.get("id")
        slug = category.get("slug")
        if not isinstance(category_id, int) or not isinstance(slug, str) or not slug:
            continue
        if category.get("read_restricted"):
            continue
        if category_id in seen_category_ids:
            continue
        seen_category_ids.add(category_id)
        result.append(category)

    return result


def _iter_category_topics(client: httpx.Client, base_url: str, category: dict):
    slug = category["slug"]
    category_id = category["id"]
    next_page_url: str | None = urljoin(base_url, f"c/{slug}/{category_id}.json")
    seen_page_urls: set[str] = set()

    while next_page_url:
        normalized_url = _normalize_api_url(base_url, next_page_url)
        if normalized_url in seen_page_urls:
            break
        seen_page_urls.add(normalized_url)

        response = client.get(normalized_url, headers=JSON_ACCEPT_HEADER)
        response.raise_for_status()
        data = response.json()

        topic_list = data.get("topic_list", {})
        topics = topic_list.get("topics", [])
        if isinstance(topics, list):
            for topic in topics:
                if isinstance(topic, dict):
                    yield topic

        more_topics_url = topic_list.get("more_topics_url")
        next_page_url = more_topics_url if isinstance(more_topics_url, str) and more_topics_url.strip() else None


def _fetch_topic_text(client: httpx.Client, base_url: str, *, topic_id: int) -> str:
    response = client.get(
        urljoin(base_url, f"t/{topic_id}.json"),
        headers=JSON_ACCEPT_HEADER,
    )
    response.raise_for_status()
    topic_data = response.json()

    post_stream = topic_data.get("post_stream", {})
    posts = post_stream.get("posts", [])
    stream = post_stream.get("stream", [])

    raw_by_post_id: dict[int, str] = {}
    if isinstance(posts, list):
        for post in posts:
            if not isinstance(post, dict):
                continue
            post_id = post.get("id")
            raw = post.get("raw")
            if isinstance(post_id, int) and isinstance(raw, str) and raw.strip():
                raw_by_post_id[post_id] = raw.strip()

    ordered_post_ids = [post_id for post_id in stream if isinstance(post_id, int)]
    if not ordered_post_ids:
        ordered_post_ids = list(raw_by_post_id.keys())

    text_parts: list[str] = []
    for post_id in ordered_post_ids:
        raw_text = raw_by_post_id.get(post_id)
        if raw_text is None:
            try:
                raw_text = _fetch_post_raw(client, base_url, post_id)
            except Exception:
                continue
        if raw_text:
            text_parts.append(raw_text)

    return "\n\n".join(text_parts).strip()


def _fetch_post_raw(client: httpx.Client, base_url: str, post_id: int) -> str:
    response = client.get(
        urljoin(base_url, f"posts/{post_id}.json"),
        headers=JSON_ACCEPT_HEADER,
    )
    response.raise_for_status()
    data = response.json()
    raw = data.get("raw")
    return raw.strip() if isinstance(raw, str) and raw.strip() else ""


def _normalize_api_url(base_url: str, url_or_path: str) -> str:
    return urljoin(base_url, url_or_path.lstrip("/"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
