import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.core.permissions import Role
from app.api.dependencies import require_roles

router = APIRouter(prefix="/upload", tags=["Uploads"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload an image file from the computer and return its static URL.
    Validates file extension, MIME type, and strictly limits file size to 10MB.
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
    
    unique_name = f"{uuid.uuid4().hex}{ext}"
    destination = os.path.join(UPLOAD_DIR, unique_name)
    total_bytes = 0
    
    try:
        with open(destination, "wb") as buffer:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    buffer.close()
                    if os.path.exists(destination):
                        os.remove(destination)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of 10MB ({round(total_bytes / (1024*1024), 2)}MB)"
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(destination):
            try:
                os.remove(destination)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    finally:
        await file.close()

    file_url = f"/uploads/{unique_name}"
    return {
        "url": file_url,
        "filename": filename,
        "size": os.path.getsize(destination)
    }
