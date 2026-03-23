"""
Colonees Safety Enforcer
Enforces safety boundaries and prevents runaway agent loops
"""

import logging
import re
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SafetyEnforcer:
    """
    Safety Enforcer for Colonees Agent Operating System

    Enforces strict safety boundaries to prevent:
    - Runaway agent loops
    - Infinite task recursion
    - Resource exhaustion
    - Malicious or harmful requests
    - Policy violations
    """

    def __init__(self):
        # Safety patterns — goals that violate safety policies
        self.forbidden_patterns = [
            r'hack|exploit|attack|malware|virus',
            r'delete\s+all|destroy|corrupt',
            r'infinite|unlimited|endless|forever',
            r'spam|flood|ddos|overwhelm'
        ]

        # Resource limits
        self.max_goal_length = 1000  # characters
        self.max_context_size = 10000  # characters

        logger.info("Safety Enforcer initialized")
    
    def check_goal_safety(self, user_goal: str) -> bool:
        """Check if user goal violates safety policies"""
        
        if not user_goal or not isinstance(user_goal, str):
            return False
        
        # Check goal length
        if len(user_goal) > self.max_goal_length:
            logger.warning(f"Goal exceeds max length: {len(user_goal)} chars")
            return False
        
        # Check for forbidden patterns
        goal_lower = user_goal.lower()
        for pattern in self.forbidden_patterns:
            if re.search(pattern, goal_lower):
                logger.warning(f"Goal contains forbidden pattern: {pattern}")
                return False
        
        return True
    
    def check_context_safety(self, context: Dict[str, Any]) -> bool:
        """Check if context violates safety policies"""
        
        if not context:
            return True
        
        # Check context size
        context_str = str(context)
        if len(context_str) > self.max_context_size:
            logger.warning(f"Context exceeds max size: {len(context_str)} chars")
            return False
        
        return True
    
    def check_execution_safety(self, execution_metrics: Dict[str, Any], limits: Dict[str, Any]) -> List[str]:
        """Check if execution violates safety boundaries"""
        
        violations = []
        
        # Check agent steps
        if execution_metrics.get('agent_steps', 0) > limits.get('max_agent_steps', 20):
            violations.append(f"Exceeded max agent steps: {execution_metrics['agent_steps']}")
        
        # Check tool calls
        if execution_metrics.get('tool_calls', 0) > limits.get('max_tool_calls', 30):
            violations.append(f"Exceeded max tool calls: {execution_metrics['tool_calls']}")
        
        # Check recursion depth
        if execution_metrics.get('recursion_depth', 0) > limits.get('max_recursion_depth', 5):
            violations.append(f"Exceeded max recursion depth: {execution_metrics['recursion_depth']}")
        
        # Check agents spawned
        if execution_metrics.get('agents_spawned', 0) > limits.get('max_agents_per_task', 10):
            violations.append(f"Exceeded max agents per task: {execution_metrics['agents_spawned']}")
        
        return violations
    
    def check_agent_communication_safety(self, message: Dict[str, Any]) -> bool:
        """Check if agent communication is safe"""
        
        if not message:
            return False
        
        # Check message size
        message_str = str(message)
        if len(message_str) > 5000:  # 5KB limit
            logger.warning(f"Agent message too large: {len(message_str)} chars")
            return False
        
        # Check for forbidden content in message
        message_lower = message_str.lower()
        for pattern in self.forbidden_patterns:
            if re.search(pattern, message_lower):
                logger.warning(f"Agent message contains forbidden pattern: {pattern}")
                return False
        
        return True
    
    def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety enforcer statistics"""
        return {
            'forbidden_patterns': len(self.forbidden_patterns),
            'max_goal_length': self.max_goal_length,
            'max_context_size': self.max_context_size,
            'safety_mode': 'strict_enforcement'
        }