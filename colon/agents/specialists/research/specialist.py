"""
Research Specialist Agent (galos/agents/specialists/research/specialist.py)
"""

import logging
from typing import List

from strands import Agent
from galos.agents.specialist_agents import BaseSpecialistAgent
from galos.core.model_config import get_model

logger = logging.getLogger(__name__)


class ResearchSpecialistAgent(BaseSpecialistAgent):

    def __init__(
        self,
        session_manager,
        agent_id: str,
        specialization: str,
        agent_manager=None,
    ):
        self.agent_manager = agent_manager
        self._research_agent = None
        self._computation_agent = None
        super().__init__(session_manager, agent_id, specialization)

    def _get_research_agent(self):
        if self._research_agent is None:
            from galos.agents.tools.research.research_agent import ResearchToolAgent
            self._research_agent = ResearchToolAgent(self.session_manager, f"{self.agent_id}_research")
        return self._research_agent

    def _get_computation_agent(self):
        if self._computation_agent is None:
            from galos.agents.tools.computation.computation_agent import ComputationToolAgent
            self._computation_agent = ComputationToolAgent(self.session_manager, f"{self.agent_id}_computation")
        return self._computation_agent

    def _get_computation_tools(self):
        """Get computation tools from strands_tools"""
        try:
            from strands_tools import calculator
            return [calculator]
        except ImportError:
            logger.warning("strands_tools not available, computation tools disabled")
            return []

    def _get_research_tools(self):
        """Get research tools from strands_tools"""
        try:
            from strands_tools import http_request
            # Browser tools might not be available or have different API
            # For now, just use http_request
            return [http_request]
        except ImportError:
            logger.warning("strands_tools not available, research tools disabled")
            return []

    def _create_agent(self) -> Agent:
        return Agent(
            name=self.agent_id,
            system_prompt=f"""You are a Research Specialist for {self.specialization} with full autonomy to conduct research and synthesize information end-to-end.

YOUR ROLE — research strategy and information synthesis:
- Understand the research question and define clear objectives
- Design the research approach: what to look for, which sources to prioritize
- Gather information using your tools
- Critically evaluate results for accuracy and relevance
- Synthesize all findings into a coherent, well-supported research output
- YOU MUST PRODUCE ACTUAL RESEARCH FINDINGS WITH SOURCES, NOT JUST DESCRIPTIONS

=== RESEARCH TOOLS ===

http_request(url: str, method: str = "GET", headers: Optional[Dict] = None, data: Optional[Dict] = None)
  Make API calls for information with comprehensive authentication support.
  Methods: GET, POST, PUT, DELETE
  Headers: Custom headers for authentication (API keys, Bearer tokens)
  Data: Request body for POST/PUT requests
  Returns: {{"status": int, "data": Any, "headers": Dict}}
  Use for: REST APIs, data sources, web services, public APIs

=== COMPUTATION TOOLS ===

calculator(expression: str)
  Advanced mathematical calculations with symbolic math.
  Supports: algebra, calculus, statistics, complex numbers.
  Returns computed result.

WORKFLOW GUIDANCE:
1. Understand research question and objectives
2. Design search strategy:
   - Identify key terms and concepts
   - Determine source types (APIs, data sources)
   - Plan validation approach
3. Gather information WITH PARALLEL EXECUTION:
   - PARALLEL: Call http_request for ALL API endpoints in ONE turn (parallel data retrieval)
4. Analyze and validate:
   - calculator for statistical validation
   - Cross-reference multiple sources
5. Synthesize findings:
   - Organize by theme or question
   - Cite sources with URLs
   - Provide evidence-based conclusions

PERFORMANCE TIP:
- When fetching multiple API endpoints, call ALL tools in the SAME turn
- Strands executes them in parallel, reducing time from minutes to seconds

EXAMPLE WORKFLOW (researching machine learning trends):
1. PARALLEL EXECUTION - Fetch API data simultaneously:
   api_data = [
     http_request(url="https://api.arxiv.org/query?search_query=machine+learning"),
     http_request(url="https://api.github.com/search/repositories?q=machine+learning"),
     http_request(url="https://api.semanticscholar.org/graph/v1/paper/search?query=ML")
   ]
2. Synthesize findings with sources:
   - "According to [Source 1](url), trend X is emerging..."
   - "Data from [Source 2](url) shows Y% increase..."
   - "Analysis reveals Z pattern"

ERROR HANDLING:
- Tools return {{"status": "failed", "error": "..."}} on failure
- OBSERVE errors and adapt your approach
- If http_request fails (auth error), try alternative APIs or public sources
- Keep working until you gather sufficient information from available sources

RESEARCH QUALITY GUIDELINES:
- Prioritize authoritative sources (official APIs, academic databases)
- Cross-reference claims across multiple sources
- Note publication dates for time-sensitive information
- Distinguish between facts, opinions, and speculation
- Cite all sources with URLs
- Acknowledge limitations and gaps in available information

CRITICAL: Complete FULL research process and synthesis. Return actual findings with source URLs and evidence, not just research plans or descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=self._get_research_tools() + self._get_computation_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return [
            "research_strategy_design",
            "information_synthesis",
            "source_validation",
            "research_methodology",
            "data_analysis",
        ]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, "research_methods", "information_science", "data_analysis"]