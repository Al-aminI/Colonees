"""
Colonees Resource Manager
Auto-scaling and resource management for the agent swarm platform
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from .config import CologeesConfig


logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    concurrent_users: int
    active_sessions: int
    agent_count: int
    memory_usage_mb: float
    cpu_utilization: float
    response_latency_ms: float
    timestamp: datetime


@dataclass
class ScalingTrigger:
    """Auto-scaling trigger configuration"""
    metric_name: str
    threshold: float
    comparison: str  # "greater_than", "less_than"
    duration_seconds: int
    action: str  # "scale_up", "scale_down"


class CologeesResourceManager:
    """
    Resource management and auto-scaling for Colonees platform
    """

    def __init__(
        self,
        config: CologeesConfig,
        runtime_client=None,
        observability_client=None
    ):
        self.runtime = runtime_client
        self.observability = observability_client
        self.config = config
        # Resource monitoring
        self.current_metrics = ResourceMetrics(
            concurrent_users=0,
            active_sessions=0,
            agent_count=0,
            memory_usage_mb=0.0,
            cpu_utilization=0.0,
            response_latency_ms=0.0,
            timestamp=datetime.now()
        )
        
        # Auto-scaling configuration
        self.scaling_triggers = self._setup_scaling_triggers()
        self.scaling_history: List[Dict[str, Any]] = []
        self.monitoring_active = False
        
        # Resource quotas
        self.resource_quotas = {
            'max_concurrent_users': config.max_concurrent_users,
            'max_active_sessions': config.max_active_sessions,
            'max_agents_per_user': config.max_agents_per_user,
            'max_memory_per_session_mb': config.max_memory_per_session_mb,
            'max_tool_invocations_per_minute': config.max_tool_invocations_per_minute
        }
        
        logger.info("CologeesResourceManager initialized with auto-scaling")
    
    def _setup_scaling_triggers(self) -> List[ScalingTrigger]:
        """Setup auto-scaling triggers based on requirements"""
        return [
            # Requirement 1.3: Scale up when user load exceeds 90,000
            ScalingTrigger(
                metric_name="concurrent_users",
                threshold=90000,
                comparison="greater_than",
                duration_seconds=60,
                action="scale_up"
            ),
            
            # Requirement 1.4: Scale up when active sessions exceed 9,500
            ScalingTrigger(
                metric_name="active_sessions", 
                threshold=9500,
                comparison="greater_than",
                duration_seconds=60,
                action="scale_up"
            ),
            
            # Scale down when utilization is low
            ScalingTrigger(
                metric_name="concurrent_users",
                threshold=50000,
                comparison="less_than",
                duration_seconds=300,  # 5 minutes
                action="scale_down"
            ),
            
            # Performance-based scaling
            ScalingTrigger(
                metric_name="response_latency_ms",
                threshold=500,  # Requirement 5.4: Log degradation at 500ms
                comparison="greater_than",
                duration_seconds=120,
                action="scale_up"
            )
        ]
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring and auto-scaling"""
        if self.monitoring_active:
            logger.warning("Resource monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Starting resource monitoring and auto-scaling")

        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._monitor_resource_metrics()),
            asyncio.create_task(self._evaluate_scaling_triggers()),
            asyncio.create_task(self._enforce_resource_quotas())
        ]

        try:
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
            self.monitoring_active = False
            raise
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring"""
        self.monitoring_active = False
        logger.info("Resource monitoring stopped")
    
    async def _monitor_resource_metrics(self) -> None:
        """Continuously monitor resource metrics"""
        while self.monitoring_active:
            try:
                # Collect current metrics from AgentCore Observability
                metrics = await self._collect_metrics()
                self.current_metrics = metrics

                # Log metrics for observability
                logger.debug(f"Resource metrics: users={metrics.concurrent_users}, "
                           f"sessions={metrics.active_sessions}, agents={metrics.agent_count}")

                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                logger.error(f"Error collecting resource metrics: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource utilization metrics"""
        try:
            # Get metrics from AgentCore Observability
            observability_data = await self.observability.get_metrics(
                metric_names=[
                    'concurrent_users',
                    'active_sessions', 
                    'agent_count',
                    'memory_usage',
                    'cpu_utilization',
                    'response_latency'
                ],
                time_range=timedelta(minutes=5)
            )

            return ResourceMetrics(
                concurrent_users=observability_data.get('concurrent_users', 0),
                active_sessions=observability_data.get('active_sessions', 0),
                agent_count=observability_data.get('agent_count', 0),
                memory_usage_mb=observability_data.get('memory_usage', 0.0),
                cpu_utilization=observability_data.get('cpu_utilization', 0.0),
                response_latency_ms=observability_data.get('response_latency', 0.0),
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            # Return current metrics as fallback
            return self.current_metrics

    async def _evaluate_scaling_triggers(self) -> None:
        """Evaluate auto-scaling triggers and take action"""
        while self.monitoring_active:
            try:
                for trigger in self.scaling_triggers:
                    await self._check_scaling_trigger(trigger)

                # Wait before next evaluation
                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                logger.error(f"Error evaluating scaling triggers: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _check_scaling_trigger(self, trigger: ScalingTrigger) -> None:
        """Check individual scaling trigger and take action if needed"""
        try:
            # Get current metric value
            current_value = getattr(self.current_metrics, trigger.metric_name, 0)

            # Check if trigger condition is met
            trigger_met = False
            if trigger.comparison == "greater_than":
                trigger_met = current_value > trigger.threshold
            elif trigger.comparison == "less_than":
                trigger_met = current_value < trigger.threshold

            if trigger_met:
                logger.info(f"Scaling trigger activated: {trigger.metric_name} "
                          f"{current_value} {trigger.comparison} {trigger.threshold}")

                # Execute scaling action
                await self._execute_scaling_action(trigger, current_value)

        except Exception as e:
            logger.error(f"Error checking scaling trigger {trigger.metric_name}: {e}")

    async def _execute_scaling_action(self, trigger: ScalingTrigger, current_value: float) -> None:
        """Execute scaling action based on trigger"""
        try:
            scaling_event = {
                'timestamp': datetime.now(),
                'trigger': trigger.metric_name,
                'current_value': current_value,
                'threshold': trigger.threshold,
                'action': trigger.action,
                'reason': f"{trigger.metric_name} {trigger.comparison} {trigger.threshold}"
            }

            if trigger.action == "scale_up":
                await self._scale_up(scaling_event)
            elif trigger.action == "scale_down":
                await self._scale_down(scaling_event)

            # Record scaling event
            self.scaling_history.append(scaling_event)

            # Keep only last 100 scaling events
            if len(self.scaling_history) > 100:
                self.scaling_history = self.scaling_history[-100:]

        except Exception as e:
            logger.error(f"Error executing scaling action {trigger.action}: {e}")

    async def _scale_up(self, scaling_event: Dict[str, Any]) -> None:
        """Scale up resources"""
        logger.info(f"Scaling UP: {scaling_event['reason']}")

        # AgentCore Runtime is serverless, so scaling is automatic
        # We can adjust quotas and limits to allow more resources
        if scaling_event['trigger'] == 'concurrent_users':
            # Increase user capacity
            self.resource_quotas['max_concurrent_users'] = min(
                self.resource_quotas['max_concurrent_users'] * 1.2,
                self.config.absolute_max_users
            )

        elif scaling_event['trigger'] == 'active_sessions':
            # Increase session capacity
            self.resource_quotas['max_active_sessions'] = min(
                self.resource_quotas['max_active_sessions'] * 1.2,
                self.config.absolute_max_sessions
            )

        # Log scaling action
        logger.info(f"Resource quotas updated: {self.resource_quotas}")
        scaling_event['status'] = 'completed'

    async def _scale_down(self, scaling_event: Dict[str, Any]) -> None:
        """Scale down resources"""
        logger.info(f"Scaling DOWN: {scaling_event['reason']}")

        # Reduce quotas to optimize costs
        if scaling_event['trigger'] == 'concurrent_users':
            # Decrease user capacity (but not below minimum)
            self.resource_quotas['max_concurrent_users'] = max(
                self.resource_quotas['max_concurrent_users'] * 0.8,
                self.config.min_concurrent_users
            )

        # Log scaling action
        logger.info(f"Resource quotas reduced: {self.resource_quotas}")
        scaling_event['status'] = 'completed'

    async def _enforce_resource_quotas(self) -> None:
        """Enforce resource quotas and limits"""
        while self.monitoring_active:
            try:
                # Check if current usage exceeds quotas
                violations = []

                if self.current_metrics.concurrent_users > self.resource_quotas['max_concurrent_users']:
                    violations.append(f"Concurrent users: {self.current_metrics.concurrent_users} > {self.resource_quotas['max_concurrent_users']}")

                if self.current_metrics.active_sessions > self.resource_quotas['max_active_sessions']:
                    violations.append(f"Active sessions: {self.current_metrics.active_sessions} > {self.resource_quotas['max_active_sessions']}")

                if violations:
                    logger.warning(f"Resource quota violations detected: {violations}")
                    await self._handle_quota_violations(violations)

                # Wait before next check
                await asyncio.sleep(120)  # Check every 2 minutes

            except Exception as e:
                logger.error(f"Error enforcing resource quotas: {e}")
                await asyncio.sleep(300)  # Wait longer on error

    async def _handle_quota_violations(self, violations: List[str]) -> None:
        """Handle resource quota violations"""
        logger.warning(f"Handling quota violations: {violations}")

        # For now, just log violations
        # In production, could implement:
        # - Request throttling
        # - Session cleanup
        # - User notification
        # - Emergency scaling

        for violation in violations:
            logger.error(f"QUOTA VIOLATION: {violation}")

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics"""
        return self.current_metrics

    def get_resource_quotas(self) -> Dict[str, Any]:
        """Get current resource quotas"""
        return self.resource_quotas.copy()

    def get_scaling_history(self) -> List[Dict[str, Any]]:
        """Get scaling history"""
        return self.scaling_history.copy()

    async def check_resource_availability(self, requested_resources: Dict[str, Any]) -> Dict[str, Any]:
        """Check if requested resources are available"""
        try:
            availability = {
                'available': True,
                'reasons': [],
                'current_usage': {
                    'concurrent_users': self.current_metrics.concurrent_users,
                    'active_sessions': self.current_metrics.active_sessions,
                    'agent_count': self.current_metrics.agent_count
                },
                'quotas': self.resource_quotas
            }

            # Check user capacity
            if requested_resources.get('users', 0) + self.current_metrics.concurrent_users > self.resource_quotas['max_concurrent_users']:
                availability['available'] = False
                availability['reasons'].append('Insufficient user capacity')

            # Check session capacity
            if requested_resources.get('sessions', 0) + self.current_metrics.active_sessions > self.resource_quotas['max_active_sessions']:
                availability['available'] = False
                availability['reasons'].append('Insufficient session capacity')

            return availability

        except Exception as e:
            logger.error(f"Error checking resource availability: {e}")
            return {
                'available': False,
                'reasons': [f'Error checking availability: {str(e)}'],
                'current_usage': {},
                'quotas': {}
            }

    def get_resource_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics"""
        return {
            'current_metrics': {
                'concurrent_users': self.current_metrics.concurrent_users,
                'active_sessions': self.current_metrics.active_sessions,
                'agent_count': self.current_metrics.agent_count,
                'memory_usage_mb': self.current_metrics.memory_usage_mb,
                'cpu_utilization': self.current_metrics.cpu_utilization,
                'response_latency_ms': self.current_metrics.response_latency_ms,
                'last_updated': self.current_metrics.timestamp.isoformat()
            },
            'resource_quotas': self.resource_quotas,
            'scaling_triggers': len(self.scaling_triggers),
            'scaling_events': len(self.scaling_history),
            'monitoring_active': self.monitoring_active,
            'last_scaling_event': self.scaling_history[-1] if self.scaling_history else None
        }