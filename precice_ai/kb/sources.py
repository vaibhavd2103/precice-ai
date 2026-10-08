"""Resolve kb_sources.json into concrete source trees (cloning when needed)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

WEBSITE_REPO = "precice/precice.github.io"


def find_sources_config() -> Path | None:
    env = os.environ.get("PRECICE_AI_KB_SOURCES")
    if env:
        candidate = Path(env)
        return candidate if candidate.exists() else None
    candidate = Path(__file__).resolve().parents[2] / "kb_sources.json"
    return candidate if candidate.exists() else None


def load_sources_config(path: Path | None = None) -> dict:
    path = path or find_sources_config()
    if path is None or not path.exists():
        raise FileNotFoundError(
            "kb_sources.json not found. Pass --config or set PRECICE_AI_KB_SOURCES "
            "(it ships at the root of the precice-ai source checkout)."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def render_sources(config: dict, category: str, checkout_map: dict[str, str]) -> list[dict]:
    """Source descriptors for the Markdown builder: label, path, url_mode,
    url_base, exclude_patterns."""
    cat_config = config.get("categories", {}).get(category)
    if cat_config is None:
        raise SystemExit(f"Unknown category: {category}")

    base_url = config.get("base_url", "https://precice.org")
    exclude_patterns = cat_config.get("exclude_patterns", [])

    sources: list[dict] = []
    for source in cat_config.get("sources", []):
        repo = source["repo"]
        checkout_path = source.get("checkout_path", "")
        local_dir = checkout_map.get(repo)
        if not local_dir:
            raise SystemExit(f"No checkout directory given for repo {repo}")
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
            url_base = f"https://github.com/{repo}/blob/{branch}"
            if checkout_path:
                url_base += f"/{checkout_path}"
            sources.append(
                {
                    "label": f"{category}-{repo.split('/')[-1]}",
                    "path": local_path,
                    "url_mode": "github",
                    "url_base": url_base,
                    "exclude_patterns": exclude_patterns,
                }
            )
    return sources


def clone_category_sources(config: dict, category: str, into: Path, timeout: int = 900) -> dict[str, str]:
    """Sparse-clone the repos a Markdown category needs; returns repo -> dir."""
    checkout_map: dict[str, str] = {}
    for source in config["categories"][category].get("sources", []):
        repo = source["repo"]
        if repo in checkout_map:
            continue
        checkout_path = source.get("checkout_path", "")
        local_dir = into / repo.replace("/", "_")
        cmd = ["git", "clone", "--filter=blob:none", "--no-checkout"]
        if checkout_path:
            cmd.append("--sparse")
        if source.get("branch"):
            cmd += ["-b", source["branch"]]
        cmd += [f"https://github.com/{repo}.git", str(local_dir)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
        if checkout_path:
            subprocess.run(
                ["git", "-C", str(local_dir), "sparse-checkout", "set", checkout_path],
                check=True, capture_output=True, timeout=timeout,
            )
        subprocess.run(["git", "-C", str(local_dir), "checkout"], check=True, capture_output=True, timeout=timeout)
        checkout_map[repo] = str(local_dir)
    return checkout_map
