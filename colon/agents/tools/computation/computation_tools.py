"""
Computation tools.

Plain strands_tools functions re-exported so specialists can import
from a consistent location.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def get_computation_tools() -> List:
    """Return computation tool callables for use in Agent(tools=[...])."""
    try:
        from strands_tools import calculator
        return [calculator]
    except ImportError:
        logger.warning("strands_tools not available — computation tools disabled")
        return []
