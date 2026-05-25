"""Convenience entry point for running the server from the repo root.

For production / pip-installed usage, prefer:
    python -m precice_ai.server
    precice-ai-server   (after pip install)
"""
from precice_ai.server import main

if __name__ == "__main__":
    main()
