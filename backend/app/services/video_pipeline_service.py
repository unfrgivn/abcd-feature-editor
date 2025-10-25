import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.edit_models import Edit, EditQueue
from services.video_editing_service import video_editing_service
from services.text_to_speech_service import text_to_speech_service

logger = logging.getLogger(__name__)


class VideoPipelineService:
    
    def apply_edit_queue(self, edit_queue: EditQueue) -> str:
        current_video_url = edit_queue.current_video_url
        
        applied_edits = edit_queue.get_applied_edits()
        new_edits = [e for e in applied_edits if not e.result_video_url]
        
        if new_edits:
            logger.info(f"Applying {len(new_edits)} new edits to video (starting from current version)")
        else:
            logger.info(f"No new edits to apply")
            return current_video_url
        
        for edit in new_edits:
            try:
                current_video_url = self.apply_single_edit(current_video_url, edit)
                edit.result_video_url = current_video_url
                logger.info(f"Applied edit {edit.id} ({edit.type})")
            except Exception as e:
                logger.error(f"Error applying edit {edit.id}: {e}")
                raise
        
        edit_queue.current_video_url = current_video_url
        return current_video_url
    
    def apply_single_edit(self, video_url: str, edit: Edit) -> str:
        if edit.type == "voiceover":
            return self._apply_voiceover(video_url, edit)
        elif edit.type == "text_overlay":
            return self._apply_text_overlay(video_url, edit)
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
    
    def _apply_text_overlay(self, video_url: str, edit: Edit) -> str:
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
            position=position
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
