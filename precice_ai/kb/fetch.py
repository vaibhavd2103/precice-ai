"""Network fetchers for the GitHub issues/pulls categories."""

from __future__ import annotations

import sys

import httpx

USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"
API_ROOT = "https://api.github.com"

# Automation accounts whose comments are noise (CI reports, dependency bumps, ...).
BOT_LOGINS = {
    "github-actions", "dependabot", "codecov", "codecov-commenter", "pre-commit-ci",
    "sonarcloud", "coveralls", "netlify", "vercel", "stale", "mergify", "renovate",
    "precice-bot",
}


def is_bot_user(user: dict | None) -> bool:
    if not isinstance(user, dict):
        return False
    login = (user.get("login") or "").lower()
    return (
        user.get("type") == "Bot"
        or login.endswith("[bot]")
        or login.endswith("-bot")
        or login in BOT_LOGINS
    )


def _headers(github_token: str | None) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _fetch_items(client: httpx.Client, repo: str, kind: str, items_limit: int) -> list[dict]:
    endpoint = f"{API_ROOT}/repos/{repo}/{'pulls' if kind == 'pulls' else 'issues'}"
    items: list[dict] = []
    page = 1
    while len(items) < items_limit:
        response = client.get(
            endpoint,
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100, "page": page},
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        for entry in batch:
            # The issues endpoint also lists PRs; "pulls" covers those.
            if kind == "issues" and "pull_request" in entry:
                continue
            items.append(entry)
            if len(items) >= items_limit:
                break
        page += 1
    return items


def _fetch_comments(client: httpx.Client, repo: str, number: int, comments_limit: int) -> list[dict]:
    """Human comments only (bots dropped), oldest first, up to comments_limit."""
    collected: list[dict] = []
    page = 1
    try:
        while len(collected) < comments_limit:
            response = client.get(
                f"{API_ROOT}/repos/{repo}/issues/{number}/comments",
                params={"per_page": 100, "page": page},
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            for c in batch:
                if isinstance(c, dict) and not is_bot_user(c.get("user")) and (c.get("body") or "").strip():
                    collected.append(c)
            if len(batch) < 100:
                break
            page += 1
    except Exception as exc:
        print(f"  skip comments for #{number}: {exc}", file=sys.stderr)
    return collected[:comments_limit]


def fetch_github_items(
    repo: str,
    kind: str,
    items_limit: int,
    comments_limit: int,
    github_token: str | None,
    timeout_seconds: int = 20,
) -> list[dict]:
    """Issues or PRs as plain dicts: number, title, url, state, labels, merged,
    closed_at, created_at, updated_at, body, comments=[{body, created_at}]."""
    with httpx.Client(timeout=timeout_seconds, headers=_headers(github_token), follow_redirects=True) as client:
        items = _fetch_items(client, repo, kind, items_limit)
        print(f"Fetched {len(items)} {kind} from {repo}", file=sys.stderr)

        out: list[dict] = []
        for item in items:
            number, url = item.get("number"), item.get("html_url", "")
            if not number or not url:
                continue
            comments = _fetch_comments(client, repo, number, comments_limit)
            out.append(
                {
                    "number": number,
                    "title": item.get("title", ""),
                    "url": url,
                    "state": item.get("state", ""),
                    "labels": [lb.get("name", "") for lb in item.get("labels", []) if isinstance(lb, dict)],
                    "merged": bool(item.get("merged_at")) if kind == "pulls" else None,
                    "closed_at": item.get("closed_at"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "body": "" if is_bot_user(item.get("user")) and kind == "pulls" else (item.get("body") or ""),
                    "comments": [{"body": c.get("body", ""), "created_at": c.get("created_at")} for c in comments],
                }
            )
        return out
