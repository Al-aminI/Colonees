"""
Dynamic Specialist Agent
Instantiates a specialist agent from a ColoneeDefinition at runtime.

This replaces the need for a separate Python class per specialist type.
Built-in and user-defined colonees are both instantiated through this class.
"""

import logging
from typing import List, Optional

from strands import Agent

from .colonee_registry import ColoneeDefinition
from .specialist_agents import BaseSpecialistAgent
from ..core.model_config import get_model

logger = logging.getLogger(__name__)


class DynamicSpecialistAgent(BaseSpecialistAgent):
    """
    A specialist agent fully described by a ColoneeDefinition.
    No subclassing required — the definition drives everything.
    """

    def __init__(
        self,
        session_manager,
        agent_id: str,
        specialization: str,
        definition: ColoneeDefinition,
        agent_manager=None,
        mcp_manager=None,
    ):
        self.definition = definition
        self.agent_manager = agent_manager
        self._specialist_type = definition.specialist_type

        # Lazy-loaded tool agent instances
        self._file_agent = None
        self._media_agent = None

        super().__init__(session_manager, agent_id, specialization, mcp_manager)

    def _extra_tools(self) -> list:
        """
        Return MCP tools for this colonee.

        Priority:
        1. If the colonee definition lists specific mcp_servers, fetch tools
           from exactly those servers (ignores global specialist_types scoping).
        2. Otherwise fall back to the global specialist-type scoping in MCPManager
           (servers whose specialist_types includes this colonee's specialist_type,
           or servers scoped to ALL).
        """
        if self.mcp_manager is None:
            return []

        defn = self.definition
        if defn.mcp_servers:
            tools = []
            for server_name in defn.mcp_servers:
                try:
                    tools.extend(self.mcp_manager.get_tools(server_name))
                except KeyError:
                    logger.warning(
                        "Colonee '%s': MCP server '%s' not registered — skipping.",
                        defn.name, server_name,
                    )
                except Exception as exc:
                    logger.warning(
                        "Colonee '%s': failed to get tools from MCP server '%s': %s",
                        defn.name, server_name, exc,
                    )
            return tools

        # No explicit server list — use global specialist-type scoping
        return self.mcp_manager.get_tools_for_specialist(self._specialist_type)

    def _create_agent(self) -> Agent:
        defn = self.definition
        system_prompt = defn.system_prompt.replace("{specialization}", self.specialization)

        # Append constraints so the LLM respects them
        c = defn.constraints
        constraint_lines = []
        if c.max_tool_calls:
            constraint_lines.append(f"- Use at most {c.max_tool_calls} tool calls per task.")
        if c.max_runtime_seconds:
            constraint_lines.append(f"- Complete your work within {c.max_runtime_seconds} seconds.")
        if c.forbidden_topics:
            constraint_lines.append(f"- Never discuss or engage with: {', '.join(c.forbidden_topics)}.")
        if c.output_format:
            constraint_lines.append(f"- Always respond in {c.output_format} format.")
        if constraint_lines:
            system_prompt += "\n\nConstraints:\n" + "\n".join(constraint_lines)

        tools = []
        for tool_key in defn.built_in_tools:
            loader = getattr(self, f"_load_{tool_key}_tools", None)
            if loader:
                tools.extend(loader())
            else:
                logger.warning("Unknown built_in_tool '%s' in colonee '%s'", tool_key, defn.name)

        # MCP tools scoped to this specialist type
        tools.extend(self._extra_tools())

        logger.info(
            "DynamicSpecialistAgent '%s' created with %d tools (built-in: %s, mcp: %s)",
            defn.name, len(tools), defn.built_in_tools, defn.mcp_servers,
        )

        return Agent(
            name=self.agent_id,
            agent_id=self.agent_id,
            system_prompt=system_prompt,
            model=get_model(),
            session_manager=self.session_manager,
            tools=tools,
        )

    def get_capabilities(self) -> List[str]:
        return list(self.definition.capabilities)

    def get_domain_expertise(self) -> List[str]:
        return [self.specialization] + self.definition.tags

    # ------------------------------------------------------------------
    # Tool loaders
    # ------------------------------------------------------------------

    def _load_research_tools(self) -> list:
        from colon.agents.tools.research.research_tools import get_research_tools
        return get_research_tools()

    def _load_computation_tools(self) -> list:
        from colon.agents.tools.computation.computation_tools import get_computation_tools
        return get_computation_tools()

    def _load_file_tools(self) -> list:
        if self._file_agent is None:
            from .tools.file.file_provider import FileToolProvider
            self._file_agent = FileToolProvider(self.session_manager, f"{self.agent_id}_file")
        fa = self._file_agent
        return [
            fa.read_file, fa.write_file, fa.append_to_file, fa.delete_file,
            fa.copy_file, fa.move_file, fa.list_files, fa.file_exists,
            fa.get_file_metadata, fa.search_in_files, fa.replace_in_file,
            fa.read_lines, fa.create_folder, fa.delete_folder, fa.get_public_url,
        ]

    def _load_media_tools(self) -> list:
        if self._media_agent is None:
            from .tools.media.media_provider import MediaToolProvider
            self._media_agent = MediaToolProvider(self.session_manager, f"{self.agent_id}_media")
        ma = self._media_agent
        return [
            ma.create_production, ma.write_script, ma.sanitize_image_prompt,
            ma.generate_image, ma.resize_image, ma.text_to_speech,
            ma.assemble_video, ma.save_to_disk, ma.load_from_disk,
            ma.list_artifacts, ma.delete_artifact, ma.get_production_info,
        ]
