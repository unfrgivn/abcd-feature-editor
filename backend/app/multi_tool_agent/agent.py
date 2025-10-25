import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from dotenv import load_dotenv
from google import genai
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import storage
from google.genai import types
from services.bigquery.bigquery_service import bigquery_service
from services.config_service import config_service

from multi_tool_agent.add_text import add_text_to_video_with_ffmpeg
from multi_tool_agent.generate_speech_tool import (
    add_audio_to_video_with_ffmpeg,
    generate_speech_from_text,
)
from multi_tool_agent.edit_queue_tools import (
    add_voiceover_edit,
    update_voiceover_timing,
    add_text_overlay_edit,
    remove_edit,
    get_edit_queue_info,
    find_voiceover_edit,
)

from .session_data import get_session_data, initialize_session_data, set_session_data

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = os.getenv("APP_NAME", "wpromote-codesprint-2025")
USER_ID = os.getenv("DEFAULT_USER_ID", "user1")
SESSION_ID = os.getenv("DEFAULT_SESSION_ID", "session1")
GCS_SCRATCH_BUCKET = os.getenv("GCS_SCRATCH_BUCKET", "creative-audit-scratch-pad")
GCS_FINAL_BUCKET = os.getenv("GCS_FINAL_BUCKET", "creative-audit-final-videos")


def analyze_creative_performance_with_gemini(creative_uri: str) -> dict[str, str]:
    """ """

    prompt = """
        I am providing you with a video that has been identified as one of our top-performing ads.
        It has successfully resonated with our audience, leading to a high [Specify Key Metrics:
        "Click-Through Rate," "Conversion Rate," "Impressions" and "Revenue"].
        My goal is not just a description of the video, but a deep analysis of what elements made it successful.
        I want to understand the "creative formula" so my team can replicate its success in future ad campaigns.
        You are an expert Creative Strategist and an Advertising Analyst.
        Your specialty is deconstructing successful video advertisements to understand
        why they perform well and turning those insights into an actionable formula for
        future creative development.

        Your Task:
        Analyze the provided video and provide a detailed breakdown.
        Please structure your analysis in the following three sections:

        Section 1: Core Messaging & Narrative
        This section analyzes what the ad communicates. It focuses on deconstructing the ad's story,
        its central theme, the emotional tone (e.g., funny, urgent), the main value proposition, and
        the specific Call to Action (CTA).

        Section 2: Visual & Audio Elements
        This section analyzes the sensory experience of the ad. It focuses on the technical and artistic
        choices, such as the "hook" used in the first 3-5 seconds, the editing pace, the appearance of people,
        the use of on-screen text, and the sound design (music or voice-over).

        Section 3: Actionable "Formula for Success"
        This is the most important part. Instead of just describing the ad, this section synthesizes all the
        analysis from the first two sections into a practical, bulleted list of 3-5 key recommendations. It's
        the "secret formula" that your creative team can use to replicate the ad's success in future campaigns.
    """
    print(f"Analyzing creative {creative_uri} with Gemini...")

    client = genai.Client(
        vertexai=False,
        api_key=os.environ.get("GOOGLE_API_KEY"),
    )

    video = types.Part.from_uri(
        file_uri=creative_uri,
        mime_type="video/*",
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt), video],
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=65535,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
    )

    response = client.models.generate_content(
        model=os.getenv("MODEL_NAME2"),
        contents=contents,
        config=generate_content_config,
    )

    if response and response.parts and len(response.parts) > 0:
        resp = response.parts[0].text
        return {
            "status": "success",
            "response": resp,
        }

    return {
        "status": "error",
        "response": f"Gemini was not able to analyze video {creative_uri}",
    }


def set_supers_audio_recommendation(
    voice_message: str, start_at_milliseconds: int
) -> dict[str, int]:
    """
    Generate audio voiceover that should be added to the video.

    Args:
        voice_message: The audio voice message
        start_at_milliseconds: When the audio should start in milliseconds

    Returns:
        Dictionary with voice_message and start_at_milliseconds
    """
    recommendations = {
        "voice_message": voice_message,
        "start_at_milliseconds": start_at_milliseconds,
    }
    print("Setting recommendations in session data: ", recommendations)
    set_session_data("current_recommendations", recommendations)
    return recommendations


