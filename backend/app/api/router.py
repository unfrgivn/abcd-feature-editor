"""Application Router that registers all the application endpoints"""

from fastapi import APIRouter
from api.endpoints import ai_editor_agent_routes

api_router = APIRouter()
api_router.include_router(ai_editor_agent_routes.router, tags=["ai_editor_agent_routes"])
