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
        specialization: str
    ):
        self.session_manager = session_manager
        self.agent_id = agent_id
        self.specialization = specialization
        self.agent = self._create_agent()
        
        # Collaboration statistics
        self.stats = {
            'tasks_completed': 0,
            'tool_calls': 0,
            'successful_operations': 0,
            'failed_operations': 0
        }
    
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
    Factory for creating Specialist Agents for the Colonees colony
    """

    @staticmethod
    def create_specialist_agent(
        specialist_type: str,
        session_manager,
        specialization: str,
        agent_id: Optional[str] = None,
        agent_manager=None,
        agent_directory=None
    ) -> BaseSpecialistAgent:
        """Create specialist agent of specified type"""
        
        if not agent_id:
            agent_id = f"{specialist_type}_{specialization}_specialist_{hash(str(session_manager))}"
        
        # Import all specialists from modular structure
        from galos.agents.specialists.tutoring import TutorSpecialistAgent
        from galos.agents.specialists.subject_expertise import SubjectExpertSpecialistAgent
        from galos.agents.specialists.research import ResearchSpecialistAgent
        from galos.agents.specialists.assessment import AssessmentSpecialistAgent
        from galos.agents.specialists.video_production import VideoProductionSpecialistAgent
        
        specialist_agents = {
            'tutor': TutorSpecialistAgent,
            'subject_expert': SubjectExpertSpecialistAgent,
            'research': ResearchSpecialistAgent,
            'assessment': AssessmentSpecialistAgent,
            'video_production': VideoProductionSpecialistAgent
        }
        
        if specialist_type not in specialist_agents:
            raise ValueError(f"Unknown specialist type: {specialist_type}. Available: {list(specialist_agents.keys())}")
        
        agent_class = specialist_agents[specialist_type]
        
        # All specialists accept agent_manager for tool access
        return agent_class(session_manager, agent_id, specialization, agent_manager)
    
    @staticmethod
    def get_available_specialist_types() -> List[str]:
        """Get list of available specialist agent types"""
        return ['tutor', 'subject_expert', 'research', 'assessment', 'video_production']
