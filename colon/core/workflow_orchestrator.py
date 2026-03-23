"""
Colonees Supervisor Agent — Agent Swarm Control Plane
Generic task orchestration without domain-specific workflows
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from strands import Agent, tool
from strands_tools import file_read, file_write

from ..agents.agent_directory import AgentDirectory, AgentStatus
from .safety_enforcer import SafetyEnforcer
from .model_config import get_model


logger = logging.getLogger(__name__)


@dataclass
class TaskExecution:
    task_id: str
    user_goal: str
    supervisor_analysis: Dict[str, Any]
    discovered_agents: List[Dict[str, Any]]
    execution_state: str  # 'analyzing', 'discovering', 'coordinating', 'completed', 'failed'
    start_time: datetime
    results: Dict[str, Any]
    trace: List[Dict[str, Any]]
    safety_metrics: Dict[str, Any]


class ColoneesSupervisorAgent:
    """
    Superagent for Colonees — the autonomous orchestration control plane.

    CRITICAL: This is an AUTONOMOUS agent with tools, NOT a hardcoded workflow engine.

    ARCHITECTURE:
    - Superagent = Autonomous Strands Agent + Orchestration Tools
    - Tools handle: agent discovery, spawning, coordination, safety, memory
    - Agent decides: when to use tools, how to coordinate, what to delegate
    - NO hardcoded workflows — pure autonomous orchestration
    """

    def __init__(
        self,
        session_manager,
        agent_directory: AgentDirectory,
        safety_enforcer: SafetyEnforcer,
        agent_manager: Optional[Any] = None,
        platform_session_manager: Optional[Any] = None
    ):
        self.session_manager = session_manager
        self.agent_directory = agent_directory
        self.safety_enforcer = safety_enforcer
        self.agent_manager = agent_manager
        self.platform_session_manager = platform_session_manager
        self.active_executions: Dict[str, TaskExecution] = {}

        # Safety boundaries
        self.max_agent_steps = 20
        self.max_tool_calls = 30
        self.max_recursion_depth = 5
        self.max_runtime_minutes = 10
        self.max_agents_per_task = 10

        self.agent = Agent(
            name="colonees_superagent",
            system_prompt=self._get_supervisor_system_prompt(),
            model=get_model(),
            session_manager=session_manager,
            tools=[
                self.analyze_goal,
                self.discover_agents_for_capabilities,
                self.spawn_agent,
                self.send_task_to_agent,
                self.synthesize_results,
                self.monitor_execution_safety,
                self.get_agent_status,
                self.list_active_agents,
                self.get_agent_capabilities
            ]
        )

        logger.info("Colonees Superagent initialized — Autonomous Orchestration")

    def _get_supervisor_system_prompt(self) -> str:
        return """You are the Colonees Superagent — an autonomous orchestration agent for the Colonees agent swarm platform.

CRITICAL ROLE: You are an ORCHESTRATOR, NOT a direct answer provider. You MUST use your tools to coordinate specialist agents.

YOUR AVAILABLE TOOLS (use these exact names):
- analyze_goal: Analyze what the user wants (call ONCE per request)
- discover_agents_for_capabilities: Find existing agents (call ONCE after analyze)
- spawn_agent: Create new specialist agents (call ONCE per needed agent)
- send_task_to_agent: Send tasks to agents (call ONCE per agent)
- synthesize_results: Combine agent outputs (call ONCE at the end)
- monitor_execution_safety: Check safety boundaries
- list_active_agents: See what agents are available
- get_agent_status: Check agent status
- get_agent_capabilities: Get agent capabilities

MANDATORY WORKFLOW (execute each step ONCE):
1. Call analyze_goal ONCE to understand the request
2. Call discover_agents_for_capabilities ONCE to find existing agents
3. If no suitable agents exist, call spawn_agent ONCE to create a specialist agent
4. Call send_task_to_agent ONCE to delegate work to the specialist agent
5. Call synthesize_results ONCE to format the final response

