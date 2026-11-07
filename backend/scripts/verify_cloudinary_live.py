#!/usr/bin/env python3
"""
Sree Sai Krishna Collections (SSK)
Safe Cloudinary & MongoDB Atlas Live Integration Verification Tool
===================================================================
Performs end-to-end verification of Cloudinary product image uploads:
1. Verifies Cloudinary configuration and credentials presence from backend/.env (masked).
2. Verifies MongoDB Atlas connectivity and accessibility with FORCE_MOCK_DB=false.
3. Performs a single safe upload of an in-memory non-sensitive test image.
4. Verifies the returned Cloudinary HTTPS CDN URL and public_id.
5. Verifies that the media asset metadata is stored in MongoDB Atlas (media_assets).
6. Verifies that the image is accessible via its returned HTTPS URL (HTTP 200).
7. Guaranteed cleanup: destroys the test asset from Cloudinary and deletes the test
   probe record from MongoDB Atlas inside a try...finally block.
Strictly masks all credentials, tokens, and secrets from all logs and output.
"""

import os
import sys
import io
import re
import argparse
from datetime import datetime, timezone
import httpx
import pymongo
from fastapi import UploadFile
from dotenv import load_dotenv

# Ensure backend directory is in python path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Explicitly load backend/.env before importing settings
ENV_FILE = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE, override=True)

from app.core.config import settings
from app.api.v1.upload import upload_file, sanitize_message as app_sanitize_message
import cloudinary
import cloudinary.uploader


# Valid 1x1 pixel non-sensitive JPEG bytes for safe testing
TEST_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
    b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)


def mask_key(val: str) -> str:
    """Masks secret or API key for safe display."""
    if not val:
        return "<EMPTY / UNCONFIGURED>"
    if len(val) <= 4:
        return "****"
    return f"{val[:3]}****{val[-2:]}"


def mask_uri(uri: str) -> str:
    """Masks MongoDB Atlas credentials for safe display."""
    if not uri:
        return "<EMPTY>"
    return re.sub(r'(mongodb(?:\+srv)?://[^:]+:)([^@]+)(@.+)', r'\1****\3', str(uri))


def sanitize_all(msg: str) -> str:
    """Masks MongoDB URIs, Cloudinary secrets, and API keys from error messages."""
    clean = mask_uri(str(msg))
    if settings.CLOUDINARY_API_SECRET and settings.CLOUDINARY_API_SECRET in clean:
        clean = clean.replace(settings.CLOUDINARY_API_SECRET, "[MASKED]")
    if settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_KEY in clean:
        clean = clean.replace(settings.CLOUDINARY_API_KEY, "[MASKED]")
    return clean


