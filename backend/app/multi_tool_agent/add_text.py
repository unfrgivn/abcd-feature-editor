import json
import logging
import os
import subprocess
import tempfile
from urllib.parse import unquote

from google.adk.tools import ToolContext
from google.cloud import storage

logger = logging.getLogger(__name__)


# async def add_text_to_video(
#     tool_context: ToolContext,
#     output_video_path: str,
#     text: str,
#     start_time: int,
#     duration: int,
#     fontsize: int,
#     color: str,
#     position: str,
# ) -> dict[str, str]:
#     """
#     Adds a text overlay to a video clip at a specified time and saves the result.
#     Uploads the edited video to GCS and returns the public URL.

#     Args:
#         output_video_path: The file path to save the output video (e.g., "edited_video.mp4").
#         text: The text content to overlay on the video.
#         start_time: The time (in seconds) when the text should appear.
#         duration: The duration (in seconds) the text should remain on screen.
#         fontsize: The font size of the text. Defaults to 70.
#         color: The color of the text (e.g., 'white', 'red'). Defaults to 'white'.
#         position: The position of the text (e.g., 'center', 'top', 'bottom').
#                   Can also be a tuple like ('left', 'top') or (10, 50) for pixels.
#                   Defaults to 'center'.

#     Returns:
#         A dictionary with status, message, and video_url.
#     """
#     video_url = tool_context.state.get("video_url")
#     print("State URI:", video_url)

#     artifact_name = tool_context.state.get("temp:video")
#     if not artifact_name:
#         print("error: Document artifact name not found in state.")
#     else:
#         print("Found artifact:", artifact_name)

#     input_video_path = await tool_context.load_artifact(artifact_name)
    
#     if not output_video_path or output_video_path.strip() == "":
#         output_video_path = tempfile.mktemp(suffix=".mp4")

#     bucket_name = video_url.split("/")[2]
#     blob_path = unquote("/".join(video_url.split("/")[3:]))

#     storage_client = storage.Client()
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.blob(blob_path)
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
#         blob.download_to_filename(tmp_file.name)

#         input_video_path = tmp_file.name

#         logger.info(f"Attempting to add text '{text}' to video {input_video_path}")

#         if not os.path.exists(input_video_path):
#             logger.error(f"Input video file not found: {input_video_path}")
#             return {"status": "error", "message": f"Input video file not found at {input_video_path}"}

#         video_clip = None
#         txt_clip = None
#         result = None

#         try:
#             video_clip = VideoFileClip(input_video_path)

#             video_duration = video_clip.duration
#             if start_time > video_duration:
#                 logger.warning(
#                     f"Start time {start_time}s is after video duration {video_duration}s."
#                 )
#                 video_clip.close()
#                 return {"status": "error", "message": f"Start time {start_time}s is after video duration {video_duration}s."}

#             actual_duration = duration
#             if start_time + duration > video_duration:
#                 actual_duration = video_duration - start_time
#                 logger.warning(
#                     f"Text duration truncated to {actual_duration}s to fit video length."
#                 )

#             txt_clip = TextClip(
#                 font=None,
#                 text=text,
#                 font_size=fontsize,
#                 color=color,
#                 duration=duration,
#             ).with_position(position)

#             txt_clip = (
#                 txt_clip.with_position(position)
#                 .with_start(start_time)
#                 .with_duration(actual_duration)
#             )

#             result = CompositeVideoClip([video_clip, txt_clip])

#             output_dir = os.path.dirname(output_video_path)
#             if output_dir:
#                 os.makedirs(output_dir, exist_ok=True)

#             result.write_videofile(
#                 output_video_path,
#                 codec="libx264",
#                 audio_codec="aac",
#                 temp_audiofile="temp-audio.m4a",
#                 remove_temp=True,
#                 logger=None,
#             )

#             logger.info(f"Successfully created video with text at {output_video_path}")

#             gcs_bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
#             file_name = f"video_{datetime.datetime.now().timestamp()}.mp4"
#             gcs_blob_path = f"videos/{file_name}"
#             gcs_blob = gcs_bucket.blob(gcs_blob_path)
            
#             gcs_blob.upload_from_filename(output_video_path)
#             gcs_blob.reload()
            
#             video_gcs_url = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{gcs_blob_path}"
#             logger.info(f"Video uploaded to GCS: {video_gcs_url}")

#             tool_context.state["edited_video_url"] = video_gcs_url
#             set_session_data("latest_video_url", video_gcs_url)

#             return {
#                 "status": "success",
#                 "message": f"Video saved to {output_video_path}",
#                 "video_url": video_gcs_url,
#             }

#         except Exception as e:
#             if "ImageMagick is not installed" in str(e) or "convert: not found" in str(
#                 e
#             ):
#                 logger.error("ImageMagick error: %s", e, exc_info=True)
#                 return {"status": "error", "message": "ImageMagick is not installed or configured correctly. TextClip requires it."}
#             logger.error(f"Failed to process video: {e}", exc_info=True)
#             return {"status": "error", "message": f"Failed to process video. {str(e)}"}

