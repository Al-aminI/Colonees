"""
Colonees Supervisor — Lightweight Router + Future Collaborative Swarm
Routes user goals to the right specialist colonee, which handles everything end-to-end.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ColoneesSupervisorAgent:
    """
    Lightweight supervisor that routes goals to the right specialist.

    Current model (v1):
        Workspace provided → use its one colonee → spawn with ALL tools scoped to workspace → done.
        No workspace → fall back to keyword-based selection across all enabled colonees.
        No decomposition, no multi-agent coordination.

    Future model (v2 — collaborative swarm via collab.md):
        Complex goals → decompose → shared board → multiple specialists → monitor → synthesize.
    """

    def __init__(
        self,
        session_manager,
        agent_directory,
        agent_manager=None,
        platform_session_manager=None,
    ):
        self.session_manager = session_manager
        self.agent_directory = agent_directory
        self.agent_manager = agent_manager
        self.platform_session_manager = platform_session_manager

        logger.info("Colonees Supervisor initialized — Lightweight Router mode")

    async def handle_request(self, user_goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route goal to the best specialist colonee.
        - Workspace provided: use its colonee directly (no selection logic).
        - No workspace: pick best colonee from all enabled ones.
        The specialist gets ALL tools scoped to the workspace.
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        specialist_session_id = None
        workspace_name = context.get("workspace") or None

        try:
            # 1. Resolve which colonee to use
            colonee_names = self._resolve_available_colonees(context)
            if not colonee_names:
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': 'No colonees available. Create colonees or check your workspace.',
                    'user_goal': user_goal,
                }

            if workspace_name and len(colonee_names) == 1:
                # Workspace has one colonee — use it directly, no selection needed
                best_colonee_name = colonee_names[0]
            else:
                # Multiple colonees or no workspace — pick the best match
                best_colonee_name = self._select_best_colonee(user_goal, colonee_names)

            logger.info("Routing to colonee '%s' (workspace: %s): %s",
                        best_colonee_name, workspace_name or 'none', user_goal[:100])

            # 2. Spawn the specialist with ALL tools scoped to this workspace
            if not self.agent_manager or not self.platform_session_manager:
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': 'Platform not fully initialized.',
                    'user_goal': user_goal,
                }

            session_result = await self.platform_session_manager.create_session(
                context={
                    'agent_type': best_colonee_name,
                    'workspace': workspace_name,
                    'goal': user_goal,
                    'spawned_by': 'supervisor_router',
                }
            )
            specialist_session_id = session_result[0] if isinstance(session_result, tuple) else session_result

            agent = await self.agent_manager.create_specialist_agent(
                specialist_type=best_colonee_name,
                specialization=user_goal[:80],
                session_id=specialist_session_id,
                workspace=workspace_name,
            )

            logger.info("Specialist '%s' spawned (workspace: %s, session: %s)",
                         agent.agent_id, workspace_name or 'global', specialist_session_id)

            # 3. Delegate the FULL goal — the specialist reasons end-to-end
            agent_result = agent(user_goal)

            # 4. Extract response
            if hasattr(agent_result, 'text'):
                response_text = agent_result.text
            elif hasattr(agent_result, 'content'):
                response_text = agent_result.content
            else:
                response_text = str(agent_result)

            runtime_sec = (datetime.now() - start_time).total_seconds()
            logger.info("Completed by '%s' in %.1fs", best_colonee_name, runtime_sec)

            return {
                'task_id': task_id,
                'status': 'completed',
                'user_goal': user_goal,
                'result': response_text,
                'colonee_used': best_colonee_name,
                'workspace': workspace_name,
                'final_asset': self._extract_final_asset(agent_result),
                'execution_trace': [{
                    'step': 'routed_to_specialist',
                    'colonee': best_colonee_name,
                    'workspace': workspace_name,
                    'session_id': specialist_session_id,
                    'runtime_seconds': runtime_sec,
                }],
                'safety_metrics': {
                    'agents_spawned': 1,
                    'runtime_seconds': runtime_sec,
                },
            }

        except Exception as e:
            logger.error("Goal execution failed: %s", e)
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e),
                'user_goal': user_goal,
            }

        finally:
            if specialist_session_id and self.platform_session_manager:
                try:
                    await self.platform_session_manager.cleanup_session(specialist_session_id)
                except Exception as cleanup_err:
                    logger.warning("Cleanup failed for session %s: %s",
                                    specialist_session_id, cleanup_err)

    # ── Routing ─────────────────────────────────────────────────────────────

    def _resolve_available_colonees(self, context: Dict[str, Any]) -> List[str]:
        """Get the colonee(s) available for this request."""
        explicit = context.get("colonees")
        if explicit:
            if self.agent_manager and hasattr(self.agent_manager, "colonee_registry"):
                enabled = {c.name for c in self.agent_manager.colonee_registry.list(enabled_only=True)}
                return [n for n in explicit if n in enabled]
            return explicit

        if self.agent_manager and hasattr(self.agent_manager, "colonee_registry"):
            return [c.name for c in self.agent_manager.colonee_registry.list(enabled_only=True)]

        return ['domain_expert', 'researcher', 'analyst', 'executor', 'media_producer']

    def _select_best_colonee(self, user_goal: str, available: List[str]) -> str:
        """Pick the best colonee when multiple are available (no workspace context)."""
        if len(available) == 1:
            return available[0]

        goal_lower = user_goal.lower()

        # Score by registry capabilities if available
        if self.agent_manager and hasattr(self.agent_manager, "colonee_registry"):
            best_name, best_score = available[0], -1
            for name in available:
                defn = self.agent_manager.colonee_registry.get(name)
                if not defn:
                    continue
                score = 0
                for cap in defn.capabilities:
                    for word in cap.lower().replace('_', ' ').split():
                        if len(word) > 2 and word in goal_lower:
                            score += 2
                for word in defn.description.lower().split():
                    if len(word) > 3 and word in goal_lower:
                        score += 1
                if score > best_score:
                    best_score = score
                    best_name = name
            if best_score > 0:
                return best_name

        # Keyword fallback
        priorities = [
            (['api', 'call', 'fetch', 'order', 'create', 'build', 'execute', 'show me',
              'list', 'get', 'post', 'delete', 'update', 'run'], 'executor'),
            (['research', 'find', 'search', 'investigate', 'look up'], 'researcher'),
            (['analyze', 'analyse', 'evaluate', 'review', 'compare', 'report'], 'analyst'),
            (['video', 'image', 'audio', 'media', 'picture'], 'media_producer'),
        ]
        for keywords, agent_type in priorities:
            if agent_type in available and any(kw in goal_lower for kw in keywords):
                return agent_type

        return 'domain_expert' if 'domain_expert' in available else available[0]

    # ── Response Extraction ─────────────────────────────────────────────────

    def _extract_final_asset(self, result) -> Optional[Dict[str, Any]]:
        """Extract deliverable asset from agent response."""
        import re
        try:
            text = result.text if hasattr(result, 'text') else str(result)
            for pattern in [r'https?://[^\s]+\.(mp4|pdf|png|mp3|jpg|csv|json)',
                            r'file://[^\s]+\.(mp4|pdf|png|mp3|jpg|csv|json)']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    ext = match.group(0).rsplit('.', 1)[-1].lower()
                    type_map = {'mp4': 'video', 'mp3': 'audio', 'pdf': 'document',
                                'png': 'image', 'jpg': 'image', 'csv': 'data', 'json': 'data'}
                    return {'type': type_map.get(ext, 'file'), 'url': match.group(0).strip(), 'format': ext}
            return None
        except Exception:
            return None