def run_live_verification(mongo_uri: str = None, database_name: str = None) -> bool:
    print("=" * 70)
    print(" SSK CLOUDINARY & MONGODB ATLAS LIVE INTEGRATION VERIFICATION")
    print("=" * 70)
    print(f"Timestamp       : {datetime.now(timezone.utc).isoformat()}")
    print(f"Env File Loaded : {ENV_FILE if os.path.exists(ENV_FILE) else 'None (os.environ)'}")
    print(f"Cloud Name      : {settings.CLOUDINARY_CLOUD_NAME or '<EMPTY>'}")
    print(f"API Key         : {mask_key(settings.CLOUDINARY_API_KEY)}")
    print(f"API Secret      : {'[CONFIGURED / MASKED]' if settings.CLOUDINARY_API_SECRET else '<EMPTY>'}")
    print(f"Cloudinary OK   : {settings.is_cloudinary_configured}")
    print(f"Folder          : {settings.CLOUDINARY_FOLDER or 'products'}")
    
    active_uri = mongo_uri or settings.active_mongo_uri
    target_db_name = database_name or settings.DATABASE_NAME
    print(f"Database Target : {target_db_name}")
    print(f"Mongo Cluster   : {mask_uri(active_uri)}")
    print(f"FORCE_MOCK_DB   : {settings.FORCE_MOCK_DB}")
    print("-" * 70)

    # --------------------------------------------------------------------------
    # Check 1: Validate Cloudinary Environment Configuration from backend/.env
    # --------------------------------------------------------------------------
    print("\n[Step 1/6] Verifying Cloudinary configuration parameters...")
    if not settings.is_cloudinary_configured:
        print("[FAIL] Cloudinary credentials incomplete or invalid.")
        if set(settings.clean_cloudinary_api_secret) == {"*"}:
            print("       CRITICAL: CLOUDINARY_API_SECRET contains masked asterisks ('**********').")
            print("       This occurs when copying the masked display from the Cloudinary Console rather than revealing the actual secret.")
            print("       Please click the eye/reveal icon in Cloudinary Dashboard -> API Keys to copy your true alphanumeric secret.")
        else:
            print("       Ensure CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET are set in backend/.env.")
        return False
    print("[PASS] Cloudinary configuration verified (cloud_name and keys present).")

    # --------------------------------------------------------------------------
    # Check 2: Verify MongoDB Atlas Connectivity & FORCE_MOCK_DB=false
    # --------------------------------------------------------------------------
    print("\n[Step 2/6] Connecting to live MongoDB Atlas cluster (FORCE_MOCK_DB=false)...")
    if settings.FORCE_MOCK_DB:
        print("[FAIL] FORCE_MOCK_DB is True. Set FORCE_MOCK_DB=false in backend/.env to connect to live MongoDB Atlas.")
        return False

    if not active_uri or "localhost" in active_uri or "127.0.0.1" in active_uri or "mock" in active_uri.lower():
        print(f"[FAIL] Active MongoDB URI does not point to live MongoDB Atlas: {mask_uri(active_uri)}")
        print("       Set MONGO_URI in backend/.env to your Atlas cluster connection string.")
        return False

    client_kwargs = {
        "serverSelectionTimeoutMS": 5000,
        "connectTimeoutMS": 5000,
        "socketTimeoutMS": 10000,
        "retryWrites": True,
        "w": "majority"
    }
    if active_uri.startswith("mongodb+srv://") or settings.DB_TLS:
        client_kwargs["tls"] = True

    try:
        mongo_client = pymongo.MongoClient(active_uri, **client_kwargs)
        mongo_client.admin.command("ping")
        atlas_db = mongo_client[target_db_name]
        print(f"[PASS] Successfully connected to Atlas cluster. Ping confirmed on '{target_db_name}'.")
    except Exception as e:
        safe_err = sanitize_all(str(e))
        print(f"[FAIL] MongoDB Atlas connection failed: {safe_err}")
        return False

    # --------------------------------------------------------------------------
    # Check 3: Perform Live Upload of a Uniquely Named Temporary Test Image
    # --------------------------------------------------------------------------
    print("\n[Step 3/6] Performing live upload of uniquely named temporary test image...")
    unique_suffix = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    test_filename = f"ssk_probe_{unique_suffix}.jpg"
    test_upload_file = UploadFile(
        file=io.BytesIO(TEST_JPEG_BYTES),
        filename=test_filename,
        headers={"content-type": "image/jpeg"}
    )

    uploaded_url = None
    uploaded_public_id = None
    overall_success = False

    try:
        upload_res = upload_file(file=test_upload_file, db=atlas_db)
        uploaded_url = upload_res.get("url")
        uploaded_public_id = upload_res.get("public_id")
        uploaded_size = upload_res.get("size")

        print(f"[PASS] Image uploaded successfully to Cloudinary!")
        print(f"       Public ID : {uploaded_public_id}")
        print(f"       HTTPS URL : {uploaded_url}")
        print(f"       File Size : {uploaded_size} bytes")

        if not uploaded_url or not uploaded_url.startswith("https://res.cloudinary.com/"):
            print(f"[FAIL] Returned URL is not a Cloudinary HTTPS URL: {uploaded_url}")
            return False
        if not uploaded_public_id:
            print("[FAIL] Missing public_id in upload response.")
            return False

        # ----------------------------------------------------------------------
        # Check 6 Guaranteed: Wrap intermediate verifications in try...finally
        # so that cleanup ALWAYS executes if an intermediate step fails.
        # ----------------------------------------------------------------------
        # Step 4: Verify Metadata Persistence in MongoDB Atlas (media_assets)
        print("\n[Step 4/6] Verifying media asset persistence in MongoDB Atlas...")
        asset_record = atlas_db["media_assets"].find_one({"public_id": uploaded_public_id})
        if not asset_record:
            print(f"[FAIL] Asset record for public_id '{uploaded_public_id}' not found in MongoDB Atlas.")
            return False

        print(f"[PASS] Asset metadata confirmed in MongoDB Atlas (media_assets):")
        print(f"       Record ID : {asset_record.get('_id')}")
        print(f"       Provider  : {asset_record.get('provider')}")
        print(f"       HTTPS URL : {asset_record.get('secure_url')}")
        print(f"       Filename  : {asset_record.get('filename')}")
        print(f"       Created   : {asset_record.get('created_at')}")

        if asset_record.get("provider") != "cloudinary":
            print(f"[FAIL] Unexpected provider in record: {asset_record.get('provider')}")
            return False
        if asset_record.get("url") != uploaded_url:
            print(f"[FAIL] Record URL does not match upload response URL.")
            return False

        # Step 5: Verify Image Accessibility via HTTPS CDN
        print("\n[Step 5/6] Verifying image accessibility over public HTTPS CDN...")
        with httpx.Client(timeout=10.0, follow_redirects=True) as http_client:
            cdn_res = http_client.get(uploaded_url)
            print(f"       CDN HTTP Status Code: {cdn_res.status_code}")
            print(f"       CDN Content-Type    : {cdn_res.headers.get('content-type')}")
            print(f"       Content Length Bytes: {len(cdn_res.content)}")

            if cdn_res.status_code != 200:
                print(f"[FAIL] Cloudinary CDN did not return HTTP 200. Got: {cdn_res.status_code}")
                return False
            if len(cdn_res.content) == 0:
                print("[FAIL] Cloudinary CDN returned 0 bytes.")
                return False
        print("[PASS] Image is publicly accessible over HTTPS and returned valid image bytes.")

        overall_success = True

    except Exception as e:
        safe_err = sanitize_all(str(e))
        print(f"[FAIL] Error during upload or verification: {safe_err}")
        overall_success = False
        return False
    finally:
        # ----------------------------------------------------------------------
        # Check 4, 5 & 6: Guaranteed Cleanup Runs Even on Failure
        # ----------------------------------------------------------------------
        if uploaded_public_id:
            print("\n[Step 6/6] Safely cleaning up temporary test probe from Cloudinary and Atlas...")
            cleanup_success = True
            try:
                # Delete ONLY the exact test image by its own Cloudinary public_id
                destroy_res = cloudinary.uploader.destroy(uploaded_public_id, resource_type="image")
                print(f"       Cloudinary destroy status: {destroy_res.get('result')}")
            except Exception as e:
                safe_err = sanitize_all(str(e))
                print(f"[WARNING] Could not destroy Cloudinary test asset: {safe_err}")
                cleanup_success = False

            try:
                # Delete ONLY the exact test document by its own public_id
                del_res = atlas_db["media_assets"].delete_one({"public_id": uploaded_public_id})
                print(f"       MongoDB Atlas cleanup deleted count: {del_res.deleted_count}")
            except Exception as e:
                safe_err = sanitize_all(str(e))
                print(f"[WARNING] Could not delete Atlas media_assets test record: {safe_err}")
                cleanup_success = False

            if cleanup_success:
                print("[PASS] Test asset cleaned up completely. Zero residual records left in production.")
        else:
            print("\n[Step 6/6] No asset uploaded to Cloudinary. No cleanup required.")

        try:
            mongo_client.close()
        except Exception:
            pass

    if overall_success:
        print("\n" + "=" * 70)
        print(" VERDICT: Cloudinary & MongoDB Atlas Integration is FULLY OPERATIONAL!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print(" VERDICT: Verification FAILED. See errors above.")
        print("=" * 70)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSK Cloudinary Live Verification Tool")
    parser.add_argument("--mongo-uri", help="MongoDB Atlas URI (optional override)", default=None)
    parser.add_argument("--db", help="Database name (default: ssk_production_db)", default=None)
    args = parser.parse_args()

    ok = run_live_verification(mongo_uri=args.mongo_uri, database_name=args.db)
    sys.exit(0 if ok else 1)
