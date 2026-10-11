"""Discover, check out, and describe the repos behind the 'adapters' KB category.
See precice_ai/kb/adapters.py.

Subcommands:
    checkout   parse .gitmodules, clone each repo into --dest, write manifest.json
    signature  combined content signature (for kb_state.py check/update)
    sources    source descriptors the Markdown builder would use (for debugging)

Usage:
    python scripts/adapter_repos.py checkout --config kb_sources.json \
        --gitmodules-file precice-docs/.gitmodules --dest adapter-repos
    python scripts/adapter_repos.py signature --manifest adapter-repos/manifest.json
    python scripts/adapter_repos.py sources --config kb_sources.json \
        --manifest adapter-repos/manifest.json

The checked-out repos are built with:
    python scripts/rebuild_kb.py --categories adapters \
        --adapter-manifest adapter-repos/manifest.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precice_ai.kb import adapters


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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

    p_sources = sub.add_parser("sources", help="Print the Markdown builder's source descriptors")
    p_sources.add_argument("--config", required=True)
    p_sources.add_argument("--manifest", required=True)

    args = parser.parse_args()

    if args.command == "checkout":
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        print(adapters.checkout_all(config, Path(args.dest), args.gitmodules_file))
    elif args.command == "signature":
        print(adapters.signature(adapters.load_manifest(args.manifest)))
    elif args.command == "sources":
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        print(json.dumps(adapters.render_sources(config, adapters.load_manifest(args.manifest))))


if __name__ == "__main__":
    main()
