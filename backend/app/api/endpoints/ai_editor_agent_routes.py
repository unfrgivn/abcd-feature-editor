"""Endpoints handled by the FastAPI Router"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Query, Body
from fastapi.responses import Response
from multi_tool_agent import agent
from multi_tool_agent.cleanup import cleanup_all
from models.request_models import UserQuery
from services.database_session_service import database_session_service
from services.video_export_service import get_video_export_service

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
        import json

        print(f"Calling agent with query: {userQuery.query}")
        
        agent_user_id = None
        agent_session_id = None
        
        if userQuery.user_id and userQuery.session_id:
            from multi_tool_agent.session_data import set_frontend_session_info
            set_frontend_session_info(userQuery.user_id, userQuery.session_id, database_session_service)
            
            agent_user_id = userQuery.user_id
            agent_session_id = userQuery.session_id
            print(f"DEBUG: Using frontend session as agent session: {agent_user_id}/{agent_session_id}")
        
        response = agent.call_agent(userQuery.query, userQuery.feature_id, agent_user_id, agent_session_id)
        print(f"Agent returned response type: {type(response)}, value: {repr(response)}")
        
        if not response:
            logging.warning("Agent returned empty or None response")
            return Response(
                content=json.dumps({"text": "I apologize, but I encountered an issue processing your request. Could you please try rephrasing or providing more details?", "media": {}}),
                media_type="application/json",
                status_code=200
            )
        
        try:
            json_data = json.loads(response)
            return Response(content=response, media_type="application/json", status_code=200)
        except (json.JSONDecodeError, TypeError):
            return Response(content=response, status_code=200)
            
    except Exception as ex:
        logging.error("AI Editor Agent - ERROR:  %s", str(ex))
        import traceback
        traceback.print_exc()

        return Response(
            content=f"ERROR: {ex}. Please try again.",
            status_code=500,
        )


@router.post("/cleanup")
async def cleanup_session():
    """Clear session state and delete temporary files"""
    try:
        result = cleanup_all(
            session_service=agent.session_service,
            app_name=agent.APP_NAME,
            user_id=agent.USER_ID,
            session_id=agent.SESSION_ID
        )
        
        import json
        return Response(content=json.dumps(result), status_code=200)
    except Exception as ex:
        logging.error("Cleanup - ERROR: %s", str(ex))
        
        return Response(
            content=f"ERROR: {ex}. Please try again.",
            status_code=500,
        )


@router.post("/sessions/create")
async def create_session(
    user_id: str = Query(...),
    session_id: str = Query(...),
    video_id: Optional[str] = Query(None),
    video_url: Optional[str] = Query(None),
    feature_id: Optional[str] = Query(None)
):
    """Create a new editing session"""
    try:
        app_name = os.getenv("APP_NAME", "wpromote-codesprint-2025")
        session_pk = database_session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            video_id=video_id,
            video_url=video_url,
            feature_id=feature_id
        )
        
        import json
        return Response(
            content=json.dumps({"session_pk": session_pk, "message": "Session created"}),
            status_code=200
        )
    except Exception as ex:
        logging.error("Create session - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.get("/sessions/list")
async def list_sessions(
    user_id: str = Query(...),
    video_id: Optional[str] = Query(None),
    feature_id: Optional[str] = Query(None)
):
    """List all sessions for a user"""
    try:
        sessions = database_session_service.list_sessions(
            user_id=user_id,
            video_id=video_id,
            feature_id=feature_id
        )
        
        import json
        return Response(content=json.dumps(sessions), status_code=200)
    except Exception as ex:
        logging.error("List sessions - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.get("/sessions/get")
async def get_session(
    user_id: str = Query(...),
    session_id: str = Query(...)
):
    """Get a specific session with state"""
    try:
        app_name = os.getenv("APP_NAME", "wpromote-codesprint-2025")
        session = database_session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            return Response(content="Session not found", status_code=404)
        
        import json
        return Response(content=json.dumps(session), status_code=200)
    except Exception as ex:
        logging.error("Get session - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.get("/sessions/versions")
async def get_session_versions(
    session_pk: int = Query(...)
):
    """Get version history for a session"""
    try:
        versions = database_session_service.get_versions(session_pk)
        
        import json
        return Response(content=json.dumps(versions), status_code=200)
    except Exception as ex:
        logging.error("Get versions - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.post("/sessions/version")
async def create_session_version(
    session_pk: int = Query(...),
    video_url: Optional[str] = Query(None)
):
    """Create a new version snapshot for a session"""
    try:
        version_id = database_session_service.create_version(
            session_pk=session_pk,
            video_url=video_url
        )
        
        import json
        return Response(
            content=json.dumps({"version_id": version_id, "message": "Version created"}),
            status_code=200
        )
    except Exception as ex:
        logging.error("Create version - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.put("/sessions/update")
async def update_session(
    user_id: str = Query(...),
    session_id: str = Query(...),
    state: dict = Body(...)
):
    """Update session state"""
    try:
        app_name = os.getenv("APP_NAME", "wpromote-codesprint-2025")
        session = database_session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            return Response(content="Session not found", status_code=404)
        
        for key, value in state.items():
            database_session_service.set_state(session["pk"], key, value)
        
        return Response(content="Session updated", status_code=200)
    except Exception as ex:
        logging.error("Update session - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.put("/sessions/rename")
async def rename_session(
    user_id: str = Query(...),
    session_id: str = Query(...),
    new_name: str = Query(...)
):
    """Rename a session by updating its feature_id"""
    try:
        app_name = os.getenv("APP_NAME", "wpromote-codesprint-2025")
        session = database_session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            return Response(content="Session not found", status_code=404)
        
        database_session_service.set_state(session["pk"], "feature_id", new_name)
        
        return Response(content="Session renamed", status_code=200)
    except Exception as ex:
        logging.error("Rename session - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.delete("/sessions/delete")
async def delete_session(
    user_id: str = Query(...),
    session_id: str = Query(...)
):
    """Delete a session"""
    try:
        app_name = os.getenv("APP_NAME", "wpromote-codesprint-2025")
        database_session_service.delete_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        return Response(content="Session deleted", status_code=200)
    except Exception as ex:
        logging.error("Delete session - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.delete("/sessions/delete-all")
async def delete_all_sessions(
    user_id: str = Query(...)
):
    """Delete all sessions for a user"""
    try:
        deleted_count = database_session_service.delete_all_sessions(user_id=user_id)
        
        import json
        return Response(
            content=json.dumps({"deleted_count": deleted_count, "message": f"Deleted {deleted_count} sessions"}),
            status_code=200
        )
    except Exception as ex:
        logging.error("Delete all sessions - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.get("/sessions/edit-queue")
async def get_edit_queue(
    user_id: str = Query(...),
    session_id: str = Query(...)
):
    """Get the edit queue for a session"""
    try:
        app_name = os.getenv("APP_NAME", "wpromote-codesprint-2025")
        session = database_session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            return Response(content="Session not found", status_code=404)
        
        edit_queue_data = database_session_service.get_state(session["pk"], "edit_queue")
        
        import json
        if edit_queue_data:
            print(f"DEBUG ai_editor_agent_routes.py: Retrieved edit queue with {len(edit_queue_data.get('edits', []))} edits")
            for e in edit_queue_data.get('edits', []):
                print(f"  Edit {e['id']}: type={e['type']}, status={e['status']}")
            return Response(content=json.dumps(edit_queue_data), status_code=200)
        else:
            print(f"DEBUG ai_editor_agent_routes.py: No edit queue found for session")
            return Response(content=json.dumps(None), status_code=200)
    except Exception as ex:
        logging.error("Get edit queue - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)


@router.post("/export")
async def export_video(
    video_path: str = Query(...),
    user_id: str = Query(...),
    feature_id: str = Query(...),
    video_id: str = Query(...)
):
    """Export final video to GCS"""
    try:
        export_service = get_video_export_service()
        public_url = export_service.export_video(
            video_path=video_path,
            user_id=user_id,
            feature_id=feature_id,
            video_id=video_id
        )
        
        import json
        return Response(
            content=json.dumps({"public_url": public_url, "message": "Video exported"}),
            status_code=200
        )
    except Exception as ex:
        logging.error("Export video - ERROR: %s", str(ex))
        return Response(content=f"ERROR: {ex}", status_code=500)