#         finally:
#             if video_clip:
#                 video_clip.close()
#             if txt_clip:
#                 txt_clip.close()
#             if result:
#                 result.close()


async def add_text_to_video_with_ffmpeg(
    tool_context: ToolContext,
    output_video_path: str,
    text: str,
    start_time: int,
    duration: int,
    fontsize: int,
    color: str,
    position: str,
) -> str:
    """
    Adds a text overlay to a video clip at a specified time and saves the result.

    Args:
        output_video_path: The file path to save the output video (e.g., "edited_video.mp4").
        text: The text content to overlay on the video.
        start_time: The time (in seconds) when the text should appear.
        duration: The duration (in seconds) the text should remain on screen.
        fontsize: The font size of the text. Defaults to 70.
        color: The color of the text (e.g., 'white', 'red'). Defaults to 'white'.
        position: The position of the text (e.g., 'center', 'top', 'bottom').
                  Can also be a tuple like ('left', 'top') or (10, 50) for pixels.
                  Defaults to 'center'.

    Returns:
        A string message indicating success and the output path, or an error message.
    """
    video_url = tool_context.state.get("edited_video_url") or tool_context.state.get("video_url")
    print("State URI:", video_url)

    artifact_name = tool_context.state.get("temp:video")
    if not artifact_name:
        print("error: Document artifact name not found in state.")
    else:
        print("Found artifact:", artifact_name)

    input_video_path = await tool_context.load_artifact(artifact_name)

    config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
    with open(config_path, "r") as f:
        config_data = json.load(f)
    
    primary_brand_color = "#1e1e1e"
    for item in config_data:
        if item.get("videoUrl") == video_url or item.get("videoUrl") == tool_context.state.get("video_url"):
            primary_brand_color = item.get("primary_brand_color", "#1e1e1e")
            break
    
    brand_color_hex = primary_brand_color.lstrip("#")
    bg_color = f"0x{brand_color_hex}@0.8"

    # TODO: Replace with video from context once working
    if video_url.startswith("gs://"):
        bucket_name = video_url.split("/")[2]
        blob_path = unquote("/".join(video_url.split("/")[3:]))
    else:
        parts = video_url.split("/")
        bucket_name = parts[3]
        blob_path = unquote("/".join(parts[4:]))

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        blob.download_to_filename(tmp_file.name)

        input_video_path = tmp_file.name

        logger.info(f"Attempting to add text '{text}' to video {input_video_path}")

        if not os.path.exists(input_video_path):
            logger.error(f"Input video file not found: {input_video_path}")
            return f"Error: Input video file not found at {input_video_path}"

        try:
            x = "(w-text_w)/2"
            y = ""
            match position:
                case "top":
                    y = "text_h+10"
                case "center":
                    y = "(h-text_h-10)/2"
                case "bottom":
                    y = "h-text_h-10"
                case _:
                    y = "(h-text_h-10)/2"
            ffmpeg_command = [
                "ffmpeg",
                "-y",  # Overwrite output file without asking
                "-i",
                input_video_path,
                "-vf",
                f"drawtext=font='Arial':text='{text}':enable='between(t,{start_time},{start_time + duration})':box=1:boxcolor={bg_color}:boxborderw=20:fontcolor={color}:fontsize={fontsize}:x={x}:y={y}",
                "-c:a",
                "copy",  # Copy audio without re-encoding
                output_video_path,
            ]

            try:
                subprocess.run(ffmpeg_command, check=True)
                logger.info(
                    f"Text successfully overlaid on {input_video_path} to create {output_video_path}"
                )
                
                # Upload to GCS
                import datetime

                from core.config import settings
                
                gcs_bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
                file_name = f"video_{datetime.datetime.now().timestamp()}.mp4"
                gcs_blob_path = f"videos/{file_name}"
                gcs_blob = gcs_bucket.blob(gcs_blob_path)
                
                gcs_blob.upload_from_filename(output_video_path)
                gcs_blob.reload()
                
                video_gcs_url = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{gcs_blob_path}"
                logger.info(f"Video uploaded to GCS: {video_gcs_url}")
                
                tool_context.state["edited_video_url"] = video_gcs_url
                
                from multi_tool_agent.session_data import set_session_data
                set_session_data("latest_video_url", video_gcs_url)
                
                return "Text successfully added to video! The edited video is ready."
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Error during FFmpeg execution: {e}")
                return f"Error adding text to video: {str(e)}"
            except FileNotFoundError:
                logger.error(
                    "FFmpeg not found. Please ensure FFmpeg is installed and in your system's PATH."
                )
                return "Error: FFmpeg not found. Please ensure FFmpeg is installed."

        except Exception as e:
            logger.error(f"Error in add_text_to_video_with_ffmpeg: {e}")
            return f"Error: {str(e)}"
