"""
Computation Tool Agent

Handles computational operations using state-of-the-art Strands tools.
"""

import logging
from typing import List, Dict, Any
from strands import Agent
from galos.agents.tool_agents import BaseToolAgent
from galos.core.model_config import get_model

logger = logging.getLogger(__name__)


class ComputationToolAgent(BaseToolAgent):
    """
    Tool Agent for computational operations using official Strands tools
    ONLY handles code execution, calculations, no reasoning
    """
    
    def _create_agent(self) -> Agent:
        """Create agent with computation tools"""
        from strands_tools import calculator
        
        tools = [calculator]
        
        logger.info(f"Computation agent initialized with {len(tools)} tools")
        
        return Agent(
            name=self.agent_id,
            system_prompt="""You are a Computation Tool Agent with advanced computational capabilities.
            
            AVAILABLE TOOLS:
            - calculator: Advanced mathematical calculations with symbolic math capabilities
            
            CRITICAL ROLE: You ONLY execute computational operations. You do NOT:
            - Decide what calculations to perform
            - Interpret results or provide explanations
            - Make domain-specific recommendations
            - Orchestrate workflows
            
            You execute calculations as requested with maximum accuracy and safety.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=tools
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            'python_execution', 
            'advanced_calculations', 
            'symbolic_math',
            'mathematical_computation',
        ]
