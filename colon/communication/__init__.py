"""
Colonees Communication
Agent-to-Agent communication and MCP server integration
"""

from .a2a_handler import StrandsA2AMessageHandler
from .mcp_manager import MCPManager

__all__ = ["StrandsA2AMessageHandler", "MCPManager"]
