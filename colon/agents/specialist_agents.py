"""
Colonees Specialist Agents
Colony architecture: Specialists reason and coordinate with Tool Agents
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from strands import Agent

from ..core.model_config import get_model

logger = logging.getLogger(__name__)


class BaseSpecialistAgent(ABC):
    """
    Base class for Specialist Agents following Colonees colony architecture

    PRINCIPLES:
    - Specialists reason and make decisions
    - They have tools available through Strands framework
    - LLM decides when to use which tool
    - Domain expertise with tool access for execution
    """

    def __init__(
        self,
        session_manager,
        agent_id: str,
        specialization: str,
        mcp_manager=None,
    ):
        self.session_manager = session_manager
        self.agent_id = agent_id
        self.specialization = specialization
        self.mcp_manager = mcp_manager
        self.agent = self._create_agent()
        
        # Collaboration statistics
        self.stats = {
            'tasks_completed': 0,
            'tool_calls': 0,
            'successful_operations': 0,
            'failed_operations': 0
        }

    # Each subclass declares its specialist type for MCP scoping.
    # Matches the keys used in MCPManager.add_server(specialist_types=[...]).
    _specialist_type: str = "base"

    def _extra_tools(self) -> list:
        """Return MCP tools scoped to this specialist type."""
        if self.mcp_manager is not None:
            return self.mcp_manager.get_tools_for_specialist(self._specialist_type)
        return []
    
    @abstractmethod
    def _create_agent(self) -> Agent:
        """Create the Strands agent with tools available"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this specialist provides"""
        pass
    
    @abstractmethod
    def get_domain_expertise(self) -> List[str]:
        """Return list of domain areas this specialist covers"""
        pass
    
    def __call__(self, prompt: str):
        """Make specialist agent callable for direct invocation"""
        return self.agent(prompt)


class SpecialistAgentFactory:
    """
    Factory for creating Specialist Agents for the Colonees colony.

    Resolution order:
    1. ColoneeRegistry — user-defined and built-in colonee definitions
    2. Hardcoded legacy classes — backward compat for direct type strings
    """

    @staticmethod
    def create_specialist_agent(
        specialist_type: str,
        session_manager,
        specialization: str,
        agent_id: Optional[str] = None,
        agent_manager=None,
        agent_directory=None,
        mcp_manager=None,
        colonee_registry=None,
    ) -> BaseSpecialistAgent:
        """Create specialist agent of specified type."""

        if not agent_id:
            agent_id = f"{specialist_type}_{specialization}_specialist_{hash(str(session_manager))}"

        # 1. Try ColoneeRegistry first (user-defined + built-in definitions)
        if colonee_registry is not None:
            defn = colonee_registry.get(specialist_type)
            if defn is None:
                # Also try the legacy type map
                _legacy_map = {
                    'tutor': 'executor',
                    'subject_expert': 'domain_expert',
                    'research': 'researcher',
                    'assessment': 'analyst',
                    'video_production': 'media_producer',
                }
                mapped = _legacy_map.get(specialist_type)
                if mapped:
                    defn = colonee_registry.get(mapped)

            if defn is not None:
                if not defn.enabled:
                    raise ValueError(f"Colonee '{defn.name}' is disabled.")
                from .dynamic_specialist import DynamicSpecialistAgent
                return DynamicSpecialistAgent(
                    session_manager=session_manager,
                    agent_id=agent_id,
                    specialization=specialization,
                    definition=defn,
                    agent_manager=agent_manager,
                    mcp_manager=mcp_manager,
                )

        # 2. Fallback: legacy hardcoded classes
        from colon.agents.specialists.tutoring import TutorSpecialistAgent
        from colon.agents.specialists.subject_expertise import SubjectExpertSpecialistAgent
        from colon.agents.specialists.research import ResearchSpecialistAgent
        from colon.agents.specialists.assessment import AssessmentSpecialistAgent
        from colon.agents.specialists.video_production import VideoProductionSpecialistAgent

        _legacy_classes = {
            'tutor': TutorSpecialistAgent,
            'subject_expert': SubjectExpertSpecialistAgent,
            'research': ResearchSpecialistAgent,
            'assessment': AssessmentSpecialistAgent,
            'video_production': VideoProductionSpecialistAgent,
        }

        if specialist_type not in _legacy_classes:
            raise ValueError(
                f"Unknown specialist type: '{specialist_type}'. "
                f"Available: {list(_legacy_classes.keys())} or any name in the ColoneeRegistry."
            )

        agent_class = _legacy_classes[specialist_type]
        return agent_class(session_manager, agent_id, specialization, agent_manager, mcp_manager)

    @staticmethod
    def get_available_specialist_types(colonee_registry=None) -> List[str]:
        legacy = ['tutor', 'subject_expert', 'research', 'assessment', 'video_production']
        if colonee_registry is not None:
            registry_names = [c.name for c in colonee_registry.list()]
            # Merge, preserving order, deduplicating
            seen = set(legacy)
            for name in registry_names:
                if name not in seen:
                    legacy.append(name)
                    seen.add(name)
        return legacy
