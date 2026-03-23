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


class InvokeResponse(BaseModel):
    status: str
    result: Any


class AgentRequest(BaseModel):
    agent_type: str = Field(..., description="Type of specialist agent to invoke directly.")
    task: str = Field(..., description="Task description for the agent.")
    context: Dict[str, Any] = Field(default_factory=dict)


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
            context={"user_id": body.user_id, **body.context},
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
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
