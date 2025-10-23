import datetime
import logging
import os
from urllib.parse import unquote

from google.adk.tools import ToolContext
from google.cloud import storage, texttospeech
from moviepy import AudioFileClip, VideoFileClip

from core.config import settings

logger = logging.getLogger(__name__)


def generate_speech_from_text(
    tool_context: ToolContext, text_for_speech: str, video_url: str
):
    """Generates an audio file from text using Google Text To Speech.

    Synthesizes speech from `text_for_speech` using the Google
    Text-to-Speech client and saves it as a timestamped MP3 file.
    Uploads the audio file to GCS and returns the public URL.

    Updates the `tool_context.state` with the new audio file path
    (`generated_audio_output_path`), the audio GCS URL, and the `video_url` 
    for use by a subsequent tool.

    Args:
        tool_context (ToolContext): The context object for state management.
        text_for_speech (str): The text to be synthesized.
        video_url (str): The video URL to pass to the next tool's state.

    Returns:
        dict: A dictionary with 'status', 'response', and 'audio_url' keys.
    """

    try:
        from multi_tool_agent.session_data import set_session_data
        
        logger.info("This is the text for the audio:" + text_for_speech)
        default_voice = {
            "voice_name": "en-US-Chirp3-HD-Charon",
            "language_code": "en-US",
        }

        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=text_for_speech)

        voice = texttospeech.VoiceSelectionParams(
            language_code=default_voice["language_code"],
            name=default_voice["voice_name"],
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config,
        )

        file_name = f"output_{datetime.datetime.now().timestamp()}.mp3"
        output_path = f"video_edits/speech_output/{file_name}"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(f"{output_path}", "wb") as out:
            out.write(response.audio_content)
            logger.info(f"Audio content written to file {output_path}")

        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
        blob_path = f"audio/{file_name}"
        blob = bucket.blob(blob_path)
        
        blob.upload_from_filename(output_path)
        blob.reload()
        
        audio_url = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{blob_path}"
        logger.info(f"Audio uploaded to GCS: {audio_url}")

        tool_context.state["generated_audio_output_path"] = output_path
        tool_context.state["video_url"] = video_url
        
        if "audio_urls" not in tool_context.state:
            tool_context.state["audio_urls"] = []
        tool_context.state["audio_urls"].append(audio_url)
        
        from multi_tool_agent.session_data import get_session_data
        current_audio_urls = get_session_data("audio_urls")
        if not isinstance(current_audio_urls, list):
            current_audio_urls = []
        current_audio_urls.append(audio_url)
        set_session_data("audio_urls", current_audio_urls)

        return {
            "status": "success",
            "response": {
                "message": "Audio generated successfully!",
                "generated_audio_path": output_path,
                "audio_url": audio_url,
            },
        }
    except Exception as ex:
        logger.error(f"ERROR: generate_speech_from_text {ex}")
        return {"status": "ERROR", "response": str(ex)}


def add_audio_to_video(tool_context: ToolContext):
    """Adds audio to a video using paths from the tool context.

    Downloads the video from GCS (via `video_url`), replaces its
    audio with the local file (`generated_audio_output_path`), and
    saves the result locally and uploads to GCS.

    Args:
        tool_context (ToolContext): Contains state with:
            - `generated_audio_output_path` (str): Local path to the audio file.
            - `video_url` (str): GCS URL for the video file.

    Returns:
        dict: A dictionary with 'status', 'response', and 'video_url' keys.
    """
    try:
        from multi_tool_agent.session_data import set_session_data
        
        generated_audio_output_path = tool_context.state.get(
            "generated_audio_output_path"
        )
        logger.info(
            f"This is generated_audio_output_path: {generated_audio_output_path} \n"
        )
        video_url = tool_context.state.get("video_url")
        logger.info(f"This is video_url: {video_url} \n")

        bucket_name = video_url.split("/")[2]
        blob_path = unquote("/".join(video_url.split("/")[3:]))
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        download_to_path = f"video_edits/videos/{blob.name}"
        
        os.makedirs(os.path.dirname(download_to_path), exist_ok=True)
        blob.download_to_filename(download_to_path)

        video_clip = VideoFileClip(download_to_path)

        audio_clip = AudioFileClip(generated_audio_output_path)

        logger.info(f"Video duration: {video_clip.duration} seconds")
        logger.info(f"Audio duration: {audio_clip.duration} seconds")

        logger.info("Setting new audio for the video...")
        if audio_clip.duration > video_clip.duration:
            video_clip.audio = audio_clip.subclipped(0, video_clip.duration)
        else:
            video_clip.audio = audio_clip

        edited_video_name = (
            f"edited_{datetime.datetime.now().timestamp()}.mp4"
        )
        edited_video_path = f"video_edits/videos/{edited_video_name}"

        video_clip.write_videofile(
            edited_video_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
        )

        gcs_bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
        gcs_blob_path = f"videos/{edited_video_name}"
        gcs_blob = gcs_bucket.blob(gcs_blob_path)
        
        gcs_blob.upload_from_filename(edited_video_path)
        gcs_blob.reload()
        
        edited_video_url = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{gcs_blob_path}"
        logger.info(f"Edited video uploaded to GCS: {edited_video_url}")

        tool_context.state["edited_video_url"] = edited_video_url
        set_session_data("latest_video_url", edited_video_url)

        return {
            "status": "success",
            "response": f"The audio was successfully added to the video {edited_video_path}!",
            "video_url": edited_video_url,
        }
    except Exception as ex:
        logger.error(f"ERROR: add_audio_to_video {ex}")
        return {
            "status": "error",
            "response": f"There was an error adding the audio to the video {ex}",
        }
