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
from google.adk.tools import load_artifacts
from google.cloud import storage
from google.genai import types

from multi_tool_agent.add_text import add_text_to_video
from services.bigquery.bigquery_service import bigquery_service

load_dotenv()

APP_NAME = "wpromote-codesprint-2025"
USER_ID = "user1"
SESSION_ID = "session1"

TEST_FEATURE_ID = "a_supers_with_audio"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.json"

UPLOADED_VIDEO_CACHE = {}


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
    CURRENT_FEATURE_ID = feature_id or TEST_FEATURE_ID

    content = types.Content(role="user", parts=[types.Part(text=query)])
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


async def init_agent(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    print(
        f"Callback running before model call for agent: {callback_context.agent_name}"
    )

    feature_id = CURRENT_FEATURE_ID or TEST_FEATURE_ID
    feature_config = get_feature_config(feature_id)
    if feature_config and feature_config.get("videoUrl"):
        video_url = feature_config["videoUrl"]
        print(f"Video URL: {video_url}")
        # print(f"Cache contents: {UPLOADED_VIDEO_CACHE}")

        # artifact_name = video_url.split("/")[-1]

        available_files = await callback_context.list_artifacts()
        print(f"Available artifacts: {available_files}")

        if len(available_files):
            artifact_name = available_files[0]
        # else:
        #     artifact_name = video_url.split("/")[-1]
        else:
            artifact_name = "test"

        artifact_part = await callback_context.load_artifact(artifact_name)
        print(f"Loaded artifact part: {artifact_part}")
        if not artifact_part:
            print(
                f"Could not load artifact or artifact has no text path: {artifact_name}"
            )

            # if video_url in UPLOADED_VIDEO_CACHE:
            #     print(f"Using cached video URI: {UPLOADED_VIDEO_CACHE[video_url]}")
            #     video_part = types.Part.from_uri(
            #         file_uri=UPLOADED_VIDEO_CACHE[video_url],
            #         mime_type="video/mp4",
            #     )
            #     llm_request.contents[0].parts.append(video_part)
            # elif video_url.startswith("gs://"):
            try:
                print(f"Downloading and uploading video from {video_url} to Gemini...")
                bucket_name = video_url.split("/")[2]
                blob_path = unquote("/".join(video_url.split("/")[3:]))

                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".mp4"
                ) as tmp_file:
                    blob.download_to_filename(tmp_file.name)

                    filename = tmp_file.name
                    # video_artifact = types.Part.from_uri(
                    #     filename=filename, mime_type="video/*"
                    # )
                    # filename = "generated_report.pdf"

                    try:
                        version = await callback_context.save_artifact(
                            filename=filename, artifact=artifact_name
                        )
                        print(
                            f"Successfully saved Python artifact '{filename}' as version {version}."
                        )
                        callback_context.state["temp:video"] = filename

                        # The event generated after this callback will contain:
                        # event.actions.artifact_delta == {"generated_report.pdf": version}
                    except ValueError as e:
                        print(
                            f"Error saving Python artifact: {e}. Is ArtifactService configured in Runner?"
                        )
                    except Exception as e:
                        # Handle potential storage errors (e.g., GCS permissions)
                        print(
                            f"An unexpected error occurred during Python artifact save: {e}"
                        )

                    # client = genai.Client(
                    #     vertexai=False,
                    #     api_key=os.environ.get("GOOGLE_API_KEY"),
                    # )

                    # uploaded_file = client.files.upload(file=tmp_file.name)
                    # print(f"Video uploaded to Gemini: {uploaded_file.uri}")

                    # print(
                    #     f"Waiting for video to become ACTIVE (state: {uploaded_file.state})..."
                    # )
                    # while uploaded_file.state != "ACTIVE":
                    #     time.sleep(2)
                    #     uploaded_file = client.files.get(name=uploaded_file.name)
                    #     print(f"Video state: {uploaded_file.state}")

                    # print("Video is now ACTIVE")

                    # UPLOADED_VIDEO_CACHE[video_url] = uploaded_file.uri

                    # video_part = types.Part.from_uri(
                    #     file_uri=uploaded_file.uri,
                    #     mime_type="video/mp4",
                    # )
                    # llm_request.contents[0].parts.append(video_part)

                os.unlink(tmp_file.name)

            except Exception as e:
                print(f"Error uploading video: {e}")

    return None


def create_agent():
    tools = [load_artifacts, add_text_to_video]

    name = "ai_editor_agent"

    description = """"""

    instruction = """
    """

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

AGENT_RUNNER = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
    artifact_service=artifact_service,
)
