import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.genai import types


@pytest.fixture
def mock_config_service():
    with patch("multi_tool_agent.agent.config_service") as mock:
        yield mock


@pytest.fixture
def mock_bigquery_service():
    with patch("multi_tool_agent.agent.bigquery_service") as mock:
        yield mock


@pytest.fixture
def mock_genai_client():
    with patch("multi_tool_agent.agent.genai.Client") as mock:
        yield mock


@pytest.fixture
def mock_storage_client():
    with patch("multi_tool_agent.agent.storage.Client") as mock:
        yield mock


@pytest.fixture
def mock_session_service():
    mock_service = MagicMock()
    mock_session = MagicMock()
    mock_session.state = {}
    mock_service.get_session_sync.return_value = mock_session
    return mock_service


@pytest.fixture
def mock_agent_runner(mock_session_service):
    with patch("multi_tool_agent.agent.AGENT_RUNNER") as mock_runner:
        mock_runner.session_service = mock_session_service
        yield mock_runner


class TestAnalyzeCreativePerformance:
    def test_analyze_creative_success(self, mock_genai_client):
        from multi_tool_agent.agent import analyze_creative_performance_with_gemini

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.parts = [MagicMock(text="Analysis result")]
        mock_client_instance.models.generate_content.return_value = mock_response

        result = analyze_creative_performance_with_gemini(
            "gs://bucket/creative.mp4"
        )

        assert result["status"] == "success"
        assert result["response"] == "Analysis result"
        mock_client_instance.models.generate_content.assert_called_once()

    def test_analyze_creative_empty_response(self, mock_genai_client):
        from multi_tool_agent.agent import analyze_creative_performance_with_gemini

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.parts = []
        mock_client_instance.models.generate_content.return_value = mock_response

        result = analyze_creative_performance_with_gemini(
            "gs://bucket/creative.mp4"
        )

        assert result["status"] == "error"
        assert "not able to analyze" in result["response"]


class TestRecommendationFunctions:
    @patch("multi_tool_agent.agent.get_session_data")
    @patch("multi_tool_agent.agent.set_session_data")
    def test_set_supers_audio_recommendation(self, mock_set, mock_get):
        from multi_tool_agent.agent import set_supers_audio_recommendation

        result = set_supers_audio_recommendation("Test message", 1000)

        assert result["voice_message"] == "Test message"
        assert result["start_at_milliseconds"] == 1000
        mock_set.assert_called_once_with("current_recommendations", result)

    @patch("multi_tool_agent.agent.get_session_data")
    @patch("multi_tool_agent.agent.set_session_data")
    def test_set_supers_text_recommendations(self, mock_set, mock_get):
        from multi_tool_agent.agent import set_supers_text_recommendations

        result = set_supers_text_recommendations("Test text", 1000, 3000)

        assert result["text_message"] == "Test text"
        assert result["start_at_milliseconds"] == 1000
        assert result["end_at_milliseconds"] == 3000
        mock_set.assert_called_once_with("current_recommendations", result)

    @patch("multi_tool_agent.agent.get_session_data")
    def test_get_current_recommendations(self, mock_get):
        from multi_tool_agent.agent import get_current_recommendations

        mock_get.return_value = {"text_message": "Test"}

        result = get_current_recommendations()

        assert result["text_message"] == "Test"
        mock_get.assert_called_once_with("current_recommendations")


class TestGetData:
    def test_get_data_success(self, mock_bigquery_service):
        from multi_tool_agent.agent import get_data

        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = {"col1": ["val1"], "col2": ["val2"]}
        mock_bigquery_service.query.return_value = mock_df

        result = get_data("SELECT * FROM table")

        assert result == {"col1": ["val1"], "col2": ["val2"]}
        mock_bigquery_service.query.assert_called_once_with("SELECT * FROM table")

    def test_get_data_empty_dataframe(self, mock_bigquery_service):
        from multi_tool_agent.agent import get_data

        mock_df = MagicMock()
        mock_df.empty = True
        mock_bigquery_service.query.return_value = mock_df

        result = get_data("SELECT * FROM table")

        assert result is None

    def test_get_data_none(self, mock_bigquery_service):
        from multi_tool_agent.agent import get_data

        mock_bigquery_service.query.return_value = None

        result = get_data("SELECT * FROM table")

        assert result is None