def set_supers_text_recommendations(
    text_message: str, start_at_milliseconds: int, end_at_milliseconds: int
) -> dict[str, int]:
    """
    Set Supers (text) recommendations that should be added to the video.

    Args:
        text_message: The text to appear on screen
        start_at_milliseconds: When the text should appear in milliseconds
        end_at_milliseconds: When the text should disappear in milliseconds

    Returns:
        Dictionary with text_message, start_at_milliseconds, and end_at_milliseconds
    """
    recommendations = {
        "text_message": text_message,
        "start_at_milliseconds": start_at_milliseconds,
        "end_at_milliseconds": end_at_milliseconds,
    }
    print("Setting recommendations in session data: ", recommendations)
    set_session_data("current_recommendations", recommendations)
    return recommendations


def get_current_recommendations() -> dict[str, str]:
    """
    Get current recommendations from session data.

    Returns:
        Dictionary with current recommendations
    """
    recommendations = get_session_data("current_recommendations")
    print("Getting current recommendations from session data: ", recommendations)
    return recommendations


def get_data(query: str):
    """"""
    logging.info("Extracting data... \n %s", query)
    data_frame = bigquery_service.query(query)

    if data_frame is not None and not data_frame.empty:
        return data_frame.to_dict("list")

    return None


async def call_agent_async(query):
    print(f"\n--- Asking the agent: '{query}' ---")
    content = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in AGENT_RUNNER.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    ):
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)


CURRENT_FEATURE_ID = None


