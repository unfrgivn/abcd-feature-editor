import os
import logging
import asyncio
import json
from pathlib import Path
from dateutil.relativedelta import relativedelta
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from services.bigquery.bigquery_service import bigquery_service
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .session_data import set_session_data, get_session_data, initialize_session_data

load_dotenv()

APP_NAME = "wpromote-codesprint-2025"
USER_ID = "user1"
SESSION_ID = "session1"

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def get_feature_config(feature_id: str):
    config = load_config()
    for feature in config:
        if feature.get("id") == feature_id:
            return feature
    return None


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


def set_supers_audio_recommendation(voice_message: str, start_at_milliseconds: int) -> dict[str, int]:
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
        text_message: str, 
        start_at_milliseconds: int, 
        end_at_milliseconds: int,
        text_position: str,
        font_size: str,
        font_color: str,
        background_color: str = "transparent"
    ) -> dict[str, int]:
    """
    Set Supers (text) recommendations that should be added to the video.
    
    Args:
        text_message: The text to appear on screen
        start_at_milliseconds: When the text should appear in milliseconds
        end_at_milliseconds: When the text should disappear in milliseconds
        text_position: Position of the text on screen (e.g., "top-left", "bottom-right")
        font_size: Size of the text font (e.g., "small", "medium", "large")
        font_color: Color of the text font (e.g., "white", "black", "red")
        background_color: Background color of the text (e.g., "transparent", "black", "red")
    Returns:
        Dictionary with text_message, start_at_milliseconds, and end_at_milliseconds
    """
    recommendations = {
        "text_message": text_message,
        "start_at_milliseconds": start_at_milliseconds,
        "end_at_milliseconds": end_at_milliseconds,
        "position": text_position,
        "font_size": font_size,
        "font_color": font_color,
        "background_color": background_color,
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


def call_agent(query, feature_id=None):
    """"""
    parts = [types.Part(text=query)]

    current_recommendations = get_session_data("current_recommendations")
    print("Current recommendations from session data: ", current_recommendations)
    
    if feature_id:
        feature_config = get_feature_config(feature_id)
        if feature_config:
            parts.append(types.Part(text=f"""
FEATURE CONTEXT:
- Feature Name: {feature_config.get('name')}
- Description: {feature_config.get('description')}
- Currently Detected: {feature_config.get('detected')}
- LLM Explanation: {feature_config.get('llmExplanation')}
- Video URL: {feature_config.get('videoUrl')}
- Current Recommendations: {current_recommendations}

USER QUERY: {query}
"""))
            video_url = feature_config.get("videoUrl")
            if video_url:
                print(f"Adding video context from {video_url} for feature {feature_id}")
                video_part = types.Part.from_uri(
                    file_uri=video_url,
                    mime_type="video/*",
                )
                parts.append(video_part)
            else:
                print(f"No videoUrl found for feature {feature_id}")
        else:
            print(f"Feature config not found for id: {feature_id}")
    
    content = types.Content(role="user", parts=parts)
    print("Running agent...")
    events = AGENT_RUNNER.run(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    )
    print("Processing agent responses...")
    for event in events:
        if event.is_final_response() and event.content:
            resp = event.content.parts[0].text.strip()
            return resp

    return None


def create_agent():
    tools = [set_supers_audio_recommendation, set_supers_text_recommendations, get_current_recommendations]

    name = "ai_editor_agent"

    description = """"""  ## TODO!!!
    
    instruction = f"""
    You are an AI editor agent specialized in video content analysis and editing recommendations.
    
    Your task is to assist users in editing video content based on the provided feature descriptions and video analysis.
    
    When a user provides a feature context, you will have access to:
    - Feature Name: The human-readable name of the feature
    - Description: A detailed description of what the feature represents
    - Detection Status: Whether this feature is currently detected in the video
    - LLM Explanation: Previous analysis or explanation about this feature
    - Video URL: A link to the video content related to this feature.
    - Current Recommendations: Suggested edits or improvements for this feature for the user to consider

    If the user is not pleased with the `Current Recommendations` or if there are no `Current Recommendations`,
    pass recommendations to the `set_supers_audio_recommendation` OR `set_supers_text_recommendations` tool. 
    Never use both tools.

    Finally, use the get_current_recommendations tool to retrieve the latest recommendations
    and describe each change attribute in the response of the tool IN FULL to the user.
    """

    agent = LlmAgent(
        model=os.environ["MODEL_NAME"],
        name=name,
        description=description,
        instruction=instruction,
        tools=tools,
    )

    return agent


# Init agent
agent = create_agent()
session_service = InMemorySessionService()


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
)
