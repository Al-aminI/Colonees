"""
Research tools.

Plain strands_tools functions re-exported so specialists can import
from a consistent location.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def get_research_tools() -> List:
    """Return research tool callables for use in Agent(tools=[...])."""
    try:
        from strands_tools import http_request
        return [http_request]
    except ImportError:
        logger.warning("strands_tools not available — research tools disabled")
        return []
