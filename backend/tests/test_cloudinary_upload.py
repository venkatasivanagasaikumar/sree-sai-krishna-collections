import io
import os
from unittest.mock import patch
import pytest
from fastapi import HTTPException, UploadFile
import cloudinary.exceptions

from app.core.config import settings
from app.database import get_db, db_manager
from app.api.v1.upload import upload_file, sanitize_message, validate_image_header
from app.api.v1.products import create_product
from app.schemas.product import ProductCreate

# Sample valid image headers
JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 50
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
WEBP_HEADER = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 50
GIF_HEADER = b"GIF89a\x01\x00\x01\x00\x80\x00\x00" + b"\x00" * 50


def make_upload_file(content: bytes, filename: str, content_type: str) -> UploadFile:
    """Helper to instantiate a valid FastAPI UploadFile for testing."""
    return UploadFile(
        file=io.BytesIO(content),
        filename=filename,
        headers={"content-type": content_type}
    )


def test_upload_validation_disallowed_extension():
    """Uploads with disallowed file extensions (.exe, .pdf, .sh) must return 400 Bad Request."""
    db = get_db()
    for bad_name, bad_type in [
        ("malicious.exe", "image/jpeg"),
        ("document.pdf", "image/png"),
        ("script.sh", "image/jpeg"),
        ("photo.bmp", "image/jpeg")
    ]:
        uf = make_upload_file(JPEG_HEADER, bad_name, bad_type)
        with pytest.raises(HTTPException) as exc_info:
            upload_file(file=uf, db=db)
        assert exc_info.value.status_code == 400
        assert "Unsupported file format" in exc_info.value.detail


def test_upload_validation_disallowed_mime_type():
    """Uploads with mismatched or disallowed MIME types must return 400 Bad Request."""
    db = get_db()
    for bad_mime in ["application/pdf", "text/plain", "application/octet-stream", "video/mp4"]:
        uf = make_upload_file(JPEG_HEADER, "valid.jpg", bad_mime)
        with pytest.raises(HTTPException) as exc_info:
            upload_file(file=uf, db=db)
        assert exc_info.value.status_code == 400
        assert "Invalid MIME content type" in exc_info.value.detail


def test_upload_validation_empty_file():
    """Empty files must return 400 Bad Request."""
    db = get_db()
    uf = make_upload_file(b"", "empty.jpg", "image/jpeg")
    with pytest.raises(HTTPException) as exc_info:
        upload_file(file=uf, db=db)
    assert exc_info.value.status_code == 400
    assert "Uploaded file is empty" in exc_info.value.detail


def test_upload_validation_mismatched_magic_bytes():
    """Files with mismatched headers (e.g. text masquerading as PNG) must return 400 Bad Request."""
    db = get_db()
    fake_png = b"THIS_IS_PLAIN_TEXT_NOT_A_PNG_FILE_HEADER"
    uf = make_upload_file(fake_png, "fake.png", "image/png")
    with pytest.raises(HTTPException) as exc_info:
        upload_file(file=uf, db=db)
    assert exc_info.value.status_code == 400
    assert "File content does not match image extension" in exc_info.value.detail


def test_upload_validation_oversized_file():
    """Files exceeding 10MB limit must raise 413 Request Entity Too Large."""
    db = get_db()
    # 10MB + 1KB
    oversized_bytes = JPEG_HEADER + (b"\x00" * (10 * 1024 * 1024 + 1024))
    uf = make_upload_file(oversized_bytes, "huge.jpg", "image/jpeg")
    with pytest.raises(HTTPException) as exc_info:
        upload_file(file=uf, db=db)
    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed size of 10MB" in exc_info.value.detail


