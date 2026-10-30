import pytest
import hmac
import hashlib
import uuid
from fastapi import HTTPException
from app.core.config import settings
from app.database import get_db
from app.schemas.payment import VerifyPaymentRequest
from app.api.v1.payments import (
    create_razorpay_order,
    verify_razorpay_payment,
    record_payment_failure,
    retry_payment,
    initiate_refund,
    razorpay_webhook
)

def test_razorpay_order_creation_and_signature_verification():
    db = get_db()
    order_id = "SSK-20261028-4412"

    # 1. Create a Razorpay order
    rzp_data = create_razorpay_order(payload={"order_id": order_id}, current_user=None, db=db)
    rzp_order_id = rzp_data.razorpay_order_id
    assert rzp_order_id.startswith("order_")
    assert rzp_data.currency == "INR"

    # 2. Test invalid signature rejection
    with pytest.raises(HTTPException) as exc:
        verify_razorpay_payment(
            payload=VerifyPaymentRequest(
                order_id=order_id,
                razorpay_order_id=rzp_order_id,
                razorpay_payment_id="pay_test_123456",
                razorpay_signature="completely_bogus_signature_hash"
            ),
            request=None,
            db=db
        )
    assert exc.value.status_code == 400

    # 3. Test genuine cryptographic HMAC SHA-256 signature
    payment_id = f"pay_{uuid.uuid4().hex[:14]}"
    msg = f"{rzp_order_id}|{payment_id}"
    valid_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    good_verify_res = verify_razorpay_payment(
        payload=VerifyPaymentRequest(
            order_id=order_id,
            razorpay_order_id=rzp_order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=valid_sig
        ),
        request=None,
        db=db
    )
    assert good_verify_res["success"] is True

def test_payment_failure_and_retry_flow():
    db = get_db()
    order_id = "SSK-20261028-4412"

    # 1. Record payment failure
    fail_res = record_payment_failure(
        order_id=order_id,
        payload={"reason": "Customer cancelled UPI intent modal"},
        db=db
    )
    assert fail_res["status"] == "FAILED"

    # Check order status in DB
    order = db.orders.find_one({"order_id": order_id})
    assert order["payment_status"] == "FAILED"

    # 2. Retry payment
    retry_data = retry_payment(order_id=order_id, db=db)
    assert retry_data["order_id"] == order_id
    assert "razorpay_order_id" in retry_data

    order_retried = db.orders.find_one({"order_id": order_id})
    assert order_retried["payment_status"] == "PENDING"

def test_refund_processing():
    db = get_db()
    order_id = "SSK-20261028-4412"

    # Ensure order is marked PAID first
    db.orders.update_one(
        {"order_id": order_id},
        {"$set": {"payment_status": "PAID", "payment_id": "pay_to_refund_123"}}
    )

    ref_data = initiate_refund(
        order_id=order_id,
        payload={"amount": 1000.0, "reason": "Customer returned item due to size issue"},
        db=db
    )
    assert ref_data["success"] is True
    assert "rfnd_" in ref_data["refund_id"]

    # Check order is updated to REFUNDED
    refunded_order = db.orders.find_one({"order_id": order_id})
    assert refunded_order["payment_status"] == "REFUNDED"

def test_webhook_idempotency():
    db = get_db()
    evt_id = f"evt_{uuid.uuid4().hex[:12]}"
    webhook_payload = {
        "id": evt_id,
        "event": "payment.captured",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_wh_123",
                    "amount": 299900,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }

    # First delivery
    res1 = razorpay_webhook(payload=webhook_payload, db=db)
    assert res1["status"] == "ok"

    # Duplicate delivery with same event_id
    res2 = razorpay_webhook(payload=webhook_payload, db=db)
    assert res2["status"] == "already_processed"
