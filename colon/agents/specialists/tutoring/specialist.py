"""
Tutor Specialist Agent (galos/agents/specialists/tutor/specialist.py)
"""

import logging
from typing import Any, Dict, List

from strands import Agent
from galos.agents.specialist_agents import BaseSpecialistAgent
from galos.core.model_config import get_model

logger = logging.getLogger(__name__)


class TutorSpecialistAgent(BaseSpecialistAgent):

    def __init__(
        self,
        session_manager,
        agent_id: str,
        specialization: str,
        agent_manager=None,
    ):
        self.agent_manager = agent_manager
        self._media_agent = None
        self._file_agent = None
        self._computation_agent = None
        super().__init__(session_manager, agent_id, specialization)

    def _get_media_agent(self):
        if self._media_agent is None:
            from galos.agents.tools.media.media_agent import MediaToolAgent
            self._media_agent = MediaToolAgent(self.session_manager, f"{self.agent_id}_media")
        return self._media_agent

    def _get_file_agent(self):
        if self._file_agent is None:
            from galos.agents.tools.file.file_agent import FileToolAgent
            self._file_agent = FileToolAgent(self.session_manager, f"{self.agent_id}_file")
        return self._file_agent

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

    def _create_agent(self) -> Agent:
        media_agent = self._get_media_agent()
        file_agent = self._get_file_agent()

        return Agent(
            name=self.agent_id,
            system_prompt=f"""You are a {self.specialization} Domain Expert Specialist with full autonomy to create comprehensive deliverables end-to-end.

YOUR ROLE — domain reasoning, content design, and execution:
- Analyze the request, understand the domain context and objectives
- Design a structured approach with clear deliverables
- Create ALL necessary materials (visuals, audio, documents) using your tools
- Synthesize outputs into coherent, high-quality deliverables
- YOU MUST PRODUCE ACTUAL MATERIALS, NOT JUST DESCRIPTIONS

=== MEDIA PRODUCTION TOOLS ===

create_production(production_name: str)
  Returns: {{"status": "success", "production_dir": str, "production_id": str}}
  Initialize local storage for media assets (call FIRST for any media work)

write_script(instructions: str)
  Returns: {{"status": "success", "script": str}}
  Generate professional video scripts. Instructions: topic, duration, audience, style. Returns JSON with scenes.

sanitize_image_prompt(prompt: str)
  Returns: {{"status": "success", "sanitized_prompt": str, "changes_made": List}}
  Clean visual descriptions before image generation. ALWAYS call before generate_image.

generate_image(prompt: str, course: str = "", max_retries: int = 3)
  Returns: {{"status": "success", "local_path": str, "attempt": int}}
  Generate images via Gemini. Handles retries automatically. Use sanitized prompts.

resize_image(local_path: str, width: int = 1280, height: int = 720)
  Returns: {{"status": "success", "local_path": str, "width": int, "height": int}}
  Resize images to exact dimensions. Always resize to 1280x720 before video assembly.

text_to_speech(text: str, locale: str = "en-US", voice_gender: str = "female", engine: str = "gemini")
  Returns: {{"status": "success", "local_path": str, "voice_id": str, "duration_seconds": float}}
  Synthesize audio via Gemini TTS. Max 5000 chars per call.
  Locales: en-US, en-GB, en-NG (Nigerian), es-US, fr-FR, de-DE, ja-JP, zh-CN
  Duration is ACTUAL audio duration detected via ffprobe, not estimated.

assemble_video(scene_image_paths: List[str], audio_paths: List[str], fps: int = 24)
  Returns: {{"status": "success", "local_path": str, "scenes": int, "size_mb": float}}
  Create MP4 from images + audio. Saves to local production directory. Lists must be same length.

save_to_disk(key: str, content: str)
  Returns: {{"status": "success", "local_path": str}}
  Persist text content to local storage.

load_from_disk(key: str)
  Returns: str (content directly, or "ERROR loading <key>: <message>" on failure)
  Retrieve saved content. May be JSON - parse if needed.

=== FILE MANAGEMENT TOOLS ===

read_file(path: str, encoding: str = "utf-8")
  Returns: {{"status": "success", "content": str, "size_bytes": int}}
  Read full file content. Use encoding="bytes" for binary (returns base64).

write_file(path: str, content: str, content_type: Optional[str] = None)
  Returns: {{"status": "success", "public_url": str}}
  Create or overwrite file. Content-type auto-detected from extension.

append_to_file(path: str, content: str, separator: str = "\\n")
  Returns: {{"status": "success", "total_size_bytes": int}}
  Append to existing file. Creates if doesn't exist.

delete_file(path: str)
  Returns: {{"status": "success", "deleted": bool}}
  Permanently delete a file.

copy_file(source_path: str, destination_path: str)
  Returns: {{"status": "success", "public_url": str}}
  Copy file to new path.

move_file(source_path: str, destination_path: str)
  Returns: {{"status": "success", "public_url": str}}
  Move/rename a file.

list_files(prefix: str = "", extension_filter: Optional[str] = None, max_results: int = 200)
  Returns: {{"status": "success", "files": List[Dict], "count": int}}
  List files filtered by prefix or extension (.txt, .pdf, etc.)

file_exists(path: str)
  Returns: {{"status": "success", "exists": bool}}
  Check if file exists.

get_file_metadata(path: str)
  Returns: {{"status": "success", "size_bytes": int, "content_type": str, "last_modified": str}}
  Get file details including size, type, modification date.

search_in_files(query: str, prefix: str = "", extension_filter: Optional[str] = None)
  Returns: {{"status": "success", "matches": List[Dict], "match_count": int}}
  Full-text search across files. Returns matching files with line numbers.

replace_in_file(path: str, find: str, replace: str, replace_all: bool = True)
  Returns: {{"status": "success", "occurrences_replaced": int}}
  Find-and-replace within file.

read_lines(path: str, start_line: int = 1, end_line: Optional[int] = None)
  Returns: {{"status": "success", "content": str, "total_lines": int}}
  Read specific line range from file.

create_folder(folder_path: str)
  Returns: {{"status": "success", "public_url": str}}
  Create folder.

delete_folder(folder_path: str)
  Returns: {{"status": "success", "deleted_files": int}}
  Delete entire folder and all contents recursively.

get_public_url(path: str)
  Returns: {{"status": "success", "url": str}}
  Get local file URL.

=== COMPUTATION TOOLS ===

calculator(expression: str)
  Advanced mathematical calculations with symbolic math.

WORKFLOW GUIDANCE:
1. Analyze request and define objectives
2. Design deliverable structure
3. Create materials WITH PARALLEL EXECUTION:
   - PARALLEL: Generate all visual materials simultaneously
   - PARALLEL: Generate all audio content simultaneously
   - PARALLEL: Create all document files simultaneously
   - Use computation tools for calculations and data processing
4. Organize and deliver complete output with actual files/URLs

PERFORMANCE TIP:
- When creating multiple independent materials (e.g., 5 diagrams, 3 worksheets), 
  call ALL tools in the SAME turn for parallel execution
- This reduces creation time significantly (e.g., 5 images: 50s sequential → 10s parallel)

ERROR HANDLING:
- Tools return {{"status": "failed", "error": "..."}} on failure
- OBSERVE errors and adapt your approach
- If write_script fails, try simpler instructions
- If generate_image fails, try different prompt or skip scene
- If tool fails 3 times, try alternative approach
- Keep working until you create complete materials

CRITICAL: Complete FULL deliverable creation. Return actual URLs/files, not descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[
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
            ] + self._get_computation_tools(),
        )

    def get_capabilities(self) -> List[str]:
        return [
            "domain_knowledge_provision",
            "concept_explanation",
            "problem_analysis",
            "solution_validation",
            "expert_guidance",
        ]

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, "domain_reasoning", "structured_delivery"]