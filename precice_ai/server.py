import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from precice_ai.core.instructions import SERVER_INSTRUCTIONS
from precice_ai.core.paths import get_env_file_path
from precice_ai.tools import register_all_tools

logger = logging.getLogger(__name__)

# MCP clients (Claude Code, Claude Desktop, etc.) launch this process with
# whatever `env` they're configured with — often empty — and don't source
# shell profiles. Load .env explicitly so OPENROUTER_API_KEY and friends are
# picked up without needing to hand-edit the client's MCP config. Doesn't
# override already-set env vars (e.g. from the client config).
load_dotenv(get_env_file_path())

mcp = FastMCP("preCICE AI", instructions=SERVER_INSTRUCTIONS)
register_all_tools(mcp)


def _bootstrap_kb() -> None:
    """Sync the local KB from the kb-latest GitHub Release before serving.

    Runs on every server start (any agentic client) so tools like
    `kb_query_precice` have an up-to-date local KB without the agent having
    to remember to call `kb_ingest_precice_data` first. Cheap when the KB is
    already fresh (no network call — see sync_kb_from_release), and never
    fatal: if the sync fails (offline, rate-limited, first run with no
    cache), the server still starts and tools fall back to
    `kb_query_precice_live` / a live crawl per the KB decision tree.
    """
    if os.environ.get("PRECICE_AI_SKIP_KB_BOOTSTRAP"):
        return
    try:
        from precice_ai.core.knowledge_base import sync_kb_from_release

        result = sync_kb_from_release()
    except Exception:
        logger.warning("KB bootstrap sync raised an error; continuing without a fresh local KB", exc_info=True)
        return

    for kind in ("vector", "lexical"):
        if isinstance(result.get(kind), dict) and result[kind].get("status") == "error":
            logger.warning("KB bootstrap sync (%s) did not complete cleanly: %s", kind, result[kind])


def main() -> None:
    _bootstrap_kb()
    mcp.run()


if __name__ == "__main__":
    main()
