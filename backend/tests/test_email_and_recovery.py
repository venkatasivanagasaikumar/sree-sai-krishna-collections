import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.services.email_service import EmailService
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.api.v1.auth import register_customer, login, forgot_password, verify_reset_token, reset_password

def test_email_service_dispatches_and_logs():
    db = get_db()
    initial_log_count = db.email_logs.count_documents({})

    res = EmailService.send_password_reset(
        to_email="test.customer@example.com",
        token="test_token_xyz_123",
        customer_name="Priya Sharma"
    )
    assert res["status"] in ["delivered", "simulated"]
    assert res["to"] == "test.customer@example.com"
    assert "password_reset" in res["template"]

    # Verify log entry in database
    assert db.email_logs.count_documents({}) == initial_log_count + 1
    last_log = db.email_logs.find_one({"to_email": "test.customer@example.com"})
    assert last_log is not None
    assert "Reset Your Password" in last_log["subject"]

def test_forgot_password_and_reset_flow():
    db = get_db()
    test_email = "recovery.test@example.com"
    db.users.delete_one({"email": test_email})
    
    # 1. Register a test user
    reg_dto = UserCreate(
        email=test_email,
        full_name="Recovery Test User",
        phone="+91 98765 43210",
        password="InitialPassword123!"
    )
    reg_res = register_customer(payload=reg_dto, request=None, db=db)
    assert reg_res.access_token is not None

    # 2. Request password reset
    forgot_dto = ForgotPasswordRequest(email=test_email)
    forgot_res = forgot_password(payload=forgot_dto, request=None, db=db)
    assert "instructions have been sent" in forgot_res["message"]

    # 3. Retrieve token from database
    token_doc = db.password_reset_tokens.find_one({"email": test_email, "used": False})
    assert token_doc is not None
    token = token_doc["token"]

    # 4. Verify token
    verify_res = verify_reset_token(token=token, db=db)
    assert verify_res["valid"] is True

    # 5. Reset password
    new_pass = "BrandNewSecurePassword456!"
    reset_dto = ResetPasswordRequest(token=token, new_password=new_pass)
    reset_res = reset_password(payload=reset_dto, request=None, db=db)
    assert "successfully updated" in reset_res["message"]

    # 6. Verify token is marked used and cannot be reused
    token_doc_after = db.password_reset_tokens.find_one({"token": token})
    assert token_doc_after["used"] is True

    with pytest.raises(HTTPException) as exc:
        reset_password(payload=reset_dto, request=None, db=db)
    assert exc.value.status_code == 400

    # 7. Login with old password fails
    with pytest.raises(HTTPException) as exc_old:
        login(payload=UserLogin(email=test_email, password="InitialPassword123!"), request=None, db=db)
    assert exc_old.value.status_code == 401

    # 8. Login with new password succeeds
    login_res = login(payload=UserLogin(email=test_email, password=new_pass), request=None, db=db)
    assert login_res.access_token is not None

def test_expired_token_rejected():
    db = get_db()
    expired_token = "expired_token_test_999"
    # Insert an already expired token
    db.password_reset_tokens.insert_one({
        "token": expired_token,
        "user_id": "test_user_id",
        "email": "expired@example.com",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
        "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
        "used": False
    })

    with pytest.raises(HTTPException) as exc:
        verify_reset_token(token=expired_token, db=db)
    assert exc.value.status_code == 400
    assert "expired" in exc.value.detail.lower()
