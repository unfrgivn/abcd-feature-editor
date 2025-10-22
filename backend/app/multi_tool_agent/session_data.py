from typing import Dict, Any

# These will be set when the module is imported
APP_NAME = None
USER_ID = None
SESSION_ID = None
session_service = None


def initialize_session_data(app_name: str, user_id: str, session_id: str, service):
    """Initialize the session data module with required parameters."""
    global APP_NAME, USER_ID, SESSION_ID, session_service
    APP_NAME = app_name
    USER_ID = user_id
    SESSION_ID = session_id
    session_service = service


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