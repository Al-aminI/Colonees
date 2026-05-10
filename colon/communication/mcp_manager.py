"""
Colonees MCP Manager
Connects the platform to external MCP (Model Context Protocol) servers.

MCP servers expose tools over a standard protocol. This manager:
- Connects to one or more MCP servers (stdio, HTTP, SSE transports)
- Retrieves their tool lists via the Strands MCPClient
- Makes those tools available to any specialist agent via get_tools()

Usage at platform startup:
    mcp = MCPManager()
    mcp.add_server("weather", "http", url="http://localhost:8001/mcp/")
    mcp.add_server("database", "stdio", command="python", args=["db_server.py"])

    # In AgentManager, pass mcp.get_tools() into the ToolRegistry or directly
    # into specialist agents via agent_manager.register_mcp_tools(mcp)
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

Transport = Literal["streamable_http", "sse", "stdio"]


@dataclass
class MCPServerConfig:
    name: str
    transport: Transport
    # Which specialist types receive this server's tools.
    # None / empty list means ALL specialists get them (opt-in broadcast).
    specialist_types: List[str] = field(default_factory=list)
    # HTTP / SSE
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None   # e.g. {"Authorization": "Bearer <token>"}
    # stdio
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None


class MCPManager:
    """
    Manages connections to external MCP servers and exposes their tools
    to the Colonees agent colony.

    Each server is registered with a name and transport config.
    Call get_tools(server_name) to retrieve Strands-compatible tool objects
    that can be passed directly into Agent(tools=[...]).
    """

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._active_clients: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Server registration
    # ------------------------------------------------------------------

    def add_server(
        self,
        name: str,
        transport: Transport,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        specialist_types: Optional[List[str]] = None,
    ) -> None:
        """
        Register an MCP server.

        Args:
            name:             Unique identifier (e.g. "weather", "database").
            transport:        "streamable_http" | "sse" | "stdio"
            url:              Server URL — required for streamable_http and sse.
            headers:          HTTP headers for streamable_http and sse transports.
                              Use this for API key auth, bearer tokens, etc.
                              e.g. {"Authorization": "Bearer sk-...", "X-API-Key": "..."}
            command:          Executable — required for stdio (e.g. "python").
            args:             CLI args for stdio (e.g. ["my_server.py"]).
            env:              Env vars for stdio transport — use for secrets the
                              server process needs (e.g. {"OPENAI_API_KEY": "sk-..."}).
            specialist_types: Which specialist types receive this server's tools.
                              Omit (or pass None) to give tools to ALL specialists.
                              Valid values: "researcher", "domain_expert", "analyst",
                                           "executor", "media_producer",
                                           and their legacy aliases:
                                           "research", "subject_expert", "assessment",
                                           "tutor", "video_production"

        Examples:
            # API-key-authenticated HTTP server, researcher only
            mcp.add_server(
                "pubmed", "streamable_http",
                url="https://pubmed-mcp.example.com/mcp/",
                headers={"X-API-Key": "your-key-here"},
                specialist_types=["researcher"]
            )

            # Bearer token auth
            mcp.add_server(
                "legal_db", "sse",
                url="https://legal-mcp.example.com/sse/",
                headers={"Authorization": "Bearer eyJ..."},
                specialist_types=["analyst", "researcher"]
            )

            # stdio server with secrets passed as env vars
            mcp.add_server(
                "database", "stdio",
                command="python", args=["db_server.py"],
                env={"DB_PASSWORD": "secret", "DB_HOST": "localhost"},
                specialist_types=["analyst"]
            )

            # All specialists get this utility server's tools
            mcp.add_server("utils", "streamable_http", url="http://localhost:8002/mcp/")
        """
        self._servers[name] = MCPServerConfig(
            name=name,
            transport=transport,
            specialist_types=specialist_types or [],
            url=url,
            headers=headers,
            command=command,
            args=args or [],
            env=env,
        )
        scope = specialist_types or ["ALL"]
        logger.info("MCP server registered: '%s' (%s) → specialists: %s", name, transport, scope)

    def remove_server(self, name: str) -> bool:
        if name in self._servers:
            del self._servers[name]
            logger.info("MCP server removed: '%s'", name)
            return True
        return False

    def list_servers(self) -> List[str]:
        return list(self._servers.keys())

    # ------------------------------------------------------------------
    # Tool retrieval
    # ------------------------------------------------------------------

    def get_tools(self, server_name: str) -> List[Any]:
        """
        Connect to a registered MCP server, retrieve its tools, and return
        them as Strands-compatible tool objects.

        The MCP client session is kept alive so tools remain callable.
        Call close_all() on platform shutdown to clean up.
        """
        if server_name not in self._servers:
            raise KeyError(f"MCP server '{server_name}' not registered. Known: {list(self._servers)}")

        cfg = self._servers[server_name]

        if server_name not in self._active_clients:
            client = self._build_client(cfg)
            client.__enter__()
            self._active_clients[server_name] = client
            logger.info("MCP client session opened: '%s'", server_name)

        client = self._active_clients[server_name]
        tools = client.list_tools_sync()
        return tools

    def close_all(self) -> None:
        """Close all active MCP client sessions. Call on platform shutdown."""
        for name, client in list(self._active_clients.items()):
            try:
                client.__exit__(None, None, None)
                logger.info("MCP client session closed: '%s'", name)
            except Exception as e:
                logger.warning("Error closing MCP client '%s': %s", name, e)
        self._active_clients.clear()

    def get_tools_for_specialist(self, specialist_type: str) -> List[Any]:
        """
        Retrieve tools from all MCP servers that are scoped to the given
        specialist type (or scoped to ALL specialists).

        Args:
            specialist_type: The specialist type string, e.g. "researcher",
                             "domain_expert", "analyst", "executor",
                             "media_producer" (and legacy aliases).

        Returns:
            Flat list of Strands tool objects for this specialist.
        """
        tools: List[Any] = []
        for name, cfg in self._servers.items():
            # Empty specialist_types means broadcast to all
            if cfg.specialist_types and specialist_type not in cfg.specialist_types:
                continue
            try:
                tools.extend(self.get_tools(name))
            except Exception as exc:
                logger.warning(
                    "Failed to get tools from MCP server '%s' for specialist '%s': %s",
                    name, specialist_type, exc,
                )
        return tools

    def get_all_tools(self) -> List[Any]:
        """Retrieve tools from ALL registered MCP servers (ignores specialist scoping)."""
        all_tools: List[Any] = []
        for name in self._servers:
            try:
                all_tools.extend(self.get_tools(name))
            except Exception as exc:
                logger.warning("Failed to get tools from MCP server '%s': %s", name, exc)
        return all_tools

    @contextmanager
    def get_client_context(self, server_name: str):
        """
        Context manager that keeps the MCP connection open for the duration
        of the block. Use this when creating agents that need the connection
        alive while they execute.

        Example:
            with mcp.get_client_context("weather") as tools:
                agent = Agent(tools=tools)
                agent("What is the weather in Lagos?")
        """
        if server_name not in self._servers:
            raise KeyError(f"MCP server '{server_name}' not registered.")

        cfg = self._servers[server_name]
        client = self._build_client(cfg)

        with client:
            tools = client.list_tools_sync()
            logger.info("MCP connection open: '%s' (%d tools)", server_name, len(tools))
            yield tools
        logger.info("MCP connection closed: '%s'", server_name)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_client(self, cfg: MCPServerConfig):
        """Build a Strands MCPClient for the given server config."""
        from strands.tools.mcp.mcp_client import MCPClient

        if cfg.transport == "streamable_http":
            if not cfg.url:
                raise ValueError(f"MCP server '{cfg.name}': url is required for streamable_http transport")
            from mcp.client.streamable_http import streamablehttp_client
            url = cfg.url
            headers = cfg.headers or {}
            return MCPClient(lambda: streamablehttp_client(url, headers=headers))

        elif cfg.transport == "sse":
            if not cfg.url:
                raise ValueError(f"MCP server '{cfg.name}': url is required for sse transport")
            from mcp.client.sse import sse_client
            url = cfg.url
            headers = cfg.headers or {}
            return MCPClient(lambda: sse_client(url, headers=headers))

        elif cfg.transport == "stdio":
            if not cfg.command:
                raise ValueError(f"MCP server '{cfg.name}': command is required for stdio transport")
            from mcp import stdio_client, StdioServerParameters
            params = StdioServerParameters(
                command=cfg.command,
                args=cfg.args,
                env=cfg.env,
            )
            return MCPClient(lambda: stdio_client(params))

        else:
            raise ValueError(f"Unknown transport '{cfg.transport}' for MCP server '{cfg.name}'")
