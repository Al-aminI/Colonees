"""
Colonees Platform — Main Application Entrypoint
Production-grade autonomous agent swarm platform.
"The Autonomous Agent Swarm Platform"
"""

import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from colon.core.platform import ColoneesPlatform
from colon.core.config import CologeesConfig
from colon.agents.colonee_registry import (
    ColoneeDefinition, MemoryConfig, ConstraintsConfig, EvaluationConfig,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Colonees",
    description="The Autonomous Agent Swarm Platform — open-source, production-grade autonomous agent swarm.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Platform singleton
# ---------------------------------------------------------------------------

_platform: Optional[ColoneesPlatform] = None


async def get_platform() -> ColoneesPlatform:
    global _platform
    if _platform is None:
        logger.info("Initializing Colonees Platform...")
        config = CologeesConfig.from_environment()
        _platform = ColoneesPlatform(config)
        await _platform.initialize()
        logger.info("Colonees Platform ready")
    return _platform


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class InvokeRequest(BaseModel):
    goal: str = Field(..., description="The goal or task for the agent swarm to accomplish.")
    user_id: str = Field("anonymous", description="Optional user identifier for session tracking.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional additional context.")
    colonees: Optional[list] = Field(
        None,
        description=(
            "Optional allowlist of colonee names the superagent may spawn for this request. "
            "If omitted, all enabled colonees are available. "
            "Example: ['researcher', 'analyst']"
        ),
    )


class InvokeResponse(BaseModel):
    status: str
    result: Any


class AgentRequest(BaseModel):
    agent_type: str = Field(..., description="Type of specialist agent to invoke directly.")
    task: str = Field(..., description="Task description for the agent.")
    context: Dict[str, Any] = Field(default_factory=dict)


# MCP schemas
class MCPServerRequest(BaseModel):
    name: str = Field(..., description="Unique name for this MCP server (e.g. 'weather', 'database').")
    transport: str = Field(..., description="Transport type: 'streamable_http', 'sse', or 'stdio'.")
    url: Optional[str] = Field(None, description="Server URL — required for streamable_http and sse transports.")
    headers: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "HTTP headers for streamable_http and sse transports. "
            "Use for API key auth, bearer tokens, or any custom headers. "
            "e.g. {\"Authorization\": \"Bearer sk-...\", \"X-API-Key\": \"...\"}"
        ),
    )
    command: Optional[str] = Field(None, description="Executable — required for stdio transport (e.g. 'python').")
    args: list = Field(default_factory=list, description="CLI args for stdio transport (e.g. ['server.py']).")
    env: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Environment variables for stdio transport. "
            "Use to pass secrets the server process needs (e.g. {\"OPENAI_API_KEY\": \"sk-...\"})."
        ),
    )
    specialist_types: list = Field(
        default_factory=list,
        description=(
            "Specialist types that receive this server's tools. "
            "Leave empty to give tools to ALL specialists. "
            "Valid values: 'researcher', 'domain_expert', 'analyst', 'executor', 'media_producer'."
        ),
    )


# Colonee schemas
class MemoryConfigSchema(BaseModel):
    enabled: bool = False
    strategy: str = "basic"
    max_size_mb: int = 512

class ConstraintsConfigSchema(BaseModel):
    max_tool_calls: int = 30
    max_runtime_seconds: int = 600
    forbidden_topics: list = Field(default_factory=list)
    output_format: Optional[str] = None

class EvaluationConfigSchema(BaseModel):
    quality_threshold: float = 0.7
    require_sources: bool = False
    require_structured_output: bool = False
    custom_criteria: list = Field(default_factory=list)

class ColoneeCreateRequest(BaseModel):
    name: str = Field(..., description="Unique slug for this colonee, e.g. 'legal_researcher'.")
    display_name: str = Field(..., description="Human-readable name.")
    description: str = Field(..., description="What this colonee does.")
    specialist_type: str = Field(
        ...,
        description=(
            "Base specialist type this colonee maps to. "
            "Valid: 'researcher', 'domain_expert', 'analyst', 'executor', 'media_producer'."
        ),
    )
    system_prompt: str = Field(
        ...,
        description="System prompt for this colonee. Use {specialization} as a placeholder.",
    )
    capabilities: list = Field(default_factory=list, description="Capability strings.")
    built_in_tools: list = Field(
        default_factory=list,
        description="Built-in tool sets to enable. Subset of: file, computation, research, media.",
    )
    mcp_servers: list = Field(
        default_factory=list,
        description="MCP server names (must be registered via /mcp/servers) to attach.",
    )
    memory: MemoryConfigSchema = Field(default_factory=MemoryConfigSchema)
    constraints: ConstraintsConfigSchema = Field(default_factory=ConstraintsConfigSchema)
    evaluation: EvaluationConfigSchema = Field(default_factory=EvaluationConfigSchema)
    tags: list = Field(default_factory=list)
    created_by: str = "api"

class ColoneeUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[list] = None
    built_in_tools: Optional[list] = None
    mcp_servers: Optional[list] = None
    memory: Optional[MemoryConfigSchema] = None
    constraints: Optional[ConstraintsConfigSchema] = None
    evaluation: Optional[EvaluationConfigSchema] = None
    tags: Optional[list] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    """Recursively coerce objects to JSON-serialisable types."""
    from datetime import date, datetime
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if hasattr(obj, "__dict__"):
        return _serialize(obj.__dict__)
    try:
        return str(obj)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health():
    """Liveness probe — returns 200 when the service is running."""
    return {"status": "ok", "service": "colonees"}


@app.get("/status", tags=["System"])
async def status():
    """
    Returns the current platform status including active sessions,
    registered agents, and resource utilisation.
    """
    try:
        platform = await get_platform()
        platform_status = await platform.get_platform_status()
        return JSONResponse(content=_serialize(platform_status))
    except Exception as e:
        logger.error("Status check failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/invoke", response_model=InvokeResponse, tags=["Agent Swarm"])
async def invoke(body: InvokeRequest):
    """
    Submit a goal to the Colonees agent swarm.

    The superagent decomposes the goal, delegates to specialist agents,
    and returns the final synthesised result.
    """
    try:
        platform = await get_platform()
        result = await platform.handle_request(
            user_goal=body.goal,
            context={"user_id": body.user_id, "colonees": body.colonees, **body.context},
        )
        return InvokeResponse(status="success", result=_serialize(result))
    except Exception as e:
        logger.error("Invoke failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/invoke", tags=["Agent Swarm"])
async def invoke_agent(body: AgentRequest):
    """
    Invoke a specific specialist agent directly by type.

    Useful for targeted tasks where you know which specialist is needed
    (e.g. `researcher`, `analyst`, `media_producer`).
    """
    try:
        platform = await get_platform()
        result = await platform.handle_request(
            user_goal=body.task,
            context={"agent_type": body.agent_type, **body.context},
        )
        return JSONResponse(content={"status": "success", "result": _serialize(result)})
    except Exception as e:
        logger.error("Agent invoke failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", tags=["Agent Swarm"])
