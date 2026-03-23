"""
Colonees Agent Directory
Dynamic agent discovery and registration system for the Agent Operating System
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class AgentType(Enum):
    SUPERVISOR = "supervisor"
    SPECIALIST = "specialist"
    TOOL = "tool"


@dataclass
class AgentCapability:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    cost_per_invocation: float = 0.0
    average_execution_time: float = 0.0  # seconds


@dataclass
class AgentMetadata:
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    specialization: str
    capabilities: List[AgentCapability]
    endpoint: str
    status: AgentStatus
    load: float  # 0.0 to 1.0
    last_heartbeat: datetime
    created_at: datetime
    version: str
    framework: str = "strands"
    memory_enabled: bool = True
    a2a_enabled: bool = True
    tools: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)


@dataclass
class AgentSelectionCriteria:
    required_capabilities: List[str]
    preferred_specializations: List[str] = field(default_factory=list)
    max_load_threshold: float = 0.8
    max_cost_per_task: float = float('inf')
    max_response_time: float = 30.0  # seconds
    require_memory: bool = False
    require_a2a: bool = False
    exclude_agents: Set[str] = field(default_factory=set)


class AgentDirectory:
    """
    Dynamic Agent Directory for Colonees Agent Operating System

    Provides:
    - Dynamic agent registration and discovery
    - Capability-based agent matching
    - Load balancing and availability tracking
    - Performance-based agent selection
    - Real-time agent health monitoring
    """
    
    def __init__(self):
            self.agents: Dict[str, AgentMetadata] = {}
            self.capability_index: Dict[str, Set[str]] = {}  # capability -> agent_ids
            self.specialization_index: Dict[str, Set[str]] = {}  # specialization -> agent_ids
            self.type_index: Dict[AgentType, Set[str]] = {
                AgentType.SUPERVISOR: set(),
                AgentType.SPECIALIST: set(),
                AgentType.TOOL: set()
            }

            # Configuration (kept for compatibility but not used for cleanup)
            self.heartbeat_timeout = timedelta(minutes=5)
            self.cleanup_interval = timedelta(minutes=10)
            self.max_agents_per_capability = 100

            # Statistics
            self.stats = {
                'total_registrations': 0,
                'total_discoveries': 0,
                'total_selections': 0,
                'average_selection_time': 0.0,
                'last_cleanup': datetime.now()
            }

            # No background tasks needed for single-process direct orchestration
            self._cleanup_task = None

            logger.info("Agent Directory initialized (single-process mode)")
    
    
    
    
    async def register_agent(self, metadata: AgentMetadata) -> bool:
        """Register a new agent in the directory"""
        try:
            agent_id = metadata.agent_id
            
            # Validate agent metadata
            if not self._validate_agent_metadata(metadata):
                logger.error(f"Invalid agent metadata for {agent_id}")
                return False
            
            # Check if agent already exists
            if agent_id in self.agents:
                logger.warning(f"Agent {agent_id} already registered, updating...")
                await self.deregister_agent(agent_id)
            
            # Register agent
            self.agents[agent_id] = metadata
            
            # Update indexes
            self._update_indexes_for_registration(metadata)
            
            # Update statistics
            self.stats['total_registrations'] += 1
            
            logger.info(f"Agent registered: {agent_id} ({metadata.agent_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {metadata.agent_id}: {e}")
            return False
    
    async def deregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the directory"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found for deregistration")
                return False
            
            metadata = self.agents[agent_id]
            
            # Remove from indexes
            self._update_indexes_for_deregistration(metadata)
            
            # Remove from main registry
            del self.agents[agent_id]
            
            logger.info(f"Agent deregistered: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deregister agent {agent_id}: {e}")
            return False
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, load: float = None) -> bool:
        """Update agent status and load"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found for status update")
                return False
            
            metadata = self.agents[agent_id]
            metadata.status = status
            metadata.last_heartbeat = datetime.now()
            
            if load is not None:
                metadata.load = max(0.0, min(1.0, load))  # Clamp to [0, 1]
            
            logger.debug(f"Agent {agent_id} status updated: {status.value}, load: {metadata.load}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} status: {e}")
            return False
    
    async def heartbeat(self, agent_id: str, performance_metrics: Dict[str, float] = None) -> bool:
        """Process agent heartbeat"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Heartbeat from unknown agent: {agent_id}")
                return False
            
            metadata = self.agents[agent_id]
            metadata.last_heartbeat = datetime.now()
            
            if performance_metrics:
                metadata.performance_metrics.update(performance_metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process heartbeat from {agent_id}: {e}")
            return False
    
    async def find_agents_by_capabilities(
        self, 
        capabilities: List[str], 
        availability_filter: bool = True
    ) -> List[AgentMetadata]:
        """Find agents that have the specified capabilities"""
        try:
            self.stats['total_discoveries'] += 1
            
            if not capabilities:
                return []
            
            # Find agents with all required capabilities
            candidate_agents = None
            
            for capability in capabilities:
                agents_with_capability = self.capability_index.get(capability, set())
                
                if candidate_agents is None:
                    candidate_agents = agents_with_capability.copy()
                else:
                    candidate_agents &= agents_with_capability
            
            if not candidate_agents:
                return []
            
            # Filter by availability if requested
            result = []
            for agent_id in candidate_agents:
                if agent_id in self.agents:
                    metadata = self.agents[agent_id]
                    
                    if availability_filter:
                        if metadata.status == AgentStatus.AVAILABLE and metadata.load < 1.0:
                            result.append(metadata)
                    else:
                        result.append(metadata)
            
            logger.debug(f"Found {len(result)} agents with capabilities: {capabilities}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to find agents by capabilities {capabilities}: {e}")
            return []
    
    async def find_agents_by_specialization(self, specialization: str) -> List[AgentMetadata]:
        """Find agents with specific specialization"""
        try:
            agent_ids = self.specialization_index.get(specialization, set())
            result = []
            
            for agent_id in agent_ids:
                if agent_id in self.agents:
                    result.append(self.agents[agent_id])
            
            logger.debug(f"Found {len(result)} agents with specialization: {specialization}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to find agents by specialization {specialization}: {e}")
            return []
    
    async def select_optimal_agent(
        self, 
        candidates: List[AgentMetadata], 
        task_requirements: Dict[str, Any]
    ) -> Optional[AgentMetadata]:
        """Select the optimal agent from candidates based on task requirements"""
        try:
            self.stats['total_selections'] += 1
            start_time = datetime.now()
            
            if not candidates:
                return None
            
            # Score each candidate
            scored_candidates = []
            
            for candidate in candidates:
                score = self._calculate_agent_score(candidate, task_requirements)
                scored_candidates.append((score, candidate))
            
            # Sort by score (higher is better)
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            
            # Update selection time statistics
            selection_time = (datetime.now() - start_time).total_seconds()
            self.stats['average_selection_time'] = (
                (self.stats['average_selection_time'] * (self.stats['total_selections'] - 1) + selection_time) /
                self.stats['total_selections']
            )
            
            selected_agent = scored_candidates[0][1]
            logger.debug(f"Selected optimal agent: {selected_agent.agent_id} (score: {scored_candidates[0][0]:.2f})")
            
            return selected_agent
            
        except Exception as e:
            logger.error(f"Failed to select optimal agent: {e}")
            return None
    
    def _calculate_agent_score(self, agent: AgentMetadata, task_requirements: Dict[str, Any]) -> float:
        """Calculate agent suitability score for a task"""
        score = 0.0
        
        # Base availability score (higher is better)
        if agent.status == AgentStatus.AVAILABLE:
            score += 100.0
        elif agent.status == AgentStatus.BUSY:
            score += 50.0
        else:
            return 0.0  # Offline or maintenance agents get 0 score
        
        # Load score (lower load is better)
        load_score = (1.0 - agent.load) * 50.0
        score += load_score
        
        # Performance score based on metrics
        if 'average_response_time' in agent.performance_metrics:
            response_time = agent.performance_metrics['average_response_time']
            # Lower response time is better
            response_score = max(0, 30.0 - response_time)
            score += response_score
        
        if 'success_rate' in agent.performance_metrics:
            success_rate = agent.performance_metrics['success_rate']
            score += success_rate * 20.0
        
        # Specialization match bonus
        preferred_specializations = task_requirements.get('preferred_specializations', [])
        if agent.specialization in preferred_specializations:
            score += 25.0
        
        # Cost penalty
        total_cost = sum(cap.cost_per_invocation for cap in agent.capabilities)
        max_cost = task_requirements.get('max_cost_per_task', float('inf'))
        if total_cost <= max_cost:
            # Lower cost is better
            cost_score = max(0, 20.0 - (total_cost / max_cost) * 20.0)
            score += cost_score
        else:
            score -= 50.0  # Penalty for exceeding cost limit
        
        return score
    
    def _validate_agent_metadata(self, metadata: AgentMetadata) -> bool:
        """Validate agent metadata"""
        if not metadata.agent_id or not metadata.name:
            return False
        
        if not metadata.endpoint:
            return False
        
        if not isinstance(metadata.capabilities, list):
            return False
        
        if metadata.load < 0.0 or metadata.load > 1.0:
            return False
        
        return True
    
    def _update_indexes_for_registration(self, metadata: AgentMetadata):
        """Update indexes when registering an agent"""
        agent_id = metadata.agent_id
        
        # Update capability index
        for capability in metadata.capabilities:
            cap_name = capability.name if isinstance(capability, AgentCapability) else str(capability)
            if cap_name not in self.capability_index:
                self.capability_index[cap_name] = set()
            self.capability_index[cap_name].add(agent_id)
        
        # Update specialization index
        if metadata.specialization not in self.specialization_index:
            self.specialization_index[metadata.specialization] = set()
        self.specialization_index[metadata.specialization].add(agent_id)
        
        # Update type index
        self.type_index[metadata.agent_type].add(agent_id)
    
    def _update_indexes_for_deregistration(self, metadata: AgentMetadata):
        """Update indexes when deregistering an agent"""
        agent_id = metadata.agent_id
        
        # Update capability index
        for capability in metadata.capabilities:
            cap_name = capability.name if isinstance(capability, AgentCapability) else str(capability)
            if cap_name in self.capability_index:
                self.capability_index[cap_name].discard(agent_id)
                if not self.capability_index[cap_name]:
                    del self.capability_index[cap_name]
        
        # Update specialization index
        if metadata.specialization in self.specialization_index:
            self.specialization_index[metadata.specialization].discard(agent_id)
            if not self.specialization_index[metadata.specialization]:
                del self.specialization_index[metadata.specialization]
        
        # Update type index
        self.type_index[metadata.agent_type].discard(agent_id)
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(
        self, 
        agent_type: Optional[AgentType] = None,
        status_filter: Optional[AgentStatus] = None
    ) -> List[AgentMetadata]:
        """List all agents with optional filters"""
        result = []
        
        for metadata in self.agents.values():
            if agent_type and metadata.agent_type != agent_type:
                continue
            
            if status_filter and metadata.status != status_filter:
                continue
            
            result.append(metadata)
        
        return result
    
    def get_directory_stats(self) -> Dict[str, Any]:
        """Get directory statistics"""
        total_agents = len(self.agents)
        agents_by_type = {
            agent_type.value: len(agent_ids) 
            for agent_type, agent_ids in self.type_index.items()
        }
        agents_by_status = {}
        
        for metadata in self.agents.values():
            status = metadata.status.value
            agents_by_status[status] = agents_by_status.get(status, 0) + 1
        
        return {
            'total_agents': total_agents,
            'agents_by_type': agents_by_type,
            'agents_by_status': agents_by_status,
            'total_capabilities': len(self.capability_index),
            'total_specializations': len(self.specialization_index),
            'discovery_stats': {
                'total_registrations': self.stats['total_registrations'],
                'total_discoveries': self.stats['total_discoveries'],
                'total_selections': self.stats['total_selections'],
                'average_selection_time': self.stats['average_selection_time'],
                'last_cleanup': self.stats['last_cleanup'].isoformat()
            }
        }
    
    async def shutdown(self):
            """Shutdown the agent directory"""
            # No background tasks to clean up in single-process mode
            logger.info("Agent Directory shutdown complete")
