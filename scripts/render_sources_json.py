"""Render the --sources-json argument for build_embeddings.py from kb_sources.json.

Resolves each category's configured {repo, checkout_path} sources to local
checkout directories (as laid out by the workflow) and picks a URL mode:
  - "website" for precice/precice.github.io (permalink-based precice.org URLs)
  - "github" for any other repo (GitHub blob URLs on its configured branch)

Usage:
    python scripts/render_sources_json.py --config kb_sources.json --category documentation \
        --checkout-dir "precice/precice.github.io=precice-docs" \
        --checkout-dir "precice/precice=precice-core"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

WEBSITE_REPO = "precice/precice.github.io"


def render(config: dict, category: str, checkout_map: dict[str, str]) -> list[dict[str, object]]:
    cat_config = config.get("categories", {}).get(category)
    if cat_config is None:
        raise SystemExit(f"Unknown category: {category}")

    base_url = config.get("base_url", "https://precice.org")
    exclude_patterns = cat_config.get("exclude_patterns", [])

    sources: list[dict[str, object]] = []
    for source in cat_config.get("sources", []):
        repo = source["repo"]
        checkout_path = source.get("checkout_path", "")
        local_dir = checkout_map.get(repo)
        if not local_dir:
            raise SystemExit(f"No --checkout-dir given for repo {repo}")

        local_path = str(Path(local_dir) / checkout_path) if checkout_path else local_dir

        if repo == WEBSITE_REPO:
            sources.append(
                {
                    "label": f"{category}-website",
                    "path": local_path,
                    "url_mode": "website",
                    "url_base": base_url,
                    "exclude_patterns": exclude_patterns,
                }
            )
        else:
            branch = source.get("branch", "main")
            repo_slug = repo.split("/")[-1]
            url_base = f"https://github.com/{repo}/blob/{branch}"
            if checkout_path:
                url_base += f"/{checkout_path}"
            sources.append(
                {
                    "label": f"{category}-{repo_slug}",
                    "path": local_path,
                    "url_mode": "github",
                    "url_base": url_base,
                    "exclude_patterns": exclude_patterns,
                }
            )

    return sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument(
        "--checkout-dir",
        action="append",
        default=[],
        help="repo=local_dir, repeatable",
    )
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    checkout_map: dict[str, str] = {}
    for pair in args.checkout_dir:
        repo, _, local_dir = pair.partition("=")
        if not repo or not local_dir:
            raise SystemExit(f"Invalid --checkout-dir value: {pair!r} (expected repo=local_dir)")
        checkout_map[repo] = local_dir

    sources = render(config, args.category, checkout_map)
    print(json.dumps(sources))


if __name__ == "__main__":
    main()
