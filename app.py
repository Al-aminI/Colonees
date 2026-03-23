"""
Colonees Platform — Main Application Entrypoint
Production-grade autonomous agent swarm platform.
"The Kubernetes + OS for AI Agents"
"""

import asyncio
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from galos.core.platform import ColoneesPlatform
from galos.core.config import CologeesConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global platform instance
platform: ColoneesPlatform = None


async def initialize_platform():
    """Initialize Colonees platform on first request"""
    global platform
    if platform is None:
        logger.info("Initializing Colonees Platform...")
        config = CologeesConfig.from_environment()
        platform = ColoneesPlatform(config)
        await platform.initialize()
        logger.info("Colonees Platform initialized successfully")
    return platform


def _serialize_for_json(obj: Any) -> Any:
    """Recursively serialize objects to JSON-compatible types"""
    from datetime import datetime, date

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return _serialize_for_json(obj.__dict__)
    else:
        try:
            return str(obj)
        except Exception:
            return None


async def handle_request(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Main request handler for the Colonees platform.
    Accepts any goal and orchestrates the agent swarm to accomplish it.
    """
    try:
        p = await initialize_platform()

        user_goal = event.get('goal') or event.get('prompt') or event.get('message', '')
        user_id = event.get('user_id', 'anonymous')
        session_context = event.get('context', {})

        if not user_goal:
            return {
                'statusCode': 400,
                'body': {'error': 'Missing required field: goal, prompt, or message'}
            }

        result = await p.handle_request(
            user_goal=user_goal,
            context={
                'user_id': user_id,
                **session_context
            }
        )

        serialized_result = _serialize_for_json(result)

        return {
            'statusCode': 200,
            'body': serialized_result
        }

    except Exception as e:
        logger.error(f"Request handler error: {e}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }


if __name__ == "__main__":
    # Local development server
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    app = FastAPI(
        title="Colonees",
        description="The Kubernetes + OS for AI Agents — Open-source autonomous agent swarm platform",
        version="1.0.0"
    )

    @app.post("/invoke")
    async def invoke(request: Request):
        event = await request.json()
        result = await handle_request(event)
        return JSONResponse(content=result)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "platform": "Colonees"}

    @app.get("/status")
    async def status():
        p = await initialize_platform()
        platform_status = await p.get_platform_status()
        return JSONResponse(content=_serialize_for_json(platform_status))

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