class TestCallAgent:
    @patch("multi_tool_agent.agent.get_session_data")
    def test_call_agent_text_only_response(
        self, mock_get_session, mock_agent_runner, mock_session_service
    ):
        from multi_tool_agent.agent import call_agent

        mock_get_session.return_value = {}

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock(text="Test response")]

        mock_agent_runner.run.return_value = [mock_event]

        result = call_agent("Test query")

        assert result == "Test response"
        mock_agent_runner.run.assert_called_once()

    @patch("multi_tool_agent.agent.get_session_data")
    def test_call_agent_with_video_url(
        self, mock_get_session, mock_agent_runner, mock_session_service
    ):
        from multi_tool_agent.agent import call_agent

        mock_get_session.return_value = {}

        mock_session_service.get_session_sync.return_value.state = {
            "edited_video_url": "https://storage.googleapis.com/bucket/video.mp4",
            "audio_urls": []
        }

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock(text="Test response")]

        mock_agent_runner.run.return_value = [mock_event]

        result = call_agent("Test query")

        result_obj = json.loads(result)
        assert result_obj["text"] == "Test response"
        assert "video_url" in result_obj["media"]
        assert result_obj["media"]["video_url"] == "https://storage.googleapis.com/bucket/video.mp4"

    @patch("multi_tool_agent.agent.get_session_data")
    def test_call_agent_with_audio_urls(
        self, mock_get_session, mock_agent_runner, mock_session_service
    ):
        from multi_tool_agent.agent import call_agent

        mock_get_session.return_value = {}

        mock_session_service.get_session_sync.return_value.state = {
            "audio_urls": ["https://storage.googleapis.com/bucket/audio.mp3"],
            "edited_video_url": None
        }

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock(text="Test response")]

        mock_agent_runner.run.return_value = [mock_event]

        result = call_agent("Test query")

        result_obj = json.loads(result)
        assert result_obj["text"] == "Test response"
        assert "audio_urls" in result_obj["media"]
        assert result_obj["media"]["audio_urls"] == ["https://storage.googleapis.com/bucket/audio.mp3"]

    @patch("multi_tool_agent.agent.get_session_data")
    @patch("multi_tool_agent.agent.config_service")
    def test_call_agent_with_feature_config(
        self, mock_config, mock_get_session, mock_agent_runner, mock_session_service
    ):
        from multi_tool_agent.agent import call_agent

        mock_get_session.return_value = {"text_message": "Test"}
        mock_config.get_feature_config.return_value = {
            "name": "Supers",
            "description": "Text overlay",
            "detected": True,
            "llmExplanation": "Text detected",
            "videoUrl": "https://storage.googleapis.com/bucket/video.mp4",
            "brand_tone": "professional"
        }

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock(text="Test response")]

        mock_agent_runner.run.return_value = [mock_event]

        result = call_agent("Test query", feature_id="feature_1")

        assert result == "Test response"
        mock_config.get_feature_config.assert_called_once_with("feature_1")

    @patch("multi_tool_agent.agent.get_session_data")
    def test_call_agent_video_preferred_over_audio(
        self, mock_get_session, mock_agent_runner, mock_session_service
    ):
        from multi_tool_agent.agent import call_agent

        mock_get_session.return_value = {}

        mock_session_service.get_session_sync.return_value.state = {
            "edited_video_url": "https://storage.googleapis.com/bucket/video.mp4",
            "audio_urls": ["https://storage.googleapis.com/bucket/audio.mp3"]
        }

        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock(text="Test response")]

        mock_agent_runner.run.return_value = [mock_event]

        result = call_agent("Test query")

        result_obj = json.loads(result)
        assert "video_url" in result_obj["media"]
        assert "audio_urls" not in result_obj["media"]


