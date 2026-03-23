"""
Research Tool Agent

Handles research and information retrieval operations using state-of-the-art Strands tools.
"""

import logging
from typing import List, Dict, Any
from strands import Agent
from galos.agents.tool_agents import BaseToolAgent
from galos.core.model_config import get_model

logger = logging.getLogger(__name__)


class ResearchToolAgent(BaseToolAgent):
    """
    Tool Agent for research and information retrieval using official Strands tools
    ONLY handles web searches, API calls, content extraction, no content analysis
    """
    
    def _create_agent(self) -> Agent:
        """Create agent with Strands research tools"""
        from strands_tools import http_request
        
        tools = [http_request]
        
        logger.info(f"Research agent initialized with {len(tools)} tools")
        
        return Agent(
            name=self.agent_id,
            system_prompt="""You are a Research Tool Agent with web research capabilities.
            
            AVAILABLE TOOLS:
            - http_request: Make API calls with comprehensive authentication support
            
            CRITICAL ROLE: You ONLY execute research operations. You do NOT:
            - Analyze or interpret research results
            - Make recommendations or synthesize findings
            - Synthesize information from multiple sources
            - Decide what to research
            
            You retrieve information with maximum accuracy and comprehensive coverage.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=tools
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            'web_browsing',
            'web_search',
            'content_extraction', 
            'api_access',
            'authenticated_requests'
        ]