CRITICAL RULES:
- Each workflow step should be called EXACTLY ONCE
- Do NOT repeat analyze_goal multiple times
- Do NOT loop on the same tool
- Move forward through the workflow sequentially
- After sending a task to an agent, WAIT for the result before synthesizing

AVAILABLE SPECIALIST AGENTS (create with spawn_agent):
- domain_expert: For deep domain knowledge and problem-solving in any field
- researcher: For information gathering, synthesis, and analysis
- analyst: For data analysis, evaluation, and structured reporting
- executor: For task execution, file operations, and computation
- media_producer: For generating media assets (images, audio, video)

ORCHESTRATION STRATEGY:
- For knowledge/analysis tasks: spawn domain_expert
- For research tasks: spawn researcher
- For data/evaluation tasks: spawn analyst
- For execution/file tasks: spawn executor
- For media creation: spawn media_producer
- For complex multi-step workflows: spawn multiple specialists and coordinate them

CRITICAL: You are a COORDINATOR. Execute the workflow ONCE and return the result.
Each specialist has tools embedded and will use them autonomously."""

    async def handle_request(self, user_goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        MAIN ENTRY POINT: Handle any user request autonomously.
        The superagent decides how to orchestrate based on the goal.
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Resolve the colonee allowlist for this request
        colonee_allowlist: Optional[List[str]] = context.get("colonees")
        if colonee_allowlist is not None:
            # Validate against enabled colonees
            if self.agent_manager and hasattr(self.agent_manager, "colonee_registry"):
                enabled_names = {
                    c.name for c in self.agent_manager.colonee_registry.list(enabled_only=True)
                }
                colonee_allowlist = [n for n in colonee_allowlist if n in enabled_names]
            available_colonees_str = ", ".join(colonee_allowlist) if colonee_allowlist else "none"
        else:
            # All enabled colonees are available
            if self.agent_manager and hasattr(self.agent_manager, "colonee_registry"):
                colonee_allowlist = [
                    c.name for c in self.agent_manager.colonee_registry.list(enabled_only=True)
                ]
            available_colonees_str = ", ".join(colonee_allowlist) if colonee_allowlist else "domain_expert, researcher, analyst, executor, media_producer"

        try:
            execution = TaskExecution(
                task_id=task_id,
                user_goal=user_goal,
                supervisor_analysis={},
                discovered_agents=[],
                execution_state='analyzing',
                start_time=datetime.now(),
                results={},
                trace=[],
                safety_metrics={
                    'agent_steps': 0,
                    'tool_calls': 0,
                    'recursion_depth': 0,
                    'agents_spawned': 0,
                    'colonee_allowlist': colonee_allowlist,
                }
            )

            self.active_executions[task_id] = execution

            orchestration_prompt = f"""
USER REQUEST FOR ORCHESTRATION:

Goal: {user_goal}
Context: {context}
Task ID: {task_id}

AVAILABLE COLONEES FOR THIS REQUEST: {available_colonees_str}
You MUST only spawn colonees from the list above. Do not spawn any other type.

Please orchestrate this task autonomously. You have tools available to:
- Analyze the goal and identify needed capabilities
- Discover and spawn appropriate specialist agents
- Send tasks to agents and coordinate their work
- Monitor safety and intervene if needed
- Synthesize results from agent collaboration

Use your tools intelligently to accomplish this goal.

CRITICAL: After completing the orchestration, provide your final response in this EXACT format:

FINAL_RESPONSE_START
{{
    "summary": "Brief summary of what was accomplished",
    "detailed_response": "Full detailed response to the user",
    "final_asset": {{
        "type": "video|document|image|audio|none",
        "url": "https://... (the actual URL of the deliverable)",
        "format": "mp4|pdf|png|mp3|etc",
        "metadata": {{}}
    }}
}}
FINAL_RESPONSE_END

