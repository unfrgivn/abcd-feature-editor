import os
import logging
import asyncio
from dateutil.relativedelta import relativedelta
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from services.bigquery.bigquery_service import bigquery_service
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

# Load environment variables from .env file
load_dotenv()

APP_NAME = "wpromote-codesprint-2025"
USER_ID = "user1"
SESSION_ID = "session1"


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


def call_agent(query):
    """"""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print("Running agent...")
    events = AGENT_RUNNER.run(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    )
    # Iterate on agent responses
    print("Processing agent responses...")
    for event in events:
        if event.is_final_response() and event.content:
            resp = event.content.parts[0].text.strip()
            return resp

    return None


def create_agent():
    tools = []  ## TODO!!!

    name = "ai_editor_agent"

    description = """"""  ## TODO!!!

    instruction = f"""
    """  ## TODO!!!

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
