"""
Colonees Agent Manager
Manages the colony of specialist agents
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.config import CologeesConfig
from ..memory import CologeesMemoryManager, ColoneesStrandsSessionManager
from ..communication.mcp_manager import MCPManager
from .colonee_registry import ColoneeRegistry

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .agent_directory import AgentDirectory


logger = logging.getLogger(__name__)


class CologeesAgentManager:
    """
    Agent manager implementing the Colonees colony architecture.

    PRINCIPLES:
    - Tool Agents: ONLY execute tools, no reasoning
    - Specialist Agents: ONLY reason and coordinate, no direct tool execution
    - Superagent: ONLY orchestrates, no tools or domain logic
    - Clear separation of responsibilities
    - Dynamic agent discovery via Agent Directory
    """

    def __init__(
        self,
        memory_manager: CologeesMemoryManager,
        agent_directory: 'AgentDirectory',
        config: CologeesConfig,
        connector_manager=None,
        kb_manager=None,
    ):
        self.memory_manager = memory_manager
        self.agent_directory = agent_directory
        self.config = config
        self.connector_manager = connector_manager
        self.kb_manager = kb_manager
        self.mcp = MCPManager()
        self.colonee_registry = ColoneeRegistry()

        from .specialist_agents import SpecialistAgentFactory
        self.specialist_factory = SpecialistAgentFactory()

        # Active specialist registry
        self.active_specialist_agents: Dict[str, Any] = {}

        # Capability mappings
        self.tool_capabilities = {
            'file_operations': 'file',
            'file_read': 'file',
            'file_write': 'file',
            'mathematical_computation': 'computation',
            'python_execution': 'computation',
            'code_interpreter': 'computation',
            'calculations': 'computation',
            'web_search': 'research',
            'information_retrieval': 'research',
            'api_access': 'research',
            'content_fetching': 'research',
            'image_generation': 'media',
            'video_processing': 'media',
            'text_to_speech': 'media',
            'diagram_creation': 'media',
            'media_processing': 'media',
            'script_generation': 'media',
            'audio_generation': 'media',
            'narration_synthesis': 'media',
            'music_generation': 'media',
            'visual_generation': 'media',
            'animation_creation': 'media',
            'video_assembly': 'media',
            'video_rendering': 'media'
        }

        self.specialist_capabilities = {
            'domain_knowledge_provision': 'domain_expert',
            'concept_explanation': 'domain_expert',
            'problem_analysis': 'domain_expert',
            'solution_validation': 'domain_expert',
            'expert_guidance': 'domain_expert',
            'research_strategy_design': 'researcher',
            'information_synthesis': 'researcher',
            'source_validation': 'researcher',
            'research_methodology': 'researcher',
            'assessment_design': 'analyst',
            'data_analysis': 'analyst',
            'progress_evaluation': 'analyst',
            'feedback_strategy': 'analyst',
            'rubric_creation': 'analyst',
            'task_automation': 'executor',
            'code_execution': 'executor',
            'file_management': 'executor',
            'video_creation': 'media_producer',
            'video_planning': 'media_producer',
            'asset_coordination': 'media_producer',
            'creative_direction': 'media_producer',
        }

        # NOTE: No _agent_type_map needed — the factory's ColoneeRegistry lookup
        # and its own internal legacy map handle all type resolution.

        logger.info("Colonees Agent Manager initialized")
        self._sync_capabilities_from_registry()

    def _sync_capabilities_from_registry(self) -> None:
        """
        Sync specialist_capabilities map from the colonee registry so that
        user-defined colonees with custom capabilities are discoverable by
        the superagent's discover_agents_for_capabilities().
        """
        for defn in self.colonee_registry.list(enabled_only=True):
            for cap in defn.capabilities:
                if cap not in self.specialist_capabilities:
                    self.specialist_capabilities[cap] = defn.name

    async def create_specialist_agent(
        self,
        specialist_type: str,
        specialization: str,
        session_id: str,
        agent_id: Optional[str] = None,
        workspace: Optional[str] = None,
    ) -> Any:
        """Create a Specialist Agent with its own Strands session manager."""
        # Each specialist gets a session-scoped Strands session manager so its
        # conversation history is persisted and restored via the memory backend.
        strands_session = ColoneesStrandsSessionManager(
            session_id=session_id,
            backend=self.memory_manager.backend,
        )

        specialist_agent = self.specialist_factory.create_specialist_agent(
            specialist_type=specialist_type,
            specialization=specialization,
            session_manager=strands_session,
            agent_id=agent_id,
            agent_manager=self,
            agent_directory=self.agent_directory,
            mcp_manager=self.mcp,
            colonee_registry=self.colonee_registry,
            connector_manager=self.connector_manager,
            kb_manager=self.kb_manager,
            workspace=workspace,
        )

        self.active_specialist_agents[specialist_agent.agent_id] = specialist_agent

        await self._register_specialist_in_directory(specialist_agent, specialist_type, specialization)

        logger.info(f"Created Specialist Agent: {specialist_agent.agent_id} (type: {specialist_type}, specialization: {specialization})")
        return specialist_agent

    async def discover_agents_for_capabilities(self, capabilities: List[str]) -> Dict[str, List[str]]:
        """Discover which agent types are needed for given capabilities"""
        discovery = {
            'tool_providers_needed': [],
            'specialist_agents_needed': [],
            'capability_coverage': {}
        }

        for capability in capabilities:
            coverage = []

            if capability in self.tool_capabilities:
                tool_type = self.tool_capabilities[capability]
                if tool_type not in discovery['tool_providers_needed']:
                    discovery['tool_providers_needed'].append(tool_type)
                coverage.append(f"tool:{tool_type}")

            if capability in self.specialist_capabilities:
                specialist_type = self.specialist_capabilities[capability]
                if specialist_type not in discovery['specialist_agents_needed']:
                    discovery['specialist_agents_needed'].append(specialist_type)
                coverage.append(f"specialist:{specialist_type}")

            discovery['capability_coverage'][capability] = coverage

        return discovery

    def get_active_agents_stats(self) -> Dict[str, Any]:
        return {
            'active_specialist_agents': len(self.active_specialist_agents),
        }

    async def cleanup_session_agents(self, session_id: str):
        """Clean up specialist agents for a specific session"""
        to_remove = [
            agent_id for agent_id, agent in self.active_specialist_agents.items()
            if hasattr(agent, 'session_manager') and session_id in str(agent.session_manager)
        ]
        for agent_id in to_remove:
            del self.active_specialist_agents[agent_id]
        logger.info("Session cleanup complete: %d specialist agents removed", len(to_remove))

    async def cleanup_agent(self, agent_id: str) -> bool:
        try:
            if agent_id in self.active_specialist_agents:
                del self.active_specialist_agents[agent_id]
                return True
            logger.warning(f"Agent {agent_id} not found for cleanup")
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup agent {agent_id}: {e}")
            return False

    def get_agent_capabilities(self, agent_type: str) -> Dict[str, Any]:
        """Get capabilities for specific agent type"""
        if agent_type in ['domain_expert', 'researcher', 'analyst', 'executor', 'media_producer']:
            return {'type': 'specialist', 'agent_type': agent_type}
        elif agent_type in ['file', 'computation', 'research_tools', 'media']:
            return {'type': 'tool', 'agent_type': agent_type}
        return {}

    def get_agent_stats(self) -> Dict[str, Any]:
        return {
            'architecture': 'colonees_colony',
            'active_agents': self.get_active_agents_stats(),
            'supported_specialist_types': self.specialist_factory.get_available_specialist_types(
                colonee_registry=self.colonee_registry
            ),
            'mcp_servers': self.mcp.list_servers(),
            'colonees': [c.name for c in self.colonee_registry.list()],
        }

    async def _register_specialist_in_directory(self, agent, specialist_type: str, specialization: str):
        """Register a specialist agent in the agent directory"""
        try:
            from .agent_directory import AgentMetadata, AgentType, AgentStatus, AgentCapability

            agent_capabilities = agent.get_capabilities()

            capabilities = [
                AgentCapability(
                    name=cap,
                    description=f"{specialist_type} capability: {cap}",
                    parameters={},
                    cost_per_invocation=0.01,
                    average_execution_time=2.0
                )
                for cap in agent_capabilities
            ]

            metadata = AgentMetadata(
                agent_id=agent.agent_id,
                name=f"{specialist_type}_{specialization}",
                description=f"Specialist agent for {specialist_type} in {specialization} domain",
                agent_type=AgentType.SPECIALIST,
                specialization=specialization,
                capabilities=capabilities,
                status=AgentStatus.AVAILABLE,
                endpoint=f"local://specialist/{agent.agent_id}",
                framework="strands",
                tools=[],
                memory_enabled=True,
                a2a_enabled=True,
                load=0.0,
                last_heartbeat=datetime.now(),
                created_at=datetime.now(),
                version="1.0.0"
            )

            await self.agent_directory.register_agent(metadata)
            logger.info(f"Registered specialist agent {agent.agent_id} in directory with {len(capabilities)} capabilities")

        except Exception as e:
            logger.error(f"Failed to register specialist agent in directory: {e}")

