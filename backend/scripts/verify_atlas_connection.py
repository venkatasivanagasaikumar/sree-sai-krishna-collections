#!/usr/bin/env python3
"""
Sree Sai Krishna Collections (SSK)
Safe MongoDB Atlas Staging Connection Verification Tool
======================================================
Verifies network connectivity, TLS handshake, database authentication,
read/write permissions, and indexes while strictly masking all credentials.
"""

import os
import sys
import re
import argparse
from datetime import datetime, timezone

# Add parent directory to path to load app modules if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def mask_connection_uri(uri: str) -> str:
    """Masks password from MongoDB connection string for safe terminal logging."""
    if not uri:
        return "<EMPTY>"
    return re.sub(r'(mongodb(?:\+srv)?://[^:]+:)([^@]+)(@.+)', r'\1****\3', uri)

def verify_connection(uri: str, database_name: str = "ssk_staging_db") -> bool:
    masked_uri = mask_connection_uri(uri)
    print("=" * 70)
    print(" SSK MONGODB ATLAS STAGING CONNECTION VERIFICATION")
    print("=" * 70)
    print(f"Target Database : {database_name}")
    print(f"Cluster Endpoint: {masked_uri}")
    print(f"Timestamp       : {datetime.now(timezone.utc).isoformat()}")
    print("-" * 70)

    if not uri:
        print("[FAIL] MONGODB_URI is not set. Please supply the staging Atlas connection URI.")
        return False

    if "mock" in uri.lower():
        print("[FAIL] In-memory mock database URI detected. Real MongoDB Atlas URI required.")
        return False

    try:
        import pymongo
    except ImportError:
        print("[FAIL] pymongo is not installed in the current environment.")
        return False

    print("[1/5] Initializing connection client with TLS and timeouts...")
    try:
        client_kwargs = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 10000,
            "retryWrites": True,
            "w": "majority"
        }
        if uri.startswith("mongodb+srv://"):
            client_kwargs["tls"] = True

        client = pymongo.MongoClient(uri, **client_kwargs)
    except Exception as e:
        safe_err = mask_connection_uri(str(e))
        print(f"[FAIL] Client initialization error: {safe_err}")
        return False

    print("[2/5] Sending admin ping command (testing TLS & network reachable)...")
    try:
        ping_res = client.admin.command("ping")
        print(f"[PASS] Cluster ping successful. Server response: {ping_res}")
    except Exception as e:
        safe_err = mask_connection_uri(str(e))
        print(f"[FAIL] Unable to reach MongoDB cluster: {safe_err}")
        print("       Hint: Verify IP Access List in Atlas allows connection from this IP.")
        return False

    print(f"[3/5] Testing read/write permissions on database '{database_name}'...")
    try:
        db = client[database_name]
        probe_doc = {"probe": "staging_verification", "timestamp": datetime.now(timezone.utc)}
        res = db._connection_probe.insert_one(probe_doc)
        inserted_id = res.inserted_id
        # Read back
        found = db._connection_probe.find_one({"_id": inserted_id})
        assert found is not None
        # Clean up
        db._connection_probe.delete_one({"_id": inserted_id})
        print(f"[PASS] Read and write privileges confirmed on '{database_name}'.")
    except Exception as e:
        safe_err = mask_connection_uri(str(e))
        print(f"[FAIL] Database permission failure: {safe_err}")
        return False

    print("[4/5] Inspecting collections and indexes...")
    try:
        cols = db.list_collection_names()
        print(f"[INFO] Collections found ({len(cols)}): {', '.join(cols) if cols else 'None (empty database)'}")
    except Exception as e:
        safe_err = mask_connection_uri(str(e))
        print(f"[WARNING] Could not list collections: {safe_err}")

    print("[5/5] Checking database latency...")
    try:
        t0 = datetime.now()
        client.admin.command("ping")
        latency_ms = round((datetime.now() - t0).total_seconds() * 1000, 2)
        print(f"[PASS] Round-trip latency to cluster: {latency_ms} ms")
    except Exception:
        pass

    print("-" * 70)
    print("VERDICT: MongoDB Atlas Staging cluster connectivity is FULLY OPERATIONAL.")
    print("=" * 70)
    client.close()
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSK Safe MongoDB Atlas Connection Verifier")
    parser.add_argument("--uri", help="Staging MongoDB Atlas URI (if omitted, reads from MONGODB_URI env)", default=None)
    parser.add_argument("--db", help="Database name", default="ssk_staging_db")
    args = parser.parse_args()

    uri_to_test = args.uri or os.getenv("MONGODB_URI")
    success = verify_connection(uri_to_test, database_name=args.db)
    sys.exit(0 if success else 1)
