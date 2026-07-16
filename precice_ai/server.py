from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from precice_ai.tools import register_all_tools

# MCP clients (Claude Code, Claude Desktop, etc.) launch this process with
# whatever `env` they're configured with — often empty — and don't source
# shell profiles. Load .env explicitly from the repo root so OPENROUTER_API_KEY
# and friends are picked up without needing to hand-edit the client's MCP
# config. Doesn't override already-set env vars (e.g. from the client config).
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

mcp = FastMCP("preCICE AI")
register_all_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
