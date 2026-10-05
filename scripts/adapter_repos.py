"""Discover, check out, and describe the repos behind the 'adapters' KB category.

The category's repo list is not hardcoded: it is read from the .gitmodules
file of precice/precice.github.io, which imports every adapter / tooling repo
whose docs are rendered on precice.org. Every submodule listed there is
ingested except the ones in EXCLUDED_SUBMODULES (the tutorials repo already
has its own 'tutorials' category).

Only the repo-root README.md and everything under docs/ are checked out
(sparse, shallow, blob-filtered clone), and only those files are ingested.

Subcommands:
    checkout   parse .gitmodules, clone each repo into --dest, write manifest.json
    signature  combined content signature (for kb_state.py check/update)
    sources    --sources-json payload for build_embeddings.py

Usage:
    python scripts/adapter_repos.py checkout --config kb_sources.json \
        --gitmodules-file precice-docs/.gitmodules --dest adapter-repos
    python scripts/adapter_repos.py signature --manifest adapter-repos/manifest.json
    python scripts/adapter_repos.py sources --config kb_sources.json \
        --manifest adapter-repos/manifest.json
"""

from __future__ import annotations

import argparse
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

_GITHUB_URL = re.compile(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$")


def _category_config(config: dict) -> dict:
    cat_config = config.get("categories", {}).get(CATEGORY)
    if cat_config is None:
        raise SystemExit(f"Category '{CATEGORY}' missing from kb_sources.json")
    return cat_config


def read_gitmodules(cat_config: dict, gitmodules_file: str | None) -> str:
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
            print(f"  skipping excluded submodule: {name}", file=sys.stderr)
            continue

        url_match = _GITHUB_URL.search(parser.get(section, "url", fallback=""))
        if not url_match:
            print(f"  skipping non-GitHub submodule: {name}", file=sys.stderr)
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
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True, timeout=timeout
    )
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
            print(f"  warning: failed to check out {entry['repo']}: {exc.stderr.strip()}", file=sys.stderr)
            continue
        print(f"  checked out {entry['repo']}@{branch}", file=sys.stderr)
        manifest.append(
            {"name": str(entry["name"]), "repo": str(entry["repo"]), "branch": branch, "dir": str(local_dir)}
        )

    if not manifest:
        raise SystemExit("No adapter repos could be checked out.")
    return manifest


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


def sources(config: dict, manifest: list[dict[str, str]]) -> list[dict[str, object]]:
    """build_embeddings.py sources: precice.org URLs for docs pages with a
    permalink (rendered on the website), GitHub blob URLs otherwise."""
    cat_config = _category_config(config)
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


def _load_manifest(path: str) -> list[dict[str, str]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_checkout = sub.add_parser("checkout", help="Clone every included submodule repo")
    p_checkout.add_argument("--config", required=True)
    p_checkout.add_argument(
        "--gitmodules-file",
        default=None,
        help="Local .gitmodules; fetched from GitHub when omitted",
    )
    p_checkout.add_argument("--dest", required=True)

    p_sig = sub.add_parser("signature", help="Print the category's content signature")
    p_sig.add_argument("--manifest", required=True)

    p_sources = sub.add_parser("sources", help="Print --sources-json for build_embeddings.py")
    p_sources.add_argument("--config", required=True)
    p_sources.add_argument("--manifest", required=True)

    args = parser.parse_args()

    if args.command == "checkout":
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        text = read_gitmodules(_category_config(config), args.gitmodules_file)
        repos = parse_gitmodules(text)
        dest = Path(args.dest)
        manifest = checkout(repos, dest)
        manifest_path = dest / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(manifest_path)
    elif args.command == "signature":
        print(signature(_load_manifest(args.manifest)))
    elif args.command == "sources":
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        print(json.dumps(sources(config, _load_manifest(args.manifest))))


if __name__ == "__main__":
    main()