def test_successful_cloudinary_upload_and_db_persistence():
    """
    Verifies that when Cloudinary is configured:
    1. The upload is processed via Cloudinary SDK.
    2. Returned HTTPS URL, public ID, filename and size match expected values.
    3. The media record is persisted into MongoDB db.media_assets.
    4. Products referencing the uploaded image URL link the Cloudinary public ID.
    """
    db = get_db()
    
    # Configure mock Cloudinary settings
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET
    settings.CLOUDINARY_CLOUD_NAME = "ssk-test-cloud"
    settings.CLOUDINARY_API_KEY = "987654321012345"
    settings.CLOUDINARY_API_SECRET = "ssk_mock_secret_key_prod_test"

    mock_cloudinary_response = {
        "public_id": "products/ssk_choker_bridal_01",
        "secure_url": "https://res.cloudinary.com/ssk-test-cloud/image/upload/v1731000000/products/ssk_choker_bridal_01.jpg",
        "url": "http://res.cloudinary.com/ssk-test-cloud/image/upload/v1731000000/products/ssk_choker_bridal_01.jpg",
        "bytes": 2048,
        "format": "jpg",
        "resource_type": "image"
    }

    try:
        with patch("cloudinary.uploader.upload", return_value=mock_cloudinary_response) as mock_upload, \
             patch.object(db_manager, "persist_to_disk"):
            uf = make_upload_file(JPEG_HEADER, "choker.jpg", "image/jpeg")
            res = upload_file(file=uf, db=db)

            # 1. Assert upload SDK called
            mock_upload.assert_called_once()

            # 2. Assert response structure matches frontend expectations
            assert res["url"] == "https://res.cloudinary.com/ssk-test-cloud/image/upload/v1731000000/products/ssk_choker_bridal_01.jpg"
            assert res["public_id"] == "products/ssk_choker_bridal_01"
            assert res["filename"] == "choker.jpg"
            assert res["size"] == 2048

            # 3. Assert persisted in MongoDB db.media_assets
            asset = db.media_assets.find_one({"public_id": "products/ssk_choker_bridal_01"})
            assert asset is not None
            assert asset["url"] == res["url"]
            assert asset["secure_url"].startswith("https://")
            assert asset["provider"] == "cloudinary"
            assert asset["filename"] == "choker.jpg"

            # 4. Assert linking when product is created
            test_sku = "SSK-CLD-TEST-99"
            db.products.delete_one({"sku": test_sku})
            prod_dto = ProductCreate(
                name="Cloudinary Linked Choker",
                sku=test_sku,
                category="1-Gram Gold Jewellery",
                description="Test product with Cloudinary image",
                mrp=2500.0,
                price=1800.0,
                stock=10,
                materials_and_finish="Brass with 1-gram gold polish",
                images=[res["url"]]
            )
            created = create_product(payload=prod_dto, db=db)
            saved_prod = db.products.find_one({"_id": created["id"]}) or db.products.find_one({"id": created["id"]})
            assert saved_prod is not None
            assert "products/ssk_choker_bridal_01" in saved_prod.get("cloudinary_public_ids", [])
            db.products.delete_one({"sku": test_sku})
    finally:
        db.media_assets.delete_many({"public_id": "products/ssk_choker_bridal_01"})
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_cloudinary_upload_failure_error_handling():
    """Verifies that Cloudinary SDK errors return HTTP 502 with sanitized error details."""
    db = get_db()
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET
    settings.CLOUDINARY_CLOUD_NAME = "ssk-test-cloud"
    settings.CLOUDINARY_API_KEY = "987654321012345"
    settings.CLOUDINARY_API_SECRET = "ssk_mock_secret_key_prod_test"

    try:
        with patch("cloudinary.uploader.upload", side_effect=cloudinary.exceptions.Error("Upload rate limit exceeded")):
            uf = make_upload_file(JPEG_HEADER, "rate_limited.jpg", "image/jpeg")
            with pytest.raises(HTTPException) as exc_info:
                upload_file(file=uf, db=db)
            assert exc_info.value.status_code == 502
            assert "Upload rate limit exceeded" in exc_info.value.detail
    finally:
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_cloudinary_secret_masking_in_error_handling():
    """Verifies that API secrets are masked and NEVER leaked in error responses or logs."""
    db = get_db()
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET
    secret_val = "SUPER_SECRET_CLOUDINARY_TOKEN_2026"
    settings.CLOUDINARY_CLOUD_NAME = "ssk-test-cloud"
    settings.CLOUDINARY_API_KEY = "987654321012345"
    settings.CLOUDINARY_API_SECRET = secret_val

    try:
        leak_attempt = f"Failed authorization with secret: {secret_val} from provider"
        with patch("cloudinary.uploader.upload", side_effect=cloudinary.exceptions.Error(leak_attempt)):
            uf = make_upload_file(JPEG_HEADER, "leak_test.jpg", "image/jpeg")
            with pytest.raises(HTTPException) as exc_info:
                upload_file(file=uf, db=db)
            assert secret_val not in exc_info.value.detail
            assert "[MASKED]" in exc_info.value.detail
    finally:
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_fallback_to_local_when_cloudinary_unconfigured():
    """When Cloudinary is unconfigured, system safely falls back to local disk and logs media asset."""
    db = get_db()
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET
    settings.CLOUDINARY_CLOUD_NAME = ""
    settings.CLOUDINARY_API_KEY = ""
    settings.CLOUDINARY_API_SECRET = ""

    try:
        uf = make_upload_file(PNG_HEADER, "fallback.png", "image/png")
        res = upload_file(file=uf, db=db)
        assert res["url"].startswith("/uploads/")
        assert res["filename"] == "fallback.png"
        assert res["size"] == len(PNG_HEADER)

        # Check local media asset record in MongoDB
        asset = db.media_assets.find_one({"public_id": res["public_id"]})
        assert asset is not None
        assert asset["provider"] == "local"
        assert asset["url"] == res["url"]
    finally:
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_cloudinary_production_readiness_validation():
    """Verifies that validate_production_readiness blocks partial Cloudinary credentials."""
    orig_env = settings.ENVIRONMENT
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET

    settings.ENVIRONMENT = "production"
    try:
        # Partial credentials: Cloud name provided, secret missing
        settings.CLOUDINARY_CLOUD_NAME = "ssk-cloud"
        settings.CLOUDINARY_API_KEY = "12345"
        settings.CLOUDINARY_API_SECRET = ""
        blockers = settings.validate_production_readiness()
        assert any("Cloudinary configuration is incomplete" in b for b in blockers)

        # Full credentials provided
        settings.CLOUDINARY_API_SECRET = "secure_secret_123"
        blockers = settings.validate_production_readiness()
        assert not any("Cloudinary configuration is incomplete" in b for b in blockers)

        # Masked asterisks provided
        settings.CLOUDINARY_API_SECRET = "**********"
        blockers = settings.validate_production_readiness()
        assert any("CLOUDINARY_API_SECRET is set to masked asterisks" in b for b in blockers)
    finally:
        settings.ENVIRONMENT = orig_env
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_cloudinary_signature_generation_and_mask_detection():
    """
    Verifies official Cloudinary SDK signature calculation.
    Demonstrates that using masked asterisks ('**********') causes signature mismatch.
    """
    import cloudinary.utils

    upload_params = {
        "folder": "products",
        "overwrite": False,
        "timestamp": 1731000000,
        "unique_filename": True,
        "use_filename": True
    }
    expected_string_to_sign = "folder=products&overwrite=0&timestamp=1731000000&unique_filename=1&use_filename=1"
    
    # 1. Official SDK parameter cleanup and string-to-sign generation
    cleaned_params = cloudinary.utils.cleanup_params(upload_params)
    actual_string_to_sign = cloudinary.utils.api_string_to_sign(cleaned_params)
    assert actual_string_to_sign == expected_string_to_sign

    # 2. Genuine secret signs properly
    genuine_secret = "my_actual_cloudinary_secret_key_123"
    valid_sig = cloudinary.utils.api_sign_request(cleaned_params, genuine_secret)
    assert isinstance(valid_sig, str) and len(valid_sig) == 40

    # 3. Masked secret produces invalid/mismatched signature
    masked_secret = "**********"
    invalid_sig = cloudinary.utils.api_sign_request(cleaned_params, masked_secret)
    assert invalid_sig != valid_sig


def test_cloudinary_config_cleaning_and_whitespace_sanitization():
    """Verifies that quotes, whitespace, and mask placeholders are cleaned and rejected."""
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET
    orig_folder = settings.CLOUDINARY_FOLDER

    try:
        # Whitespace and quotation stripping
        settings.CLOUDINARY_CLOUD_NAME = '  "ssk-cloud"  '
        settings.CLOUDINARY_API_KEY = " '123456789012345' "
        settings.CLOUDINARY_API_SECRET = ' "valid_secret_9988" '
        settings.CLOUDINARY_FOLDER = " 'products' "

        assert settings.clean_cloudinary_cloud_name == "ssk-cloud"
        assert settings.clean_cloudinary_api_key == "123456789012345"
        assert settings.clean_cloudinary_api_secret == "valid_secret_9988"
        assert settings.clean_cloudinary_folder == "products"
        assert settings.is_cloudinary_configured is True

        # Mask placeholder rejection
        settings.CLOUDINARY_API_SECRET = "**********"
        assert settings.is_cloudinary_configured is False
    finally:
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret
        settings.CLOUDINARY_FOLDER = orig_folder
