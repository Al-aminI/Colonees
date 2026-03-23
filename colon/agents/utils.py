"""
Utility functions for agent creation and tool management
"""

from typing import List, Callable


def extract_tool_metadata(tools: List[Callable]) -> str:
    """
    Extract tool metadata from a list of tool functions
    Returns formatted string for inclusion in system prompts
    
    Args:
        tools: List of tool functions (decorated with @tool)
    
    Returns:
        Formatted string with tool names and descriptions
    """
    tool_descriptions = []
    
    for tool_func in tools:
        tool_name = tool_func.__name__
        tool_doc = tool_func.__doc__ or "No description"
        # Clean up docstring (remove extra whitespace)
        tool_doc_clean = " ".join(tool_doc.split())
        tool_descriptions.append(f"  - {tool_name}: {tool_doc_clean}")
    
    return "\n".join(tool_descriptions) if tool_descriptions else "  No tools available"
