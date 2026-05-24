from mcp.server.fastmcp import FastMCP

from tools.project_tools import register_project_tools
from tools.config_tools import register_config_tools
from tools.log_tools import register_log_tools


def register_all_tools(mcp: FastMCP) -> None:
    """
    Register all MCP tools.
    """
    register_project_tools(mcp)
    register_config_tools(mcp)
    register_log_tools(mcp)