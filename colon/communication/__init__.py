"""
Colonees Communication
Agent-to-Agent communication protocols and message handling
"""

from .a2a_handler import StrandsA2AMessageHandler
from .mcp_manager import StrandsMCPToolManager

__all__ = ['StrandsA2AMessageHandler', 'StrandsMCPToolManager']