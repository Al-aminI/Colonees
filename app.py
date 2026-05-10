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

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from colon.core.platform import ColoneesPlatform
from colon.core.config import CologeesConfig
from colon.agents.colonee_registry import (
    ColoneeDefinition, MemoryConfig, ConstraintsConfig, EvaluationConfig,
)
from colon.core.workspace import WorkspaceManager, WorkspaceDefinition
from colon.core.knowledge_base import KnowledgeBaseManager, KnowledgeBaseDefinition
from colon.core.templates import TemplateRegistry
from colon.connectors import ConnectorManager, ConnectorCatalog, OpenAPIConnector, RepoConnector

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Platform singleton
# ---------------------------------------------------------------------------

_platform: Optional[ColoneesPlatform] = None
_workspace_manager: Optional[WorkspaceManager] = None
_kb_manager: Optional[KnowledgeBaseManager] = None
_template_registry = TemplateRegistry()  # read-only, no persistence needed
_connector_manager: Optional[ConnectorManager] = None


async def get_platform() -> ColoneesPlatform:
    global _platform
    if _platform is None:
        logger.info("Initializing Colonees Platform...")
        config = CologeesConfig.from_environment()
        _platform = ColoneesPlatform(config)
        await _platform.initialize()
        logger.info("Colonees Platform ready")
    return _platform


def get_workspace_manager() -> WorkspaceManager:
    global _workspace_manager
    if _workspace_manager is None:
        storage_dir = os.getenv("COLONEES_STORAGE_DIR", "colonees_files")
        _workspace_manager = WorkspaceManager(storage_dir=storage_dir)
        logger.info("WorkspaceManager initialized (storage: %s)", storage_dir)
    return _workspace_manager


def get_kb_manager() -> KnowledgeBaseManager:
    global _kb_manager
    if _kb_manager is None:
        storage_dir = os.getenv("COLONEES_STORAGE_DIR", "colonees_files")
        _kb_manager = KnowledgeBaseManager(storage_dir=storage_dir)
        logger.info("KnowledgeBaseManager initialized (storage: %s)", storage_dir)
    return _kb_manager


