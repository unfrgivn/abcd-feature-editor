import datetime
import os

from google.adk.tools import ToolContext
from google.cloud import texttospeech


def generate_speech_from_text(
    tool_context: ToolContext,
    text_for_speech: str,
):
    """"""

    try:
        print("This is the text:" + text_for_speech)
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

        file_name = f"output_{datetime.datetime.now().timestamp()}"

        output_path = f"video_edits/speech_output/{file_name}"

        if not os.path.exists(output_path):
            # The response's audio_content is binary.
            with open(f"{output_path}.mp3", "wb") as out:
                out.write(response.audio_content)
                print(f"Audio content written to file {output_path}.mp3")
        else:
            print(f"File '{file_name}' already exists.")

        tool_context.state["temp:generated_audio_output_path"] = output_path

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
