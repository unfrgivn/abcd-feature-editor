import logging
import os
from pathlib import Path
from typing import Optional

from google.cloud import storage

logger = logging.getLogger(__name__)


class VideoExportService:
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv("GCS_FINAL_BUCKET")
        self.project_id = project_id or os.getenv("GCS_PROJECT_ID")
        
        if not self.bucket_name:
            raise ValueError("GCS_FINAL_BUCKET environment variable not set")
        if not self.project_id:
            raise ValueError("GCS_PROJECT_ID environment variable not set")
        
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        logger.info(f"VideoExportService initialized for bucket: {self.bucket_name}")
    
    def export_video(
        self,
        video_path: str,
        user_id: str,
        feature_id: str,
        video_id: str
    ) -> str:
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        extension = video_path_obj.suffix
        blob_name = f"{user_id}/{feature_id}/{video_id}{extension}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(video_path)
        
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
        logger.info(f"Exported video to GCS: {blob_name}")
        return public_url
    
    def export_video_from_bytes(
        self,
        video_data: bytes,
        user_id: str,
        feature_id: str,
        video_id: str,
        extension: str = ".mp4"
    ) -> str:
        blob_name = f"{user_id}/{feature_id}/{video_id}{extension}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(video_data)
        
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
        logger.info(f"Exported video bytes to GCS: {blob_name}")
        return public_url
    
    def list_exported_videos(
        self,
        user_id: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> list[dict]:
        prefix = ""
        if user_id and feature_id:
            prefix = f"{user_id}/{feature_id}/"
        elif user_id:
            prefix = f"{user_id}/"
        
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        
        videos = []
        for blob in blobs:
            videos.append({
                "name": blob.name,
                "size": blob.size,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "public_url": f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}"
            })
        
        return videos
    
    def delete_video(self, blob_name: str):
        blob = self.bucket.blob(blob_name)
        blob.delete()
        logger.info(f"Deleted video from GCS: {blob_name}")


def get_video_export_service() -> VideoExportService:
    return VideoExportService()
