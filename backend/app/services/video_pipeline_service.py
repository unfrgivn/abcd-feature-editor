import logging
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.edit_models import Edit, EditQueue
from services.video_editing_service import video_editing_service
from services.text_to_speech_service import text_to_speech_service

logger = logging.getLogger(__name__)


class VideoPipelineService:
    
    def apply_edit_queue(self, edit_queue: EditQueue) -> str:
        applied_edits = edit_queue.get_applied_edits()
        
        has_overwritten_edits = any(e.status == "overwritten" for e in edit_queue.edits)
        needs_rebuild = any(e.result_video_url is None for e in applied_edits)
        
        if has_overwritten_edits or needs_rebuild:
            logger.info(f"Full rebuild required (overwritten={has_overwritten_edits}, needs_rebuild={needs_rebuild})")
            
            for edit in edit_queue.edits:
                edit.result_video_url = None
            
            current_video_url = edit_queue.original_video_url
            
            logger.info(f"Rebuilding video from original with {len(applied_edits)} applied edits")
            for edit in applied_edits:
                try:
                    current_video_url = self.apply_single_edit(current_video_url, edit, edit_queue.video_id)
                    edit.result_video_url = current_video_url
                    logger.info(f"Applied edit {edit.id} ({edit.type})")
                except Exception as e:
                    logger.error(f"Error applying edit {edit.id}: {e}")
                    raise
            
            edit_queue.current_video_url = current_video_url
        else:
            logger.info(f"No changes needed, returning current video")
            current_video_url = edit_queue.current_video_url
        
        return current_video_url
    
    def apply_single_edit(self, video_url: str, edit: Edit, video_id: Optional[str] = None) -> str:
        if edit.type == "voiceover":
            return self._apply_voiceover(video_url, edit)
        elif edit.type == "text_overlay":
            return self._apply_text_overlay(video_url, edit, video_id)
        elif edit.type == "trim":
            return self._apply_trim(video_url, edit)
        elif edit.type == "filter":
            return self._apply_filter(video_url, edit)
        else:
            raise ValueError(f"Unknown edit type: {edit.type}")
    
    def _apply_voiceover(self, video_url: str, edit: Edit) -> str:
        text = edit.params.get("text", "")
        start_ms = edit.params.get("start_ms", 0)
        audio_path = edit.params.get("audio_path")
        
        if not audio_path:
            logger.info(f"Generating speech for voiceover edit {edit.id}")
            tts_result = text_to_speech_service.generate_speech(text)
            if tts_result["status"] != "success":
                raise Exception(f"Failed to generate speech: {tts_result.get('message')}")
            audio_path = tts_result["local_path"]
            edit.params["audio_path"] = audio_path
        
        start_seconds = start_ms / 1000.0
        result = video_editing_service.add_audio_overlay(
            video_url=video_url,
            audio_path=audio_path,
            start_offset=int(start_seconds),
            volume_overlay=1.0,
            volume_original=0.3
        )
        
        if result["status"] != "success":
            raise Exception(f"Failed to add voiceover: {result.get('message')}")
        
        return result["video_url"]
    
    def _apply_text_overlay(self, video_url: str, edit: Edit, video_id: Optional[str] = None) -> str:
        text = edit.params.get("text", "")
        start_ms = edit.params.get("start_ms", 0)
        end_ms = edit.params.get("end_ms", 3000)
        fontsize = edit.params.get("fontsize", 70)
        color = edit.params.get("color", "white")
        position = edit.params.get("position", "center")
        
        start_seconds = start_ms / 1000.0
        duration_seconds = (end_ms - start_ms) / 1000.0
        
        result = video_editing_service.add_text_overlay(
            video_url=video_url,
            text=text,
            start_time=int(start_seconds),
            duration=int(duration_seconds),
            fontsize=fontsize,
            color=color,
            position=position,
            video_id=video_id
        )
        
        if result["status"] != "success":
            raise Exception(f"Failed to add text overlay: {result.get('message')}")
        
        return result["video_url"]
    
    def _apply_trim(self, video_url: str, edit: Edit) -> str:
        logger.warning("Trim edit not yet implemented")
        return video_url
    
    def _apply_filter(self, video_url: str, edit: Edit) -> str:
        logger.warning("Filter edit not yet implemented")
        return video_url


video_pipeline_service = VideoPipelineService()
