"""
Domain Expert Specialist Agent
"""

import logging
from typing import List

from strands import Agent
from colon.agents.specialist_agents import BaseSpecialistAgent
from colon.agents.tools.research.research_tools import get_research_tools
from colon.agents.tools.computation.computation_tools import get_computation_tools
from colon.agents.tools.media.media_provider import MediaToolProvider
from colon.core.model_config import get_model

logger = logging.getLogger(__name__)


class SubjectExpertSpecialistAgent(BaseSpecialistAgent):
    _specialist_type = "domain_expert"

    def __init__(self, session_manager, agent_id: str, specialization: str,
                 agent_manager=None, mcp_manager=None):
        self.agent_manager = agent_manager
        self._media_provider = None
        super().__init__(session_manager, agent_id, specialization, mcp_manager)

    def _get_media_provider(self):
        if self._media_provider is None:
            self._media_provider = MediaToolProvider(self.session_manager, f"{self.agent_id}_media")
        return self._media_provider

    def _create_agent(self) -> Agent:
        ma = self._get_media_provider()
        return Agent(
            name=self.agent_id,
            system_prompt=f"""You are a {self.specialization} Subject Expert Specialist with full autonomy to provide deep domain knowledge end-to-end.

YOUR ROLE — domain expertise and knowledge provision:
- Provide accurate domain knowledge and explanations
- Analyze complex problems in your domain
- Validate information and solutions
- Create supporting materials (visualizations, calculations, research)
- YOU MUST PRODUCE ACTUAL EXPLANATIONS WITH SUPPORTING MATERIALS, NOT JUST DESCRIPTIONS

Use create_production first for any media work, then sanitize_image_prompt before generate_image.
Use calculator for demonstrations. Use http_request for current information.

CRITICAL: Return actual supporting materials (image paths, calculations), not descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[
                ma.create_production,
                ma.write_script, ma.sanitize_image_prompt,
                ma.generate_image, ma.resize_image, ma.text_to_speech,
                ma.assemble_video, ma.save_to_disk, ma.load_from_disk,
                ma.list_artifacts, ma.delete_artifact, ma.get_production_info,
            ] + get_computation_tools() + get_research_tools() + self._extra_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return [
            "domain_knowledge_provision", "concept_explanation",
            "problem_analysis", "solution_validation", "expert_guidance",
        ]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, f"{self.specialization}_theory", f"{self.specialization}_applications"]
