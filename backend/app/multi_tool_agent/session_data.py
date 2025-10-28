import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, Optional
from models.edit_models import EditQueue

APP_NAME = None
USER_ID = None
SESSION_ID = None
session_service = None

FRONTEND_USER_ID = None
FRONTEND_SESSION_ID = None
frontend_session_service = None


def initialize_session_data(app_name: str, user_id: str, session_id: str, service):
    """Initialize the session data module with required parameters."""
    global APP_NAME, USER_ID, SESSION_ID, session_service
    APP_NAME = app_name
    USER_ID = user_id
    SESSION_ID = session_id
    session_service = service


def set_frontend_session_info(user_id: str, session_id: str, db_session_service):
    """Set frontend session info to use database session service for edit queue."""
    global FRONTEND_USER_ID, FRONTEND_SESSION_ID, frontend_session_service
    
    session_changed = (FRONTEND_USER_ID != user_id or FRONTEND_SESSION_ID != session_id)
    
    FRONTEND_USER_ID = user_id
    FRONTEND_SESSION_ID = session_id
    frontend_session_service = db_session_service
    print(f"DEBUG session_data.py: Set frontend session info - user_id={user_id}, session_id={session_id}, session_changed={session_changed}")


def _get_active_session_info():
    """Get the active session info (frontend if set, otherwise default)."""
    if FRONTEND_USER_ID and FRONTEND_SESSION_ID and frontend_session_service:
        return FRONTEND_USER_ID, FRONTEND_SESSION_ID, frontend_session_service, True
    return USER_ID, SESSION_ID, session_service, False


def set_session_data(key: str, data: Dict[str, Any]) -> Dict[str, str]:
    session = session_service.get_session_sync(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=SESSION_ID
    )
    session.state[key] = data


def get_session_data(key: str) -> Dict[str, Any]:
    """
    Retrieve a JSON object from the session state.
    
    Args:
        key: The key to retrieve data for
        
    Returns:
        Dictionary with status and data or error message
    """
    session = session_service.get_session_sync(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=SESSION_ID
    )
    
    if session and key in session.state:
        return session.state[key]
    return ''


def clear_session_state() -> Dict[str, str]:
    """
    Clear all session state data.
    
    Returns:
        Dictionary with status message
    """
    session = session_service.get_session_sync(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=SESSION_ID
    )
    
    if session:
        session.state.clear()
        return {"status": "success", "message": "Session state cleared"}
    
    return {"status": "error", "message": "Session not found"}


def get_edit_queue() -> Optional[EditQueue]:
    """Get the edit queue for the current session."""
    user_id, session_id, service, is_frontend = _get_active_session_info()
    
    if is_frontend:
        session = service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        if session:
            queue_data = service.get_state(session["pk"], "edit_queue")
            if queue_data:
                print(f"DEBUG session_data.py: Loaded edit queue from database for {user_id}/{session_id}")
                return EditQueue.from_dict(queue_data)
        print(f"DEBUG session_data.py: No edit queue found in database for {user_id}/{session_id}")
        return None
    
    queue_data = get_session_data("edit_queue")
    if queue_data:
        return EditQueue.from_dict(queue_data)
    return None


def save_edit_queue(edit_queue: EditQueue) -> None:
    """Save the edit queue to the session state."""
    user_id, session_id, service, is_frontend = _get_active_session_info()
    
    queue_dict = edit_queue.to_dict()
    print(f"DEBUG session_data.py: Saving edit queue with {len(queue_dict.get('edits', []))} edits")
    for e in queue_dict.get('edits', []):
        print(f"  Edit {e['id']}: type={e['type']}, status={e['status']}")
    
    if is_frontend:
        session = service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        if session:
            service.set_state(session["pk"], "edit_queue", queue_dict)
            print(f"DEBUG session_data.py: Saved edit queue to database for {user_id}/{session_id}")
        return
    
    set_session_data("edit_queue", queue_dict)


def initialize_edit_queue(original_video_url: str, video_id: Optional[str] = None) -> EditQueue:
    """Initialize a new edit queue for the session."""
    user_id, session_id, service, is_frontend = _get_active_session_info()
    
    edit_queue = EditQueue(
        session_id=session_id,
        original_video_url=original_video_url,
        edits=[],
        current_video_url=original_video_url,
        video_id=video_id
    )
    
    if is_frontend:
        session = service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        if session:
            service.set_state(session["pk"], "edit_queue", edit_queue.to_dict())
            print(f"DEBUG session_data.py: Initialized edit queue in database for {user_id}/{session_id}")
    else:
        save_edit_queue(edit_queue)
    
    return edit_queue