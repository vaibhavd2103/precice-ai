"""Track per-category ingestion state so the KB workflow only rebuilds
categories whose underlying sources actually changed.

State is persisted in kb_state.json (committed to this repo) as:

    {
      "categories": {
        "about": {"signature": "<repo>@<sha>", "updated_at": "..."},
        "forum": {"signature": "2026-07-01T12:00:00Z", "updated_at": "..."}
      }
    }

A category's "signature" is a stable string derived from its sources
(git commit SHA per {repo, path}, or the latest forum post timestamp).
If the signature differs from what's stored, the category is stale.

CLI usage:
    python scripts/kb_state.py git-sha --repo-dir precice-docs --path content/docs
    python scripts/kb_state.py forum-sig --url https://precice.discourse.group
    python scripts/kb_state.py check --state-file kb_state.json --category docs --signature "a@sha1+b@sha2"
    python scripts/kb_state.py update --state-file kb_state.json --category docs --signature "a@sha1+b@sha2"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"


def git_sha_for_path(repo_dir: Path, rel_path: str) -> str:
    """Latest commit SHA touching rel_path (or HEAD if rel_path is empty)."""
    args = ["git", "-C", str(repo_dir), "log", "-1", "--format=%H"]
    if rel_path:
        args += ["--", rel_path]
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    sha = result.stdout.strip()
    if not sha:
        # No commit touched this exact path (e.g. empty dir) — fall back to HEAD.
        head = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = head.stdout.strip()
    return sha


def forum_signature(forum_url: str, timeout_seconds: int = 20) -> str:
    """Max last_posted_at across recent topics — advances whenever the forum changes."""
    url = forum_url.rstrip("/") + "/latest.json"
    with httpx.Client(timeout=timeout_seconds, headers={"User-Agent": USER_AGENT}) as client:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()

    topics = data.get("topic_list", {}).get("topics", [])
    timestamps = [t.get("last_posted_at") for t in topics if t.get("last_posted_at")]
    return max(timestamps) if timestamps else ""


def load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {"categories": {}}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {"categories": {}}
    if not isinstance(data, dict) or "categories" not in data:
        return {"categories": {}}
    return data


def save_state(state_file: Path, state: dict) -> None:
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_stale(state: dict, category: str, signature: str) -> bool:
    stored = state.get("categories", {}).get(category, {})
    return stored.get("signature") != signature


def update_category(state: dict, category: str, signature: str) -> dict:
    state.setdefault("categories", {})[category] = {
        "signature": signature,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return state


def category_signature(
    config: dict, category: str, checkout_map: dict[str, str]
) -> str:
    """Combined signature for a category: forum timestamp, or repo@path@sha parts joined."""
    cat_config = config.get("categories", {}).get(category)
    if cat_config is None:
        raise SystemExit(f"Unknown category: {category}")

    if cat_config.get("type") == "discourse":
        return forum_signature(cat_config["forum_url"])

    parts: list[str] = []
    for source in cat_config.get("sources", []):
        repo = source["repo"]
        checkout_path = source.get("checkout_path", "")
        local_dir = checkout_map.get(repo)
        if not local_dir:
            raise SystemExit(f"No --checkout-dir given for repo {repo}")
        sha = git_sha_for_path(Path(local_dir), checkout_path)
        parts.append(f"{repo}@{checkout_path}@{sha}")
    return "+".join(parts)


def _parse_checkout_dirs(pairs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for pair in pairs:
        repo, _, local_dir = pair.partition("=")
        if not repo or not local_dir:
            raise SystemExit(f"Invalid --checkout-dir value: {pair!r} (expected repo=local_dir)")
        mapping[repo] = local_dir
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_git = sub.add_parser("git-sha", help="Print latest commit SHA for a path")
    p_git.add_argument("--repo-dir", required=True)
    p_git.add_argument("--path", default="")

    p_forum = sub.add_parser("forum-sig", help="Print forum change signature")
    p_forum.add_argument("--url", required=True)

    p_sig = sub.add_parser("category-signature", help="Print a category's combined signature")
    p_sig.add_argument("--config", required=True)
    p_sig.add_argument("--category", required=True)
    p_sig.add_argument(
        "--checkout-dir",
        action="append",
        default=[],
        help="repo=local_dir, repeatable (one per source repo used by this category)",
    )

    p_check = sub.add_parser("check", help="Exit 0 if stale, 1 if unchanged")
    p_check.add_argument("--state-file", required=True)
    p_check.add_argument("--category", required=True)
    p_check.add_argument("--signature", required=True)

    p_update = sub.add_parser("update", help="Persist a category's new signature")
    p_update.add_argument("--state-file", required=True)
    p_update.add_argument("--category", required=True)
    p_update.add_argument("--signature", required=True)

    args = parser.parse_args()

    if args.command == "git-sha":
        print(git_sha_for_path(Path(args.repo_dir), args.path))
    elif args.command == "forum-sig":
        print(forum_signature(args.url))
    elif args.command == "category-signature":
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        checkout_map = _parse_checkout_dirs(args.checkout_dir)
        print(category_signature(config, args.category, checkout_map))
    elif args.command == "check":
        state = load_state(Path(args.state_file))
        stale = is_stale(state, args.category, args.signature)
        print("stale" if stale else "unchanged")
        sys.exit(0 if stale else 1)
    elif args.command == "update":
        state_file = Path(args.state_file)
        state = load_state(state_file)
        state = update_category(state, args.category, args.signature)
        save_state(state_file, state)


if __name__ == "__main__":
    main()
