"""
Colonees Core Platform Components
Agent swarm core components — The Kubernetes + OS for AI Agents
"""

from .platform import ColoneesPlatform
from .config import CologeesConfig
from .workflow_orchestrator import ColoneesSupervisorAgent
from ..agents.agent_directory import AgentDirectory, AgentMetadata, AgentType, AgentStatus
from ..agents.agent_manager import CologeesAgentManager
from .safety_enforcer import SafetyEnforcer

__all__ = [
    "ColoneesPlatform",
    "CologeesConfig",
    "CologeesAgentManager",
    "ColoneesSupervisorAgent",
    "AgentDirectory",
    "AgentMetadata",
    "AgentType",
    "AgentStatus",
    "SafetyEnforcer"
]

# Backward-compat aliases
GALOSPlatform = ColoneesPlatform
GALOSConfig = CologeesConfig
GALOSAgentManager = CologeesAgentManager
GALOSSupervisorAgent = ColoneesSupervisorAgent