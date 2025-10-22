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


@router.post("/call_ai_editor_agent")
async def call_ai_editor_agent(userQuery: UserQuery) -> Response:
    """Call AI Editor agent to edit videos"""
    try:

        print("Calling agent...")
        response = agent.call_agent(userQuery.query)

        return response
    except Exception as ex:
        logging.error("AI Editor Agent - ERROR:  %s", str(ex))

        return Response(
            content=f"ERROR: {ex}. Please try again.",
            status_code=500,
        )
