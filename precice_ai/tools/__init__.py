from mcp.server.fastmcp import FastMCP

from precice_ai.tools.project_tools import register_project_tools
from precice_ai.tools.config_tools import register_config_tools
from precice_ai.tools.log_tools import register_log_tools
from precice_ai.tools.knowledge_tools import register_knowledge_tools


def register_all_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""
    register_project_tools(mcp)
    register_config_tools(mcp)
    register_log_tools(mcp)
    register_knowledge_tools(mcp)
