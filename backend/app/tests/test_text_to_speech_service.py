import pytest
from unittest.mock import Mock, patch, MagicMock
from services.text_to_speech_service import TextToSpeechService


class TestTextToSpeechService:
    @pytest.fixture
    def service(self):
        with patch('services.text_to_speech_service.texttospeech.TextToSpeechClient'), \
             patch('services.text_to_speech_service.storage.Client'):
            return TextToSpeechService()
    
    @pytest.fixture
    def mock_tts_response(self):
        response = Mock()
        response.audio_content = b"fake_audio_content"
        return response
    
    def test_init(self, service):
        assert service.default_voice["voice_name"] == "en-US-Chirp3-HD-Charon"
        assert service.default_voice["language_code"] == "en-US"
    
    @patch('services.text_to_speech_service.os.unlink')
    @patch('services.text_to_speech_service.tempfile.NamedTemporaryFile')
    def test_generate_speech_success(self, mock_tempfile, mock_unlink, service, mock_tts_response):
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_audio.mp3"
        mock_temp.__enter__.return_value = mock_temp
        mock_tempfile.return_value = mock_temp
        
        service.tts_client.synthesize_speech = Mock(return_value=mock_tts_response)
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        service.storage_client.bucket.return_value = mock_bucket
        
        result = service.generate_speech("Hello world")
        
        assert result["status"] == "success"
        assert "audio_url" in result
        assert "https://storage.googleapis.com/" in result["audio_url"]
        service.tts_client.synthesize_speech.assert_called_once()
        mock_blob.upload_from_filename.assert_called_once()
    
    def test_generate_speech_with_custom_voice(self, service, mock_tts_response):
        service.tts_client.synthesize_speech = Mock(return_value=mock_tts_response)
        
        with patch('services.text_to_speech_service.tempfile.NamedTemporaryFile'), \
             patch('services.text_to_speech_service.os.unlink'):
            mock_bucket = Mock()
            mock_blob = Mock()
            mock_bucket.blob.return_value = mock_blob
            service.storage_client.bucket.return_value = mock_bucket
            
            result = service.generate_speech(
                "Test",
                voice_name="en-GB-Standard-A",
                language_code="en-GB"
            )
            
            assert result["status"] == "success"
    
    def test_generate_speech_error_handling(self, service):
        service.tts_client.synthesize_speech = Mock(side_effect=Exception("API Error"))
        
        result = service.generate_speech("Test")
        
        assert result["status"] == "error"
        assert "Error generating speech" in result["message"]
