import os
import io
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import cloudinary
import cloudinary.uploader
import cloudinary.exceptions

from app.core.config import settings
from app.core.permissions import Role
from app.api.dependencies import require_roles
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Uploads"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def sanitize_message(msg: str) -> str:
    """Masks any sensitive credentials from error messages or logs."""
    if not msg:
        return "Unknown error"
    if settings.CLOUDINARY_API_SECRET and settings.CLOUDINARY_API_SECRET in msg:
        msg = msg.replace(settings.CLOUDINARY_API_SECRET, "[MASKED]")
    if settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_KEY in msg:
        msg = msg.replace(settings.CLOUDINARY_API_KEY, "[MASKED]")
    return msg


def validate_image_header(data: bytes, ext: str) -> bool:
    """
    Validates magic bytes to ensure file content matches the claimed image extension.
    Permits minimal valid mock payloads in tests if starting with recognized signatures.
    """
    if len(data) < 3:
        return False
    if ext in [".jpg", ".jpeg"]:
        return data.startswith(b"\xff\xd8\xff")
    if ext == ".png":
        return data.startswith(b"\x89PNG")
    if ext == ".gif":
        return data.startswith(b"GIF87a") or data.startswith(b"GIF89a")
    if ext == ".webp":
        return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return True


def init_cloudinary():
    """Initializes Cloudinary configuration with strict HTTPS transport."""
    if settings.is_cloudinary_configured:
        cloudinary.config(
            cloud_name=settings.clean_cloudinary_cloud_name,
            api_key=settings.clean_cloudinary_api_key,
            api_secret=settings.clean_cloudinary_api_secret,
            secure=True
        )


@router.post("", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def upload_file(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    """
    Upload an image file from the computer and return its HTTPS URL and public ID.
    Validates file extension, MIME type, magic bytes, and enforces a strict 10MB size limit.
    If Cloudinary credentials are configured, securely stores image in Cloudinary and
    persists public ID and HTTPS URL in MongoDB. Otherwise, falls back to local uploads.
    """
    filename = file.filename or "image.jpg"
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file.content_type and file.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME content type '{file.content_type}'. Allowed image types: jpeg, png, webp, gif"
        )

    # Read content in chunks to strictly enforce 10MB limit
    file_bytes = bytearray()
    try:
        reader = file.file
        while True:
            chunk = reader.read(64 * 1024)
            if not chunk:
                break
            file_bytes.extend(chunk)
            if len(file_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                    detail=f"File exceeds maximum allowed size of 10MB ({round(len(file_bytes) / (1024*1024), 2)}MB)"
                )
    finally:
        try:
            file.file.close()
        except Exception:
            pass

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    if not validate_image_header(bytes(file_bytes), ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content does not match image extension '{ext}'"
        )

    # Upload via Cloudinary if configured, else fall back to local disk
    if settings.is_cloudinary_configured:
        init_cloudinary()
        try:
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(file_bytes),
                folder=settings.clean_cloudinary_folder,
                resource_type="image",
                use_filename=True,
                unique_filename=True,
                overwrite=False
            )
            file_url = upload_result.get("secure_url") or upload_result.get("url")
            public_id = upload_result.get("public_id")
            total_size = upload_result.get("bytes", len(file_bytes))
            provider = "cloudinary"
        except cloudinary.exceptions.Error as ce:
            logger.error("Cloudinary SDK error during upload: %s", sanitize_message(str(ce)))
            clean_err = sanitize_message(str(ce))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Cloudinary upload failed: {clean_err}"
            )
        except Exception as e:
            logger.error("Unexpected error during Cloudinary upload: %s", sanitize_message(str(e)))
            clean_err = sanitize_message(str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process image upload: {clean_err}"
            )
    else:
        unique_name = f"{uuid.uuid4().hex}{ext}"
        destination = os.path.join(UPLOAD_DIR, unique_name)
        try:
            with open(destination, "wb") as buffer:
                buffer.write(file_bytes)
        except Exception as e:
            logger.error("Failed to write local file: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save local file: {str(e)}"
            )
        file_url = f"/uploads/{unique_name}"
        public_id = unique_name
        total_size = len(file_bytes)
        provider = "local"

    # Persist media asset details in MongoDB
    if db is not None:
        try:
            asset_doc = {
                "public_id": public_id,
                "url": file_url,
                "secure_url": file_url,
                "filename": filename,
                "format": ext.lstrip("."),
                "size": total_size,
                "provider": provider,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            db.media_assets.insert_one(asset_doc)
        except Exception as dbe:
            logger.warning("Failed to store media asset metadata in MongoDB: %s", str(dbe))

    return {
        "url": file_url,
        "public_id": public_id,
        "filename": filename,
        "size": total_size
    }
