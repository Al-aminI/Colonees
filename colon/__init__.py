"""
Colonees - Open-source, production-grade autonomous agent swarm platform.
Hierarchical superagent/specialist architecture — "The Autonomous Agent Swarm Platform".
Domain-agnostic orchestration platform where complex workflows emerge from autonomous agent collaboration.
"""

__version__ = "1.0.0"
__author__ = "Colonees"

from .core.platform import ColoneesPlatform
from .core.config import CologeesConfig
from .agents.agent_directory import AgentDirectory, AgentMetadata, AgentType, AgentStatus
from .memory import CologeesMemoryManager, CologeesSessionManager

__all__ = [
    "ColoneesPlatform",
    "CologeesConfig",
    "AgentDirectory",
    "AgentMetadata",
    "AgentType",
    "AgentStatus",
    "CologeesSessionManager",
    "CologeesMemoryManager"
]