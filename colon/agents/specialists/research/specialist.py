"""
Research Specialist Agent
"""

import logging
from typing import List

from strands import Agent
from colon.agents.specialist_agents import BaseSpecialistAgent
from colon.agents.tools.research.research_tools import get_research_tools
from colon.agents.tools.computation.computation_tools import get_computation_tools
from colon.core.model_config import get_model

logger = logging.getLogger(__name__)


class ResearchSpecialistAgent(BaseSpecialistAgent):
    _specialist_type = "researcher"

    def __init__(self, session_manager, agent_id: str, specialization: str,
                 agent_manager=None, mcp_manager=None):
        self.agent_manager = agent_manager
        super().__init__(session_manager, agent_id, specialization, mcp_manager)

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

http_request(url, method="GET", headers=None, data=None)
  Make API calls for information. Returns: {{"status": int, "data": Any, "headers": Dict}}

=== COMPUTATION TOOLS ===

calculator(expression)
  Mathematical calculations. Supports algebra, calculus, statistics.

WORKFLOW:
1. Design search strategy — key terms, source types, validation approach
2. PARALLEL: Call http_request for ALL endpoints in ONE turn
3. Validate with calculator where needed
4. Synthesize findings with source URLs

CRITICAL: Return actual findings with source URLs, not descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=get_research_tools() + get_computation_tools() + self._extra_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return [
            "research_strategy_design", "information_synthesis",
            "source_validation", "research_methodology", "data_analysis",
        ]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, "research_methods", "information_science", "data_analysis"]
