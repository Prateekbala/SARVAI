from minio import Minio
from minio.error import S3Error
from typing import BinaryIO, Optional
from uuid import UUID
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

class MinIOService:
    """Service for managing file storage in MinIO"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        user_id: UUID,
        content_type: str,
        filename: str,
        content_type_header: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO
        
        Args:
            file_data: File binary data
            user_id: User UUID
            content_type: Memory content type (image, pdf, audio)
            filename: Original filename
            content_type_header: MIME type
            
        Returns:
            Object path in MinIO
        """
        try:
            # Construct object path: user_id/content_type/filename
            object_path = f"{user_id}/{content_type}s/{filename}"
            
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_path,
                data=file_data,
                length=file_size,
                content_type=content_type_header
            )
            
            logger.info(f"Uploaded file to MinIO: {object_path}")
            return object_path
            
        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def download_file(self, object_path: str) -> bytes:
        """
        Download file from MinIO
        
        Args:
            object_path: Path to object in MinIO
            
        Returns:
            File binary data
        """
        try:
            response = self.client.get_object(self.bucket, object_path)
            data = response.read()
            response.close()
            response.release_conn()
            return data
            
        except S3Error as e:
            logger.error(f"MinIO download failed: {e}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    def delete_file(self, object_path: str) -> bool:
        """
        Delete file from MinIO
        
        Args:
            object_path: Path to object in MinIO
            
        Returns:
            True if successful
        """
        try:
            self.client.remove_object(self.bucket, object_path)
            logger.info(f"Deleted file from MinIO: {object_path}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO delete failed: {e}")
            return False
    
    def get_file_url(self, object_path: str, expires_in: int = 3600) -> str:
        """
        Get presigned URL for file access
        
        Args:
            object_path: Path to object in MinIO
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket, 
                object_path,
                expires=expires_in
            )
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate file URL: {str(e)}")
    
    def file_exists(self, object_path: str) -> bool:
        """Check if file exists in MinIO"""
        try:
            self.client.stat_object(self.bucket, object_path)
            return True
        except S3Error:
            return False

# Global instance
minio_service = MinIOService()
