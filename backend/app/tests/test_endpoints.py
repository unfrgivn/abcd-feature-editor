import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from main import app


client = TestClient(app)


class TestEndpoints:
    def test_healthcheck(self):
        response = client.get("/api/test")
        assert response.status_code == 200
        assert response.json() == {"status": "Success!"}
    
    @patch('builtins.open')
    @patch('json.load')
    def test_get_config(self, mock_json_load, mock_open):
        mock_config = [{"id": "1", "name": "Test Video"}]
        mock_json_load.return_value = mock_config
        
        response = client.get("/api/config.json")
        
        assert response.status_code == 200
        assert response.json() == mock_config
    
    @patch('api.endpoints.ai_editor_agent_routes.agent.call_agent')
    def test_call_ai_editor_agent_success(self, mock_call_agent):
        mock_call_agent.return_value = '{"text": "Response", "media": null}'
        
        response = client.post("/api/call_ai_editor_agent", json={
            "query": "Add text overlay",
            "feature_id": "feature-123"
        })
        
        assert response.status_code == 200
        mock_call_agent.assert_called_once_with("Add text overlay", "feature-123")
    
    @patch('api.endpoints.ai_editor_agent_routes.agent.call_agent')
    def test_call_ai_editor_agent_error(self, mock_call_agent):
        mock_call_agent.side_effect = Exception("Agent error")
        
        response = client.post("/api/call_ai_editor_agent", json={
            "query": "Test query",
            "feature_id": "feature-123"
        })
        
        assert response.status_code == 500
        assert "ERROR" in response.text
    
    @patch('api.endpoints.ai_editor_agent_routes.cleanup_all')
    @patch('api.endpoints.ai_editor_agent_routes.agent')
    def test_cleanup_session_success(self, mock_agent, mock_cleanup):
        mock_cleanup.return_value = {"status": "success", "message": "Cleaned up"}
        mock_agent.session_service = Mock()
        mock_agent.APP_NAME = "test-app"
        mock_agent.USER_ID = "user-1"
        mock_agent.SESSION_ID = "session-1"
        
        response = client.post("/api/cleanup")
        
        assert response.status_code == 200
        mock_cleanup.assert_called_once()
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.create_session')
    def test_create_session(self, mock_create):
        mock_create.return_value = 123
        
        response = client.post("/api/sessions/create?user_id=user1&session_id=sess1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_pk"] == 123
        assert "Session created" in data["message"]
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.list_sessions')
    def test_list_sessions(self, mock_list):
        mock_sessions = [
            {"session_id": "sess1", "created_at": "2025-01-01"},
            {"session_id": "sess2", "created_at": "2025-01-02"}
        ]
        mock_list.return_value = mock_sessions
        
        response = client.get("/api/sessions/list?user_id=user1")
        
        assert response.status_code == 200
        assert response.json() == mock_sessions
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.get_session')
    def test_get_session_found(self, mock_get):
        mock_session = {"session_id": "sess1", "state": {}}
        mock_get.return_value = mock_session
        
        response = client.get("/api/sessions/get?user_id=user1&session_id=sess1")
        
        assert response.status_code == 200
        assert response.json() == mock_session
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.get_session')
    def test_get_session_not_found(self, mock_get):
        mock_get.return_value = None
        
        response = client.get("/api/sessions/get?user_id=user1&session_id=sess1")
        
        assert response.status_code == 404
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.get_versions')
    def test_get_session_versions(self, mock_get_versions):
        mock_versions = [
            {"version_id": 1, "video_url": "url1"},
            {"version_id": 2, "video_url": "url2"}
        ]
        mock_get_versions.return_value = mock_versions
        
        response = client.get("/api/sessions/versions?session_pk=123")
        
        assert response.status_code == 200
        assert response.json() == mock_versions
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.create_version')
    def test_create_session_version(self, mock_create_version):
        mock_create_version.return_value = 1
        
        response = client.post("/api/sessions/version?session_pk=123&video_url=test.mp4")
        
        assert response.status_code == 200
        data = response.json()
        assert data["version_id"] == 1
    
    @patch('api.endpoints.ai_editor_agent_routes.database_session_service.delete_session')
    def test_delete_session(self, mock_delete):
        response = client.delete("/api/sessions/delete?user_id=user1&session_id=sess1")
        
        assert response.status_code == 200
        assert "deleted" in response.text.lower()
        mock_delete.assert_called_once()
    
    @patch('api.endpoints.ai_editor_agent_routes.get_video_export_service')
    def test_export_video(self, mock_get_export):
        mock_export_service = Mock()
        mock_export_service.export_video.return_value = "https://storage.googleapis.com/exported.mp4"
        mock_get_export.return_value = mock_export_service
        
        response = client.post(
            "/api/export?video_path=/tmp/video.mp4&user_id=user1&feature_id=feat1&video_id=vid1"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "public_url" in data
        assert "Video exported" in data["message"]
