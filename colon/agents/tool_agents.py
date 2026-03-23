"""
Colonees Tool Agents
World-class architecture: Tools are separate agents, not embedded in supervisors
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from strands import Agent

from ..core.model_config import get_model

logger = logging.getLogger(__name__)


class BaseToolAgent(ABC):
    """
    Base class for Tool Agents following Colonees colony architecture

    PRINCIPLES:
    - Tool agents ONLY execute tools, no reasoning/orchestration
    - Single responsibility: one category of tools per agent
    - Stateless and horizontally scalable
    - Discoverable through Agent Directory
    """

    def __init__(self, session_manager, agent_id: str):
        self.session_manager = session_manager
        self.agent_id = agent_id
        self.agent = self._create_agent()
        
        # Tool execution statistics
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0
        }
    
    @abstractmethod
    def _create_agent(self) -> Agent:
        """Create the Strands agent with appropriate tools"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this tool agent provides"""
        pass
    
    def __call__(self, prompt: str):
        """Make tool agent callable for direct invocation"""
        return self.agent(prompt)


class ToolAgentFactory:
    """
    Factory for creating Tool Agents following world-class patterns
    """
    
    @staticmethod
    def create_tool_agent(
        tool_type: str,
        session_manager,
        agent_id: Optional[str] = None
    ) -> BaseToolAgent:
        """Create tool agent of specified type"""
        
        if not agent_id:
            agent_id = f"{tool_type}_tool_agent_{hash(str(session_manager))}"
        
        # Import all tool agents from modular structure
        from galos.agents.tools import (
            FileToolAgent,
            ComputationToolAgent,
            ResearchToolAgent,
            MediaToolAgent
        )
        
        tool_agents = {
            'file': FileToolAgent,
            'computation': ComputationToolAgent,
            'research': ResearchToolAgent,
            'media': MediaToolAgent,
            # Aliases for backward compatibility
            'script': MediaToolAgent,
            'audio': MediaToolAgent,
            'visual': MediaToolAgent,
            'video_assembly': MediaToolAgent
        }
        
        if tool_type not in tool_agents:
            raise ValueError(f"Unknown tool type: {tool_type}. Available: {list(tool_agents.keys())}")
        
        agent_class = tool_agents[tool_type]
        return agent_class(session_manager, agent_id)
    
    @staticmethod
    def get_available_tool_types() -> List[str]:
        """Get list of available tool agent types"""
        return ['file', 'computation', 'research', 'media']
