import datetime
import json
import logging
import os
import subprocess
import tempfile
from typing import Optional
from urllib.parse import unquote

from core.config import settings
from google.cloud import storage

logger = logging.getLogger(__name__)


class VideoEditingService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.scratch_bucket = settings.GCS_BUCKET_NAME
    
    def _download_video_from_gcs(self, video_url: str) -> str:
        if video_url.startswith("gs://"):
            bucket_name = video_url.split("/")[2]
            blob_path = unquote("/".join(video_url.split("/")[3:]))
        else:
            parts = video_url.split("/")
            bucket_name = parts[3]
            blob_path = unquote("/".join(parts[4:]))
        
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            blob.download_to_filename(tmp_file.name)
            return tmp_file.name
    
    def _upload_video_to_gcs(self, local_path: str, filename: str) -> str:
        bucket = self.storage_client.bucket(self.scratch_bucket)
        blob_path = f"videos/{filename}"
        blob = bucket.blob(blob_path)
        
        blob.upload_from_filename(local_path)
        blob.reload()
        
        video_url = f"https://storage.googleapis.com/{self.scratch_bucket}/{blob_path}"
        logger.info(f"Video uploaded to GCS: {video_url}")
        return video_url
    
    def _get_video_dimensions(self, video_path: str) -> tuple[int, int]:
        probe_command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            video_path
        ]
        
        probe_result = subprocess.run(probe_command, capture_output=True, text=True, check=True)
        video_width, video_height = map(int, probe_result.stdout.strip().split(','))
        logger.info(f"Video dimensions: {video_width}x{video_height}")
        return video_width, video_height
    
    def _wrap_text(self, text: str, max_width: int, fontsize: int) -> list[str]:
        avg_char_width = fontsize * 0.55
        max_chars_per_line = int(max_width / avg_char_width)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = current_line + [word]
            test_text = ' '.join(test_line)
            
            if len(test_text) <= max_chars_per_line:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        logger.info(f"Wrapped text into {len(lines)} lines, max width: {max_width}px")
        return lines
    
    def _get_brand_color(self, video_url: str) -> str:
        config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
        with open(config_path, "r") as f:
            config_data = json.load(f)
        
        primary_brand_color = "#1e1e1e"
        for item in config_data:
            if item.get("videoUrl") == video_url:
                primary_brand_color = item.get("primary_brand_color", "#1e1e1e")
                break
        
        return primary_brand_color
    
    def add_text_overlay(
        self,
        video_url: str,
        text: str,
        start_time: int,
        duration: int,
        fontsize: int = 70,
        color: str = "white",
        position: str = "center"
    ) -> dict[str, str]:
        try:
            input_video_path = self._download_video_from_gcs(video_url)
            
            if not os.path.exists(input_video_path):
                logger.error(f"Input video file not found: {input_video_path}")
                return {
                    "status": "error",
                    "message": f"Input video file not found at {input_video_path}"
                }
            
            video_width, video_height = self._get_video_dimensions(input_video_path)
            max_text_width = int(video_width * 0.8)
            
            lines = self._wrap_text(text, max_text_width, fontsize)
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as text_file:
                text_file.write('\n'.join(lines))
                text_file_path = text_file.name
            
            logger.info(f"Created text file: {text_file_path}")
            
            brand_color = self._get_brand_color(video_url)
            brand_color_hex = brand_color.lstrip("#")
            alpha_hex = format(int(0.8 * 255), '02X')
            text_bg_color = f"0x{brand_color_hex}{alpha_hex}"
            
            x = "(w-text_w)/2"
            y_position = {
                "top": "30",
                "center": "(h-text_h)/2",
                "bottom": "h-text_h-30"
            }.get(position, "(h-text_h)/2")
            
            output_video_path = tempfile.mktemp(suffix=".mp4")
            
            ffmpeg_command = [
                "ffmpeg",
                "-y",
                "-i", input_video_path,
                "-vf",
                f"drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:textfile={text_file_path}:fontcolor={color}:fontsize={fontsize}:x={x}:y={y_position}:box=1:boxcolor={text_bg_color}:boxborderw=20:line_spacing=10:enable='between(t,{start_time},{start_time + duration})'",
                "-c:a", "copy",
                output_video_path,
            ]
            
            logger.info(f"FFmpeg command: {' '.join(ffmpeg_command)}")
            subprocess.run(ffmpeg_command, check=True, capture_output=True)
            
            logger.info(f"Text successfully overlaid on video")
            
            file_name = f"video_{datetime.datetime.now().timestamp()}.mp4"
            video_gcs_url = self._upload_video_to_gcs(output_video_path, file_name)
            
            try:
                os.unlink(text_file_path)
                os.unlink(input_video_path)
                os.unlink(output_video_path)
            except Exception as cleanup_error:
                logger.warning(f"Could not delete temp files: {cleanup_error}")
            
            return {
                "status": "success",
                "message": "Text successfully added to video! The edited video is ready.",
                "video_url": video_gcs_url
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during FFmpeg execution: {e}")
            return {
                "status": "error",
                "message": f"Error adding text to video: {str(e)}"
            }
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please ensure FFmpeg is installed.")
            return {
                "status": "error",
                "message": "Error: FFmpeg not found. Please ensure FFmpeg is installed."
            }
        except Exception as e:
            logger.error(f"Error in add_text_overlay: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def add_audio_overlay(
        self,
        video_url: str,
        audio_path: str,
        start_offset: int = 0,
        volume_overlay: float = 1.0,
        volume_original: float = 0.3
    ) -> dict[str, str]:
        try:
            input_video_path = self._download_video_from_gcs(video_url)
            
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found: {audio_path}")
                return {
                    "status": "error",
                    "message": f"Audio file not found at {audio_path}"
                }
            
            output_video_path = tempfile.mktemp(suffix=".mp4")
            
            command = [
                "ffmpeg",
                "-i", input_video_path,
                "-i", audio_path,
                "-filter_complex",
                f"[0:a]volume={volume_original}[a0];"
                f"[1:a]adelay={start_offset * 1000}|{start_offset * 1000},"
                f"volume={volume_overlay}[a1];"
                f"[a0][a1]amix=inputs=2:duration=longest[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-y",
                output_video_path,
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            logger.info(f"Successfully added audio to video")
            
            file_name = f"video_{datetime.datetime.now().timestamp()}.mp4"
            video_gcs_url = self._upload_video_to_gcs(output_video_path, file_name)
            
            try:
                os.unlink(input_video_path)
                os.unlink(output_video_path)
            except Exception as cleanup_error:
                logger.warning(f"Could not delete temp files: {cleanup_error}")
            
            return {
                "status": "success",
                "message": "The audio was successfully added to the video!",
                "video_url": video_gcs_url
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error adding audio to video: {e}")
            return {
                "status": "error",
                "message": f"There was an error adding the audio to the video: {e}"
            }
        except FileNotFoundError:
            logger.error("FFmpeg command not found. Please ensure FFmpeg is installed.")
            return {
                "status": "error",
                "message": "FFmpeg not found. Please ensure FFmpeg is installed."
            }
        except Exception as e:
            logger.error(f"Error in add_audio_overlay: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }


video_editing_service = VideoEditingService()