def get_connector_manager() -> ConnectorManager:
    global _connector_manager
    if _connector_manager is None:
        storage_dir = os.getenv("COLONEES_STORAGE_DIR", "colonees_files")
        _connector_manager = ConnectorManager(storage_dir=storage_dir)
        logger.info("ConnectorManager initialized (storage: %s)", storage_dir)
    return _connector_manager


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class InvokeRequest(BaseModel):
    goal: str = Field(..., description="The goal or task for the agent swarm to accomplish.")
    session_id: Optional[str] = Field(
        None,
        description=(
            "Session ID to group this request with previous ones for conversation history. "
            "If omitted, a new session key is generated automatically. "
            "Pass the same session_id across requests to maintain history continuity."
        ),
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional additional context.")
    colonees: Optional[list] = Field(
        None,
        description=(
            "Optional allowlist of colonee names the superagent may spawn for this request. "
            "If omitted, all enabled colonees are available. "
            "Example: ['researcher', 'analyst']"
        ),
    )
    workspace: Optional[str] = Field(
        None,
        description=(
            "Optional workspace name. When provided and `colonees` is not explicitly set, "
            "the colonee list is auto-populated from the workspace definition."
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
            "Specialist type this colonee maps to. Used for MCP server tool scoping "
            "and capability matching. Standard types: 'researcher', 'domain_expert', "
            "'analyst', 'executor', 'media_producer'. Custom types are also accepted."
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

    If `workspace` is provided and `colonees` is not explicitly set,
    the colonee allowlist is auto-populated from the workspace definition.
    """
    try:
        platform = await get_platform()

        # Resolve colonees from workspace when not explicitly provided
        colonees = body.colonees
        if colonees is None and body.workspace:
            ws_mgr = get_workspace_manager()
            ws = ws_mgr.get(body.workspace)
            if ws is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workspace '{body.workspace}' not found.",
                )
            if not ws.enabled:
                raise HTTPException(
                    status_code=400,
                    detail=f"Workspace '{body.workspace}' is disabled.",
                )
            colonees = ws.colonees or None

        result = await platform.handle_request(
            user_goal=body.goal,
            context={"session_id": body.session_id, "workspace": body.workspace, "colonees": colonees, **body.context},
        )
        return InvokeResponse(status="success", result=_serialize(result))
    except HTTPException:
        raise
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


@app.get("/history/{session_id}", tags=["Agent Swarm"])
async def get_history(session_id: str, limit: Optional[int] = None):
    """
    Retrieve conversation history for a session.

    Returns all stored turns (user goals + assistant responses) ordered oldest-first.
    Pass `limit` to cap the number of entries returned.
    """
    try:
        platform = await get_platform()
        history = await platform.memory_manager.get_history(session_id, limit=limit)
        return {"session_id": session_id, "history": history, "count": len(history)}
    except Exception as e:
        logger.error("Get history failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{session_id}", tags=["Agent Swarm"])
async def clear_history(session_id: str):
    """Clear all conversation history for a session (human-readable turns + Strands messages)."""
    try:
        platform = await get_platform()
        # Clear human-readable history
        await platform.memory_manager.clear(session_id)
        # Also clear the Strands-level messages and state for this session
        from colon.memory.strands_session import ColoneesStrandsSessionManager
        strands_session = ColoneesStrandsSessionManager(
            session_id=session_id,
            backend=platform.memory_manager.backend,
        )
        await strands_session.clear()
        return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        logger.error("Clear history failed: %s", e)
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
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# API Key Auth
# ---------------------------------------------------------------------------

_API_KEY = os.getenv("COLONEES_API_KEY", "")
_security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    x_api_key: Optional[str] = None,
):
    """Require API key via Bearer token or X-API-Key header."""
    from fastapi import Header
    return True  # public by default unless COLONEES_API_KEY is set


async def require_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
):
    """Require a valid API key. If COLONEES_API_KEY is not set, all requests pass."""
    if not _API_KEY:
        return True

    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.headers.get("X-API-Key")

    if token != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True


# ---------------------------------------------------------------------------
# Workspace productization: invoke, export, import
# ---------------------------------------------------------------------------

class WorkspaceInvokeRequest(BaseModel):
    goal: str = Field(..., description="The goal or task for the workspace agent to accomplish.")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context.")


@app.post("/workspaces/{name}/invoke", tags=["Workspaces"])
async def invoke_workspace(name: str, body: WorkspaceInvokeRequest, _auth=Depends(require_api_key)):
    """
    Invoke a workspace directly — the workspace acts as a standalone agent API.

    This is the primary productization endpoint. Once you've configured a
    workspace with colonees, tools, and knowledge bases, call this endpoint
    to use it from any external application.

    Authentication: set ``COLONEES_API_KEY`` env var and pass it as a
    ``Bearer`` token or ``X-API-Key`` header.
    """
    try:
        ws_mgr = get_workspace_manager()
        ws = ws_mgr.get(name)
        if not ws:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found.")
        if not ws.enabled:
            raise HTTPException(status_code=400, detail=f"Workspace '{name}' is disabled.")

        platform = await get_platform()

        result = await platform.handle_request(
            user_goal=body.goal,
            context={
                "session_id": body.session_id,
                "workspace": name,
                "colonees": ws.colonees or None,
                **body.context,
            },
        )
        return {
            "status": "success",
            "workspace": name,
            "result": _serialize(result.get("response", result)),
            "session_id": result.get("session_id"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workspace invoke failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workspaces/{name}/export", tags=["Workspaces"])
async def export_workspace(name: str):
    """
    Export a workspace definition as JSON, including all associated colonees
    and knowledge bases. Use this to share, version, or migrate workspaces.
    """
    try:
        ws_mgr = get_workspace_manager()
        ws = ws_mgr.get(name)
        if not ws:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found.")

        platform = await get_platform()
        registry = platform.agent_manager.colonee_registry
        kb_mgr = get_kb_manager()

        colonees = []
        for cn in ws.colonees:
            c = registry.get(cn)
            if c:
                colonees.append(c.to_dict())

        kbs = []
        for kbn in ws.knowledge_bases:
            kb = kb_mgr.get(kbn)
            if kb:
                kbs.append(kb.to_dict())

        return {
            "workspace": ws.to_dict(),
            "colonees": colonees,
            "knowledge_bases": kbs,
            "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Export workspace failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class WorkspaceImportRequest(BaseModel):
    workspace: Dict[str, Any] = Field(..., description="Workspace definition dict.")
    colonees: Optional[list] = Field(default_factory=list, description="Colonee definitions to create.")
    knowledge_bases: Optional[list] = Field(default_factory=list, description="Knowledge base definitions to create.")


@app.post("/workspaces/import", tags=["Workspaces"], status_code=201)
async def import_workspace(body: WorkspaceImportRequest):
    """
    Import a workspace from a previously-exported JSON definition.

    Creates the workspace, its colonees, and knowledge bases. Skips any
    resources that already exist (name collision).
    """
    try:
        ws_mgr = get_workspace_manager()
        platform = await get_platform()
        registry = platform.agent_manager.colonee_registry
        kb_mgr = get_kb_manager()

        ws_data = body.workspace
        ws_name = ws_data.get("name")
        if not ws_name:
            raise HTTPException(status_code=400, detail="Workspace data must include 'name'.")

        created_colonees = []
        for cdata in (body.colonees or []):
            cn = cdata.get("name")
            if cn and not registry.get(cn):
                try:
                    defn = ColoneeDefinition.from_dict(cdata)
                    registry.create(defn)
                    created_colonees.append(cn)
                except Exception as e:
                    logger.warning("Import: failed to create colonee '%s': %s", cn, e)

        created_kbs = []
        for kbdata in (body.knowledge_bases or []):
            kbn = kbdata.get("name")
            if kbn and not kb_mgr.get(kbn):
                try:
                    kdef = KnowledgeBaseDefinition.from_dict(kbdata)
                    kb_mgr.create(kdef)
                    created_kbs.append(kbn)
                except Exception as e:
                    logger.warning("Import: failed to create KB '%s': %s", kbn, e)

        if not ws_mgr.get(ws_name):
            ws_def = WorkspaceDefinition.from_dict(ws_data)
            ws_mgr.create(ws_def)
            workspace_created = True
        else:
            workspace_created = False

        if created_colonees:
            platform.agent_manager._sync_capabilities_from_registry()

        return {
            "status": "imported",
            "workspace": ws_name,
            "workspace_created": workspace_created,
            "colonees_created": created_colonees,
            "knowledge_bases_created": created_kbs,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Import workspace failed: %s", e)
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
# Workspace Schemas
# ---------------------------------------------------------------------------

class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., description="Unique slug for this workspace, e.g. 'customer_support'.")
    display_name: str = Field(..., description="Human-readable name, e.g. 'Customer Support'.")
    description: str = Field(..., description="What this workspace is for.")
    colonees: list = Field(default_factory=list, description="Colonee names to include.")
    mcp_servers: list = Field(default_factory=list, description="MCP server names to include.")
    knowledge_bases: list = Field(default_factory=list, description="Knowledge base names to include.")
    icon: str = Field(default="", description="Emoji or icon name for the UI.")
    color: str = Field(default="#3b82f6", description="Hex color for the UI.")
    created_by: str = "api"


class WorkspaceUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    colonees: Optional[list] = None
    mcp_servers: Optional[list] = None
    knowledge_bases: Optional[list] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    enabled: Optional[bool] = None


# ---------------------------------------------------------------------------
# Workspace Routes
# ---------------------------------------------------------------------------

@app.post("/workspaces", tags=["Workspaces"], status_code=201)
async def create_workspace(body: WorkspaceCreateRequest):
    """
    Create a new Workspace — a logical grouping of colonees, MCP servers,
    and knowledge bases for a specific use case.

    Once created, pass the workspace name in `/invoke` to automatically
    scope the agent swarm to the workspace's colonees.
    """
    try:
        ws_mgr = get_workspace_manager()
        defn = WorkspaceDefinition(
            name=body.name,
            display_name=body.display_name,
            description=body.description,
            colonees=body.colonees,
            mcp_servers=body.mcp_servers,
            knowledge_bases=body.knowledge_bases,
            icon=body.icon,
            color=body.color,
            created_by=body.created_by,
        )
        created = ws_mgr.create(defn)
        return created.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Create workspace failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workspaces", tags=["Workspaces"])
async def list_workspaces(enabled_only: bool = False):
    """
    List all workspaces.

    Filter by `enabled_only=true` to see only active workspaces.
    """
    try:
        ws_mgr = get_workspace_manager()
        workspaces = ws_mgr.list(enabled_only=enabled_only)
        return {"workspaces": [ws.to_dict() for ws in workspaces], "count": len(workspaces)}
    except Exception as e:
        logger.error("List workspaces failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workspaces/{name}", tags=["Workspaces"])
async def get_workspace(name: str):
    """Get a single workspace by name."""
    try:
        ws_mgr = get_workspace_manager()
        defn = ws_mgr.get(name)
        if not defn:
            raise HTTPException(status_code=404, detail=f"Workspace '{name}' not found.")
        return defn.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/workspaces/{name}", tags=["Workspaces"])
async def update_workspace(name: str, body: WorkspaceUpdateRequest):
    """
    Update a workspace definition.

    You can update any field except `name`, `created_at`, and `created_by`.
    """
    try:
        ws_mgr = get_workspace_manager()
        updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
        updated = ws_mgr.update(name, updates)
        return updated.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Update workspace failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/workspaces/{name}", tags=["Workspaces"])
async def delete_workspace(name: str):
    """Delete a workspace by name."""
    try:
        ws_mgr = get_workspace_manager()
        ws_mgr.delete(name)
        return {"status": "deleted", "name": name}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspaces/{name}/enable", tags=["Workspaces"])
async def enable_workspace(name: str):
    """Enable a workspace so it can be used in /invoke calls."""
    try:
        ws_mgr = get_workspace_manager()
        updated = ws_mgr.enable(name)
        return {"status": "enabled", "name": name, "workspace": updated.to_dict()}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workspaces/{name}/disable", tags=["Workspaces"])
async def disable_workspace(name: str):
    """
    Disable a workspace. Disabled workspaces cannot be used in /invoke calls.
    """
    try:
        ws_mgr = get_workspace_manager()
        updated = ws_mgr.disable(name)
        return {"status": "disabled", "name": name, "workspace": updated.to_dict()}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Knowledge Base Schemas
# ---------------------------------------------------------------------------

class KBCreateRequest(BaseModel):
    name: str = Field(..., description="Unique slug for this knowledge base, e.g. 'product_docs'.")
    display_name: str = Field(..., description="Human-readable name.")
    description: str = Field(..., description="What this knowledge base contains.")
    type: str = Field(
        default="files",
        description="Knowledge base type: 'files', 'database', or 'api'.",
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Connection config for database/api types.",
    )
    specialist_types: list = Field(
        default_factory=list,
        description=(
            "Specialist types that can access this KB. "
            "Leave empty to allow ALL specialists."
        ),
    )
    workspaces: list = Field(
        default_factory=list,
        description="Workspace names that include this KB.",
    )
    enabled: bool = True


class KBUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    specialist_types: Optional[list] = None
    workspaces: Optional[list] = None
    enabled: Optional[bool] = None


class KBSearchRequest(BaseModel):
    query: str = Field(..., description="Search query.")
    top_k: int = Field(default=5, description="Maximum number of results to return.")


# ---------------------------------------------------------------------------
# Knowledge Base Routes
# ---------------------------------------------------------------------------

@app.post("/knowledge-bases", tags=["Knowledge Bases"], status_code=201)
async def create_knowledge_base(body: KBCreateRequest):
    """
    Create a new Knowledge Base.

    A Knowledge Base holds uploaded documents (PDFs, CSVs, text files, markdown)
    that specialist agents can search at runtime. Once created, upload files
    via ``POST /knowledge-bases/{name}/upload``.
    """
    try:
        kb_mgr = get_kb_manager()
        defn = KnowledgeBaseDefinition(
            name=body.name,
            display_name=body.display_name,
            description=body.description,
            type=body.type,
            config=body.config,
            specialist_types=body.specialist_types,
            workspaces=body.workspaces,
            enabled=body.enabled,
        )
        created = kb_mgr.create(defn)
        return created.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Create knowledge base failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge-bases", tags=["Knowledge Bases"])
async def list_knowledge_bases(enabled_only: bool = False):
    """
    List all knowledge bases.

    Filter by ``enabled_only=true`` to see only active knowledge bases.
    """
    try:
        kb_mgr = get_kb_manager()
        kbs = kb_mgr.list(enabled_only=enabled_only)
        return {"knowledge_bases": [kb.to_dict() for kb in kbs], "count": len(kbs)}
    except Exception as e:
        logger.error("List knowledge bases failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge-bases/{name}", tags=["Knowledge Bases"])
async def get_knowledge_base(name: str):
    """Get a single knowledge base by name."""
    try:
        kb_mgr = get_kb_manager()
        defn = kb_mgr.get(name)
        if not defn:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{name}' not found.")
        return defn.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/knowledge-bases/{name}", tags=["Knowledge Bases"])
async def update_knowledge_base(name: str, body: KBUpdateRequest):
    """
    Update a knowledge base definition.

    You can update any field except ``name`` and ``created_at``.
    """
    try:
        kb_mgr = get_kb_manager()
        updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
        updated = kb_mgr.update(name, updates)
        return updated.to_dict()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Update knowledge base failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/knowledge-bases/{name}", tags=["Knowledge Bases"])
async def delete_knowledge_base(name: str):
    """Delete a knowledge base and all its uploaded files."""
    try:
        kb_mgr = get_kb_manager()
        kb_mgr.delete(name)
        return {"status": "deleted", "name": name}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge-bases/{name}/upload", tags=["Knowledge Bases"])
async def upload_kb_file(name: str, file: UploadFile = File(...)):
    """
    Upload a file to a knowledge base.

    Supported formats: PDF, CSV, TXT, MD, JSON, and other text-based files.
    The file will be available for search immediately after upload.
    """
    try:
        kb_mgr = get_kb_manager()
        content = await file.read()
        file_path = kb_mgr.upload_file(name, file.filename, content)
        return {
            "status": "uploaded",
            "knowledge_base": name,
            "filename": file.filename,
            "path": file_path,
            "size_bytes": len(content),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Upload file to KB failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/knowledge-bases/{name}/files/{filename}", tags=["Knowledge Bases"])
async def delete_kb_file(name: str, filename: str):
    """Delete a single file from a knowledge base."""
    try:
        kb_mgr = get_kb_manager()
        kb_mgr.delete_file(name, filename)
        return {"status": "deleted", "knowledge_base": name, "filename": filename}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge-bases/{name}/files", tags=["Knowledge Bases"])
async def list_kb_files(name: str):
    """List all files in a knowledge base with metadata (size, modified date)."""
    try:
        kb_mgr = get_kb_manager()
        files = kb_mgr.list_files(name)
        return {"knowledge_base": name, "files": files, "count": len(files)}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge-bases/{name}/search", tags=["Knowledge Bases"])
async def search_knowledge_base(name: str, body: KBSearchRequest):
    """
    Search a knowledge base for relevant content.

    Splits uploaded files into chunks and scores them by query-term frequency.
    Returns the top-k most relevant chunks with source file and score.
    """
    try:
        kb_mgr = get_kb_manager()
        results = kb_mgr.search(name, body.query, top_k=body.top_k)
        return {
            "knowledge_base": name,
            "query": body.query,
            "results": results,
            "result_count": len(results),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Search KB failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Template Routes
# ---------------------------------------------------------------------------

@app.get("/templates", tags=["Templates"])
async def list_templates(category: Optional[str] = None):
    """
    List all available use-case templates.

    Templates provide pre-built configurations (colonees, workspace layout,
    MCP server suggestions, knowledge base recommendations) for common
    use cases such as customer support, legal, finance, and more.

    Optionally filter by ``category`` (e.g. ``?category=support``).
    """
    templates = _template_registry.list_templates(category=category)
    return {
        "templates": [t.to_dict() for t in templates],
        "count": len(templates),
    }


@app.get("/templates/categories", tags=["Templates"])
async def list_template_categories():
    """
    List all template categories with counts.

    Returns ``[{name, display_name, icon, count}, ...]``.
    """
    categories = _template_registry.get_categories()
    return {"categories": categories, "count": len(categories)}


@app.get("/templates/{name}", tags=["Templates"])
async def get_template(name: str):
    """Get a single use-case template by slug name."""
    tpl = _template_registry.get_template(name)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found.")
    return tpl.to_dict()


@app.post("/templates/{name}/apply", tags=["Templates"])
async def apply_template(name: str):
    """
    Apply a use-case template to the platform.

    This will:
    1. Create colonees defined in the template (skipping any that already exist).
    2. Create a workspace containing those colonees.
    3. Create empty knowledge base placeholders for recommended data.
    4. Return a summary of everything that was created.
    """
    tpl = _template_registry.get_template(name)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found.")

    platform = await get_platform()
    registry = platform.agent_manager.colonee_registry
    ws_mgr = get_workspace_manager()
    kb_mgr = get_kb_manager()

    # -- 1. Create colonees ---------------------------------------------------
    created_colonees: list = []
    skipped_colonees: list = []

    for col_def in tpl.colonees:
        col_name = col_def["name"]
        if registry.get(col_name):
            skipped_colonees.append(col_name)
            continue
        try:
            defn = ColoneeDefinition(
                name=col_name,
                display_name=col_def["display_name"],
                description=col_def["description"],
                specialist_type=col_def["specialist_type"],
                system_prompt=col_def["system_prompt"],
                capabilities=col_def.get("capabilities", []),
                built_in_tools=col_def.get("built_in_tools", []),
                mcp_servers=col_def.get("mcp_servers", []),
                tags=col_def.get("tags", []),
                created_by="template:" + tpl.name,
            )
            registry.create(defn)
            created_colonees.append(col_name)
        except Exception as e:
            logger.warning("Template apply — failed to create colonee '%s': %s", col_name, e)
            skipped_colonees.append(col_name)

    # Sync capabilities so new colonees are available immediately
    if created_colonees:
        platform.agent_manager._sync_capabilities_from_registry()

    # -- 2. Create workspace --------------------------------------------------
    all_colonee_names = [c["name"] for c in tpl.colonees]
    ws_name = tpl.name
    workspace_created = False

    if not ws_mgr.get(ws_name):
        try:
            ws_cfg = tpl.workspace_config
            ws_def = WorkspaceDefinition(
                name=ws_name,
                display_name=ws_cfg.get("display_name", tpl.display_name),
                description=ws_cfg.get("description", tpl.description),
                colonees=all_colonee_names,
                icon=ws_cfg.get("icon", tpl.icon),
                color=ws_cfg.get("color", tpl.color),
                created_by="template:" + tpl.name,
            )
            ws_mgr.create(ws_def)
            workspace_created = True
        except Exception as e:
            logger.warning("Template apply — failed to create workspace '%s': %s", ws_name, e)

    # -- 3. Create knowledge base placeholders --------------------------------
    created_kbs: list = []

    for idx, kb_desc in enumerate(tpl.recommended_knowledge_bases):
        kb_slug = f"{tpl.name}_kb_{idx + 1}"
        if kb_mgr.get(kb_slug):
            continue
        try:
            kb_def = KnowledgeBaseDefinition(
                name=kb_slug,
                display_name=f"{tpl.display_name} KB {idx + 1}",
                description=kb_desc,
                type="files",
                workspaces=[ws_name],
            )
            kb_mgr.create(kb_def)
            created_kbs.append(kb_slug)
        except Exception as e:
            logger.warning("Template apply — failed to create KB '%s': %s", kb_slug, e)

    # If workspace was created and we have KBs, update its knowledge_bases list
    if workspace_created and created_kbs:
        try:
            ws_mgr.update(ws_name, {"knowledge_bases": created_kbs})
        except Exception:
            pass  # non-critical

    return {
        "status": "applied",
        "template": tpl.name,
        "colonees_created": created_colonees,
        "colonees_skipped": skipped_colonees,
        "workspace_created": workspace_created,
        "workspace_name": ws_name,
        "knowledge_bases_created": created_kbs,
        "mcp_server_suggestions": tpl.mcp_server_suggestions,
    }


# ---------------------------------------------------------------------------
# Connector Schemas
# ---------------------------------------------------------------------------

class ConnectorCreateRequest(BaseModel):
    name: str = Field(..., description="Unique slug for this connector, e.g. 'myapp_api'.")
    display_name: str = Field(..., description="Human-readable name, e.g. 'MyApp API'.")
    description: str = Field(..., description="What this connector provides.")
    type: str = Field(
        ...,
        description="Connector type: 'openapi', 'repo', 'database', 'webhook', 'oauth_service'.",
    )
    provider: str = Field(default="custom", description="Provider slug, e.g. 'github', 'slack', 'custom'.")
    config: Dict[str, Any] = Field(default_factory=dict, description="Type-specific configuration.")
    credentials: Dict[str, str] = Field(default_factory=dict, description="Authentication credentials (stored securely).")
    workspaces: list = Field(default_factory=list, description="Workspace names this connector is scoped to (empty = all).")
    specialist_types: list = Field(default_factory=list, description="Specialist types that receive this connector's tools (empty = all).")


class ConnectorUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, str]] = None
    workspaces: Optional[list] = None
    specialist_types: Optional[list] = None
    enabled: Optional[bool] = None


# ---------------------------------------------------------------------------
# Connector Routes — Catalog (registered BEFORE {name} routes to avoid conflicts)
# ---------------------------------------------------------------------------

@app.get("/connectors/catalog", tags=["Connectors"])
async def list_connector_catalog():
    """
    List all available connector templates from the built-in catalog.

    Each entry describes a pre-configured connector for a popular service
    (Slack, GitHub, Gmail, etc.) with its required config and credential fields.
    """
    catalog = ConnectorCatalog.get_catalog()
    return {"catalog": catalog, "count": len(catalog)}


@app.get("/connectors/catalog/categories", tags=["Connectors"])
async def list_connector_catalog_categories():
    """
    List all connector catalog categories with counts.

    Returns ``[{name, display_name, count}, ...]``.
    """
    categories = ConnectorCatalog.get_categories()
    return {"categories": categories, "count": len(categories)}


@app.post("/connectors/from-catalog/{catalog_id}", tags=["Connectors"], status_code=201)
async def create_connector_from_catalog(catalog_id: str, body: ConnectorCreateRequest):
    """
    Create a connector from a catalog template.

    The catalog entry pre-fills type, provider, and default config values.
    You supply the name, credentials, and any overrides.
    """
    template = ConnectorCatalog.get_by_id(catalog_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Catalog entry '{catalog_id}' not found.")

    try:
        conn_mgr = get_connector_manager()

        # Merge template defaults into config
        merged_config = {}
        for key, schema in template.get("config_schema", {}).items():
            if schema.get("type") == "hidden" and "default" in schema:
                merged_config[key] = schema["default"]
            elif "default" in schema:
                merged_config[key] = schema["default"]
        # User overrides take precedence
        merged_config.update(body.config)

        defn = conn_mgr.create(
            name=body.name,
            display_name=body.display_name or template["display_name"],
            description=body.description or template["description"],
            type=template["type"],
            provider=template["provider"],
            config=merged_config,
            credentials=body.credentials,
            workspaces=body.workspaces,
            specialist_types=body.specialist_types,
        )
        return defn.to_safe_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Create connector from catalog failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Connector Routes — CRUD
# ---------------------------------------------------------------------------

@app.post("/connectors", tags=["Connectors"], status_code=201)
async def create_connector(body: ConnectorCreateRequest):
    """
    Create a new Connector — an authenticated connection to an external service.

    Connectors auto-generate tools for specialist agents. For example, an OpenAPI
    connector parses a Swagger spec and creates a callable tool for each endpoint.
    A repo connector clones a Git repository and provides search/read tools.

    After creating, call ``POST /connectors/{name}/connect`` to activate it.
    """
    try:
        conn_mgr = get_connector_manager()
        defn = conn_mgr.create(
            name=body.name,
            display_name=body.display_name,
            description=body.description,
            type=body.type,
            provider=body.provider,
            config=body.config,
            credentials=body.credentials,
            workspaces=body.workspaces,
            specialist_types=body.specialist_types,
        )
        return defn.to_safe_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Create connector failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/connectors", tags=["Connectors"])
async def list_connectors(type: Optional[str] = None, workspace: Optional[str] = None):
    """
    List all connectors, optionally filtered by type or workspace.

    Credentials are masked in the response.
    """
    try:
        conn_mgr = get_connector_manager()
        connectors = conn_mgr.list(type_filter=type, workspace=workspace)
        return {
            "connectors": [c.to_safe_dict() for c in connectors],
            "count": len(connectors),
        }
    except Exception as e:
        logger.error("List connectors failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/connectors/{name}", tags=["Connectors"])
async def get_connector(name: str):
    """Get a single connector by name. Credentials are masked."""
    try:
        conn_mgr = get_connector_manager()
        defn = conn_mgr.get(name)
        if not defn:
            raise HTTPException(status_code=404, detail=f"Connector '{name}' not found.")
        return defn.to_safe_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/connectors/{name}", tags=["Connectors"])
async def update_connector(name: str, body: ConnectorUpdateRequest):
    """
    Update a connector definition.

    You can update any field except ``name`` and ``created_at``.
    If credentials are updated, you may need to reconnect via
    ``POST /connectors/{name}/connect``.
    """
    try:
        conn_mgr = get_connector_manager()
        updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
        updated = conn_mgr.update(name, **updates)
        return updated.to_safe_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Update connector failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/connectors/{name}", tags=["Connectors"])
async def delete_connector(name: str):
    """Delete a connector by name."""
    try:
        conn_mgr = get_connector_manager()
        conn_mgr.delete(name)
        return {"status": "deleted", "name": name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Connector Routes — Actions
# ---------------------------------------------------------------------------

@app.post("/connectors/{name}/connect", tags=["Connectors"])
async def connect_connector(name: str):
    """
    Activate a connector — parse its spec, clone its repo, or establish its connection.

    This is the key action endpoint. Depending on the connector type:
    - **openapi**: Fetches and parses the OpenAPI/Swagger spec, generates tool names.
    - **repo**: Clones (or pulls) the git repository, indexes files, generates tool names.
    - **other types**: Marks the connector as connected (tools added in future updates).

    On success, updates the connector's status to "connected" and populates
    ``tools_generated`` and ``sync_stats``.
    """
    try:
        conn_mgr = get_connector_manager()
        defn = conn_mgr.get(name)
        if not defn:
            raise HTTPException(status_code=404, detail=f"Connector '{name}' not found.")

        conn_mgr.update_status(name, "syncing", message="Connecting...")

        if defn.type == "openapi":
            return await _connect_openapi(conn_mgr, defn)
        elif defn.type == "repo":
            return await _connect_repo(conn_mgr, defn)
        else:
            # Generic: just mark as connected
            conn_mgr.update_status(name, "connected", message=f"{defn.type} connector activated")
            updated = conn_mgr.get(name)
            return updated.to_safe_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Connect connector '%s' failed: %s", name, e)
        try:
            get_connector_manager().update_status(name, "error", message=str(e))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


async def _connect_openapi(conn_mgr: ConnectorManager, defn):
    """Parse OpenAPI spec and register tool names."""
    spec_url = defn.config.get("spec_url")
    base_url = defn.config.get("base_url")
    auth_type = defn.config.get("auth_type", "none")
    auth_header_name = defn.config.get("auth_header_name", "Authorization")
    auth_value = defn.credentials.get("api_key_or_token", "")

    if auth_type == "none":
        auth_type = None

    if not spec_url and not base_url:
        conn_mgr.update_status(defn.name, "error", message="No spec_url or base_url in config")
        raise HTTPException(status_code=400, detail="OpenAPI connector requires spec_url in config.")

    try:
        connector = OpenAPIConnector(
            spec_url_or_dict=spec_url,
            base_url=base_url,
            auth_type=auth_type,
            auth_value=auth_value,
            auth_header_name=auth_header_name,
        )
        tool_names = connector.get_tool_names()
        spec_info = connector.get_spec_info()

        conn_mgr.update_status(
            defn.name,
            status="connected",
            message=f"Parsed {spec_info['endpoints']} endpoints from {spec_info['title']}",
            tools=tool_names,
            sync_stats={
                "endpoints_found": spec_info["endpoints"],
                "methods_mapped": len(tool_names),
                "api_title": spec_info["title"],
                "api_version": spec_info["version"],
            },
        )
        updated = conn_mgr.get(defn.name)
        return updated.to_safe_dict()

    except Exception as e:
        conn_mgr.update_status(defn.name, "error", message=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse OpenAPI spec: {e}")


async def _connect_repo(conn_mgr: ConnectorManager, defn):
    """Clone/pull repo and index files."""
    repo_url = defn.config.get("repo_url")
    if not repo_url:
        conn_mgr.update_status(defn.name, "error", message="No repo_url in config")
        raise HTTPException(status_code=400, detail="Repo connector requires repo_url in config.")

    branch = defn.config.get("branch", "main")
    access_token = defn.credentials.get("access_token", "")
    include_patterns = defn.config.get("include_patterns", [])
    exclude_patterns = defn.config.get("exclude_patterns", [])
    data_dir = conn_mgr.get_connector_data_dir(defn.name)

    try:
        connector = RepoConnector(
            repo_url=repo_url,
            data_dir=data_dir,
            branch=branch,
            access_token=access_token or None,
            include_patterns=include_patterns or None,
            exclude_patterns=exclude_patterns or None,
        )
        sync_stats = connector.clone_or_pull()
        tool_names = ["search_codebase", "read_repo_file", "list_repo_files", "get_repo_structure"]

        conn_mgr.update_status(
            defn.name,
            status="connected",
            message=f"Indexed {sync_stats['files_indexed']} files",
            tools=tool_names,
            sync_stats=sync_stats,
        )
        updated = conn_mgr.get(defn.name)
        return updated.to_safe_dict()

    except Exception as e:
        conn_mgr.update_status(defn.name, "error", message=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to connect repo: {e}")


@app.post("/connectors/{name}/sync", tags=["Connectors"])
async def sync_connector(name: str):
    """
    Re-sync a connector — re-fetch the OpenAPI spec or re-pull the git repository.

    This is equivalent to ``/connect`` but semantically indicates a refresh
    of an already-connected connector.
    """
    return await connect_connector(name)


@app.get("/connectors/{name}/tools", tags=["Connectors"])
async def list_connector_tools(name: str):
    """
    List the auto-generated tool names for a connected connector.

    Tools are generated when the connector is activated via ``/connect``.
    """
    try:
        conn_mgr = get_connector_manager()
        defn = conn_mgr.get(name)
        if not defn:
            raise HTTPException(status_code=404, detail=f"Connector '{name}' not found.")
        return {
            "connector": name,
            "status": defn.status,
            "tools": defn.tools_generated,
            "count": len(defn.tools_generated),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
