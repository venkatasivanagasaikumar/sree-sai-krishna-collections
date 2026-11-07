import os
import io
import pytest
from unittest.mock import patch
from fastapi import HTTPException, UploadFile

from app.core.config import settings, is_secret_key_secure, verify_production_secret_key
from app.core.security import get_password_hash, verify_password
from app.database import get_db, db_manager
from app.api.v1.upload import upload_file, UPLOAD_DIR
from app.seeds.seed_data import run_seed

VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"


def make_upload_file(data: bytes, filename: str, content_type: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename=filename,
        headers={"content-type": content_type}
    )


# ==============================================================================
# Task 1: SECRET_KEY Production Security Tests
# ==============================================================================

def test_is_secret_key_secure_validation():
    """Verifies that is_secret_key_secure accurately rejects weak or default secrets."""
    # Empty or whitespace
    assert is_secret_key_secure("")[0] is False
    assert is_secret_key_secure("   ")[0] is False
    assert is_secret_key_secure(None)[0] is False

    # Below 32 characters
    assert is_secret_key_secure("short_key_123")[0] is False
    assert is_secret_key_secure("1234567890123456789012345678901")[0] is False  # 31 chars

    # Insecure default / demo patterns
    assert is_secret_key_secure("ssk-royal-navy-gold-super-secure-jwt-secret-key-2026-prod")[0] is False
    assert is_secret_key_secure("REPLACE_WITH_OPENSSL_RAND_HEX_32_GENERATED_SECRET")[0] is False
    assert is_secret_key_secure("generate_with_openssl_rand_hex_32")[0] is False
    assert is_secret_key_secure("super_secret_changeme_key_for_testing_purposes")[0] is False
    assert is_secret_key_secure("my_admin_password_12345678901234567890")[0] is False

    # Insufficient character entropy
    assert is_secret_key_secure("a" * 64)[0] is False
    assert is_secret_key_secure("12121212121212121212121212121212")[0] is False

    # Valid cryptographically strong secret (e.g. openssl rand -hex 32)
    valid_secret = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
    is_valid, err = is_secret_key_secure(valid_secret)
    assert is_valid is True
    assert err == ""


def test_verify_production_secret_key_enforcement():
    """Verifies that verify_production_secret_key enforces strong secrets in production and permits dev defaults."""
    # 1. In production: default development key raises RuntimeError
    insecure_default = "ssk-royal-navy-gold-super-secure-jwt-secret-key-2026-prod"
    with pytest.raises(RuntimeError) as exc:
        verify_production_secret_key(insecure_default, environment="production")
    assert "CRITICAL MISCONFIGURATION: Insecure SECRET_KEY in production" in str(exc.value)
    # The secret value itself must NEVER be exposed in the error message
    assert insecure_default not in str(exc.value)

    # 2. In production: short key raises RuntimeError
    with pytest.raises(RuntimeError) as exc_short:
        verify_production_secret_key("too_short_key", environment="production")
    assert "below the required 32-character minimum" in str(exc_short.value)

    # 3. In production: valid 64-character secret passes cleanly
    strong_secret = "f7e8d9c0b1a203948576a1b2c3d4e5f6f7e8d9c0b1a203948576a1b2c3d4e5f6"
    verify_production_secret_key(strong_secret, environment="production")

    # 4. In development: default development key passes without raising
    verify_production_secret_key(insecure_default, environment="development")


def test_validate_production_readiness_secret_key_integration():
    """Verifies that Settings.validate_production_readiness integrates the strict SECRET_KEY check."""
    orig_env = settings.ENVIRONMENT
    orig_sec = settings.SECRET_KEY

    try:
        settings.ENVIRONMENT = "production"

        # Insecure key -> flagged as blocker
        settings.SECRET_KEY = "ssk-royal-navy-gold-super-secure-jwt-secret-key-2026-prod"
        blockers = settings.validate_production_readiness()
        assert any("SECRET_KEY is insecure for production" in b for b in blockers)

        # Strong key -> not flagged
        settings.SECRET_KEY = "f7e8d9c0b1a203948576a1b2c3d4e5f6f7e8d9c0b1a203948576a1b2c3d4e5f6"
        blockers = settings.validate_production_readiness()
        assert not any("SECRET_KEY is insecure for production" in b for b in blockers)
    finally:
        settings.ENVIRONMENT = orig_env
        settings.SECRET_KEY = orig_sec


# ==============================================================================
# Task 2: Cloudinary Production Upload & Local Fallback Disabling Tests
# ==============================================================================

