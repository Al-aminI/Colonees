"""
Colonees Platform Core
Main platform class that orchestrates the agent swarm
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from strands import Agent

from .config import CologeesConfig, get_config
from .workflow_orchestrator import ColoneesSupervisorAgent
from .safety_enforcer import SafetyEnforcer
from .resource_manager import CologeesResourceManager
from ..agents.agent_manager import CologeesAgentManager
from ..agents.agent_directory import AgentDirectory
from ..session import CologeesSessionManager
from ..memory import CologeesMemoryManager


logger = logging.getLogger(__name__)



class ColoneesPlatform:
    """
    Main Colonees platform class — The Kubernetes + OS for AI Agents.
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
        self.safety_enforcer: Optional[SafetyEnforcer] = None
        self.resource_manager: Optional[CologeesResourceManager] = None
        self.supervisor_agent: Optional[ColoneesSupervisorAgent] = None

        # Platform state
        self.is_initialized = False
        self.active_sessions: Dict[str, Any] = {}
        self.platform_metrics = {
            'total_sessions_created': 0,
            'active_users': 0,
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

            self.agent_manager = CologeesAgentManager(
                session_manager=self.session_manager,
                memory_manager=self.memory_manager,
                agent_directory=self.agent_directory,
                config=self.config
            )
            logger.info("Agent Manager initialized")

            self.safety_enforcer = SafetyEnforcer()
            logger.info("Safety Enforcer initialized")

            self.resource_manager = CologeesResourceManager(config=self.config)
            logger.info("Resource Manager initialized")

            supervisor_user_id = "system_supervisor"
            logger.info("Memory disabled: Skipping supervisor memory creation")

            supervisor_session_data = await self.session_manager.create_session(
                user_id=supervisor_user_id,
                context={
                    'agent_type': 'supervisor',
                    'specialization': 'generic_orchestration',
                    'system_agent': True
                }
            )

            supervisor_session_manager = supervisor_session_data[1]['memory_session_manager']

            self.supervisor_agent = ColoneesSupervisorAgent(
                session_manager=supervisor_session_manager,
                agent_directory=self.agent_directory,
                safety_enforcer=self.safety_enforcer,
                agent_manager=self.agent_manager,
                platform_session_manager=self.session_manager
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
            if not self.safety_enforcer:
                self.safety_enforcer = SafetyEnforcer()
        except Exception as fallback_error:
            logger.critical(f"Fallback initialization also failed: {fallback_error}")
            raise

    async def create_session(self, user_id: str, context: Dict[str, Any]) -> str:
        """Create new session"""
        if not self.is_initialized:
            raise RuntimeError("Platform not initialized. Call initialize() first.")

        session_id, session_data = await self.session_manager.create_session(
            user_id=user_id,
            context=context
        )

        self.active_sessions[session_id] = session_data
        self.platform_metrics['total_sessions_created'] += 1
        logger.info(f"Session created: {session_id} for user: {user_id}")
        return session_id

    async def handle_request(self, user_goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        MAIN ENTRY POINT: Handle any user request through the agent swarm.
        The superagent autonomously orchestrates specialist agents to accomplish the goal.
        """
        if not self.is_initialized:
            raise RuntimeError("Platform not initialized. Call initialize() first.")

        try:
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

            return {
                'status': result.get('status', 'completed'),
                'response': response_text,
                'final_asset': result.get('final_asset'),
                'agents_used': result.get('execution_trace', []),
                'execution_time': 0,
                'session_id': context.get('session_id'),
                'task_id': result.get('task_id'),
                'user_goal': user_goal,
                'metadata': {
                    'platform': 'Colonees',
                    'orchestration_type': 'autonomous_superagent',
                    'safety_metrics': result.get('safety_metrics', {})
                }
            }

        except Exception as e:
            logger.error(f"Failed to handle request: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'response': f"Error processing request: {str(e)}",
                'user_goal': user_goal
            }

    async def get_platform_status(self) -> Dict[str, Any]:
        """Get current platform status and metrics"""
        resource_stats = {}
        if self.resource_manager:
            resource_stats = self.resource_manager.get_resource_stats()

        return {
            'platform_initialized': self.is_initialized,
            'active_sessions': len(self.active_sessions),
            'metrics': self.platform_metrics.copy(),
            'resource_stats': resource_stats,
            'config_summary': {
                'max_concurrent_users': self.config.max_concurrent_users,
                'max_active_sessions': self.config.max_active_sessions,
                'memory_region': self.config.runtime.memory_region
            }
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the platform"""
        logger.info("Shutting down Colonees Platform...")

        if self.resource_manager:
            await self.resource_manager.stop_monitoring()

        for session_id in list(self.active_sessions.keys()):
            try:
                await self.session_manager.cleanup_session(session_id)
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")

        self.is_initialized = False
        logger.info("Colonees Platform shutdown complete")


# Backward-compat alias
GALOSPlatform = ColoneesPlatform
