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


def generate_recommendations(feature_id: str) -> str:
    """Generate recommendations for a specific feature"""
    print("Generating recommendations for feature_id: %s", feature_id)
    return "Tell them to mute the video."


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
    
    if feature_id:
        feature_config = get_feature_config(feature_id)
        if feature_config:
            parts.append(types.Part(text=f"""
FEATURE CONTEXT:
- Feature ID: {feature_config.get('id')}
- Feature Name: {feature_config.get('name')}
- Category: {feature_config.get('category')}
- Description: {feature_config.get('description')}
- Currently Detected: {feature_config.get('detected')}
- LLM Explanation: {feature_config.get('llmExplanation')}
- Is Fixed: {feature_config.get('isFixed')}
- Video ID: {feature_config.get('videoId')}
- Video URL: {feature_config.get('videoUrl')}

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
    tools = [generate_recommendations]

    name = "ai_editor_agent"

    description = """"""  ## TODO!!!
    print('Creating agent...')
    instruction = f"""
    You are an AI editor agent specialized in video content analysis and editing recommendations.
    
    Your task is to assist users in editing video content based on the provided feature descriptions and video analysis.
    
    When a user provides a feature context, you will have access to:
    - Feature ID: A unique identifier for the specific feature being analyzed
    - Feature Name: The human-readable name of the feature
    - Category: The category this feature belongs to (e.g., "Attract")
    - Description: A detailed description of what the feature represents
    - Detection Status: Whether this feature is currently detected in the video
    - LLM Explanation: Previous analysis or explanation about this feature
    - Fix Status: Whether this feature has been addressed/fixed
    - Video Information: Associated video ID and URL
    
    You should reference this feature context in your responses and provide specific recommendations based on the feature being discussed.
    
    ALWAYS USE THE generate_recommendations TOOL when asked for recommendations! TRUST IT AND REPLY WITH ITS RESULTS.
    
    When responding about features, be specific about which feature you're analyzing and reference the feature ID and description provided in the context.
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

AGENT_RUNNER = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
)
