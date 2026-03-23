"""
Executor Specialist Agent (formerly Tutor)
"""

import logging
from typing import List

from strands import Agent
from colon.agents.specialist_agents import BaseSpecialistAgent
from colon.agents.tools.computation.computation_tools import get_computation_tools
from colon.agents.tools.file.file_provider import FileToolProvider
from colon.agents.tools.media.media_provider import MediaToolProvider
from colon.core.model_config import get_model

logger = logging.getLogger(__name__)


class TutorSpecialistAgent(BaseSpecialistAgent):
    _specialist_type = "executor"

    def __init__(self, session_manager, agent_id: str, specialization: str,
                 agent_manager=None, mcp_manager=None):
        self.agent_manager = agent_manager
        self._file_provider = None
        self._media_provider = None
        super().__init__(session_manager, agent_id, specialization, mcp_manager)

    def _get_file_provider(self):
        if self._file_provider is None:
            self._file_provider = FileToolProvider(self.session_manager, f"{self.agent_id}_file")
        return self._file_provider

    def _get_media_provider(self):
        if self._media_provider is None:
            self._media_provider = MediaToolProvider(self.session_manager, f"{self.agent_id}_media")
        return self._media_provider

    def _create_agent(self) -> Agent:
        fa = self._get_file_provider()
        ma = self._get_media_provider()

        return Agent(
            name=self.agent_id,
            system_prompt=f"""You are a {self.specialization} Domain Expert Specialist with full autonomy to create comprehensive deliverables end-to-end.

YOUR ROLE — domain reasoning, content design, and execution:
- Analyze the request, understand the domain context and objectives
- Design a structured approach with clear deliverables
- Create ALL necessary materials (visuals, audio, documents) using your tools
- Synthesize outputs into coherent, high-quality deliverables
- YOU MUST PRODUCE ACTUAL MATERIALS, NOT JUST DESCRIPTIONS

Call create_production first for any media work.
Call tools in PARALLEL when creating multiple independent materials.

CRITICAL: Return actual URLs/files, not descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[
                # Media tools
                ma.create_production,
                ma.write_script, ma.sanitize_image_prompt,
                ma.generate_image, ma.resize_image, ma.text_to_speech,
                ma.assemble_video, ma.save_to_disk, ma.load_from_disk,
                ma.list_artifacts, ma.delete_artifact, ma.get_production_info,
                # File tools
                fa.read_file, fa.write_file, fa.append_to_file, fa.delete_file,
                fa.copy_file, fa.move_file, fa.list_files, fa.file_exists,
                fa.get_file_metadata, fa.search_in_files, fa.replace_in_file,
                fa.read_lines, fa.create_folder, fa.delete_folder, fa.get_public_url,
            ] + get_computation_tools() + self._extra_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return [
            "domain_knowledge_provision", "concept_explanation",
            "problem_analysis", "solution_validation", "expert_guidance",
        ]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, "domain_reasoning", "structured_delivery"]
