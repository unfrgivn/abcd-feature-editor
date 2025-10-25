import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from models.edit_models import Edit, EditQueue
from services.video_pipeline_service import video_pipeline_service
from multi_tool_agent.session_data import get_edit_queue, save_edit_queue, initialize_edit_queue

logger = logging.getLogger(__name__)


def add_voiceover_edit(tool_context, text: str, start_ms: int, original_video_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a voiceover edit to the queue and regenerate the video.
    
    Args:
        tool_context: Agent tool context containing state
        text: The text to convert to speech
        start_ms: Start time in milliseconds
        original_video_url: URL of the original video (optional, will use from state if not provided)
    
    Returns:
        Dictionary with status, message, and video_url
    """
    try:
        if not original_video_url:
            original_video_url = tool_context.state.get("edited_video_url") or tool_context.state.get("video_url")
        
        if not original_video_url:
            return {
                "status": "error",
                "message": "No video URL found in context or parameters"
            }
        
        edit_queue = get_edit_queue()
        if not edit_queue:
            edit_queue = initialize_edit_queue(original_video_url)
        
        edit = Edit(
            id=str(uuid.uuid4()),
            type="voiceover",
            params={
                "text": text,
                "start_ms": start_ms
            },
            timestamp=datetime.now().isoformat(),
            status="applied"
        )
        
        edit_queue.add_edit(edit)
        
        result_video_url = video_pipeline_service.apply_edit_queue(edit_queue)
        
        save_edit_queue(edit_queue)
        
        tool_context.state["edited_video_url"] = result_video_url
        logger.info(f"Set edited_video_url in tool_context.state: {result_video_url}")
        
        return {
            "status": "success",
            "message": f"Added voiceover at {start_ms}ms",
            "video_url": result_video_url,
            "edit_id": edit.id
        }
    except Exception as e:
        logger.error(f"Error adding voiceover edit: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def update_voiceover_timing(tool_context, edit_id: str, new_start_ms: int) -> Dict[str, Any]:
    """
    Update the timing of an existing voiceover edit and regenerate the video.
    
    Args:
        tool_context: Agent tool context containing state
        edit_id: ID of the edit to update
        new_start_ms: New start time in milliseconds
    
    Returns:
        Dictionary with status, message, and video_url
    """
    try:
        edit_queue = get_edit_queue()
        if not edit_queue:
            return {
                "status": "error",
                "message": "No edit queue found"
            }
        
        success = edit_queue.update_edit(edit_id, {"start_ms": new_start_ms})
        if not success:
            return {
                "status": "error",
                "message": f"Edit {edit_id} not found"
            }
        
        result_video_url = video_pipeline_service.apply_edit_queue(edit_queue)
        
        save_edit_queue(edit_queue)
        
        tool_context.state["edited_video_url"] = result_video_url
        logger.info(f"Set edited_video_url in tool_context.state: {result_video_url}")
        
        return {
            "status": "success",
            "message": f"Updated voiceover timing to {new_start_ms}ms",
            "video_url": result_video_url
        }
    except Exception as e:
        logger.error(f"Error updating voiceover timing: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def add_text_overlay_edit(
    tool_context,
    text: str,
    start_ms: int,
    end_ms: int,
    original_video_url: Optional[str] = None,
    fontsize: int = 70,
    color: str = "white",
    position: str = "center"
) -> Dict[str, Any]:
    """
    Add a text overlay edit to the queue and regenerate the video.
    
    Args:
        tool_context: Agent tool context containing state
        text: Text to display
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        original_video_url: URL of the original video (optional, will use from state if not provided)
        fontsize: Font size (default 70)
        color: Text color (default "white")
        position: Text position (default "center")
    
    Returns:
        Dictionary with status, message, and video_url
    """
    try:
        if not original_video_url:
            original_video_url = tool_context.state.get("edited_video_url") or tool_context.state.get("video_url")
        
        if not original_video_url:
            return {
                "status": "error",
                "message": "No video URL found in context or parameters"
            }
        
        edit_queue = get_edit_queue()
        if not edit_queue:
            edit_queue = initialize_edit_queue(original_video_url)
        
        edit = Edit(
            id=str(uuid.uuid4()),
            type="text_overlay",
            params={
                "text": text,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "fontsize": fontsize,
                "color": color,
                "position": position
            },
            timestamp=datetime.now().isoformat(),
            status="applied"
        )
        
        edit_queue.add_edit(edit)
        
        result_video_url = video_pipeline_service.apply_edit_queue(edit_queue)
        
        save_edit_queue(edit_queue)
        
        tool_context.state["edited_video_url"] = result_video_url
        logger.info(f"Set edited_video_url in tool_context.state: {result_video_url}")
        
        return {
            "status": "success",
            "message": f"Added text overlay '{text}' from {start_ms}ms to {end_ms}ms",
            "video_url": result_video_url,
            "edit_id": edit.id
        }
    except Exception as e:
        logger.error(f"Error adding text overlay edit: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def remove_edit(tool_context, edit_id: str) -> Dict[str, Any]:
    """
    Remove an edit from the queue and regenerate the video.
    
    Args:
        tool_context: Agent tool context containing state
        edit_id: ID of the edit to remove
    
    Returns:
        Dictionary with status, message, and video_url
    """
    try:
        edit_queue = get_edit_queue()
        if not edit_queue:
            return {
                "status": "error",
                "message": "No edit queue found"
            }
        
        success = edit_queue.remove_edit(edit_id)
        if not success:
            return {
                "status": "error",
                "message": f"Edit {edit_id} not found"
            }
        
        edit_queue.current_video_url = edit_queue.original_video_url
        for edit in edit_queue.edits:
            edit.result_video_url = None
        
        result_video_url = video_pipeline_service.apply_edit_queue(edit_queue)
        
        save_edit_queue(edit_queue)
        
        tool_context.state["edited_video_url"] = result_video_url
        logger.info(f"Set edited_video_url in tool_context.state: {result_video_url}")
        
        return {
            "status": "success",
            "message": "Edit removed successfully",
            "video_url": result_video_url
        }
    except Exception as e:
        logger.error(f"Error removing edit: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def get_edit_queue_info() -> Dict[str, Any]:
    """
    Get information about the current edit queue.
    
    Returns:
        Dictionary with status and edit queue data
    """
    try:
        edit_queue = get_edit_queue()
        if not edit_queue:
            return {
                "status": "success",
                "message": "No edit queue found",
                "edit_queue": None
            }
        
        return {
            "status": "success",
            "edit_queue": edit_queue.to_dict()
        }
    except Exception as e:
        logger.error(f"Error getting edit queue: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def find_voiceover_edit() -> Dict[str, Any]:
    """
    Find the most recent voiceover edit in the queue.
    
    Returns:
        Dictionary with status and edit data
    """
    try:
        edit_queue = get_edit_queue()
        if not edit_queue:
            return {
                "status": "success",
                "message": "No edit queue found",
                "edit": None
            }
        
        edit = edit_queue.find_edit_by_type("voiceover")
        if not edit:
            return {
                "status": "success",
                "message": "No voiceover edit found",
                "edit": None
            }
        
        return {
            "status": "success",
            "edit": edit.to_dict()
        }
    except Exception as e:
        logger.error(f"Error finding voiceover edit: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
