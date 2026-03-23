"""
Assessment Specialist Agent (galos/agents/specialists/assessment/specialist.py)
"""

import logging
from typing import List

from strands import Agent
from galos.agents.specialist_agents import BaseSpecialistAgent
from galos.core.model_config import get_model

logger = logging.getLogger(__name__)


class AssessmentSpecialistAgent(BaseSpecialistAgent):

    def __init__(
        self,
        session_manager,
        agent_id: str,
        specialization: str,
        agent_manager=None,
    ):
        self.agent_manager = agent_manager
        self._computation_agent = None
        self._file_agent = None
        self._media_agent = None
        super().__init__(session_manager, agent_id, specialization)

    def _get_computation_agent(self):
        if self._computation_agent is None:
            from galos.agents.tools.computation.computation_agent import ComputationToolAgent
            self._computation_agent = ComputationToolAgent(self.session_manager, f"{self.agent_id}_computation")
        return self._computation_agent

    def _get_file_agent(self):
        if self._file_agent is None:
            from galos.agents.tools.file.file_agent import FileToolAgent
            self._file_agent = FileToolAgent(self.session_manager, f"{self.agent_id}_file")
        return self._file_agent

    def _get_media_agent(self):
        if self._media_agent is None:
            from galos.agents.tools.media.media_agent import MediaToolAgent
            self._media_agent = MediaToolAgent(self.session_manager, f"{self.agent_id}_media")
        return self._media_agent

    def _get_computation_tools(self):
        """Get computation tools from strands_tools"""
        try:
            from strands_tools import calculator
            return [calculator]
        except ImportError:
            logger.warning("strands_tools not available, computation tools disabled")
            return []

    def _create_agent(self) -> Agent:
        file_agent = self._get_file_agent()
        media_agent = self._get_media_agent()

        return Agent(
            name=self.agent_id,
            system_prompt=f"""You are an Analyst Specialist for {self.specialization} with full autonomy to design evaluations and produce structured reports end-to-end.

YOUR ROLE — analysis, evaluation design, and reporting:
- Understand the analysis objectives and context
- Design the right evaluation or analysis approach
- Create ALL output materials using your tools
- Interpret results and produce actionable reports
- YOU MUST PRODUCE ACTUAL OUTPUT FILES, NOT JUST DESCRIPTIONS

=== FILE MANAGEMENT TOOLS ===

read_file(path: str, encoding: str = "utf-8")
  Returns: {{"status": "success", "content": str, "size_bytes": int}}
  Read source documents, existing reports, or input data files.

write_file(path: str, content: str, content_type: Optional[str] = None)
  Returns: {{"status": "success", "public_url": str}}
  Create output reports, structured data files, or analysis documents. Content-type auto-detected.

append_to_file(path: str, content: str, separator: str = "\\n")
  Returns: {{"status": "success", "total_size_bytes": int}}
  Add entries to existing documents. Creates if doesn't exist.

delete_file(path: str)
  Returns: {{"status": "success", "deleted": bool}}
  Delete outdated files or drafts.

copy_file(source_path: str, destination_path: str)
  Returns: {{"status": "success", "public_url": str}}
  Duplicate document templates or report structures.

move_file(source_path: str, destination_path: str)
  Returns: {{"status": "success", "public_url": str}}
  Reorganize output files.

list_files(prefix: str = "", extension_filter: Optional[str] = None, max_results: int = 200)
  Returns: {{"status": "success", "files": List[Dict], "count": int}}
  Browse available files filtered by prefix or extension.

file_exists(path: str)
  Returns: {{"status": "success", "exists": bool}}
  Check if a file exists before reading.

get_file_metadata(path: str)
  Returns: {{"status": "success", "size_bytes": int, "content_type": str, "last_modified": str}}
  Get file details.

search_in_files(query: str, prefix: str = "", extension_filter: Optional[str] = None)
  Returns: {{"status": "success", "matches": List[Dict], "match_count": int}}
  Find specific content across files.

replace_in_file(path: str, find: str, replace: str, replace_all: bool = True)
  Returns: {{"status": "success", "occurrences_replaced": int}}
  Update content in existing files.

read_lines(path: str, start_line: int = 1, end_line: Optional[int] = None)
  Returns: {{"status": "success", "content": str, "total_lines": int}}
  Read specific sections of large files.

create_folder(folder_path: str)
  Returns: {{"status": "success", "public_url": str}}
  Organize outputs by topic or type.

delete_folder(folder_path: str)
  Returns: {{"status": "success", "deleted_files": int}}
  Remove entire output category.

get_public_url(path: str)
  Returns: {{"status": "success", "url": str}}
  Get shareable local URL for output files.

=== MEDIA PRODUCTION TOOLS ===

create_production(production_name: str)
  Returns: {{"status": "success", "production_dir": str, "production_id": str}}
  Initialize local storage for visual output materials.

write_script(instructions: str)
  Returns: {{"status": "success", "script": str}}
  Generate professional video scripts or narration content.

sanitize_image_prompt(prompt: str)
  Returns: {{"status": "success", "sanitized_prompt": str}}
  Clean prompts before image generation. ALWAYS call before generate_image.

generate_image(prompt: str, course: str = "", max_retries: int = 3)
  Returns: {{"status": "success", "local_path": str, "attempt": int}}
  Create charts, diagrams, visual assets, and infographics.

resize_image(local_path: str, width: int = 1280, height: int = 720)
  Returns: {{"status": "success", "local_path": str}}
  Resize images for consistent display.

text_to_speech(text: str, locale: str = "en-US", voice_gender: str = "female", engine: str = "gemini")
  Returns: {{"status": "success", "local_path": str, "voice_id": str, "duration_seconds": float}}
  Generate audio narration or spoken output. Duration is ACTUAL audio duration detected via ffprobe.

assemble_video(scene_image_paths: List[str], audio_paths: List[str])
  Returns: {{"status": "success", "local_path": str, "scenes": int, "size_mb": float}}
  Create video output from images and audio narration.

save_to_disk(key: str, content: str)
  Returns: {{"status": "success", "local_path": str}}
  Store structured data or intermediate state to local storage.

load_from_disk(key: str)
  Returns: str (content directly, or "ERROR loading <key>: <message>" on failure)
  Retrieve previously saved data.

list_artifacts(category: Optional[str] = None)
  Returns: {{"status": "success", "artifacts": Dict, "total_count": int}}
  List all generated output materials.

delete_artifact(local_path: str)
  Returns: {{"status": "success", "deleted": bool}}
  Remove outdated or superseded output materials.

get_production_info()
  Returns: {{"status": "success", "production_id": str, "artifact_counts": Dict}}
  Summary of current production state.

=== COMPUTATION TOOLS ===

calculator(expression: str)
  Mathematical calculations for scoring, statistics, and data analysis.
  Returns computed result.

WORKFLOW GUIDANCE:
1. Understand objectives and context
2. Design analysis or evaluation structure
3. Create materials WITH PARALLEL EXECUTION:
   - PARALLEL: Write all output files simultaneously
   - PARALLEL: Generate all visual assets simultaneously
   - Use calculator for scoring, statistics, and data analysis
4. Deliver complete output with:
   - Output file with public_url
   - Analysis report
   - Scoring or evaluation logic (if applicable)

PERFORMANCE TIP:
- When creating multiple output files or visual materials, call ALL tools in the SAME turn
- Example: 10 diagrams sequentially = 100s, in parallel = 10s

EXAMPLE WORKFLOW (creating analysis report):
1. write_file(path="reports/analysis.json", content='{"title": "Analysis Report", "findings": [...]}')
2. write_file(path="reports/summary.md", content="# Summary\n...")
3. create_production_bucket(production_name="Report Visuals")
4. generate_image(prompt="data visualization chart", course="Analysis")
5. get_public_url(path="reports/analysis.json")
6. Return report URL and analysis findings

ERROR HANDLING:
- Tools return {{"status": "failed", "error": "..."}} on failure
- OBSERVE errors and adapt your approach
- If write_file fails, try different path or simpler content
- If generate_image fails, skip visual or use text-based output
- Keep working until you create complete output

CRITICAL: Complete FULL analysis and output creation. Return actual file URLs and reports, not just descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[
                # File tools
                file_agent.read_file,
                file_agent.write_file,
                file_agent.append_to_file,
                file_agent.delete_file,
                file_agent.copy_file,
                file_agent.move_file,
                file_agent.list_files,
                file_agent.file_exists,
                file_agent.get_file_metadata,
                file_agent.search_in_files,
                file_agent.replace_in_file,
                file_agent.read_lines,
                file_agent.create_folder,
                file_agent.delete_folder,
                file_agent.get_public_url,
                # Media tools
                media_agent.create_production,
                media_agent.create_production_bucket,  # backward-compat alias
                media_agent.write_script,
                media_agent.sanitize_image_prompt,
                media_agent.generate_image,
                media_agent.resize_image,
                media_agent.text_to_speech,
                media_agent.assemble_video,
                media_agent.save_to_disk,
                media_agent.save_to_s3,  # backward-compat alias
                media_agent.load_from_disk,
                media_agent.load_from_s3,  # backward-compat alias
                media_agent.list_artifacts,
                media_agent.delete_artifact,
                media_agent.get_production_info,
            ] + self._get_computation_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return [
            "analysis_design",
            "data_analysis",
            "evaluation",
            "reporting",
            "structured_output",
        ]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, "analysis", "evaluation", "reporting"]