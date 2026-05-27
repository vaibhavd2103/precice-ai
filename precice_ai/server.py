from mcp.server.fastmcp import FastMCP

from precice_ai.tools import register_all_tools

mcp = FastMCP("preCICE AI")
register_all_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