@pytest.mark.asyncio
class TestInitAgent:
    async def test_init_agent_no_video_url(self, mock_config_service):
        from multi_tool_agent.agent import init_agent

        mock_config_service.get_feature_config.return_value = None

        mock_context = MagicMock()
        mock_request = MagicMock()

        result = await init_agent(mock_context, mock_request)

        assert result is None

    async def test_init_agent_with_existing_artifact(
        self, mock_config_service, mock_storage_client
    ):
        from multi_tool_agent.agent import init_agent

        mock_config_service.get_feature_config.return_value = {
            "videoUrl": "https://storage.googleapis.com/bucket/video.mp4"
        }

        mock_context = MagicMock()
        mock_context.list_artifacts = AsyncMock(return_value=["input_video.mp4"])

        mock_artifact = MagicMock()
        mock_artifact.inline_data = MagicMock()
        mock_artifact.inline_data.data = b"video_data"
        mock_context.load_artifact = AsyncMock(return_value=mock_artifact)

        mock_request = MagicMock()

        result = await init_agent(mock_context, mock_request)

        assert result is None
        mock_context.load_artifact.assert_called_once_with("input_video.mp4")

    async def test_init_agent_download_video(
        self, mock_config_service, mock_storage_client
    ):
        from multi_tool_agent.agent import init_agent

        mock_config_service.get_feature_config.return_value = {
            "videoUrl": "https://storage.googleapis.com/bucket/video.mp4"
        }

        mock_context = MagicMock()
        mock_context.list_artifacts = AsyncMock(return_value=[])
        mock_context.save_artifact = AsyncMock(return_value=1)
        mock_context.state = {}

        mock_blob = MagicMock()
        mock_blob.download_to_filename = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_instance = MagicMock()
        mock_storage_instance.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_storage_instance

        mock_request = MagicMock()

        with patch("builtins.open", MagicMock()):
            result = await init_agent(mock_context, mock_request)

        assert result is None
        mock_blob.download_to_filename.assert_called_once()


class TestGenerateDynamicInstruction:
    def test_generate_dynamic_instruction_no_config(self):
        from multi_tool_agent.agent import generate_dynamic_instruction

        instruction = generate_dynamic_instruction()

        assert "AI editor agent" in instruction
        assert "WORKFLOW" in instruction

    def test_generate_dynamic_instruction_supers_with_audio(self):
        from multi_tool_agent.agent import generate_dynamic_instruction

        feature_config = {
            "id": "supers_with_audio",
            "brand_tone": "friendly",
            "primary_brand_color": "#FF0000",
            "secondary_brand_color": "#00FF00"
        }

        instruction = generate_dynamic_instruction(feature_config)

        assert "Supers with Audio" in instruction
        assert "friendly" in instruction
        assert "#FF0000" in instruction
        assert "generate_speech_from_text" in instruction

    def test_generate_dynamic_instruction_supers_text_only(self):
        from multi_tool_agent.agent import generate_dynamic_instruction

        feature_config = {
            "id": "supers",
            "brand_tone": "professional",
            "primary_brand_color": "#0000FF",
            "secondary_brand_color": "#FF00FF"
        }

        instruction = generate_dynamic_instruction(feature_config)

        assert "Supers (Text overlays only)" in instruction
        assert "professional" in instruction
        assert "add_text_to_video_with_ffmpeg" in instruction

    def test_generate_dynamic_instruction_voice_and_tone(self):
        from multi_tool_agent.agent import generate_dynamic_instruction

        feature_config = {
            "id": "voice_and_tone",
            "brand_tone": "energetic"
        }

        instruction = generate_dynamic_instruction(feature_config)

        assert "Voice and Tone" in instruction
        assert "energetic" in instruction


class TestCreateAgent:
    @patch.dict(os.environ, {"MODEL_NAME": "test-model"})
    def test_create_agent(self):
        from multi_tool_agent.agent import create_agent

        agent = create_agent()

        assert agent.name == "ai_editor_agent"
        assert len(agent.tools) == 6
        assert agent.before_model_callback is not None
