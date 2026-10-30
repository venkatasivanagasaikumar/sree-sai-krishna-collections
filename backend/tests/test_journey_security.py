"""
Journey 4: Comprehensive Security & Access Control Tests
Tests OWASP Top 10 vulnerabilities including Broken Access Control (BOLA/IDOR),
Price Manipulation, Unauthorized Administrative Actions, Privilege Escalation,
and Cryptographic Signature Verification.
"""
import pytest
from fastapi import HTTPException
from app.database import get_db
from app.api.v1.auth import register_customer, create_staff_user
from app.api.v1.orders import get_order_by_id, create_order, update_order_status_admin
from app.api.v1.inventory import adjust_stock
from app.api.v1.payments import verify_razorpay_payment, razorpay_webhook
from app.api.v1.cart import calculate_cart_totals
from app.api.v1.sheets_sync import get_appscript_template
from app.api.dependencies import require_admin, require_roles
from app.core.permissions import Role
from app.schemas.auth import UserCreate, Address
from app.schemas.order import CreateOrderRequest, OrderStatusUpdate
from app.schemas.inventory import StockAdjustment
from app.schemas.payment import VerifyPaymentRequest

def test_security_idor_order_access_blocked_for_unauthenticated_stranger():
    """Unauthenticated requests without email/phone/token verification must be rejected with 401."""
    db = get_db()
    with pytest.raises(HTTPException) as exc:
        get_order_by_id(order_id="SSK-20261028-4412", verification=None, current_user=None, db=db)
    assert exc.value.status_code == 401

def test_security_idor_order_access_blocked_for_wrong_verification():
    """Unauthenticated requests with wrong email or phone must be rejected with 403."""
    db = get_db()
    with pytest.raises(HTTPException) as exc:
        get_order_by_id(order_id="SSK-20261028-4412", verification="attacker@evil.com", current_user=None, db=db)
    assert exc.value.status_code == 403

def test_security_cross_customer_order_access_blocked():
    """Customer A cannot view Customer B's order."""
    db = get_db()
    customer_a = {
        "id": "user_customer_a_id",
        "_id": "user_customer_a_id",
        "email": "customer.a@example.com",
        "role": Role.CUSTOMER
    }
    with pytest.raises(HTTPException) as exc:
        # SSK-20261028-4412 belongs to priya.sharma@example.com
        get_order_by_id(order_id="SSK-20261028-4412", current_user=customer_a, db=db)
    assert exc.value.status_code == 403

def test_security_role_escalation_on_public_registration_prevented():
    """Public customer registration must ALWAYS assign Role.CUSTOMER, even if attacker crafts input."""
    db = get_db()
    attacker_email = "malicious.attacker@example.com"
    db.users.delete_one({"email": attacker_email})

    reg_dto = UserCreate(
        email=attacker_email,
        full_name="Attacker",
        phone="+91 99999 00000",
        password="Password123!"
    )
    reg_res = register_customer(payload=reg_dto, request=None, db=db)
    assert reg_res.user["role"] == Role.CUSTOMER

    user_in_db = db.users.find_one({"email": attacker_email})
    assert user_in_db["role"] == Role.CUSTOMER
    db.users.delete_one({"email": attacker_email})

def test_security_customer_cannot_access_admin_role_checker():
    """Regular customer attempting to execute admin actions must be rejected with 403."""
    customer_user = {
        "id": "cust_123",
        "email": "shopper@example.com",
        "role": Role.CUSTOMER
    }
    with pytest.raises(HTTPException) as exc:
        require_admin(customer_user)
    assert exc.value.status_code == 403

def test_security_cart_price_tampering_prevented():
    """Client cannot submit fake product prices; totals are strictly calculated from database."""
    db = get_db()
    # Attacker tries to pass price of ₹1.00 for a ₹1899 item
    totals = calculate_cart_totals(
        [{"product_id": "SSK-JWL-101", "quantity": 1, "price": 1.0, "total_price": 1.0}],
        None,
        db
    )
    assert totals.subtotal == 1899.0
    assert totals.items[0].price == 1899.0

def test_security_invalid_payment_signature_rejected():
    """Tampered or invalid Razorpay payment signature must be rejected with 400."""
    db = get_db()
    with pytest.raises(HTTPException) as exc:
        verify_razorpay_payment(
            payload=VerifyPaymentRequest(
                order_id="SSK-20261028-4412",
                razorpay_order_id="order_fake123",
                razorpay_payment_id="pay_fake123",
                razorpay_signature="invalid_tampered_signature_12345"
            ),
            request=None,
            db=db
        )
    assert exc.value.status_code == 400

def test_security_inventory_negative_stock_prevented():
    """Inventory adjustment cannot result in negative stock."""
    db = get_db()
    admin_user = {"id": "admin_id", "email": "admin@sskcollections.com", "role": "Super Admin"}
    with pytest.raises(HTTPException) as exc:
        adjust_stock(
            payload=StockAdjustment(
                product_id="test_pid_101",
                sku="SSK-JWL-101",
                quantity_change=-99999,
                adjustment_type="DAMAGE",
                reason="Malicious stock drain attempt"
            ),
            current_user=admin_user,
            db=db
        )
    assert exc.value.status_code == 400
    assert "negative" in exc.value.detail