def call_agent(query, feature_id=None):
    """"""
    global CURRENT_FEATURE_ID
    CURRENT_FEATURE_ID = feature_id

    parts = [types.Part(text=query)]

    current_recommendations = get_session_data("current_recommendations")
    print("Current recommendations from session data: ", current_recommendations)

    if feature_id:
        feature_config = config_service.get_feature_config(feature_id)
        if feature_config:
            dynamic_instruction = generate_dynamic_instruction(feature_config)
            parts.append(
                types.Part(
                    text=f"""
FEATURE CONTEXT:
- Feature Name: {feature_config.get("name")}
- Description: {feature_config.get("description")}
- Currently Detected: {feature_config.get("detected")}
- LLM Explanation: {feature_config.get("llmExplanation")}
- Video URL: {feature_config.get("videoUrl")}
- Brand Tone: {feature_config.get("brand_tone")}
- Current Recommendations: {current_recommendations}

{dynamic_instruction}

USER QUERY: {query}
"""
                )
            )
        else:
            print(f"Feature config not found for id: {feature_id}")

    content = types.Content(role="user", parts=parts)
    print("Running agent...")
    events = AGENT_RUNNER.run(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    )
    print("Processing agent responses...")
    
    media_assets = {}
    event_count = 0
    final_responses = []
    
    for event in events:
        event_count += 1
        print(f"DEBUG agent.py: Event #{event_count}: is_final={event.is_final_response()}, has_content={hasattr(event, 'content') and event.content is not None}")
        if hasattr(event, 'content') and event.content:
            print(f"DEBUG agent.py: Event content parts: {event.content.parts}")
        if event.is_final_response() and event.content:
            resp = event.content.parts[0].text.strip()
            print(f"DEBUG agent.py: Final response #{len(final_responses) + 1} text: {resp}")
            final_responses.append(resp)
    
    print(f"DEBUG agent.py: Collected {len(final_responses)} final responses")
    
    if not final_responses:
        print(f"WARNING agent.py: No final response found after processing {event_count} events")
        return ""
    
    last_response = final_responses[-1]
    print(f"DEBUG agent.py: Using last final response: {last_response}")
    
    try:
        session = AGENT_RUNNER.session_service.get_session_sync(
            app_name=APP_NAME, 
            user_id=USER_ID, 
            session_id=SESSION_ID
        )
        if session and hasattr(session, 'state'):
            print(f"DEBUG agent.py: Session state keys: {session.state.keys()}")
            print(f"DEBUG agent.py: Session state: {session.state}")
            
            has_audio = 'audio_urls' in session.state and session.state['audio_urls']
            has_new_video = 'edited_video_url' in session.state and session.state['edited_video_url']
            
            print(f"DEBUG agent.py: has_audio={has_audio}, has_new_video={has_new_video}")
            
            if has_audio and has_new_video:
                media_assets['video_url'] = session.state['edited_video_url']
                print(f"DEBUG agent.py: Both audio and video present - sending video_url: {media_assets['video_url']}")
                session.state['audio_urls'] = []
                print(f"DEBUG agent.py: Cleared audio_urls from session state (keeping edited_video_url for edit queue)")
            elif has_new_video:
                media_assets['video_url'] = session.state['edited_video_url']
                print(f"DEBUG agent.py: Setting video_url in media_assets: {media_assets['video_url']}")
                print(f"DEBUG agent.py: Keeping edited_video_url in session state for edit queue")
            elif has_audio:
                media_assets['audio_urls'] = session.state['audio_urls']
                print(f"DEBUG agent.py: Setting audio_urls in media_assets: {media_assets['audio_urls']}")
                session.state['audio_urls'] = []
                print(f"DEBUG agent.py: Cleared audio_urls from session state")
    except Exception as e:
        print(f"ERROR agent.py: getting session state: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"DEBUG agent.py: Final media_assets: {media_assets}")
    
    if media_assets:
        import json
        response_obj = {
            "text": last_response,
            "media": media_assets
        }
        print(f"DEBUG agent.py: Returning JSON: {response_obj}")
        return json.dumps(response_obj)
    print(f"DEBUG agent.py: Returning plain text response")
    return last_response


async def init_agent(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    print(
        f"Callback running before model call for agent: {callback_context.agent_name}"
    )

    feature_id = CURRENT_FEATURE_ID
    feature_config = config_service.get_feature_config(feature_id)
    
    if feature_config and feature_config.get("videoUrl"):
        video_url = feature_config["videoUrl"]
        print(f"Video URL: {video_url}")

        artifact_filename = "input_video.mp4"

        available_files = await callback_context.list_artifacts()
        print(f"Available artifacts: {available_files}")

        artifact_part = None
        if artifact_filename in available_files:
            print(f"Loading existing artifact: {artifact_filename}")
            artifact_part = await callback_context.load_artifact(artifact_filename)

        if artifact_part:
            print("Artifact loaded successfully, extracting to temp file...")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                if artifact_part.inline_data and artifact_part.inline_data.data:
                    tmp_file.write(artifact_part.inline_data.data)
                    tmp_file.flush()
                    callback_context.state["temp:video"] = tmp_file.name
                    print(f"Extracted artifact to temp file: {tmp_file.name}")
                else:
                    print("Artifact has no inline_data, will re-download")
                    artifact_part = None

        if not artifact_part:
            print(f"No artifact found, downloading from {video_url}...")
            try:
                bucket_name = video_url.split("/")[2]
                blob_path = unquote("/".join(video_url.split("/")[3:]))

                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".mp4"
                ) as tmp_file:
                    blob.download_to_filename(tmp_file.name)

                    callback_context.state["video_url"] = video_url
                    callback_context.state["temp:video"] = tmp_file.name

                    try:
                        with open(tmp_file.name, "rb") as video_file:
                            video_bytes = video_file.read()

                        video_artifact = types.Part.from_bytes(
                            data=video_bytes, mime_type="video/mp4"
                        )

                        version = await callback_context.save_artifact(
                            filename=artifact_filename, artifact=video_artifact
                        )
                        print(
                            f"Successfully saved video artifact '{artifact_filename}' as version {version}."
                        )

                    except ValueError as e:
                        print(
                            f"Error saving artifact: {e}. Is ArtifactService configured in Runner?"
                        )
                    except Exception as e:
                        print(f"An unexpected error occurred during artifact save: {e}")

            except Exception as e:
                print(f"Error downloading video: {e}")

    return None


def generate_dynamic_instruction(feature_config: Optional[dict] = None) -> str:
    base_instruction = """
    You are an AI editor agent specialized in video content analysis and editing recommendations.
    
    Your task is to assist users in editing video content based on the provided feature descriptions and video analysis.
    
    When a user provides a feature context, you will have access to:
    - Feature Name: The human-readable name of the feature
    - Description: A detailed description of what the feature represents
    - Detection Status: Whether this feature is currently detected in the video
    - LLM Explanation: Previous analysis or explanation about this feature
    - Current Recommendations: Suggested edits or improvements for this feature for the user to consider
    
    EDIT QUEUE SYSTEM - CRITICAL UNDERSTANDING:
    You now have access to an Edit Queue system that tracks all edits made to the video. This is ESSENTIAL for handling user requests correctly:
    
    1. DETECTING UPDATE vs ADD REQUESTS:
       - "Move the voiceover from 0.5s to 2s" → UPDATE (modify existing edit)
       - "Change the voiceover timing to 3s" → UPDATE
       - "Make the voiceover start at 1s instead" → UPDATE
       - "Add another voiceover at 5s" → ADD (new edit)
       - "Also add text at 2s" → ADD
    
    2. WORKFLOW FOR UPDATES:
       When user wants to MODIFY an existing edit:
       a) Call `find_voiceover_edit()` to get the current voiceover edit ID
       b) Call `update_voiceover_timing(edit_id, new_start_ms)` with the edit ID and new timing
       c) This will regenerate the video with the UPDATED timing (NOT duplicate)
    
    3. WORKFLOW FOR NEW EDITS:
       When user wants to ADD a new edit:
       a) Call `add_voiceover_edit(text, start_ms, original_video_url)` for new voiceovers
       b) Call `add_text_overlay_edit(text, start_ms, end_ms, original_video_url)` for new text
    
    4. CHECKING CURRENT STATE:
       - Before making changes, you can call `get_edit_queue_info()` to see all current edits
       - Use `find_voiceover_edit()` to check if a voiceover already exists
    
    5. REMOVING EDITS:
       - Call `remove_edit(edit_id)` to remove an edit and regenerate the video
    
    CRITICAL: Always determine if the user wants to UPDATE an existing edit or ADD a new one before calling tools.
    """
    
    if feature_config:
        feature_id = feature_config.get("id", "")
        brand_tone = feature_config.get("brand_tone", "professional and engaging")
        primary_color = feature_config.get("primary_brand_color", "#5db1bd")
        secondary_color = feature_config.get("secondary_brand_color", "#313e48")
        
        if "supers_with_audio" in feature_id:
            workflow_instruction = f"""
    FEATURE TYPE: Supers with Audio (Text overlays + Voiceover)
    BRAND TONE: {brand_tone}
    BRAND COLORS: Primary: {primary_color}, Secondary: {secondary_color}

    WORKFLOW FOR INITIAL RECOMMENDATIONS:
    1. If there are no `Current Recommendations` OR if the user requests initial recommendations:
       a) Call `set_supers_audio_recommendation` tool with voiceover message and timing
       
       b) IMMEDIATELY generate the actual media:
          * ALWAYS call `generate_speech_from_text` to create the audio file FIRST
          * Then ask the user to review the audio preview
          * Ask if they want to add this voiceover to the video
          * WAIT for user confirmation (e.g., "Yes", "Sure", "Go ahead")
       
       c) Finally, call `get_current_recommendations` to retrieve and describe them
    
    WORKFLOW FOR USER CONFIRMATION:
    When user confirms (says "Yes", "Sure", "Go ahead", etc.) to add the voiceover:
    1. Get the current recommendations using `get_current_recommendations` to retrieve voice_message and start_at_milliseconds
    2. Extract the Video URL from the FEATURE CONTEXT section above (it's listed as "- Video URL: ...")
     3. CRITICAL: Call `add_voiceover_edit(text=voice_message, start_ms=start_at_milliseconds)` - the video_url is automatically retrieved from the agent's context
    4. The tool will return a new video_url - you MUST include this in your response media
    5. DO NOT just say you've added it - actually call the tool and return the new video
    
    WORKFLOW FOR USER EDITS:
    When a user requests changes to audio:
    - Use `generate_speech_from_text` to create the audio file preview
    - Ask the user to review the audio
    - Ask if they want to add this voiceover to the video
    - WAIT for user confirmation before calling `add_voiceover_edit`
    
    VOICEOVER COPY RULES:
    - Voiceover copy MUST be 1-2 sentences maximum
    - Keep it concise, punchy, and impactful
    - Match the brand tone: {brand_tone}
    - Never generate voiceover copy longer than 2 sentences
    """
        elif "supers" in feature_id and "audio" not in feature_id:
            workflow_instruction = f"""
    FEATURE TYPE: Supers (Text overlays only)
    BRAND TONE: {brand_tone}
    BRAND COLORS: Primary: {primary_color}, Secondary: {secondary_color}

    WORKFLOW FOR INITIAL RECOMMENDATIONS:
    1. If there are no `Current Recommendations` OR if the user requests initial recommendations:
       a) Call `set_supers_text_recommendations` tool with text message and timing
       
       b) IMMEDIATELY generate the actual media:
          * ALWAYS call `add_text_to_video_with_ffmpeg` to create the video with text overlay
       
       c) Finally, call `get_current_recommendations` to retrieve and describe them
    
    WORKFLOW FOR USER EDITS:
    When a user requests changes to text overlays:
    - Use `add_text_to_video_with_ffmpeg` to create the video with text
    - Don't just describe what you would do - actually call the tool to generate the file
    
    TEXT OVERLAY RULES:
    - Keep text short and impactful
    - Match the brand tone: {brand_tone}
    - Use brand colors when applicable: Primary: {primary_color}, Secondary: {secondary_color}
    """
        elif "voice_and_tone" in feature_id or "tone" in feature_id:
            workflow_instruction = f"""
    FEATURE TYPE: Voice and Tone Analysis
    BRAND TONE: {brand_tone}

    WORKFLOW FOR INITIAL RECOMMENDATIONS:
    1. If there are no `Current Recommendations` OR if the user requests initial recommendations:
       a) Call `set_supers_audio_recommendation` tool with voiceover message that matches the brand tone
       
       b) IMMEDIATELY generate the actual media:
          * ALWAYS call `generate_speech_from_text` to create the audio file FIRST
          * Then ask the user to review the audio preview
          * Ask if they want to add this voiceover to the video
          * WAIT for user confirmation (e.g., "Yes", "Sure", "Go ahead")
       
       c) Finally, call `get_current_recommendations` to retrieve and describe them
    
    WORKFLOW FOR USER CONFIRMATION:
    When user confirms (says "Yes", "Sure", "Go ahead", etc.) to add the voiceover:
    1. Get the current recommendations using `get_current_recommendations` to retrieve voice_message and start_at_milliseconds
    2. Extract the Video URL from the FEATURE CONTEXT section above (it's listed as "- Video URL: ...")
     3. CRITICAL: Call `add_voiceover_edit(text=voice_message, start_ms=start_at_milliseconds)` - the video_url is automatically retrieved from the agent's context
    4. The tool will return a new video_url - you MUST include this in your response media
    5. DO NOT just say you've added it - actually call the tool and return the new video
    
    WORKFLOW FOR USER EDITS:
    When a user requests changes to voiceover:
    - Use `generate_speech_from_text` to create the audio file preview
    - Ask the user to review the audio
    - Ask if they want to add this voiceover to the video
    - WAIT for user confirmation before calling `add_voiceover_edit`
    
    VOICEOVER COPY RULES:
    - Voiceover copy MUST be 1-2 sentences maximum
    - Keep it concise, punchy, and impactful
    - CRITICAL: Match the brand tone precisely: {brand_tone}
    - Never generate voiceover copy longer than 2 sentences
    """
        else:
            workflow_instruction = """
    FEATURE TYPE: General Video Editing
    
    WORKFLOW:
    - Analyze the video based on the feature description
    - Provide recommendations based on best practices
    - Use available tools to generate previews when requested
    """
    else:
        workflow_instruction = """
    WORKFLOW FOR INITIAL RECOMMENDATIONS:
    1. If there are no `Current Recommendations` OR if the user requests initial recommendations:
       a) Determine feature type from Feature Name:
          - If Feature Name contains "with Audio" → This is a Supers with Audio feature
          - Otherwise → This is a text-only Supers feature
       
       b) Set recommendations:
          - For Supers with Audio: Call `set_supers_audio_recommendation` tool
          - For text-only Supers: Call `set_supers_text_recommendations` tool
       
       c) IMMEDIATELY generate the actual media:
          - For Supers with Audio: 
            * ALWAYS call `generate_speech_from_text` to create the audio file FIRST
            * Then ask the user to review the audio preview
            * Ask if they want to add this voiceover to the video
            * WAIT for user confirmation (e.g., "Yes", "Sure", "Go ahead")
          - For text-only Supers: ALWAYS call `add_text_to_video_with_ffmpeg` to create the video with text overlay
       
       d) Finally, call `get_current_recommendations` to retrieve and describe them
    
    WORKFLOW FOR USER CONFIRMATION:
    When user confirms (says "Yes", "Sure", "Go ahead", etc.) to add the voiceover:
    1. Get the current recommendations using `get_current_recommendations` to retrieve voice_message and start_at_milliseconds
    2. Extract the Video URL from the FEATURE CONTEXT section above (it's listed as "- Video URL: ...")
     3. CRITICAL: Call `add_voiceover_edit(text=voice_message, start_ms=start_at_milliseconds)` - the video_url is automatically retrieved from the agent's context
    4. The tool will return a new video_url - you MUST include this in your response media
    5. DO NOT just say you've added it - actually call the tool and return the new video
    
    WORKFLOW FOR USER EDITS:
    When a user requests changes to audio or text:
    - For audio changes: 
      * Use `generate_speech_from_text` to create the audio file preview
      * Ask the user to review the audio
      * Ask if they want to add this voiceover to the video
      * WAIT for user confirmation before calling `add_voiceover_edit`
    - For text overlay changes: Use `add_text_to_video_with_ffmpeg` to create the video with text
    - Don't just describe what you would do - actually call the tool to generate the file
    
    VOICEOVER COPY RULES:
    - Voiceover copy MUST be 1-2 sentences maximum
    - Keep it concise, punchy, and impactful
    - Never generate voiceover copy longer than 2 sentences
    """
    
    footer = """
    CRITICAL RESPONSE RULES:
    1. ALWAYS provide a final text response to the user after using tools
    2. When you generate audio files or videos using the tools, DO NOT include the file URLs (like https://storage.googleapis.com/...) in your text response
    3. The generated media will automatically appear as playable previews below your message
    4. Only describe what you've created in natural language
    5. After completing any tool calls, you MUST respond with a user-friendly message explaining what you did
    6. CRITICAL: When you generate an audio preview and ask the user if they want to apply it, your message MUST end with a question mark (?)
       - This is required for the UI to detect that you're asking for confirmation
       - Example: "I've generated an audio preview. Would you like me to add this voiceover to your video?"
    
    Example responses:
    - "I've generated an audio preview with the message 'Feeling stuck? Let's break through!' starting at 0.5 seconds. Listen to the preview above - would you like me to add this voiceover to your video?"
    - "I've created a video with the text overlay 'New Feature' appearing from 1.0 to 3.0 seconds. Check out the preview and let me know what you think!"
    """
    
    return base_instruction + workflow_instruction + footer


def create_agent():
    tools = [
        set_supers_audio_recommendation,
        set_supers_text_recommendations,
        get_current_recommendations,
        generate_speech_from_text,
        add_text_to_video_with_ffmpeg,
        add_audio_to_video_with_ffmpeg,
        add_voiceover_edit,
        update_voiceover_timing,
        add_text_overlay_edit,
        remove_edit,
        get_edit_queue_info,
        find_voiceover_edit,
    ]

    name = "ai_editor_agent"

    description = """"""

    instruction = generate_dynamic_instruction()

    agent = LlmAgent(
        model=os.environ["MODEL_NAME"],
        name=name,
        description=description,
        instruction=instruction,
        tools=tools,
        before_model_callback=init_agent,
    )

    return agent


agent = create_agent()
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()


async def create_session():
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )


asyncio.run(create_session())

# Initialize session data module
initialize_session_data(APP_NAME, USER_ID, SESSION_ID, session_service)

AGENT_RUNNER = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
    artifact_service=artifact_service,
)
