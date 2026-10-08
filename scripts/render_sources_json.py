"""Render the per-category source descriptors (label, path, url_mode, url_base) from kb_sources.json.

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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precice_ai.kb.sources import render_sources as render

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
