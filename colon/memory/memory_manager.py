"""
Colonees Memory Manager

Provides conversation history storage for agent sessions.

Default backend: in-process dict (no persistence across restarts).
Pluggable: pass a `backend` implementing the MemoryBackend protocol
to swap in Redis, DynamoDB, Postgres, etc.

Strands handles within-turn LLM conversation state via its own
session_manager. This manager handles cross-request / cross-session
history that YOU want to persist and query.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.config import CologeesConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------

class MemoryBackend(ABC):
    """
    Implement this to plug in a persistent memory store.

    Example implementations: Redis, DynamoDB, Postgres, SQLite.
    """

    @abstractmethod
    async def append(self, session_id: str, entry: Dict[str, Any]) -> None:
        """Append a history entry for the session."""

    @abstractmethod
    async def get(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return history entries for the session, newest-last."""

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete all history for the session."""


# ---------------------------------------------------------------------------
# Default in-process backend
# ---------------------------------------------------------------------------

class InProcessMemoryBackend(MemoryBackend):
    """
    Simple in-memory store. Fast, zero dependencies.
    Data is lost on restart — swap for a persistent backend in production.
    """

    def __init__(self, max_entries_per_session: int = 1000):
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._max = max_entries_per_session

    async def append(self, session_id: str, entry: Dict[str, Any]) -> None:
        bucket = self._store.setdefault(session_id, [])
        bucket.append(entry)
        if len(bucket) > self._max:
            bucket.pop(0)

    async def get(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        bucket = self._store.get(session_id, [])
        return bucket[-limit:] if limit else list(bucket)

    async def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def total_sessions(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class CologeesMemoryManager:
    """
    Memory manager for Colonees platform.

    Stores and retrieves conversation/event history per session.
    Uses InProcessMemoryBackend by default; swap via the `backend` param.
    """

    def __init__(
        self,
        config: CologeesConfig,
        backend: Optional[MemoryBackend] = None,
    ):
        self.config = config
        self.backend: MemoryBackend = backend or InProcessMemoryBackend()
        logger.info(
            "Memory Manager initialized (backend: %s)",
            type(self.backend).__name__,
        )

    async def store(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a conversation turn or event for a session.

        Args:
            session_id: The session this entry belongs to.
            role: 'user', 'assistant', 'tool', or any custom label.
            content: The text content of the entry.
            metadata: Optional extra data (agent_id, tool_name, etc.).
        """
        entry = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }
        await self.backend.append(session_id, entry)

    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.

        Args:
            session_id: The session to query.
            limit: Max number of entries to return (newest last).
        """
        return await self.backend.get(session_id, limit=limit)

    async def clear(self, session_id: str) -> None:
        """Delete all history for a session."""
        await self.backend.delete(session_id)

    def get_stats(self) -> Dict[str, Any]:
        backend_name = type(self.backend).__name__
        extra = {}
        if isinstance(self.backend, InProcessMemoryBackend):
            extra["total_sessions_with_history"] = self.backend.total_sessions()
        return {"backend": backend_name, **extra}
