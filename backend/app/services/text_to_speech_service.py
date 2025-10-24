import datetime
import logging
import os
import tempfile

from core.config import settings
from google.cloud import storage, texttospeech

logger = logging.getLogger(__name__)


class TextToSpeechService:
    def __init__(self):
        self.tts_client = texttospeech.TextToSpeechClient()
        self.storage_client = storage.Client()
        self.scratch_bucket = settings.GCS_BUCKET_NAME
        self.default_voice = {
            "voice_name": "en-US-Chirp3-HD-Charon",
            "language_code": "en-US",
        }
    
    def generate_speech(
        self,
        text: str,
        voice_name: str | None = None,
        language_code: str | None = None
    ) -> dict[str, str]:
        try:
            logger.info(f"Generating speech for text: {text}")
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code or self.default_voice["language_code"],
                name=voice_name or self.default_voice["voice_name"],
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            input_text = texttospeech.SynthesisInput(text=text)
            
            response = self.tts_client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config,
            )
            
            file_name = f"output_{datetime.datetime.now().timestamp()}.mp3"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.audio_content)
                local_path = tmp_file.name
                logger.info(f"Audio content written to temp file: {local_path}")
            
            bucket = self.storage_client.bucket(self.scratch_bucket)
            blob_path = f"audio/{file_name}"
            blob = bucket.blob(blob_path)
            
            blob.upload_from_filename(local_path)
            blob.reload()
            
            audio_url = f"https://storage.googleapis.com/{self.scratch_bucket}/{blob_path}"
            logger.info(f"Audio uploaded to GCS: {audio_url}")
            
            return {
                "status": "success",
                "message": "Audio generated successfully!",
                "audio_url": audio_url,
                "local_path": local_path
            }
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return {
                "status": "error",
                "message": f"Error generating speech: {str(e)}"
            }


text_to_speech_service = TextToSpeechService()
