"""
Colonees Tool Providers

Tool providers are stateful containers that expose @tool-decorated functions
to specialist agents. They hold shared state (base dirs, API keys, etc.) and
group related tools into a single instantiable object.

Specialists pull tool methods off a provider instance and pass them directly
into Agent(tools=[...]).
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)


class ToolProvider(ABC):
    """
    Base class for tool providers.

    Instantiated once per specialist agent. Its @tool-decorated methods are
    passed directly into Agent(tools=[...]).
    """

    def __init__(self, session_manager, agent_id: str):
        self.session_manager = session_manager
        self.agent_id = agent_id

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return the capability strings this provider covers."""
        pass
