from app.database import get_db
from app.api.v1.auth import register_customer, login, get_current_user_profile, change_password, add_address
from app.schemas.auth import UserCreate, UserLogin, PasswordChange, Address
from app.core.security import decode_token
from app.core.permissions import Role
import pytest
from fastapi import HTTPException

def test_customer_registration_and_login():
    db = get_db()
    email = "test.shopper.direct@example.com"
    # Ensure clean state
    db.users.delete_one({"email": email})

    # Register
    create_dto = UserCreate(
        email=email,
        full_name="Direct Test Shopper",
        phone="+91 99887 76655",
        password="ValidPassword123!"
    )
    reg_res = register_customer(payload=create_dto, request=None, db=db)
    assert reg_res.access_token is not None
    assert reg_res.user["email"] == email
    assert reg_res.user["role"] == Role.CUSTOMER

    # Decode token
    payload = decode_token(reg_res.access_token)
    assert payload["sub"] == reg_res.user["id"]
    assert payload["role"] == Role.CUSTOMER

    # Login
    login_dto = UserLogin(email=email, password="ValidPassword123!")
    login_res = login(payload=login_dto, request=None, db=db)
    assert login_res.access_token is not None
    assert login_res.user["full_name"] == "Direct Test Shopper"

def test_login_invalid_password():
    db = get_db()
    db.audit_logs.delete_many({"user_email": "admin@sskcollections.com", "action": "LOGIN_FAILED"})
    login_dto = UserLogin(email="admin@sskcollections.com", password="IncorrectPassword!")
    with pytest.raises(HTTPException) as exc:
        login(payload=login_dto, request=None, db=db)
    assert exc.value.status_code == 401

def test_login_brute_force_lockout():
    db = get_db()
    test_email = "brute.force.test@example.com"
    db.audit_logs.delete_many({"user_email": test_email})
    login_dto = UserLogin(email=test_email, password="WrongPassword123!")
    
    # 5 failed attempts trigger audit logging
    for _ in range(5):
        with pytest.raises(HTTPException) as exc:
            login(payload=login_dto, request=None, db=db)
        assert exc.value.status_code == 401
    
    # 6th attempt triggers 429 rate limit
    with pytest.raises(HTTPException) as exc_blocked:
        login(payload=login_dto, request=None, db=db)
    assert exc_blocked.value.status_code == 429
    assert "Too many failed login attempts" in exc_blocked.value.detail

def test_address_management():
    db = get_db()
    user = db.users.find_one({"email": "priya.sharma@example.com"})
    user["id"] = str(user["_id"])

    addr_dto = Address(
        name="Priya Office",
        phone="+91 98765 43210",
        address_line1="HITEC City, Cyber Towers",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        is_default=False,
        type="Work"
    )
    res = add_address(address=addr_dto, current_user=user, db=db)
    assert res["message"] == "Address added successfully"
    assert res["address"]["city"] == "Hyderabad"

def test_production_blocks_default_demo_admin_credentials():
    """Phase 3 Security: Default demo admin credentials strictly forbidden in production."""
    db = get_db()
    from app.core.config import settings
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        login_dto = UserLogin(email="admin@sskcollections.com", password="Admin@SSK2026!")
        with pytest.raises(HTTPException) as exc:
            login(payload=login_dto, request=None, db=db)
        assert exc.value.status_code == 403
        assert "Default demo administrator credentials cannot be used in production" in exc.value.detail
        
        # Verify password is never logged in audit trail
        last_log = db.audit_logs.find_one({"action": "LOGIN_BLOCKED_DEMO_CREDENTIALS"}, sort=[("created_at", -1)])
        assert last_log is not None
        assert "password" not in last_log
        assert "Admin@SSK2026!" not in str(last_log)
    finally:
        settings.ENVIRONMENT = orig_env

def test_registration_role_escalation_impossible():
    """Phase 3 Security: Customer registration can never escalate to administrator role."""
    db = get_db()
    email = "hacker.wannabe@example.com"
    db.users.delete_one({"email": email})
    
    reg_dto = UserCreate(
        email=email,
        full_name="Attacker Trying Escalation",
        phone="+91 99887 76655",
        password="ValidPassword123!"
    )
    res = register_customer(payload=reg_dto, request=None, db=db)
    assert res.user["role"] == Role.CUSTOMER
    
    # Check directly in database
    db_user = db.users.find_one({"email": email})
    assert db_user["role"] == Role.CUSTOMER
    assert db_user["role"] != Role.SUPER_ADMIN

def test_audit_logs_never_store_passwords():
    """Phase 3 Security: Passwords must never be written to database audit logs."""
    db = get_db()
    logs = list(db.audit_logs.find({}))
    for log in logs:
        assert "password" not in log
        assert "hashed_password" not in log
        # Check details dictionary if present
        details = log.get("details", {})
        if isinstance(details, dict):
            assert "password" not in details
