"""
Colonees Configuration Management
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CologeesConfig:
    """Colonees platform configuration."""

    # Concurrency limits
    max_concurrent_users: int = 100000
    max_active_sessions: int = 10000
    session_timeout_minutes: int = 60

    # Agent limits
    max_agents_per_user: int = 5
    max_agents_per_session: int = 10
    agent_execution_timeout: int = 300

    # Memory limits
    max_memory_per_session_mb: int = 512

    # Tool limits
    max_tool_invocations_per_minute: int = 1000

    # Storage paths
    files_dir: str = "colonees_files"
    media_dir: str = "colonees_media"
    registry_path: str = "colonees_files/colonee_registry.json"

    # Logging
    log_level: str = "INFO"
    environment: str = "local"

    @classmethod
    def from_environment(cls) -> "CologeesConfig":
        return cls(
            max_concurrent_users=int(os.getenv("COLONEES_MAX_USERS", "100000")),
            max_active_sessions=int(os.getenv("COLONEES_MAX_SESSIONS", "10000")),
            session_timeout_minutes=int(os.getenv("COLONEES_SESSION_TIMEOUT", "60")),
            max_agents_per_user=int(os.getenv("COLONEES_MAX_AGENTS_PER_USER", "5")),
            agent_execution_timeout=int(os.getenv("COLONEES_AGENT_TIMEOUT", "300")),
            max_memory_per_session_mb=int(os.getenv("COLONEES_MAX_MEMORY_PER_SESSION_MB", "512")),
            max_tool_invocations_per_minute=int(os.getenv("COLONEES_MAX_TOOL_INVOCATIONS_PER_MINUTE", "1000")),
            files_dir=os.getenv("COLONEES_FILES_DIR", "colonees_files"),
            media_dir=os.getenv("COLONEES_MEDIA_DIR", "colonees_media"),
            registry_path=os.getenv("COLONEES_REGISTRY_PATH", "colonees_files/colonee_registry.json"),
            log_level=os.getenv("COLONEES_LOG_LEVEL", "INFO"),
            environment=os.getenv("COLONEES_ENVIRONMENT", "local"),
        )

    def validate(self) -> bool:
        if self.max_concurrent_users <= 0:
            raise ValueError("max_concurrent_users must be positive")
        if self.max_active_sessions <= 0:
            raise ValueError("max_active_sessions must be positive")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_concurrent_users": self.max_concurrent_users,
            "max_active_sessions": self.max_active_sessions,
            "session_timeout_minutes": self.session_timeout_minutes,
            "max_agents_per_user": self.max_agents_per_user,
            "max_agents_per_session": self.max_agents_per_session,
            "agent_execution_timeout": self.agent_execution_timeout,
            "max_memory_per_session_mb": self.max_memory_per_session_mb,
            "max_tool_invocations_per_minute": self.max_tool_invocations_per_minute,
            "files_dir": self.files_dir,
            "media_dir": self.media_dir,
            "environment": self.environment,
        }


# Global singleton
_config: Optional[CologeesConfig] = None


def get_config() -> CologeesConfig:
    global _config
    if _config is None:
        _config = CologeesConfig.from_environment()
        _config.validate()
    return _config


def set_config(config: CologeesConfig) -> None:
    global _config
    config.validate()
    _config = config
