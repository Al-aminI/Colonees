"""
Colonees Session Manager
Session lifecycle management for the agent swarm platform
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

from ..core.config import CologeesConfig

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    session_id: str
    user_id: str
    context: Dict[str, Any]
    created_at: datetime
    last_activity: datetime
    timeout_minutes: int = 60
    memory_enabled: bool = False
    session_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeSession:
    session_id: str
    user_id: str
    runtime_session_id: str
    created_at: datetime
    status: str = "active"


class CologeesSessionManager:
    """
    Session Manager for Colonees platform.

    Provides:
    - Session lifecycle management
    - Session restoration and cleanup
    - Multi-user session isolation
    - Session timeout and cleanup mechanisms
    """

    def __init__(self, config: CologeesConfig):
        self.config = config

        # Session storage
        self.active_sessions: Dict[str, SessionContext] = {}
        self.runtime_sessions: Dict[str, RuntimeSession] = {}

        # Configuration
        self.default_session_timeout = timedelta(hours=1)
        self.cleanup_interval = timedelta(minutes=15)
        self.max_sessions_per_user = 10

        # Statistics
        self.stats = {
            'total_sessions_created': 0,
            'active_sessions': 0,
            'sessions_cleaned_up': 0,
            'last_cleanup': datetime.now()
        }

        self._cleanup_task = None
        self._start_background_tasks()

        logger.info("Colonees Session Manager initialized")

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._cleanup_task is None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            except RuntimeError:
                pass  # No event loop yet — will be started later

    async def _periodic_cleanup(self):
        """Periodically clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self._cleanup_expired_sessions()
                self.stats['last_cleanup'] = datetime.now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic session cleanup: {e}")

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, context in self.active_sessions.items():
            session_timeout = timedelta(minutes=context.timeout_minutes)
            if current_time - context.last_activity > session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            logger.info(f"Cleaning up expired session: {session_id}")
            await self.cleanup_session(session_id)
            self.stats['sessions_cleaned_up'] += 1

    async def create_session(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Create new session"""
        try:
            session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Check user session limits
            user_sessions = [s for s in self.active_sessions.values() if s.user_id == user_id]
            if len(user_sessions) >= self.max_sessions_per_user:
                oldest_session = min(user_sessions, key=lambda s: s.last_activity)
                await self.cleanup_session(oldest_session.session_id)

            # Create runtime session
            runtime_session = RuntimeSession(
                session_id=session_id,
                user_id=user_id,
                runtime_session_id=f"runtime_{session_id}",
                created_at=datetime.now()
            )
            self.runtime_sessions[session_id] = runtime_session

            # Create session context
            session_context = SessionContext(
                session_id=session_id,
                user_id=user_id,
                context=context,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                timeout_minutes=context.get('timeout_minutes', 60),
                memory_enabled=False  # Memory disabled by default
            )

            self.active_sessions[session_id] = session_context

            self.stats['total_sessions_created'] += 1
            self.stats['active_sessions'] = len(self.active_sessions)

            session_data = {
                'runtime_session': runtime_session,
                'memory_session_manager': None,  # Memory disabled
                'context': context,
                'session_context': session_context
            }

            logger.info(f"Session created: {session_id} for user: {user_id}")
            return session_id, session_data

        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise

    def get_session_manager(self, session_id: str):
        """Get session manager for a specific session (returns None — memory disabled)"""
        return None

    def get_user_id_from_session(self, session_id: str) -> Optional[str]:
        """Get user ID from session ID"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].user_id
        return None

    async def update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].last_activity = datetime.now()

    async def get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """Get session context"""
        return self.active_sessions.get(session_id)

    async def list_user_sessions(self, user_id: str) -> List[SessionContext]:
        """List all sessions for a user"""
        return [context for context in self.active_sessions.values() if context.user_id == user_id]

    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up session and associated resources"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found for cleanup")
                return False

            if session_id in self.runtime_sessions:
                del self.runtime_sessions[session_id]

            del self.active_sessions[session_id]
            self.stats['active_sessions'] = len(self.active_sessions)

            logger.info(f"Session cleaned up: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            return False

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session management statistics"""
        active_users = len(set(context.user_id for context in self.active_sessions.values()))
        return {
            'total_sessions_created': self.stats['total_sessions_created'],
            'active_sessions': self.stats['active_sessions'],
            'active_users': active_users,
            'sessions_cleaned_up': self.stats['sessions_cleaned_up'],
            'last_cleanup': self.stats['last_cleanup'].isoformat(),
            'runtime_sessions': len(self.runtime_sessions)
        }

    async def shutdown(self):
        """Shutdown session manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            await self.cleanup_session(session_id)

        logger.info("Colonees Session Manager shutdown complete")


# Backward-compat alias
GALOSStrandsSessionManager = CologeesSessionManager
