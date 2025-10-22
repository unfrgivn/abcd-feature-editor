"""Endpoints handled by the FastAPI Router"""

import logging
from fastapi import APIRouter
from fastapi.responses import Response
from multi_tool_agent import agent
from models.request_models import UserQuery

router = APIRouter()


@router.get("/test")
def healthcheck():
    """AI Video Editor healthcheck"""
    return {"status": "Success!"}

@router.get("/config.json")
def get_config():
    """Get config.json contents"""
    import json
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    with open(config_path, "r") as f:
        config_data = json.load(f)
    return config_data

@router.post("/call_ai_editor_agent")
async def call_ai_editor_agent(userQuery: UserQuery):
    """Call AI Editor agent to edit videos"""
    try:

        print("Calling agent...")
        response = agent.call_agent(userQuery.query, userQuery.feature_id)

        return Response(content=response or "", status_code=200)
    except Exception as ex:
        logging.error("AI Editor Agent - ERROR:  %s", str(ex))

        return Response(
            content=f"ERROR: {ex}. Please try again.",
            status_code=500,
        )