def test_production_rejects_upload_when_cloudinary_unconfigured():
    """Verifies that in production, missing Cloudinary credentials raises HTTP 503 and never saves to disk."""
    db = get_db()
    orig_env = settings.ENVIRONMENT
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET

    settings.ENVIRONMENT = "production"
    settings.CLOUDINARY_CLOUD_NAME = ""
    settings.CLOUDINARY_API_KEY = ""
    settings.CLOUDINARY_API_SECRET = ""

    existing_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()

    try:
        uf = make_upload_file(VALID_PNG_BYTES, "prod_test.png", "image/png")
        with pytest.raises(HTTPException) as exc:
            upload_file(file=uf, db=db)
        assert exc.value.status_code == 503
        assert "Local storage fallback is disabled in production" in exc.value.detail

        # Confirm no file was created on local disk
        current_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()
        assert current_files == existing_files
    finally:
        settings.ENVIRONMENT = orig_env
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_production_cloudinary_failure_returns_safe_http_error_without_local_save():
    """Verifies that in production, Cloudinary SDK failure raises 502 and does NOT write to local disk."""
    import cloudinary.exceptions

    db = get_db()
    orig_env = settings.ENVIRONMENT
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET

    settings.ENVIRONMENT = "production"
    settings.CLOUDINARY_CLOUD_NAME = "ssk-live-cloud"
    settings.CLOUDINARY_API_KEY = "123456789012345"
    settings.CLOUDINARY_API_SECRET = "strong_prod_secret_12345"

    existing_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()

    try:
        with patch("cloudinary.uploader.upload", side_effect=cloudinary.exceptions.Error("Upload service timeout")):
            uf = make_upload_file(VALID_PNG_BYTES, "prod_fail.png", "image/png")
            with pytest.raises(HTTPException) as exc:
                upload_file(file=uf, db=db)
            assert exc.value.status_code == 502
            assert "Cloudinary upload failed" in exc.value.detail

        # Confirm no file was created on local disk
        current_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()
        assert current_files == existing_files
    finally:
        settings.ENVIRONMENT = orig_env
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


def test_development_maintains_local_upload_fallback():
    """Verifies development environment still supports local disk fallback when Cloudinary is not configured."""
    orig_env = settings.ENVIRONMENT
    orig_cloud = settings.CLOUDINARY_CLOUD_NAME
    orig_key = settings.CLOUDINARY_API_KEY
    orig_secret = settings.CLOUDINARY_API_SECRET

    settings.ENVIRONMENT = "development"
    settings.CLOUDINARY_CLOUD_NAME = ""
    settings.CLOUDINARY_API_KEY = ""
    settings.CLOUDINARY_API_SECRET = ""

    db = get_db()
    created_path = None

    try:
        uf = make_upload_file(VALID_PNG_BYTES, "dev_fallback.png", "image/png")
        res = upload_file(file=uf, db=db)
        assert res["url"].startswith("/uploads/")
        created_path = os.path.join(UPLOAD_DIR, os.path.basename(res["url"]))
        assert os.path.exists(created_path)
    finally:
        if created_path and os.path.exists(created_path):
            try:
                os.remove(created_path)
            except Exception:
                pass
        settings.ENVIRONMENT = orig_env
        settings.CLOUDINARY_CLOUD_NAME = orig_cloud
        settings.CLOUDINARY_API_KEY = orig_key
        settings.CLOUDINARY_API_SECRET = orig_secret


# ==============================================================================
# Task 3: Administrator Credential Protection Regression Test
# ==============================================================================

def test_seed_protects_existing_administrator_credentials():
    """
    Regression Test:
    Proves that an existing administrator's password hash remains unchanged
    even if categories are empty and run_seed() is executed.
    """
    db = get_db()
    test_admin_email = "owner_protect_test@sskcollections.com"

    # 1. Clean any previous test residue
    db.users.delete_one({"email": test_admin_email})

    # 2. Admin account created with initial password
    initial_hash = get_password_hash("InitialPassword@2026!")
    db.users.update_one(
        {"email": test_admin_email},
        {
            "$setOnInsert": {
                "email": test_admin_email,
                "full_name": "Store Owner",
                "role": "Super Admin",
                "hashed_password": initial_hash,
                "is_active": True
            }
        },
        upsert=True
    )
    assert verify_password("InitialPassword@2026!", initial_hash) is True

    # 3. Store owner changes their password to a custom strong passphrase
    custom_owner_password = "MyCustomSecretPassphrase@987654321!"
    custom_hash = get_password_hash(custom_owner_password)
    db.users.update_one(
        {"email": test_admin_email},
        {"$set": {"hashed_password": custom_hash}}
    )

    # Verify custom password is active in database
    user_before_seed = db.users.find_one({"email": test_admin_email})
    assert user_before_seed["hashed_password"] == custom_hash

    # 4. Simulate a situation where categories are missing/wiped, triggering run_seed()
    orig_env = settings.ENVIRONMENT
    orig_admin_email = settings.INITIAL_ADMIN_EMAIL
    orig_admin_password = settings.INITIAL_ADMIN_PASSWORD

    try:
        settings.ENVIRONMENT = "production"
        settings.INITIAL_ADMIN_EMAIL = test_admin_email
        settings.INITIAL_ADMIN_PASSWORD = "AttemptedOverwritePassword@123!"

        # Temporarily wipe categories to trigger category seeding
        db.categories.delete_many({})
        assert db.categories.count_documents({}) == 0

        # Execute run_seed()
        with patch.object(db_manager, "persist_to_disk"):
            run_seed()

        # Categories must be re-seeded
        assert db.categories.count_documents({}) > 0

        # CRITICAL ASSERTION: The administrator's password hash must NOT have been overwritten
        user_after_seed = db.users.find_one({"email": test_admin_email})
        assert user_after_seed["hashed_password"] == custom_hash
        assert verify_password(custom_owner_password, user_after_seed["hashed_password"]) is True
        assert verify_password("AttemptedOverwritePassword@123!", user_after_seed["hashed_password"]) is False
        assert verify_password("InitialPassword@2026!", user_after_seed["hashed_password"]) is False
    finally:
        # Clean test user
        db.users.delete_one({"email": test_admin_email})
        settings.ENVIRONMENT = orig_env
        settings.INITIAL_ADMIN_EMAIL = orig_admin_email
        settings.INITIAL_ADMIN_PASSWORD = orig_admin_password
