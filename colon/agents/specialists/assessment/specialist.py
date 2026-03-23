"""
Assessment / Analyst Specialist Agent
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


class AssessmentSpecialistAgent(BaseSpecialistAgent):
    _specialist_type = "analyst"

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
            system_prompt=f"""You are an Analyst Specialist for {self.specialization} with full autonomy to design evaluations and produce structured reports end-to-end.

YOUR ROLE — analysis, evaluation design, and reporting:
- Understand the analysis objectives and context
- Design the right evaluation or analysis approach
- Create ALL output materials using your tools
- Interpret results and produce actionable reports
- YOU MUST PRODUCE ACTUAL OUTPUT FILES, NOT JUST DESCRIPTIONS

Use write_file for reports, generate_image for visuals, calculator for statistics.
Call tools in PARALLEL when creating multiple independent outputs.

CRITICAL: Return actual file URLs and reports, not descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[
                # File tools
                fa.read_file, fa.write_file, fa.append_to_file, fa.delete_file,
                fa.copy_file, fa.move_file, fa.list_files, fa.file_exists,
                fa.get_file_metadata, fa.search_in_files, fa.replace_in_file,
                fa.read_lines, fa.create_folder, fa.delete_folder, fa.get_public_url,
                # Media tools
                ma.create_production,
                ma.write_script, ma.sanitize_image_prompt,
                ma.generate_image, ma.resize_image, ma.text_to_speech,
                ma.assemble_video, ma.save_to_disk, ma.load_from_disk,
                ma.list_artifacts, ma.delete_artifact, ma.get_production_info,
            ] + get_computation_tools() + self._extra_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return ["analysis_design", "data_analysis", "evaluation", "reporting", "structured_output"]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, "analysis", "evaluation", "reporting"]
