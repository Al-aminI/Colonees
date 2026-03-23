"""
Colonees Resource Manager
Tracks resource usage and enforces quotas for the agent swarm platform.
"""

import logging
from typing import Any, Dict

from .config import CologeesConfig

logger = logging.getLogger(__name__)


class CologeesResourceManager:
    """
    Tracks active sessions, agents, and tool invocations.
    Enforces the quotas defined in CologeesConfig.
    """

    def __init__(self, config: CologeesConfig):
        self.config = config
        self._active_sessions: int = 0
        self._active_agents: int = 0
        self._tool_invocations: int = 0

        logger.info("Resource Manager initialized")

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------

    def record_session_created(self) -> None:
        self._active_sessions += 1

    def record_session_closed(self) -> None:
        self._active_sessions = max(0, self._active_sessions - 1)

    def record_agent_spawned(self) -> None:
        self._active_agents += 1

    def record_agent_closed(self) -> None:
        self._active_agents = max(0, self._active_agents - 1)

    def record_tool_invocation(self) -> None:
        self._tool_invocations += 1

    # ------------------------------------------------------------------
    # Quota checks
    # ------------------------------------------------------------------

    def check_session_quota(self) -> bool:
        """Returns True if a new session can be created."""
        return self._active_sessions < self.config.max_active_sessions

    def check_agent_quota(self, agents_for_user: int) -> bool:
        """Returns True if a new agent can be spawned for this user."""
        return agents_for_user < self.config.max_agents_per_user

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_resource_stats(self) -> Dict[str, Any]:
        return {
            "active_sessions": self._active_sessions,
            "active_agents": self._active_agents,
            "tool_invocations_total": self._tool_invocations,
            "quotas": {
                "max_active_sessions": self.config.max_active_sessions,
                "max_agents_per_user": self.config.max_agents_per_user,
                "max_tool_invocations_per_minute": self.config.max_tool_invocations_per_minute,
            },
        }

    async def stop_monitoring(self) -> None:
        """No-op — kept for interface compatibility."""
        pass
