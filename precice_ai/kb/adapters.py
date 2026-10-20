"""Discover and check out the repos behind the 'adapters' KB category.

The category's repo list is not hardcoded: it is read from the .gitmodules
file of precice/precice.github.io, which imports every adapter / tooling repo
whose docs are rendered on precice.org. Every submodule listed there is
ingested except the ones in EXCLUDED_SUBMODULES (the tutorials repo already
has its own 'tutorials' category).

Only the repo-root README.md and everything under docs/ are checked out
(sparse, shallow, blob-filtered clone), and only those files are ingested.
"""

from __future__ import annotations

import configparser
import json
import re
import subprocess
import sys
from pathlib import Path

import httpx

CATEGORY = "adapters"
USER_AGENT = "precice-ai-mcp/1.0 (+https://github.com/precice)"

EXCLUDED_SUBMODULES = {"tutorials"}

INCLUDE_PATHS = ["README.md", "docs"]

MANIFEST_NAME = "manifest.json"

_GITHUB_URL = re.compile(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$")


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def category_config(config: dict) -> dict:
    cat_config = config.get("categories", {}).get(CATEGORY)
    if cat_config is None:
        raise SystemExit(f"Category '{CATEGORY}' missing from kb_sources.json")
    return cat_config


def read_gitmodules(cat_config: dict, gitmodules_file: str | Path | None = None) -> str:
    """Return .gitmodules text from a local checkout, or fetch it from GitHub."""
    if gitmodules_file:
        return Path(gitmodules_file).read_text(encoding="utf-8")
    repo = cat_config["gitmodules_repo"]
    branch = cat_config.get("gitmodules_branch", "master")
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/.gitmodules"
    response = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_gitmodules(text: str) -> list[dict[str, str | None]]:
    """Return [{name, repo, branch}] for every included GitHub submodule."""
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.read_string("\n".join(line.strip() for line in text.splitlines()))

    repos: list[dict[str, str | None]] = []
    for section in parser.sections():
        match = re.fullmatch(r'submodule\s+"(.+)"', section)
        if not match:
            continue
        name = match.group(1)
        path = parser.get(section, "path", fallback=name)
        short_name = path.rstrip("/").split("/")[-1]
        if name in EXCLUDED_SUBMODULES or short_name in EXCLUDED_SUBMODULES:
            _log(f"  skipping excluded submodule: {name}")
            continue

        url_match = _GITHUB_URL.search(parser.get(section, "url", fallback=""))
        if not url_match:
            _log(f"  skipping non-GitHub submodule: {name}")
            continue
        repos.append(
            {
                "name": short_name,
                "repo": f"{url_match.group(1)}/{url_match.group(2)}",
                "branch": parser.get(section, "branch", fallback=None),
            }
        )
    return repos


def _git(*args: str, timeout: int = 300) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True, timeout=timeout)
    return result.stdout.strip()


def checkout(repos: list[dict[str, str | None]], dest: Path) -> list[dict[str, str]]:
    """Sparse-clone README.md + docs/ of each repo into dest; return the manifest."""
    dest.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for entry in repos:
        local_dir = dest / str(entry["name"])
        clone_cmd = ["clone", "--depth", "1", "--filter=blob:none", "--no-checkout"]
        if entry["branch"]:
            clone_cmd += ["-b", str(entry["branch"])]
        clone_cmd += [f"https://github.com/{entry['repo']}.git", str(local_dir)]
        try:
            _git(*clone_cmd)
            _git("-C", str(local_dir), "sparse-checkout", "set", "--no-cone",
                 *[f"/{p}" if p.endswith(".md") else f"/{p}/" for p in INCLUDE_PATHS])
            _git("-C", str(local_dir), "checkout")
            branch = _git("-C", str(local_dir), "rev-parse", "--abbrev-ref", "HEAD")
        except subprocess.CalledProcessError as exc:
            _log(f"  warning: failed to check out {entry['repo']}: {exc.stderr.strip()}")
            continue
        _log(f"  checked out {entry['repo']}@{branch}")
        manifest.append(
            {"name": str(entry["name"]), "repo": str(entry["repo"]), "branch": branch, "dir": str(local_dir)}
        )

    if not manifest:
        raise SystemExit("No adapter repos could be checked out.")
    return manifest


def checkout_all(config: dict, dest: Path, gitmodules_file: str | Path | None = None) -> Path:
    """Discover repos from .gitmodules, check them out into dest, and write
    dest/manifest.json. Returns the manifest path."""
    repos = parse_gitmodules(read_gitmodules(category_config(config), gitmodules_file))
    manifest = checkout(repos, dest)
    manifest_path = dest / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def load_manifest(path: str | Path) -> list[dict[str, str]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def signature(manifest: list[dict[str, str]]) -> str:
    """Content signature: git object ids of each repo's README.md and docs/.

    Like kb_state.py's tree hashes, this only changes when the ingested
    files change, not on unrelated commits. Adding/removing a submodule
    changes the repo list and therefore the signature too.
    """
    parts: list[str] = []
    for entry in sorted(manifest, key=lambda e: e["repo"]):
        hashes = []
        for rel_path in INCLUDE_PATHS:
            try:
                hashes.append(_git("-C", entry["dir"], "rev-parse", f"HEAD:{rel_path}"))
            except subprocess.CalledProcessError:
                hashes.append("none")
        parts.append(f"{entry['repo']}@{','.join(hashes)}")
    return "+".join(parts)


def render_sources(config: dict, manifest: list[dict[str, str]]) -> list[dict]:
    """Source descriptors for builder.build_markdown_chunks: precice.org URLs
    for docs pages with a permalink (rendered on the website), GitHub blob
    URLs otherwise. title_prefix keeps the many README.md files apart."""
    cat_config = category_config(config)
    base_url = config.get("base_url", "https://precice.org")
    return [
        {
            "label": f"{CATEGORY}-{entry['name']}",
            "path": entry["dir"],
            "url_mode": "permalink_or_github",
            "url_base": f"https://github.com/{entry['repo']}/blob/{entry['branch']}",
            "website_base": base_url,
            "title_prefix": entry["name"],
            "include_paths": INCLUDE_PATHS,
            "exclude_patterns": cat_config.get("exclude_patterns", []),
        }
        for entry in manifest
    ]
