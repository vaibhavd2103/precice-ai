"""Rebuild both KB stores (vector npz + lexical JSON + manifest) from scratch in the canonical chunk format. See precice_ai/kb/rebuild.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from precice_ai.kb.rebuild import main

if __name__ == "__main__":
    main()
