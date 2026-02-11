"""
Image upload routes for CollectorStream API
Handles card image uploads to S3 or local storage
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import boto3
import os
import uuid
from datetime import datetime
from PIL import Image
import io

from auth import get_current_user

router = APIRouter()

# S3 Configuration
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "collectorstream-cards")
S3_BASE_URL = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com"

# Local storage fallback
LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

# ============================================================================
# Pydantic Models
# ============================================================================

class ImageUploadResponse(BaseModel):
    url: str
    thumbnailUrl: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def get_s3_client():
    """Get S3 client if configured."""
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        return None

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

def generate_filename(user_id: str, side: str, extension: str = "jpg") -> str:
    """Generate a unique filename for the image."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"cards/{user_id}/{timestamp}_{unique_id}_{side}.{extension}"

def create_thumbnail(image_data: bytes, max_size: tuple = (200, 280)) -> bytes:
    """Create a thumbnail from image data."""
    image = Image.open(io.BytesIO(image_data))

    # Convert to RGB if necessary
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Calculate aspect ratio
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85)
    return output.getvalue()

async def upload_to_s3(s3_client, image_data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """Upload image to S3 and return URL."""
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=filename,
        Body=image_data,
        ContentType=content_type,
        ACL="public-read"
    )
    return f"{S3_BASE_URL}/{filename}"

async def upload_locally(image_data: bytes, filename: str) -> str:
    """Upload image to local storage and return URL."""
    # Create directory structure
    full_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Write file
    with open(full_path, "wb") as f:
        f.write(image_data)

    # Return absolute URL with API base
    api_base = os.environ.get("API_BASE_URL", "https://api.collectorstream.com")
    return f"{api_base}/uploads/{filename}"

# ============================================================================
# Routes
# ============================================================================

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    image: UploadFile = File(...),
    side: str = Form(...),  # "front" or "back"
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a card image.

    - **image**: The image file (JPEG, PNG)
    - **side**: Which side of the card ("front" or "back")
    """
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read image data
    image_data = await image.read()

    # Validate file size (max 10MB)
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    # Generate filename
    extension = "jpg"
    if image.content_type == "image/png":
        extension = "png"

    filename = generate_filename(current_user["id"], side, extension)
    thumbnail_filename = filename.replace(f".{extension}", f"_thumb.jpg")

    # Create thumbnail
    try:
        thumbnail_data = create_thumbnail(image_data)
    except Exception as e:
        print(f"Thumbnail creation failed: {e}")
        thumbnail_data = None

    # Upload to S3 or local storage
    s3_client = get_s3_client()

    if s3_client:
        # Upload to S3
        try:
            url = await upload_to_s3(s3_client, image_data, filename, image.content_type)
            thumbnail_url = None

            if thumbnail_data:
                thumbnail_url = await upload_to_s3(s3_client, thumbnail_data, thumbnail_filename)

            return ImageUploadResponse(url=url, thumbnailUrl=thumbnail_url)
        except Exception as e:
            print(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail="Image upload failed")
    else:
        # Upload locally
        try:
            url = await upload_locally(image_data, filename)
            thumbnail_url = None

            if thumbnail_data:
                thumbnail_url = await upload_locally(thumbnail_data, thumbnail_filename)

            return ImageUploadResponse(url=url, thumbnailUrl=thumbnail_url)
        except Exception as e:
            print(f"Local upload failed: {e}")
            raise HTTPException(status_code=500, detail="Image upload failed")

@router.delete("/{filename:path}")
async def delete_image(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an uploaded image."""
    # Verify the user owns this image
    if f"/{current_user['id']}/" not in filename:
        raise HTTPException(status_code=403, detail="Access denied")

    s3_client = get_s3_client()

    if s3_client:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=filename)
            # Also delete thumbnail if exists
            thumbnail_key = filename.replace(".jpg", "_thumb.jpg").replace(".png", "_thumb.jpg")
            s3_client.delete_object(Bucket=S3_BUCKET, Key=thumbnail_key)
        except Exception as e:
            print(f"S3 delete failed: {e}")
    else:
        # Delete locally
        full_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
        if os.path.exists(full_path):
            os.remove(full_path)

        thumbnail_path = full_path.replace(".jpg", "_thumb.jpg").replace(".png", "_thumb.jpg")
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

    return {"message": "Image deleted"}
