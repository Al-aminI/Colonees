"""
Colonees Session Manager
Session lifecycle management for the agent swarm platform.

Responsibilities:
- Create and track session IDs with metadata/context
- Enforce session timeouts via background cleanup
- Provide session stats

NOT responsible for conversation history — that lives in CologeesMemoryManager.
NOT responsible for Strands agent state — Strands manages its own LLM turn state.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from ..core.config import CologeesConfig

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    session_id: str
    context: Dict[str, Any]
    created_at: datetime
    last_activity: datetime
    timeout_minutes: int = 60


class CologeesSessionManager:
    """
    Session lifecycle manager for the Colonees platform.
    Tracks active sessions, enforces timeouts, and handles cleanup.
    """

    def __init__(self, config: CologeesConfig):
        self.config = config
        self.active_sessions: Dict[str, SessionContext] = {}
        self.cleanup_interval = timedelta(minutes=15)
        self.stats = {
            "total_sessions_created": 0,
            "active_sessions": 0,
            "sessions_cleaned_up": 0,
            "last_cleanup": datetime.now(),
        }
        self._cleanup_task = None
        self._start_background_tasks()
        logger.info("Colonees Session Manager initialized")

    def _start_background_tasks(self):
        try:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No running loop at construction time (e.g. tests) — skip background task
            pass

    async def _periodic_cleanup(self):
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self._cleanup_expired_sessions()
                self.stats["last_cleanup"] = datetime.now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic session cleanup: %s", e)

    async def _cleanup_expired_sessions(self):
        now = datetime.now()
        expired = [
            sid for sid, ctx in self.active_sessions.items()
            if now - ctx.last_activity > timedelta(minutes=ctx.timeout_minutes)
        ]
        for sid in expired:
            removed = await self.cleanup_session(sid)
            if removed:
                self.stats["sessions_cleaned_up"] += 1

    async def create_session(self, context: Dict[str, Any]) -> Tuple[str, SessionContext]:
        """
        Create a new session.

        Returns:
            (session_id, SessionContext)
        """
        try:
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            ctx = SessionContext(
                session_id=session_id,
                context=context,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                timeout_minutes=context.get("timeout_minutes", self.config.session_timeout_minutes),
            )
            self.active_sessions[session_id] = ctx
            self.stats["total_sessions_created"] += 1
            self.stats["active_sessions"] = len(self.active_sessions)
            logger.info("Session created: %s", session_id)
            return session_id, ctx
        except Exception as e:
            logger.error("Failed to create session: %s", e)
            raise

    async def update_session_activity(self, session_id: str) -> None:
        if session_id in self.active_sessions:
            self.active_sessions[session_id].last_activity = datetime.now()

    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        return self.active_sessions.get(session_id)

    async def cleanup_session(self, session_id: str) -> bool:
        try:
            if session_id not in self.active_sessions:
                return False
            del self.active_sessions[session_id]
            self.stats["active_sessions"] = len(self.active_sessions)
            logger.info("Session cleaned up: %s", session_id)
            return True
        except Exception as e:
            logger.error("Failed to cleanup session %s: %s", session_id, e)
            return False

    def get_session_stats(self) -> Dict[str, Any]:
        return {
            "total_sessions_created": self.stats["total_sessions_created"],
            "active_sessions": self.stats["active_sessions"],
            "sessions_cleaned_up": self.stats["sessions_cleaned_up"],
            "last_cleanup": self.stats["last_cleanup"].isoformat(),
        }

    async def shutdown(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        for sid in list(self.active_sessions.keys()):
            await self.cleanup_session(sid)
        logger.info("Colonees Session Manager shutdown complete")
