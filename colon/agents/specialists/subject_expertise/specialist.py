"""
Domain Expert Specialist Agent

Provides deep domain expertise and knowledge capabilities for any vertical.
Uses Strands framework with tool access for domain reasoning.
"""

from typing import List
from strands import Agent
from galos.agents.specialist_agents import BaseSpecialistAgent
from galos.agents.utils import extract_tool_metadata
from galos.core.model_config import get_model
import logging

logger = logging.getLogger(__name__)


class SubjectExpertSpecialistAgent(BaseSpecialistAgent):
    """
    Specialist Agent for domain expertise and knowledge
    Reasons about domain concepts and uses tools through Strands framework
    """
    
    def __init__(self, session_manager, agent_id: str, specialization: str, agent_manager=None):
        self.agent_manager = agent_manager
        self._media_agent = None
        self._computation_agent = None
        self._research_agent = None
        super().__init__(session_manager, agent_id, specialization)
    
    def _get_media_agent(self):
        if self._media_agent is None:
            from galos.agents.tools.media.media_agent import MediaToolAgent
            self._media_agent = MediaToolAgent(self.session_manager, f"{self.agent_id}_media")
        return self._media_agent

    def _get_computation_agent(self):
        if self._computation_agent is None:
            from galos.agents.tools.computation.computation_agent import ComputationToolAgent
            self._computation_agent = ComputationToolAgent(self.session_manager, f"{self.agent_id}_computation")
        return self._computation_agent

    def _get_research_agent(self):
        if self._research_agent is None:
            from galos.agents.tools.research.research_agent import ResearchToolAgent
            self._research_agent = ResearchToolAgent(self.session_manager, f"{self.agent_id}_research")
        return self._research_agent

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
        """Create specialist agent with direct tool access"""
        media_agent = self._get_media_agent()
        
        return Agent(
            name=self.agent_id,
            system_prompt=f"""You are a {self.specialization} Subject Expert Specialist with full autonomy to provide deep domain knowledge end-to-end.
            
YOUR ROLE — domain expertise and knowledge provision:
- Provide accurate domain knowledge and explanations
- Analyze complex problems in your domain
- Validate information and solutions
- Guide problem-solving approaches
- Create supporting materials (visualizations, calculations, research)
- YOU MUST PRODUCE ACTUAL EXPLANATIONS WITH SUPPORTING MATERIALS, NOT JUST DESCRIPTIONS

=== MEDIA PRODUCTION TOOLS ===

create_production(production_name: str)
  Returns: {{"status": "success", "production_dir": str, "production_id": str}}
  Initialize local storage for visual materials (call FIRST for any media work)

sanitize_image_prompt(prompt: str)
  Returns: {{"status": "success", "sanitized_prompt": str, "changes_made": List}}
  Clean visual descriptions before image generation. ALWAYS call before generate_image.

generate_image(prompt: str, course: str = "", max_retries: int = 3)
  Returns: {{"status": "success", "local_path": str, "attempt": int}}
  Generate diagrams, visualizations, concept illustrations via Gemini.
  Handles retries and content-filter fallbacks automatically. Use sanitized prompts.

resize_image(local_path: str, width: int = 1280, height: int = 720)
  Returns: {{"status": "success", "local_path": str, "width": int, "height": int}}
  Resize images to exact dimensions for consistent display.

save_to_disk(key: str, content: str)
  Returns: {{"status": "success", "local_path": str}}
  Persist text content (explanations, notes) to local storage.

load_from_disk(key: str)
  Returns: str (content directly, or "ERROR loading <key>: <message>" on failure)
  Retrieve saved content. May be JSON - parse if needed.

=== COMPUTATION TOOLS ===

calculator(expression: str)
  Advanced mathematical calculations with symbolic math capabilities.
  Supports: algebra, calculus, trigonometry, complex numbers, matrices.
  Returns computed result.

=== RESEARCH TOOLS ===

http_request(url: str, method: str = "GET", headers: Optional[Dict] = None, data: Optional[Dict] = None)
  Make API calls for current information. Supports authentication.
  Returns response data.

WORKFLOW GUIDANCE:
1. Understand the concept and complexity level needed
2. Provide expert definition and key principles
3. Use tools to enhance explanation:
   - generate_image for visual concepts (diagrams, charts, illustrations)
   - calculator for calculations and demonstrations
   - http_request for current information and validation
4. Synthesize into comprehensive explanation with supporting materials

EXAMPLE WORKFLOW (explaining a complex concept):
1. create_production_bucket(production_name="Domain Explanation")
2. Provide expert definition and key principles
3. sanitize_image_prompt(prompt="diagram illustrating the concept with clear labels")
4. generate_image(prompt=sanitized_prompt, course=self.specialization)
5. calculator(expression="relevant calculation or formula demonstration")
6. Synthesize explanation with actual image URLs and calculation results

ERROR HANDLING:
- Tools return {{"status": "failed", "error": "..."}} on failure
- OBSERVE errors and adapt your approach
- If generate_image fails, try simpler prompt or skip visualization
- Keep working until you provide complete explanation

CRITICAL: Focus on domain expertise and conceptual depth. Complete FULL explanations with actual supporting materials (URLs, calculations, visualizations), not just descriptions.""",
            model=get_model(),
            session_manager=self.session_manager,
            tools=[
                # Media tools (ALL 12 tools)
                media_agent.create_production_bucket,
                media_agent.write_script,
                media_agent.sanitize_image_prompt,
                media_agent.generate_image,
                media_agent.resize_image,
                media_agent.text_to_speech,
                media_agent.assemble_video,
                media_agent.save_to_s3,
                media_agent.load_from_s3,
                media_agent.list_artifacts,
                media_agent.delete_artifact,
                media_agent.get_production_info,
            ] + self._get_computation_tools() + self._get_research_tools()
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            'domain_knowledge_provision',
            'concept_explanation',
            'problem_analysis',
            'solution_validation',
            'expert_guidance'
        ]
    
    def get_domain_expertise(self) -> List[str]:
        return [self.specialization, f'{self.specialization}_theory', f'{self.specialization}_applications']
