import pytest
from unittest.mock import Mock, patch, MagicMock
from services.video_editing_service import VideoEditingService


class TestVideoEditingService:
    @pytest.fixture
    def service(self):
        with patch('services.video_editing_service.storage.Client'):
            return VideoEditingService()
    
    def test_init(self, service):
        assert service.storage_client is not None
        assert service.scratch_bucket is not None
    
    @patch('services.video_editing_service.tempfile.NamedTemporaryFile')
    def test_download_video_from_gcs_gs_url(self, mock_tempfile, service):
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_video.mp4"
        mock_temp.__enter__.return_value = mock_temp
        mock_tempfile.return_value = mock_temp
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        service.storage_client.bucket.return_value = mock_bucket
        
        result = service._download_video_from_gcs("gs://test-bucket/videos/test.mp4")
        
        assert result == "/tmp/test_video.mp4"
        service.storage_client.bucket.assert_called_with("test-bucket")
        mock_blob.download_to_filename.assert_called_once()
    
    @patch('services.video_editing_service.tempfile.NamedTemporaryFile')
    def test_download_video_from_gcs_https_url(self, mock_tempfile, service):
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_video.mp4"
        mock_temp.__enter__.return_value = mock_temp
        mock_tempfile.return_value = mock_temp
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        service.storage_client.bucket.return_value = mock_bucket
        
        result = service._download_video_from_gcs("https://storage.googleapis.com/test-bucket/videos/test.mp4")
        
        assert result == "/tmp/test_video.mp4"
        mock_blob.download_to_filename.assert_called_once()
    
    @patch('services.video_editing_service.subprocess.run')
    def test_get_video_dimensions(self, mock_subprocess, service):
        mock_result = Mock()
        mock_result.stdout = "1920,1080\n"
        mock_subprocess.return_value = mock_result
        
        width, height = service._get_video_dimensions("/tmp/test.mp4")
        
        assert width == 1920
        assert height == 1080
        mock_subprocess.assert_called_once()
    
    def test_wrap_text_single_line(self, service):
        result = service._wrap_text("Hello", 1000, 70)
        
        assert len(result) == 1
        assert result[0] == "Hello"
    
    def test_wrap_text_multiple_lines(self, service):
        long_text = "This is a very long text that should be wrapped into multiple lines"
        result = service._wrap_text(long_text, 300, 50)
        
        assert len(result) > 1
        assert all(isinstance(line, str) for line in result)
    
    @patch('services.video_editing_service.open', create=True)
    def test_get_brand_color_found(self, mock_open, service):
        mock_file_data = '[{"videoUrl": "test.mp4", "primary_brand_color": "#FF0000"}]'
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_data
        
        with patch('services.video_editing_service.json.load', return_value=[
            {"videoUrl": "test.mp4", "primary_brand_color": "#FF0000"}
        ]):
            result = service._get_brand_color("test.mp4")
            assert result == "#FF0000"
    
    @patch('services.video_editing_service.open', create=True)
    def test_get_brand_color_not_found(self, mock_open, service):
        with patch('services.video_editing_service.json.load', return_value=[
            {"videoUrl": "other.mp4", "primary_brand_color": "#FF0000"}
        ]):
            result = service._get_brand_color("test.mp4")
            assert result == "#1e1e1e"
    
    @patch('services.video_editing_service.os.unlink')
    @patch('services.video_editing_service.subprocess.run')
    @patch('services.video_editing_service.tempfile.mktemp')
    @patch('services.video_editing_service.tempfile.NamedTemporaryFile')
    def test_add_text_overlay_success(self, mock_tempfile, mock_mktemp, mock_subprocess, mock_unlink, service):
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.txt"
        mock_temp.__enter__.return_value = mock_temp
        mock_tempfile.return_value = mock_temp
        mock_mktemp.return_value = "/tmp/output.mp4"
        
        with patch.object(service, '_download_video_from_gcs', return_value="/tmp/input.mp4"), \
             patch.object(service, '_get_video_dimensions', return_value=(1920, 1080)), \
             patch.object(service, '_get_brand_color', return_value="#1e1e1e"), \
             patch.object(service, '_upload_video_to_gcs', return_value="https://storage.googleapis.com/bucket/output.mp4"), \
             patch('services.video_editing_service.os.path.exists', return_value=True):
            
            result = service.add_text_overlay(
                "gs://bucket/input.mp4",
                "Test Text",
                start_time=0,
                duration=5
            )
            
            assert result["status"] == "success"
            assert "video_url" in result
            mock_subprocess.assert_called_once()
    
    @patch('services.video_editing_service.os.path.exists', return_value=False)
    def test_add_text_overlay_file_not_found(self, mock_exists, service):
        with patch.object(service, '_download_video_from_gcs', return_value="/tmp/missing.mp4"):
            result = service.add_text_overlay(
                "gs://bucket/input.mp4",
                "Test",
                start_time=0,
                duration=5
            )
            
            assert result["status"] == "error"
            assert "not found" in result["message"]
    
    @patch('services.video_editing_service.os.unlink')
    @patch('services.video_editing_service.subprocess.run')
    @patch('services.video_editing_service.tempfile.mktemp')
    def test_add_audio_overlay_success(self, mock_mktemp, mock_subprocess, mock_unlink, service):
        mock_mktemp.return_value = "/tmp/output.mp4"
        
        with patch.object(service, '_download_video_from_gcs', return_value="/tmp/input.mp4"), \
             patch.object(service, '_upload_video_to_gcs', return_value="https://storage.googleapis.com/bucket/output.mp4"), \
             patch('services.video_editing_service.os.path.exists', return_value=True):
            
            result = service.add_audio_overlay(
                "gs://bucket/input.mp4",
                "/tmp/audio.mp3"
            )
            
            assert result["status"] == "success"
            assert "video_url" in result
            mock_subprocess.assert_called_once()
    
    @patch('services.video_editing_service.os.path.exists', return_value=False)
    def test_add_audio_overlay_audio_not_found(self, mock_exists, service):
        with patch.object(service, '_download_video_from_gcs', return_value="/tmp/input.mp4"):
            result = service.add_audio_overlay(
                "gs://bucket/input.mp4",
                "/tmp/missing_audio.mp3"
            )
            
            assert result["status"] == "error"
            assert "Audio file not found" in result["message"]
