import os
import datetime
from google.cloud import texttospeech
from moviepy import VideoFileClip, AudioFileClip
from google.adk.tools import ToolContext
from google.cloud import storage
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)


def generate_speech_from_text(
    tool_context: ToolContext, text_for_speech: str, video_url: str
):
    """Generates an audio file from text using Google Text To Speech.

    Synthesizes speech from `text_for_speech` using the Google
    Text-to-Speech client and saves it as a timestamped MP3 file.

    Updates the `tool_context.state` with the new audio file path
    (`generated_audio_output_path`) and the `video_url` for use by
    a subsequent tool.

    Args:
        tool_context (ToolContext): The context object for state management.
        text_for_speech (str): The text to be synthesized.
        video_url (str): The video URL to pass to the next tool's state.

    Returns:
        dict: A dictionary with 'status' and 'response' keys.
    """

    try:
        logger.info("This is the text for the audio:" + text_for_speech)
        default_voice = {
            "voice_name": "en-US-Chirp3-HD-Charon",
            "language_code": "en-US",
        }  # TODO (ae) make this dynamic

        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=text_for_speech)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
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

        if not os.path.exists(output_path):
            # The response's audio_content is binary.
            with open(f"{output_path}", "wb") as out:
                out.write(response.audio_content)
                print(f"Audio content written to file {output_path}.mp3")
        else:
            print(f"File '{file_name}' already exists.")

        # Set state for the next tool
        tool_context.state["generated_audio_output_path"] = output_path
        tool_context.state["video_url"] = video_url

        return {
            "status": "success",
            "response": {
                "message": "Audio generated successfully!",
                "generated_audio_path": output_path,
            },
        }
    except Exception as ex:
        print(f"ERROR: generate_speech_from_text {ex}")
        return {"status": "ERROR", "response": ex}


def add_audio_to_video(tool_context: ToolContext):
    """Adds audio to a video using paths from the tool context.

    Downloads the video from GCS (via `video_url`), replaces its
    audio with the local file (`generated_audio_output_path`), and
    saves the result locally.

    Args:
        tool_context (ToolContext): Contains state with:
            - `generated_audio_output_path` (str): Local path to the audio file.
            - `video_url` (str): GCS URL for the video file.

    Returns:
        dict: A dictionary with 'status' and 'response' keys.
    """
    try:
        generated_audio_output_path = tool_context.state.get(
            "generated_audio_output_path"
        )
        logger.info(
            f"This is generated_audio_output_path: {generated_audio_output_path} \n"
        )
        video_url = tool_context.state.get("video_url")
        logger.info(f"This is video_url: {generated_audio_output_path} \n")

        bucket_name = video_url.split("/")[2]
        blob_path = unquote("/".join(video_url.split("/")[3:]))
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        download_to_path = f"video_edits/videos/{blob.name}"
        blob.download_to_filename(download_to_path)

        video_clip = VideoFileClip(download_to_path)

        # Load the audio clip
        audio_clip = AudioFileClip(generated_audio_output_path)

        logger.info(f"Video duration: {video_clip.duration} seconds")
        logger.info(f"Audio duration: {audio_clip.duration} seconds")

        # Set the audio of the video clip
        # This replaces the original audio.
        logger.info("Setting new audio for the video...")
        if audio_clip.duration > video_clip.duration:
            video_clip.audio = audio_clip.subclipped(0, video_clip.duration)
        else:
            video_clip.audio = audio_clip

        edited_video_name = (
            f"{blob.name}_edited_{datetime.datetime.now().timestamp()}.mp4"
        )
        edited_video_path = f"video_edits/videos/{edited_video_name}"

        video_clip.write_videofile(
            edited_video_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
        )
        return {
            "status": "success",
            "response": f"The audio was successfully added to the video {edited_video_path}!",
        }
    except Exception as ex:
        logger.error(f"ERROR: add_audio_to_video {ex}")
        return {
            "status": "error",
            "response": f"There was an error adding the audio to the video {ex}",
        }
