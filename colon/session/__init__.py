"""
Colonees Session Management
Session lifecycle management for the agent swarm platform
"""

from .session_manager import CologeesSessionManager

__all__ = ['CologeesSessionManager']

# Backward-compat alias
GALOSStrandsSessionManager = CologeesSessionManager