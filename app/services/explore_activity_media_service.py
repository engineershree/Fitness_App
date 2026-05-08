import os
import uuid
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from pathlib import Path
import io

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 35 * 1024 * 1024  # 35 MB

class ExploreActivityMediaService:
    def __init__(self):
        self.base_folder = os.getenv("CLOUDINARY_BASE_FOLDER", "fitness-app")
        self.image_upload_folder = f"{self.base_folder}/explore_activity/image"
        self.video_upload_folder = f"{self.base_folder}/explore_activity/video"

    def validate_image(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format. Allowed formats: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )

        # Check file size
        if file.size and file.size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image size exceeds maximum limit of {MAX_IMAGE_SIZE // (1024 * 1024)}MB"
            )

    def validate_video(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid video format. Allowed formats: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
            )

        # Check file size
        if file.size and file.size > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Video size exceeds maximum limit of {MAX_VIDEO_SIZE // (1024 * 1024)}MB"
            )

    async def save_activity_image(self, file: UploadFile, activity_id: int, activity_name: str) -> str:
        self.validate_image(file)

        # Generate unique public ID for Cloudinary (add timestamp to avoid overwriting)
        import time
        file_extension = Path(file.filename).suffix.lower()
        # Sanitize activity name for filename
        sanitized_name = "".join(c for c in activity_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        sanitized_name = sanitized_name.replace(' ', '_')
        timestamp = int(time.time())
        public_id = f"{activity_id}_{sanitized_name}_{timestamp}"

        try:
            # Read and validate image content
            content = await file.read()

            # Validate it's actually an image
            try:
                Image.open(io.BytesIO(content))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid image file")

            # Reset file pointer
            await file.seek(0)

            # Upload to Cloudinary (no overwrite to create new image)
            upload_result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                folder=self.image_upload_folder,
                resource_type="image",
                format=file_extension.replace(".", ""),
                overwrite=False
            )

            # Return the secure URL
            return upload_result["secure_url"]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image to Cloudinary: {str(e)}")

    async def save_activity_video(self, file: UploadFile, activity_id: int, activity_name: str) -> str:
        self.validate_video(file)

        # Generate unique public ID for Cloudinary (add timestamp to avoid overwriting)
        import time
        file_extension = Path(file.filename).suffix.lower()
        # Sanitize activity name for filename
        sanitized_name = "".join(c for c in activity_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        sanitized_name = sanitized_name.replace(' ', '_')
        timestamp = int(time.time())
        public_id = f"{activity_id}_{sanitized_name}_{timestamp}"

        try:
            # Read video content
            content = await file.read()

            # Reset file pointer
            await file.seek(0)

            # Upload to Cloudinary (no overwrite to create new video)
            upload_result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                folder=self.video_upload_folder,
                resource_type="video",
                format=file_extension.replace(".", ""),
                overwrite=False,
                timeout=60,  # 60 second timeout
                chunk_size=6000000  # 6MB chunks for large files
            )

            # Return the secure URL
            return upload_result["secure_url"]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload video to Cloudinary: {str(e)}")

    async def save_activity_media(self, image_file: Optional[UploadFile] = None, 
                                video_file: Optional[UploadFile] = None,
                                activity_id: int = None, 
                                activity_name: str = None) -> Tuple[Optional[str], Optional[str]]:
        image_path = None
        video_path = None

        if image_file and activity_id and activity_name:
            image_path = await self.save_activity_image(image_file, activity_id, activity_name)

        if video_file and activity_id and activity_name:
            video_path = await self.save_activity_video(video_file, activity_id, activity_name)

        return image_path, video_path

    def delete_old_activity_media(self, old_image_url: Optional[str], old_video_url: Optional[str]) -> None:
        # Delete old image from Cloudinary
        if old_image_url and "cloudinary" in old_image_url:
            try:
                # Extract public_id from Cloudinary URL
                parts = old_image_url.split('/')
                if len(parts) >= 8:
                    upload_index = parts.index('upload')
                    folder_and_public_id = '/'.join(parts[upload_index+2:])
                    public_id = folder_and_public_id.rsplit('.', 1)[0]
                    cloudinary.uploader.destroy(public_id, resource_type="image")
            except Exception:
                pass

        # Delete old video from Cloudinary
        if old_video_url and "cloudinary" in old_video_url:
            try:
                # Extract public_id from Cloudinary URL
                parts = old_video_url.split('/')
                if len(parts) >= 8:
                    upload_index = parts.index('upload')
                    folder_and_public_id = '/'.join(parts[upload_index+2:])
                    public_id = folder_and_public_id.rsplit('.', 1)[0]
                    cloudinary.uploader.destroy(public_id, resource_type="video")
            except Exception:
                pass
