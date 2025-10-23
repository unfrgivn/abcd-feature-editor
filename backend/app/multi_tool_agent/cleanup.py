import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def clear_session_state(session_service, app_name: str, user_id: str, session_id: str) -> dict[str, str]:
    """
    Clear all session state data.
    
    Returns:
        Dictionary with status message
    """
    try:
        session = session_service.get_session_sync(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        
        if session:
            session.state.clear()
            logger.info("Session state cleared successfully")
            return {"status": "success", "message": "Session state cleared"}
        
        return {"status": "error", "message": "Session not found"}
    except Exception as e:
        logger.error(f"Error clearing session state: {e}")
        return {"status": "error", "message": str(e)}


def delete_temp_video_files() -> dict[str, Any]:
    """
    Delete all temporary video files from video_edits directory.
    
    Returns:
        Dictionary with status and count of deleted files
    """
    try:
        video_edits_path = Path(__file__).parent.parent / "video_edits"
        
        if not video_edits_path.exists():
            return {"status": "success", "message": "No video_edits directory found", "files_deleted": 0}
        
        deleted_count = 0
        
        for pattern in ["**/*.mp4", "**/*.mp3", "**/*.m4a"]:
            for file_path in video_edits_path.glob(pattern):
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted temp file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
        
        logger.info(f"Deleted {deleted_count} temporary video/audio files")
        return {"status": "success", "message": f"Deleted {deleted_count} files", "files_deleted": deleted_count}
    
    except Exception as e:
        logger.error(f"Error deleting temp video files: {e}")
        return {"status": "error", "message": str(e), "files_deleted": 0}


def delete_temp_system_files() -> dict[str, Any]:
    """
    Delete temporary video files from /tmp directory.
    
    Returns:
        Dictionary with status and count of deleted files
    """
    try:
        tmp_dir = Path("/tmp")
        deleted_count = 0
        
        for pattern in ["tmp*.mp4", "*.mp4"]:
            for file_path in tmp_dir.glob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted system temp file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {e}")
        
        logger.info(f"Deleted {deleted_count} system temporary files")
        return {"status": "success", "message": f"Deleted {deleted_count} files", "files_deleted": deleted_count}
    
    except Exception as e:
        logger.error(f"Error deleting system temp files: {e}")
        return {"status": "error", "message": str(e), "files_deleted": 0}


def cleanup_all(session_service, app_name: str, user_id: str, session_id: str) -> dict[str, Any]:
    """
    Clear all session state and delete all temporary files.
    
    Returns:
        Dictionary with results from all cleanup operations
    """
    results = {
        "session_state": clear_session_state(session_service, app_name, user_id, session_id),
        "video_edits_files": delete_temp_video_files(),
        "system_temp_files": delete_temp_system_files()
    }
    
    total_files_deleted = int(
        results["video_edits_files"].get("files_deleted", 0) + 
        results["system_temp_files"].get("files_deleted", 0)
    )
    
    logger.info(f"Cleanup completed. Total files deleted: {total_files_deleted}")
    
    return {
        "status": "success",
        "message": f"Cleanup completed. {total_files_deleted} files deleted.",
        "details": results
    }
