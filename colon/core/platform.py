"""
Colonees Platform Core
Main platform class that orchestrates the agent swarm
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .config import CologeesConfig, get_config
from .workflow_orchestrator import ColoneesSupervisorAgent
from .resource_manager import CologeesResourceManager
from ..agents.agent_manager import CologeesAgentManager
from ..agents.agent_directory import AgentDirectory
from ..memory import CologeesMemoryManager, ColoneesStrandsSessionManager, CologeesSessionManager


logger = logging.getLogger(__name__)



class ColoneesPlatform:
    """
    Main Colonees platform class — The Autonomous Agent Swarm Platform.
    Coordinates a superagent with an extensible colony of domain-specialist agents.
    Domain-agnostic: deployable across any vertical.
    """

    def __init__(self, config: Optional[CologeesConfig] = None):
        self.config = config or get_config()

        # Platform components
        self.session_manager: Optional[CologeesSessionManager] = None
        self.memory_manager: Optional[CologeesMemoryManager] = None
        self.agent_manager: Optional[CologeesAgentManager] = None
        self.agent_directory: Optional[AgentDirectory] = None
        self.resource_manager: Optional[CologeesResourceManager] = None
        self.supervisor_agent: Optional[ColoneesSupervisorAgent] = None

        # Platform state
        self.is_initialized = False
        self.active_sessions: Dict[str, Any] = {}
        self.platform_metrics = {
            'total_sessions_created': 0,
            'total_agents_spawned': 0,
            'total_requests_handled': 0,
            'platform_start_time': None
        }

        logger.info("Colonees Platform initialized")

    async def initialize(self) -> None:
        """Initialize all platform components"""
        if self.is_initialized:
            logger.warning("Platform already initialized")
            return

        try:
            logger.info("Initializing Colonees Platform components...")
            await self._initialize_platform_components()
            self.is_initialized = True
            self.platform_metrics['platform_start_time'] = datetime.now()
            logger.info("Colonees Platform successfully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Colonees Platform: {e}")
            raise

    async def _initialize_platform_components(self) -> None:
        """Initialize Colonees platform-specific components"""
        try:
            self.session_manager = CologeesSessionManager(config=self.config)
            logger.info("Session Manager initialized")

            self.memory_manager = CologeesMemoryManager(config=self.config)
            logger.info("Memory Manager initialized")

            self.agent_directory = AgentDirectory()
            logger.info("Agent Directory initialized")

            # Lazily import connector and KB managers so the platform
            # wires them into agent spawning automatically.
            from colon.connectors.connector_registry import ConnectorManager
            from colon.core.knowledge_base import KnowledgeBaseManager
            import os

            storage_dir = os.getenv("COLONEES_STORAGE_DIR", "colonees_files")
            connector_manager = ConnectorManager(storage_dir=storage_dir)
            kb_manager = KnowledgeBaseManager(storage_dir=storage_dir)

            self.agent_manager = CologeesAgentManager(
                memory_manager=self.memory_manager,
                agent_directory=self.agent_directory,
                config=self.config,
                connector_manager=connector_manager,
                kb_manager=kb_manager,
            )
            logger.info("Agent Manager initialized (with connector + KB managers)")

            self.resource_manager = CologeesResourceManager(config=self.config)
            logger.info("Resource Manager initialized")

            supervisor_session_id, _ = await self.session_manager.create_session(
                context={
                    "agent_type": "supervisor",
                    "specialization": "generic_orchestration",
                    "system_agent": True,
                }
            )

            # Give the supervisor a Strands-native session manager so its
            # conversation history persists across requests.
            supervisor_strands_session = ColoneesStrandsSessionManager(
                session_id=supervisor_session_id,
                backend=self.memory_manager.backend,
            )

            self.supervisor_agent = ColoneesSupervisorAgent(
                session_manager=supervisor_strands_session,
                agent_directory=self.agent_directory,
                agent_manager=self.agent_manager,
                platform_session_manager=self.session_manager,
            )
            logger.info("Supervisor Agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize platform components: {e}")
            await self._handle_component_initialization_failure(e)
            raise

    async def _handle_component_initialization_failure(self, error: Exception):
        """Handle component initialization failures with graceful degradation"""
        logger.error(f"Component initialization failed: {error}")
        try:
            if not self.agent_directory:
                self.agent_directory = AgentDirectory()
        except Exception as fallback_error:
            logger.critical(f"Fallback initialization also failed: {fallback_error}")
            raise

    async def handle_request(self, user_goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        MAIN ENTRY POINT: Handle any user request through the agent swarm.
        The superagent autonomously orchestrates specialist agents to accomplish the goal.
        """
        if not self.is_initialized:
            raise RuntimeError("Platform not initialized. Call initialize() first.")

        # Track this request as an active session so status reflects real load
        request_key = f"request_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}"
        self.active_sessions[request_key] = {'started_at': datetime.now(), 'goal': user_goal}

        # Resolve session_id for memory storage — caller may pass one in context
        session_id: Optional[str] = context.get("session_id") or request_key

        try:
            # Store the incoming request in conversation history
            await self.memory_manager.store(
                session_id=session_id,
                role="user",
                content=user_goal,
                metadata={"context": {k: v for k, v in context.items() if k != "session_id"}},
            )

            result = await self.supervisor_agent.handle_request(user_goal, context)
            self.platform_metrics['total_requests_handled'] = self.platform_metrics.get('total_requests_handled', 0) + 1

            agent_result = result.get('result')
            if agent_result:
                if hasattr(agent_result, 'text'):
                    response_text = agent_result.text
                elif hasattr(agent_result, 'content'):
                    response_text = agent_result.content
                else:
                    response_text = str(agent_result)
            else:
                response_text = "Request processed."

            # Store the assistant response
            await self.memory_manager.store(
                session_id=session_id,
                role="assistant",
                content=response_text,
                metadata={
                    "task_id": result.get("task_id"),
                    "status": result.get("status", "completed"),
                    "final_asset": result.get("final_asset"),
                },
            )

            return {
                'status': result.get('status', 'completed'),
                'response': response_text,
                'final_asset': result.get('final_asset'),
                'agents_used': result.get('execution_trace', []),
                'task_id': result.get('task_id'),
                'session_id': session_id,
                'user_goal': user_goal,
                'metadata': {
                    'platform': 'Colonees',
                    'orchestration_type': 'autonomous_superagent',
                    'safety_metrics': result.get('safety_metrics', {})
                }
            }

        except Exception as e:
            logger.error(f"Failed to handle request: {e}")
            await self.memory_manager.store(
                session_id=session_id,
                role="error",
                content=str(e),
                metadata={"user_goal": user_goal},
            )
            return {
                'status': 'failed',
                'error': str(e),
                'response': f"Error processing request: {str(e)}",
                'session_id': session_id,
                'user_goal': user_goal
            }

        finally:
            self.active_sessions.pop(request_key, None)

    async def get_platform_status(self) -> Dict[str, Any]:
        """Get current platform status and metrics"""
        resource_stats = {}
        if self.resource_manager:
            resource_stats = self.resource_manager.get_resource_stats()

        memory_stats = {}
        if self.memory_manager:
            memory_stats = self.memory_manager.get_stats()

        return {
            'platform_initialized': self.is_initialized,
            'active_sessions': len(self.active_sessions),
            'metrics': self.platform_metrics.copy(),
            'resource_stats': resource_stats,
            'memory_stats': memory_stats,
            'config_summary': {
                'max_concurrent_users': self.config.max_concurrent_users,
                'max_active_sessions': self.config.max_active_sessions,
                'environment': self.config.environment,
            }
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the platform"""
        logger.info("Shutting down Colonees Platform...")

        if self.resource_manager:
            await self.resource_manager.stop_monitoring()

        if self.session_manager:
            await self.session_manager.shutdown()

        self.active_sessions.clear()
        self.is_initialized = False
        logger.info("Colonees Platform shutdown complete")

