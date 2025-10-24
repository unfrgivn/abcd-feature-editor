import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.cloud import storage

logger = logging.getLogger(__name__)


class GcsArtifactService:
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv("GCS_SCRATCH_BUCKET")
        self.project_id = project_id or os.getenv("GCS_PROJECT_ID")
        
        if not self.bucket_name:
            raise ValueError("GCS_SCRATCH_BUCKET environment variable not set")
        if not self.project_id:
            raise ValueError("GCS_PROJECT_ID environment variable not set")
        
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
        logger.info(f"GcsArtifactService initialized for bucket: {self.bucket_name}")
    
    def upload_artifact(
        self,
        file_path: str,
        user_id: str,
        session_id: str,
        artifact_type: str = "video"
    ) -> str:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = file_path_obj.suffix
        blob_name = f"{user_id}/{session_id}/{artifact_type}_{timestamp}{extension}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
        logger.info(f"Uploaded artifact to GCS: {blob_name}")
        return public_url
    
    def upload_from_bytes(
        self,
        data: bytes,
        user_id: str,
        session_id: str,
        artifact_type: str,
        extension: str = ".mp4"
    ) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"{user_id}/{session_id}/{artifact_type}_{timestamp}{extension}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(data)
        
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
        logger.info(f"Uploaded artifact bytes to GCS: {blob_name}")
        return public_url
    
    def download_artifact(self, blob_name: str, destination_path: str):
        blob = self.bucket.blob(blob_name)
        
        dest_path = Path(destination_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        blob.download_to_filename(destination_path)
        logger.info(f"Downloaded artifact from GCS: {blob_name} to {destination_path}")
    
    def download_to_bytes(self, blob_name: str) -> bytes:
        blob = self.bucket.blob(blob_name)
        data = blob.download_as_bytes()
        logger.info(f"Downloaded artifact bytes from GCS: {blob_name}")
        return data
    
    def list_artifacts(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> list[dict]:
        prefix = ""
        if user_id and session_id:
            prefix = f"{user_id}/{session_id}/"
        elif user_id:
            prefix = f"{user_id}/"
        
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        
        artifacts = []
        for blob in blobs:
            artifacts.append({
                "name": blob.name,
                "size": blob.size,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "public_url": f"https://storage.googleapis.com/{self.bucket_name}/{blob.name}"
            })
        
        return artifacts
    
    def delete_artifact(self, blob_name: str):
        blob = self.bucket.blob(blob_name)
        blob.delete()
        logger.info(f"Deleted artifact from GCS: {blob_name}")
    
    def delete_session_artifacts(self, user_id: str, session_id: str):
        prefix = f"{user_id}/{session_id}/"
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        
        count = 0
        for blob in blobs:
            blob.delete()
            count += 1
        
        logger.info(f"Deleted {count} artifacts for session: {user_id}/{session_id}")


def get_gcs_artifact_service() -> GcsArtifactService:
    return GcsArtifactService()
