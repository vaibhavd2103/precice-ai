from mcp.server.fastmcp import FastMCP

from tools import register_all_tools


mcp = FastMCP("preCICE AI")


register_all_tools(mcp)


if __name__ == "__main__":
    mcp.run()