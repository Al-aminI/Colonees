"""
Colonees Strands Session Manager

Implements the Strands SessionManager protocol so that agent conversation
history is persisted and restored across invocations using our MemoryBackend.

Key design decisions:
- initialize() is called synchronously by Strands during Agent.__init__,
  which always happens inside FastAPI's running event loop. We therefore
  schedule the async restore as a fire-and-forget task and accept that the
  very first invocation of a brand-new agent instance may not have history
  loaded yet (it will on the next call). For the supervisor this is fine
  because it is created once at startup before any requests arrive.
  For specialists, each one is freshly spawned per task so there is no
  prior history to restore anyway.

- append_message() and sync_agent() are also called synchronously by Strands
  hooks. We schedule them as async tasks on the running loop. Because these
  are fire-and-forget, we use asyncio.ensure_future() which is safe inside
  a running loop.

- sync_agent() REPLACES the state snapshot (not appends) to avoid unbounded
  growth. Only the latest agent state is needed for restore.

- redact_latest_message() replaces the last message entry in-place.

Namespace separation (same backend, different keys):
  CologeesMemoryManager  →  key = session_id          (human-readable turns)
  ColoneesStrandsSessionManager:
    messages              →  key = "strands:msg:{session_id}"
    agent state           →  key = "strands:state:{session_id}"
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from strands.session.session_manager import SessionManager
from strands.types.session import SessionAgent, SessionMessage

from .memory_manager import MemoryBackend

logger = logging.getLogger(__name__)


class ColoneesStrandsSessionManager(SessionManager):
    """
    Strands-native SessionManager backed by a MemoryBackend.

    Persists the full Strands messages array and agent state per session_id,
    enabling true cross-request conversation continuity at the LLM level.
    """

    def __init__(self, session_id: str, backend: MemoryBackend):
        super().__init__()
        self.session_id = session_id
        self.backend = backend
        self._msg_key = f"strands:msg:{session_id}"
        self._state_key = f"strands:state:{session_id}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _schedule(self, coro) -> None:
        """Schedule a coroutine on the running loop, or run it directly."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.ensure_future(coro, loop=loop)
        except RuntimeError:
            # No running loop — run synchronously (e.g. tests, CLI)
            asyncio.run(coro)

    # ------------------------------------------------------------------
    # Strands SessionManager protocol
    # ------------------------------------------------------------------

    def initialize(self, agent: Any, **kwargs: Any) -> None:
        """
        Called by Strands synchronously during Agent.__init__.
        Schedules an async restore of messages + state onto the running loop.

        Note: for agents created inside an already-running event loop (FastAPI),
        the restore completes asynchronously. The supervisor is created at
        startup before requests arrive, so its history is fully loaded before
        the first request. Specialists are freshly spawned per task and have
        no prior history to restore.
        """
        self._schedule(self._restore(agent))

    async def _restore(self, agent: Any) -> None:
        """Restore messages and agent state from storage into the agent."""
        # Restore messages
        try:
            raw_messages = await self.backend.get(self._msg_key)
            if raw_messages:
                messages = [SessionMessage.from_dict(e).to_message() for e in raw_messages]
                agent.messages = messages
                logger.debug("Restored %d messages for session %s", len(messages), self.session_id)
        except Exception as e:
            logger.warning("Failed to restore messages for %s: %s", self.session_id, e)

        # Restore agent state (latest snapshot only)
        try:
            state_entries = await self.backend.get(self._state_key)
            if state_entries:
                session_agent = SessionAgent.from_dict(state_entries[-1])
                if hasattr(agent, "conversation_manager") and session_agent.conversation_manager_state:
                    agent.conversation_manager.restore_from_session(
                        session_agent.conversation_manager_state
                    )
                if session_agent.state:
                    agent.state.set(session_agent.state)
                session_agent.initialize_internal_state(agent)
        except Exception as e:
            logger.warning("Failed to restore agent state for %s: %s", self.session_id, e)

    def append_message(self, message: Any, agent: Any, **kwargs: Any) -> None:
        """
        Called by Strands every time a message is added to the agent.
        Persists the new message immediately (fire-and-forget).
        """
        try:
            index = len(agent.messages) - 1
            entry = SessionMessage.from_message(message, index).to_dict()
            self._schedule(self.backend.append(self._msg_key, entry))
        except Exception as e:
            logger.warning("Failed to append message for %s: %s", self.session_id, e)

    def sync_agent(self, agent: Any, **kwargs: Any) -> None:
        """
        Called by Strands after each invocation.
        Replaces the stored agent state snapshot with the latest.
        """
        self._schedule(self._replace_state(agent))

    async def _replace_state(self, agent: Any) -> None:
        """Delete old state snapshot and write the new one."""
        try:
            entry = SessionAgent.from_agent(agent).to_dict()
            await self.backend.delete(self._state_key)
            await self.backend.append(self._state_key, entry)
        except Exception as e:
            logger.warning("Failed to sync agent state for %s: %s", self.session_id, e)

    def redact_latest_message(self, redact_message: Any, agent: Any, **kwargs: Any) -> None:
        """
        Called when the latest message should be redacted.
        Replaces the last stored message entry.
        """
        self._schedule(self._redact(redact_message))

    async def _redact(self, redact_message: Any) -> None:
        entries = await self.backend.get(self._msg_key)
        if not entries:
            return
        try:
            last = SessionMessage.from_dict(entries[-1])
            last.redact_message = redact_message
            last.updated_at = datetime.now(timezone.utc).isoformat()
            entries[-1] = last.to_dict()
            # Rewrite the full list atomically
            await self.backend.delete(self._msg_key)
            for entry in entries:
                await self.backend.append(self._msg_key, entry)
        except Exception as e:
            logger.warning("Failed to redact message for %s: %s", self.session_id, e)

    async def clear(self) -> None:
        """Delete all stored messages and state for this session."""
        await self.backend.delete(self._msg_key)
        await self.backend.delete(self._state_key)
        logger.info("Cleared Strands session: %s", self.session_id)
