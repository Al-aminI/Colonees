"""
Colonees Configuration Management
Handles environment configuration for the agent swarm platform
"""

import os
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class RuntimeConfig:
    """Runtime service configuration"""
    runtime_url: str
    memory_region: str
    memory_id: Optional[str] = None
    gateway_endpoint: str = ""
    identity_service_url: str = ""
    policy_service_url: str = ""
    observability_endpoint: str = ""
    evaluations_endpoint: str = ""


@dataclass
class MemoryStrategyConfig:
    """Memory strategy configuration"""
    enable_basic_consolidation: bool = True
    enable_entity_extraction: bool = True
    enable_relationship_mapping: bool = True
    enable_preference_tracking: bool = True
    enable_skill_assessment: bool = True
    enable_semantic_memory: bool = True

    # Strategy-specific configurations
    consolidation_frequency: str = "session_end"
    entity_extraction_threshold: float = 0.7
    relationship_mapping_depth: int = 3
    preference_adaptation_rate: float = 0.1
    skill_assessment_granularity: str = "fine_grained"

    # Domain context settings
    domain_context_enabled: bool = True
    domain_specific_extraction: bool = True
    progress_tracking_enabled: bool = True


@dataclass
class StrandsConfig:
    """Strands framework configuration"""
    default_tools: list
    session_timeout: int
    memory_retrieval_threshold: float
    max_memory_results: int
    memory_strategies: MemoryStrategyConfig