If there is no final asset, set final_asset.type to "none" and omit url/format.
"""

            result = self.agent(orchestration_prompt)

            execution.execution_state = 'completed'
            execution.results = {'orchestration_result': result}

            final_asset = self._extract_final_asset(result)

            return {
                'task_id': task_id,
                'status': 'completed',
                'user_goal': user_goal,
                'result': result,
                'final_asset': final_asset,
                'execution_trace': execution.trace,
                'safety_metrics': execution.safety_metrics
            }

        except Exception as e:
            logger.error(f"Autonomous orchestration failed: {e}")
            if task_id in self.active_executions:
                self.active_executions[task_id].execution_state = 'failed'

            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e),
                'user_goal': user_goal
            }

        finally:
            if task_id in self.active_executions:
                del self.active_executions[task_id]

    def _extract_final_asset(self, result: Any) -> Optional[Dict[str, Any]]:
        """Extract final deliverable asset from agent's structured response"""
        import re
        import json

        try:
            if hasattr(result, 'text'):
                text = result.text
            elif hasattr(result, 'content'):
                text = result.content
            else:
                text = str(result)

            json_pattern = r'FINAL_RESPONSE_START\s*(\{.*?\})\s*FINAL_RESPONSE_END'
            match = re.search(json_pattern, text, re.DOTALL | re.IGNORECASE)

            if match:
                try:
                    response_data = json.loads(match.group(1))
                    final_asset = response_data.get('final_asset')
                    if final_asset and final_asset.get('type') != 'none':
                        return {
                            'type': final_asset.get('type'),
                            'url': final_asset.get('url'),
                            'format': final_asset.get('format'),
                            'metadata': final_asset.get('metadata', {})
                        }
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse structured response JSON: {e}")

            # Fallback: extract local file paths or URLs
            url_patterns = [
                r'https?://[^\s]+\.(mp4|pdf|png|mp3)',
                r'file://[^\s]+\.(mp4|pdf|png|mp3)',
                r'/[^\s]+\.(mp4|pdf|png|mp3)',
            ]
            for pattern in url_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    url = match.group(0)
                    ext = url.rsplit('.', 1)[-1].lower()
                    type_map = {'mp4': 'video', 'mp3': 'audio', 'pdf': 'document', 'png': 'image'}
                    return {
                        'type': type_map.get(ext, 'file'),
                        'url': url.strip(),
                        'format': ext
                    }

            return None

        except Exception as e:
            logger.warning(f"Failed to extract final asset: {e}")
            return None

    @tool
    async def analyze_goal(self, user_goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze user goal to identify required capabilities.

        Args:
            user_goal: The user's request or goal to analyze
            context: Optional additional context about the request

        Returns:
            Dict with goal, context, analysis, required_capabilities, and timestamp
        """
        if context is None:
            context = {}

        if not self.safety_enforcer.check_goal_safety(user_goal):
            raise ValueError(f"Goal violates safety policies: {user_goal}")

        capabilities = await self._extract_capabilities_from_analysis(user_goal)

        return {
            'goal': user_goal,
            'context': context,
            'analysis': f"Analyzed goal: {user_goal}",
            'required_capabilities': capabilities,
            'timestamp': datetime.now().isoformat()
        }

    @tool
    async def discover_agents_for_capabilities(self, required_capabilities: List[str]) -> Dict[str, Any]:
        """Discover available agents that can handle the required capabilities"""
        discovered_agents = []

        for capability in required_capabilities:
            suitable_agents = await self.agent_directory.find_agents_by_capabilities(
                capabilities=[capability],
                availability_filter=True
            )

            if suitable_agents:
                selected_agent = await self.agent_directory.select_optimal_agent(
                    candidates=suitable_agents,
                    task_requirements={'capability': capability}
                )

                if selected_agent:
                    discovered_agents.append({
                        'capability': capability,
                        'agent_id': selected_agent.agent_id,
                        'agent_type': selected_agent.agent_type,
                        'specialization': selected_agent.specialization,
                        'endpoint': selected_agent.endpoint,
                        'status': 'discovered'
                    })

        return {
            'required_capabilities': required_capabilities,
            'discovered_agents': discovered_agents,
            'discovery_timestamp': datetime.now().isoformat()
        }

    @tool
    async def spawn_agent(
        self,
        agent_type: str,
        specialization: str,
        user_id: str = "anonymous",
        capabilities_needed: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Spawn a new specialist agent.

        Args:
            agent_type: Type of specialist agent (domain_expert, researcher, analyst, executor, media_producer, tutor, subject_expert, research, assessment, video_production)
            specialization: Specific domain or focus area for the agent
            user_id: User identifier for session management
            capabilities_needed: Optional list of required capabilities

        Returns:
            Dict with status, agent_id, and spawn details
        """
        try:
            if not self.agent_manager or not self.platform_session_manager:
                agent_id = f"{agent_type}_{specialization}_{hash(str(datetime.now()))}"
                logger.warning("Agent manager not available, creating mock spawn result")
                return {
                    'status': 'mock_spawned',
                    'agent_id': agent_id,
                    'agent_type': agent_type,
                    'specialization': specialization,
                    'capabilities': capabilities_needed or [],
                    'spawn_timestamp': datetime.now().isoformat()
                }

            valid_specialist_types = [
                'domain_expert', 'researcher', 'analyst', 'executor', 'media_producer',
                # legacy aliases
                'tutor', 'subject_expert', 'research', 'assessment', 'video_production'
            ]
            # Also include any user-defined colonees from the registry
            if self.agent_manager and hasattr(self.agent_manager, 'colonee_registry'):
                registry_names = [
                    c.name for c in self.agent_manager.colonee_registry.list(enabled_only=True)
                ]
                valid_specialist_types = list(set(valid_specialist_types + registry_names))

            # Enforce per-request colonee allowlist if set
            for execution in self.active_executions.values():
                allowlist = execution.safety_metrics.get('colonee_allowlist')
                if allowlist is not None:
                    valid_specialist_types = [t for t in valid_specialist_types if t in allowlist]
                    break

            if agent_type not in valid_specialist_types:
                return {
                    'status': 'failed',
                    'error': f'Invalid agent type: {agent_type}. Valid types: {valid_specialist_types}',
                    'agent_type': agent_type
                }

            learning_context = {
                'agent_type': agent_type,
                'specialization': specialization,
                'capabilities_needed': capabilities_needed or [],
                'spawned_by': 'superagent',
                'user_id': user_id
            }

            session_result = await self.platform_session_manager.create_session(
                user_id=user_id,
                context=learning_context
            )

            if isinstance(session_result, tuple):
                session_id, session_data = session_result
            else:
                session_id = session_result

            agent = await self.agent_manager.create_specialist_agent(
                specialist_type=agent_type,
                specialization=specialization,
                session_id=session_id
            )

            for task_id, execution in self.active_executions.items():
                execution.safety_metrics['agents_spawned'] += 1
                execution.trace.append({
                    'step': 'agent_spawned',
                    'timestamp': datetime.now(),
                    'agent_id': agent.agent_id,
                    'agent_type': agent_type,
                    'specialization': specialization,
                    'session_id': session_id
                })

            return {
                'status': 'spawned',
                'agent_id': agent.agent_id,
                'agent_type': agent_type,
                'specialization': specialization,
                'session_id': session_id,
                'capabilities': capabilities_needed or [],
                'spawn_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to spawn agent {agent_type}_{specialization}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'agent_type': agent_type,
                'specialization': specialization
            }

    @tool
    async def send_task_to_agent(
        self,
        agent_id: str,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a specific task to a specialist agent via direct invocation"""
        try:
            if not self.agent_manager or agent_id not in self.agent_manager.active_specialist_agents:
                logger.warning(f"Specialist agent {agent_id} not found in active agents")
                return {
                    'status': 'failed',
                    'error': f'Specialist agent {agent_id} not found.',
                    'agent_id': agent_id,
                    'task_description': task_description,
                    'method': 'direct_invocation_failed'
                }

            agent = self.agent_manager.active_specialist_agents[agent_id]

            for task_id, execution in self.active_executions.items():
                execution.safety_metrics['tool_calls'] += 1
                execution.trace.append({
                    'step': 'task_sent_to_specialist',
                    'timestamp': datetime.now(),
                    'agent_id': agent_id,
                    'task_description': task_description,
                    'method': 'direct_invocation'
                })

            prompt = f"""
Task: {task_description}

Context: {context if context else 'No additional context provided'}

IMPORTANT INSTRUCTIONS:
- Use your available tools to complete this task
- If a tool fails, observe the error and try a different approach
- Do NOT give up after one failure — adapt your strategy
- Continue working until you succeed or exhaust all reasonable options
- Provide a detailed response when complete

Complete this task using your tools autonomously.
"""

            agent_result = agent(prompt)

            if hasattr(agent_result, 'text'):
                response_text = agent_result.text
            elif hasattr(agent_result, 'content'):
                response_text = agent_result.content
            else:
                response_text = str(agent_result)

            return {
                'status': 'completed',
                'agent_id': agent_id,
                'task_description': task_description,
                'agent_response': {
                    'text': response_text,
                    'result': agent_result
                },
                'method': 'direct_invocation',
                'completion_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send task to specialist agent {agent_id}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'agent_id': agent_id,
                'task_description': task_description,
                'method': 'direct_invocation_error'
            }

    @tool
    async def synthesize_results(self, task_results: List[Dict[str, Any]], user_goal: str) -> Dict[str, Any]:
        """Synthesize results from multiple specialist agents into a coherent response.

        Args:
            task_results: List of results from specialist agents
            user_goal: The original user goal

        Returns:
            Dict with synthesized response
        """
        try:
            combined_responses = []
            for result in task_results:
                if result.get('status') == 'completed':
                    agent_response = result.get('agent_response', {})
                    text = agent_response.get('text', '')
                    if text:
                        combined_responses.append(text)

            synthesized = "\n\n".join(combined_responses) if combined_responses else "Task completed."

            return {
                'status': 'synthesized',
                'user_goal': user_goal,
                'synthesized_response': synthesized,
                'agents_contributed': len([r for r in task_results if r.get('status') == 'completed']),
                'synthesis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to synthesize results: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'user_goal': user_goal
            }

    @tool
    async def monitor_execution_safety(self) -> Dict[str, Any]:
        """Monitor all active executions for safety boundary violations"""
        safety_status = {
            'boundaries_enforced': True,
            'violations': [],
            'interventions': [],
            'active_executions': len(self.active_executions)
        }

        for task_id, execution in self.active_executions.items():
            violations = []

            if execution.safety_metrics['agent_steps'] > self.max_agent_steps:
                violations.append(f"Exceeded max agent steps: {execution.safety_metrics['agent_steps']}")

            if execution.safety_metrics['tool_calls'] > self.max_tool_calls:
                violations.append(f"Exceeded max tool calls: {execution.safety_metrics['tool_calls']}")

            runtime = (datetime.now() - execution.start_time).total_seconds() / 60
            if runtime > self.max_runtime_minutes:
                violations.append(f"Exceeded max runtime: {runtime:.1f} minutes")

            if execution.safety_metrics['agents_spawned'] > self.max_agents_per_task:
                violations.append(f"Exceeded max agents: {execution.safety_metrics['agents_spawned']}")

            if violations:
                safety_status['violations'].extend(violations)
                safety_status['interventions'].append({
                    'task_id': task_id,
                    'violations': violations,
                    'action': 'intervention_required'
                })

        return safety_status

    @tool
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the current status of a specific agent.

        Args:
            agent_id: The ID of the agent to check

        Returns:
            Dict with agent status information
        """
        try:
            if self.agent_manager and agent_id in self.agent_manager.active_specialist_agents:
                return {
                    'agent_id': agent_id,
                    'status': 'active',
                    'type': 'specialist',
                    'timestamp': datetime.now().isoformat()
                }
            return {
                'agent_id': agent_id,
                'status': 'not_found',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'agent_id': agent_id, 'status': 'error', 'error': str(e)}

    @tool
    async def list_active_agents(self) -> Dict[str, Any]:
        """List all currently active agents.

        Returns:
            Dict with lists of active specialist and tool agents
        """
        try:
            specialist_agents = []
            if self.agent_manager:
                for agent_id in self.agent_manager.active_specialist_agents:
                    specialist_agents.append({'agent_id': agent_id, 'type': 'specialist'})

            return {
                'specialist_agents': specialist_agents,
                'total_active': len(specialist_agents),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e), 'specialist_agents': [], 'total_active': 0}

    @tool
    async def get_agent_capabilities(self, agent_type: str) -> Dict[str, Any]:
        """Get the capabilities of a specific agent type.

        Args:
            agent_type: The type of agent to query

        Returns:
            Dict with agent capabilities
        """
        capabilities_map = {
            'domain_expert': ['domain_knowledge_provision', 'concept_explanation', 'problem_analysis', 'solution_validation'],
            'researcher': ['research_strategy_design', 'information_synthesis', 'source_validation', 'data_analysis'],
            'analyst': ['assessment_design', 'data_analysis', 'progress_evaluation', 'feedback_strategy'],
            'executor': ['file_operations', 'code_execution', 'computation', 'task_automation'],
            'media_producer': ['image_generation', 'video_production', 'audio_synthesis', 'content_creation'],
            # legacy aliases
            'tutor': ['personalized_instruction', 'learning_path_design', 'pedagogical_analysis'],
            'subject_expert': ['domain_knowledge_provision', 'concept_explanation', 'problem_analysis'],
            'research': ['research_strategy_design', 'information_synthesis', 'source_validation'],
            'assessment': ['assessment_design', 'learning_analytics', 'progress_evaluation'],
            'video_production': ['video_creation', 'video_planning', 'asset_coordination'],
        }

        # Check registry for user-defined colonees
        if self.agent_manager and hasattr(self.agent_manager, 'colonee_registry'):
            defn = self.agent_manager.colonee_registry.get(agent_type)
            if defn:
                return {
                    'agent_type': agent_type,
                    'capabilities': defn.capabilities,
                    'description': defn.description,
                    'timestamp': datetime.now().isoformat()
                }

        return {
            'agent_type': agent_type,
            'capabilities': capabilities_map.get(agent_type, []),
            'timestamp': datetime.now().isoformat()
        }

    async def _extract_capabilities_from_analysis(self, user_goal: str) -> List[str]:
        """Extract required capabilities from user goal analysis"""
        goal_lower = user_goal.lower()
        capabilities = []

        if any(word in goal_lower for word in ['research', 'find', 'search', 'look up', 'investigate']):
            capabilities.append('research_strategy_design')
        if any(word in goal_lower for word in ['analyze', 'analyse', 'evaluate', 'assess', 'review']):
            capabilities.append('data_analysis')
        if any(word in goal_lower for word in ['create', 'generate', 'build', 'make', 'produce']):
            capabilities.append('domain_knowledge_provision')
        if any(word in goal_lower for word in ['video', 'image', 'audio', 'media', 'visual']):
            capabilities.append('image_generation')
        if any(word in goal_lower for word in ['code', 'script', 'program', 'compute', 'calculate']):
            capabilities.append('code_execution')
        if any(word in goal_lower for word in ['file', 'document', 'write', 'save', 'store']):
            capabilities.append('file_operations')

        if not capabilities:
            capabilities.append('domain_knowledge_provision')

        return capabilities