async def list_agents():
    """List all registered specialist agents and their capabilities."""
    try:
        platform = await get_platform()
        agents = await platform.list_agents() if hasattr(platform, "list_agents") else []
        return {"agents": _serialize(agents)}
    except Exception as e:
        logger.error("List agents failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# MCP Routes
# ---------------------------------------------------------------------------

@app.post("/mcp/servers", tags=["MCP"])
async def register_mcp_server(body: MCPServerRequest):
    """
    Register an external MCP server with the platform.

    The server's tools will be injected into specialist agents at spawn time,
    scoped to the specialist types listed in `specialist_types`.
    Omit `specialist_types` (or pass an empty list) to give the tools to all specialists.

    Transports:
    - `streamable_http` — provide `url`
    - `sse`             — provide `url`
    - `stdio`           — provide `command` and optionally `args` / `env`
    """
    try:
        platform = await get_platform()
        platform.agent_manager.mcp.add_server(
            name=body.name,
            transport=body.transport,
            url=body.url,
            headers=body.headers,
            command=body.command,
            args=body.args,
            env=body.env,
            specialist_types=body.specialist_types or [],
        )
        return {
            "status": "registered",
            "server": body.name,
            "transport": body.transport,
            "specialist_types": body.specialist_types or ["ALL"],
        }
    except Exception as e:
        logger.error("MCP server registration failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/mcp/servers/{server_name}", tags=["MCP"])
async def remove_mcp_server(server_name: str):
    """Remove a registered MCP server by name."""
    try:
        platform = await get_platform()
        removed = platform.agent_manager.mcp.remove_server(server_name)
        if not removed:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found.")
        return {"status": "removed", "server": server_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("MCP server removal failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/servers", tags=["MCP"])
async def list_mcp_servers():
    """List all registered MCP servers and their specialist scoping."""
    try:
        platform = await get_platform()
        mcp = platform.agent_manager.mcp
        servers = [
            {
                "name": cfg.name,
                "transport": cfg.transport,
                "url": cfg.url,
                "command": cfg.command,
                "args": cfg.args,
                # Mask header values — show keys only so secrets aren't leaked
                "headers": {k: "***" for k in cfg.headers} if cfg.headers else None,
                "specialist_types": cfg.specialist_types or ["ALL"],
            }
            for cfg in mcp._servers.values()
        ]
        return {"servers": servers, "count": len(servers)}
    except Exception as e:
        logger.error("List MCP servers failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Colonee Routes
# ---------------------------------------------------------------------------

@app.post("/colonees", tags=["Colonees"], status_code=201)
async def create_colonee(body: ColoneeCreateRequest):
    """
    Create a new Colonee — a fully-described specialist agent definition.

    A Colonee defines a specialist's role, system prompt, tools (built-in + MCP),
    memory config, constraints, and evaluation criteria. Once created, it can be
    spawned by the superagent just like any built-in specialist.

    Built-in tool sets: `file`, `computation`, `research`, `media`
    MCP servers must be registered first via `POST /mcp/servers`.
    """
    try:
        platform = await get_platform()
        registry = platform.agent_manager.colonee_registry

        defn = ColoneeDefinition(
            name=body.name,
            display_name=body.display_name,
            description=body.description,
            specialist_type=body.specialist_type,
            system_prompt=body.system_prompt,
            capabilities=body.capabilities,
            built_in_tools=body.built_in_tools,
            mcp_servers=body.mcp_servers,
            memory=MemoryConfig(**body.memory.model_dump()),
            constraints=ConstraintsConfig(**body.constraints.model_dump()),
            evaluation=EvaluationConfig(**body.evaluation.model_dump()),
            tags=body.tags,
            created_by=body.created_by,
        )
        created = registry.create(defn)
        platform.agent_manager._sync_capabilities_from_registry()
        return created.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Create colonee failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/colonees", tags=["Colonees"])
async def list_colonees(enabled_only: bool = False, tag: Optional[str] = None):
    """
    List all Colonee definitions — built-in and user-defined.

    Filter by `enabled_only=true` to see only active colonees.
    Filter by `tag` to find colonees by domain (e.g. `tag=healthcare`).
    """
    try:
        platform = await get_platform()
        registry = platform.agent_manager.colonee_registry
        tags = [tag] if tag else None
        colonees = registry.list(enabled_only=enabled_only, tags=tags)
        return {"colonees": [c.to_dict() for c in colonees], "count": len(colonees)}
    except Exception as e:
        logger.error("List colonees failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/colonees/{name}", tags=["Colonees"])
async def get_colonee(name: str):
    """Get a single Colonee definition by name."""
    try:
        platform = await get_platform()
        defn = platform.agent_manager.colonee_registry.get(name)
        if not defn:
            raise HTTPException(status_code=404, detail=f"Colonee '{name}' not found.")
        return defn.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/colonees/{name}", tags=["Colonees"])
async def update_colonee(name: str, body: ColoneeUpdateRequest):
    """
    Update a Colonee definition.

    You can update any field except `name`, `builtin`, and `created_at`.
    Changes take effect for agents spawned after the update.
    """
    try:
        platform = await get_platform()
        updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
        updated = platform.agent_manager.colonee_registry.update(name, updates)
        platform.agent_manager._sync_capabilities_from_registry()
        return updated.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Update colonee failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/colonees/{name}", tags=["Colonees"])
async def delete_colonee(name: str):
    """Delete a user-defined Colonee. Built-in colonees cannot be deleted."""
    try:
        platform = await get_platform()
        platform.agent_manager.colonee_registry.delete(name)
        return {"status": "deleted", "name": name}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/colonees/{name}/enable", tags=["Colonees"])
async def enable_colonee(name: str):
    """Enable a Colonee so it can be spawned by the superagent."""
    try:
        platform = await get_platform()
        updated = platform.agent_manager.colonee_registry.enable(name)
        return {"status": "enabled", "name": name, "colonee": updated.to_dict()}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/colonees/{name}/disable", tags=["Colonees"])
async def disable_colonee(name: str):
    """
    Disable a Colonee. Disabled colonees cannot be spawned.
    Use this to temporarily remove a specialist from the swarm without deleting it.
    """
    try:
        platform = await get_platform()
        updated = platform.agent_manager.colonee_registry.disable(name)
        return {"status": "disabled", "name": name, "colonee": updated.to_dict()}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
