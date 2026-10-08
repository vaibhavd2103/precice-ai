"""Validate the local KB stores against the canonical chunk schema and print per-category stats. See precice_ai/kb/validate.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precice_ai.kb.validate import main

if __name__ == "__main__":
    main()
