import logging
import os
import tempfile
from urllib.parse import unquote

from google.adk.tools import ToolContext
from google.cloud import storage
from moviepy import CompositeVideoClip, TextClip, VideoFileClip
import subprocess

logger = logging.getLogger(__name__)


async def add_text_to_video(
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
    video_url = tool_context.state.get("video_url")
    print("State URI:", video_url)

    artifact_name = tool_context.state.get("temp:video")
    if not artifact_name:
        print("error: Document artifact name not found in state.")
    else:
        print("Found artifact:", artifact_name)

    input_video_path = await tool_context.load_artifact(artifact_name)

    # TODO: Replace with video from context once working
    bucket_name = video_url.split("/")[2]
    blob_path = unquote("/".join(video_url.split("/")[3:]))

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

        video_clip = None
        txt_clip = None
        result = None

        try:
            # Load the main video clip
            video_clip = VideoFileClip(input_video_path)

            # Ensure duration doesn't exceed video length
            video_duration = video_clip.duration
            if start_time > video_duration:
                logger.warning(
                    f"Start time {start_time}s is after video duration {video_duration}s."
                )
                # Closing clip before returning error
                video_clip.close()
                return f"Error: Start time {start_time}s is after video duration {video_duration}s."

            actual_duration = duration
            if start_time + duration > video_duration:
                actual_duration = video_duration - start_time
                logger.warning(
                    f"Text duration truncated to {actual_duration}s to fit video length."
                )

            # Create the text clip
            # Using a built-in font for better compatibility in containers
            txt_clip = TextClip(
                # font="config/arial.ttf",
                font=None,
                text=text,
                font_size=fontsize,
                color=color,
                duration=duration,
            ).with_position(position)

            # Set position, start time, and duration
            txt_clip = (
                txt_clip.with_position(position)
                .with_start(start_time)
                .with_duration(actual_duration)
            )

            # Composite the video and text clips
            result = CompositeVideoClip([video_clip, txt_clip])

            # Write the result to the output file
            # Specifying codecs for broad compatibility
            result.write_videofile(
                output_video_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                logger=None,  # To avoid moviepy's default verbose logging
            )

            logger.info(f"Successfully created video with text at {output_video_path}")
            return f"Success: Video saved to {output_video_path}"

        except Exception as e:
            # Check for common ImageMagick error
            if "ImageMagick is not installed" in str(e) or "convert: not found" in str(
                e
            ):
                logger.error("ImageMagick error: %s", e, exc_info=True)
                return "Error: ImageMagick is not installed or configured correctly. TextClip requires it."
            logger.error(f"Failed to process video: {e}", exc_info=True)
            return f"Error: Failed to process video. {str(e)}"

        finally:
            # Close clips to release file handles
            if video_clip:
                video_clip.close()
            if txt_clip:
                txt_clip.close()
            if result:
                result.close()


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
    video_url = tool_context.state.get("video_url")
    print("State URI:", video_url)

    artifact_name = tool_context.state.get("temp:video")
    if not artifact_name:
        print("error: Document artifact name not found in state.")
    else:
        print("Found artifact:", artifact_name)

    input_video_path = await tool_context.load_artifact(artifact_name)

    # TODO: Replace with video from context once working
    bucket_name = video_url.split("/")[2]
    blob_path = unquote("/".join(video_url.split("/")[3:]))

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
                "-i",
                input_video_path,
                "-vf",
                f"drawtext=font='Times New Roman':text='{text}':enable='between(t,{start_time},{start_time + duration})':fontcolor={color}:fontsize={fontsize}:x={x}:y={y}",
                "-c:a",
                "copy",  # Copy audio without re-encoding
                output_video_path,
            ]

            try:
                subprocess.run(ffmpeg_command, check=True)
                logger.info(
                    f"Text successfully overlaid on {input_video_path} to create {output_video_path}"
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Error during FFmpeg execution: {e}")
            except FileNotFoundError:
                logger.error(
                    "FFmpeg not found. Please ensure FFmpeg is installed and in your system's PATH."
                )

        except Exception as e:
            print(e)
