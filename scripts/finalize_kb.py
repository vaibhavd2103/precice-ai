"""Derive the lexical store (kb-lexical.json) and kb-manifest.json from the
kb-embeddings-<category>.npz files in a directory, then validate everything.

Used by the kb-ingest.yml workflow after the changed categories were rebuilt
and the unchanged ones were fetched back from the release. Because the lexical
store is generated from the npz files, both stores carry identical chunks and
chunk_ids by construction.

    python scripts/finalize_kb.py --dir . --lexical-name kb-lexical.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precice_ai.kb import store
from precice_ai.kb.validate import print_report, validate_directory


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", type=Path, default=Path("."))
    p.add_argument("--lexical-name", default="kb-lexical.json")
    args = p.parse_args()

    manifest = store.finalize_store(args.dir, lexical_name=args.lexical_name)
    print(json.dumps(manifest, indent=2))
    report = validate_directory(args.dir, lexical_name=args.lexical_name)
    print_report(report)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
