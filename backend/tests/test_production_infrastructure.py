import os
import hmac
import hashlib
import json
import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.database import Database, db_manager, get_db
from app.main import app, readiness_check, health_check
from app.api.v1.payments import razorpay_webhook

def test_production_fails_safely_if_mock_db_configured_in_production():
    """Ensures production refuses to start if FORCE_MOCK_DB is True."""
    original_env = settings.ENVIRONMENT
    original_mock = settings.FORCE_MOCK_DB
    test_db = Database()
    try:
        settings.ENVIRONMENT = "production"
        settings.FORCE_MOCK_DB = True
        with pytest.raises(RuntimeError) as exc:
            test_db.connect()
        assert "CRITICAL MISCONFIGURATION" in str(exc.value)
    finally:
        settings.ENVIRONMENT = original_env
        settings.FORCE_MOCK_DB = original_mock

def test_production_fails_safely_if_cluster_unreachable():
    """Ensures production never silently falls back to MongoMock when Atlas/cluster is unreachable."""
    original_env = settings.ENVIRONMENT
    original_mock = settings.FORCE_MOCK_DB
    original_uri = settings.MONGODB_URI
    test_db = Database()
    try:
        settings.ENVIRONMENT = "production"
        settings.FORCE_MOCK_DB = False
        settings.MONGODB_URI = "mongodb://unreachable-cluster.example.invalid:27017"
        with pytest.raises(RuntimeError) as exc:
            test_db.connect()
        assert "FATAL: Could not connect to production MongoDB cluster" in str(exc.value)
    finally:
        settings.ENVIRONMENT = original_env
        settings.FORCE_MOCK_DB = original_mock
        settings.MONGODB_URI = original_uri

def test_database_connection_pool_and_ping():
    """Verifies connection pool configuration and ping helper."""
    assert settings.DB_MAX_POOL_SIZE >= 50
    assert settings.DB_MIN_POOL_SIZE >= 10
    assert settings.DB_MAX_IDLE_TIME_MS == 45000
    ping = db_manager.ping()
    assert ping["status"] == "connected"
    assert "database" in ping

def test_cors_origins_dynamic_parsing(monkeypatch):
    """Verifies BACKEND_CORS_ORIGINS parses JSON array and comma-separated string."""
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["https://shop.ssk.com", "https://admin.ssk.com"]')
    assert "https://shop.ssk.com" in settings.cors_origins
    assert "https://admin.ssk.com" in settings.cors_origins

    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "https://one.ssk.com, https://two.ssk.com")
    assert "https://one.ssk.com" in settings.cors_origins
    assert "https://two.ssk.com" in settings.cors_origins

def test_production_config_validation_rules():
    """Verifies pre-flight validation catches mock db and default secrets in production."""
    original_env = settings.ENVIRONMENT
    original_mock = settings.FORCE_MOCK_DB
    original_secret = settings.SECRET_KEY
    try:
        settings.ENVIRONMENT = "production"
        settings.FORCE_MOCK_DB = True
        settings.SECRET_KEY = "ssk-royal-navy-gold-super-secure-jwt-secret-key-2026-prod"
        blockers = settings.validate_production_readiness()
        assert any("SECRET_KEY" in b for b in blockers)
        assert any("FORCE_MOCK_DB" in b for b in blockers)
    finally:
        settings.ENVIRONMENT = original_env
        settings.FORCE_MOCK_DB = original_mock
        settings.SECRET_KEY = original_secret

def test_razorpay_webhook_signature_validation():
    """Verifies webhook signature verification rejects forged signatures and accepts valid ones."""
    db = get_db()
    payload = {"id": "evt_sig_test_001", "event": "payment.captured", "amount": 1000}
    secret = settings.RAZORPAY_WEBHOOK_SECRET

    raw_data = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    valid_sig = hmac.new(secret.encode('utf-8'), raw_data, hashlib.sha256).hexdigest()

    # Valid signature
    res = razorpay_webhook(payload=payload, x_razorpay_signature=valid_sig, db=db)
    assert res["status"] in ["ok", "already_processed"]

    # Invalid signature
    with pytest.raises(HTTPException) as exc:
        razorpay_webhook(payload={"id": "evt_sig_fail_999"}, x_razorpay_signature="bad_forged_hash", db=db)
    assert exc.value.status_code == 400
    assert "Invalid webhook signature" in exc.value.detail

def test_health_and_readiness_probes():
    """Verifies liveness /health and readiness /ready endpoints."""
    health = health_check()
    assert health["status"] == "healthy"

    ready = readiness_check()
    assert ready["status"] == "ready"
    assert "database" in ready
    assert "products_count" in ready