@dataclass
class CologeesConfig:
    """Main Colonees platform configuration"""

    # Runtime Services
    runtime: RuntimeConfig

    # Strands Framework
    strands: StrandsConfig

    # Platform Settings
    max_concurrent_users: int = 100000
    max_active_sessions: int = 10000
    session_timeout_minutes: int = 60

    # Agent Limits
    max_agents_per_session: int = 10
    max_agents_per_user: int = 5
    agent_execution_timeout: int = 300

    # Memory Settings
    memory_consolidation_interval: int = 3600
    max_memory_size_mb: int = 1024
    max_memory_per_session_mb: int = 512

    # Resource Quotas
    max_tool_invocations_per_minute: int = 1000
    absolute_max_users: int = 150000
    absolute_max_sessions: int = 15000
    min_concurrent_users: int = 1000

    @classmethod
    def from_environment(cls) -> 'CologeesConfig':
        """Create configuration from environment variables and YAML config"""

        yaml_config = {}
        yaml_path = Path('.env.yaml')
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}

        def get_config(yaml_key_path: str, env_var: str, default: Any) -> Any:
            value = yaml_config
            for key in yaml_key_path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            return value if value is not None else os.getenv(env_var, default)

        runtime_config = RuntimeConfig(
            runtime_url=get_config('runtime.runtime_url', 'RUNTIME_URL', 'http://127.0.0.1:9000/'),
            memory_region=get_config('memory.region', 'MEMORY_REGION', 'us-east-1'),
            memory_id=get_config('memory.id', 'MEMORY_ID', None),
            gateway_endpoint=get_config('runtime.gateway_endpoint', 'GATEWAY_ENDPOINT', 'http://127.0.0.1:9001/'),
            identity_service_url=get_config('runtime.identity_service_url', 'IDENTITY_URL', 'http://127.0.0.1:9002/'),
            policy_service_url=get_config('runtime.policy_service_url', 'POLICY_URL', 'http://127.0.0.1:9003/'),
            observability_endpoint=get_config('observability.endpoint', 'OBSERVABILITY_URL', 'http://127.0.0.1:9004/'),
            evaluations_endpoint=os.getenv('EVALUATIONS_URL', 'http://127.0.0.1:9005/')
        )

        strands_config = StrandsConfig(
            default_tools=['file_read', 'file_write'],
            session_timeout=int(os.getenv('STRANDS_SESSION_TIMEOUT', '3600')),
            memory_retrieval_threshold=float(os.getenv('STRANDS_MEMORY_THRESHOLD', '0.7')),
            max_memory_results=int(os.getenv('STRANDS_MAX_MEMORY_RESULTS', '10')),
            memory_strategies=MemoryStrategyConfig(
                enable_basic_consolidation=os.getenv('MEMORY_BASIC_CONSOLIDATION', 'true').lower() == 'true',
                enable_entity_extraction=os.getenv('MEMORY_ENTITY_EXTRACTION', 'true').lower() == 'true',
                enable_relationship_mapping=os.getenv('MEMORY_RELATIONSHIP_MAPPING', 'true').lower() == 'true',
                enable_preference_tracking=os.getenv('MEMORY_PREFERENCE_TRACKING', 'true').lower() == 'true',
                enable_skill_assessment=os.getenv('MEMORY_SKILL_ASSESSMENT', 'true').lower() == 'true',
                enable_semantic_memory=os.getenv('MEMORY_SEMANTIC', 'true').lower() == 'true',
                consolidation_frequency=os.getenv('MEMORY_CONSOLIDATION_FREQUENCY', 'session_end'),
                entity_extraction_threshold=float(os.getenv('MEMORY_ENTITY_THRESHOLD', '0.7')),
                relationship_mapping_depth=int(os.getenv('MEMORY_RELATIONSHIP_DEPTH', '3')),
                preference_adaptation_rate=float(os.getenv('MEMORY_PREFERENCE_RATE', '0.1')),
                skill_assessment_granularity=os.getenv('MEMORY_SKILL_GRANULARITY', 'fine_grained'),
                domain_context_enabled=os.getenv('MEMORY_DOMAIN_CONTEXT', 'true').lower() == 'true',
                domain_specific_extraction=os.getenv('MEMORY_DOMAIN_SPECIFIC', 'true').lower() == 'true',
                progress_tracking_enabled=os.getenv('MEMORY_PROGRESS_TRACKING', 'true').lower() == 'true'
            )
        )

        return cls(
            runtime=runtime_config,
            strands=strands_config,
            max_concurrent_users=int(os.getenv('COLONEES_MAX_USERS', '100000')),
            max_active_sessions=int(os.getenv('COLONEES_MAX_SESSIONS', '10000')),
            session_timeout_minutes=int(os.getenv('COLONEES_SESSION_TIMEOUT', '60')),
            max_agents_per_user=int(os.getenv('COLONEES_MAX_AGENTS_PER_USER', '5')),
            max_memory_per_session_mb=int(os.getenv('COLONEES_MAX_MEMORY_PER_SESSION_MB', '512')),
            max_tool_invocations_per_minute=int(os.getenv('COLONEES_MAX_TOOL_INVOCATIONS_PER_MINUTE', '1000')),
            absolute_max_users=int(os.getenv('COLONEES_ABSOLUTE_MAX_USERS', '150000')),
            absolute_max_sessions=int(os.getenv('COLONEES_ABSOLUTE_MAX_SESSIONS', '15000')),
            min_concurrent_users=int(os.getenv('COLONEES_MIN_CONCURRENT_USERS', '1000'))
        )

    def validate(self) -> bool:
        """Validate configuration settings"""
        if self.max_concurrent_users <= 0:
            raise ValueError("max_concurrent_users must be positive")
        if self.max_active_sessions <= 0:
            raise ValueError("max_active_sessions must be positive")
        if self.strands.memory_retrieval_threshold < 0 or self.strands.memory_retrieval_threshold > 1:
            raise ValueError("memory_retrieval_threshold must be between 0 and 1")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'runtime': {
                'runtime_url': self.runtime.runtime_url,
                'memory_region': self.runtime.memory_region,
                'gateway_endpoint': self.runtime.gateway_endpoint,
                'identity_service_url': self.runtime.identity_service_url,
                'policy_service_url': self.runtime.policy_service_url,
                'observability_endpoint': self.runtime.observability_endpoint,
                'evaluations_endpoint': self.runtime.evaluations_endpoint
            },
            'strands': {
                'default_tools': self.strands.default_tools,
                'session_timeout': self.strands.session_timeout,
                'memory_retrieval_threshold': self.strands.memory_retrieval_threshold,
                'max_memory_results': self.strands.max_memory_results,
            },
            'platform': {
                'max_concurrent_users': self.max_concurrent_users,
                'max_active_sessions': self.max_active_sessions,
                'session_timeout_minutes': self.session_timeout_minutes,
                'max_agents_per_session': self.max_agents_per_session,
                'max_agents_per_user': self.max_agents_per_user,
                'agent_execution_timeout': self.agent_execution_timeout,
                'max_memory_per_session_mb': self.max_memory_per_session_mb,
                'max_tool_invocations_per_minute': self.max_tool_invocations_per_minute,
            }
        }


# Backward-compat alias
GALOSConfig = CologeesConfig

# Global configuration instance
_config: Optional[CologeesConfig] = None


def get_config() -> CologeesConfig:
    """Get global Colonees configuration"""
    global _config
    if _config is None:
        _config = CologeesConfig.from_environment()
        _config.validate()
    return _config


def set_config(config: CologeesConfig) -> None:
    """Set global Colonees configuration"""
    global _config
    config.validate()
    _config = config
