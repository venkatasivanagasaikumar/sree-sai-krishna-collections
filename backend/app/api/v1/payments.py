from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any
from datetime import datetime, timezone
import hmac
import hashlib
import uuid
from app.database import get_db, db_manager
from app.core.config import settings
from app.core.logging import AuditLogger, logger
from app.schemas.payment import RazorpayOrderResponse, VerifyPaymentRequest, PaymentStatusResponse
from app.api.dependencies import get_current_user, get_optional_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-razorpay-order", response_model=RazorpayOrderResponse)
def create_razorpay_order(
    payload: Dict[str, str],
    current_user: Optional[dict] = Depends(get_optional_current_user),
    db = Depends(get_db)
):
    order_id = payload.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")

    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    amount_in_paise = int(round(order["final_amount"] * 100))
    # Simulated/Sandbox Razorpay order ID
    rzp_order_id = f"order_{uuid.uuid4().hex[:14]}"

    db.orders.update_one(
        {"order_id": order_id},
        {"$set": {"razorpay_order_id": rzp_order_id, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()

    return RazorpayOrderResponse(
        order_id=order_id,
        razorpay_order_id=rzp_order_id,
        amount_in_paise=amount_in_paise,
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID,
        business_name=settings.BRAND_NAME,
        prefill={
            "name": order.get("customer_name") or "Valued Customer",
            "email": order.get("customer_email") or "",
            "contact": order.get("customer_phone") or ""
        }
    )

@router.post("/verify-razorpay-payment")
def verify_razorpay_payment(
    payload: VerifyPaymentRequest,
    request: Request,
    db = Depends(get_db)
):
    order = db.orders.find_one({"order_id": payload.order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify signature using constant-time comparison to prevent timing attacks
    msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # In production, require strict cryptographic HMAC match.
    # Allow test mock signature only when explicitly enabled in non-production environments.
    is_valid = hmac.compare_digest(generated_signature, payload.razorpay_signature)
    if not is_valid and settings.ENVIRONMENT != "production" and settings.ALLOW_MOCK_PAYMENTS:
        if payload.razorpay_signature.startswith("mock_sig_") or payload.razorpay_signature == "sandbox_success":
            is_valid = True

    if not is_valid:
        AuditLogger.log_event(
            db,
            action="PAYMENT_VERIFICATION_FAILED",
            resource_type="PAYMENT",
            resource_id=payload.order_id,
            details={"payment_id": payload.razorpay_payment_id},
            status="FAILURE"
        )
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    now = datetime.now(timezone.utc)
    timeline = order.get("timeline", [])
    timeline.append({
        "status": "PAYMENT_CONFIRMED",
        "message": f"Payment of ₹{order['final_amount']} received via Razorpay (Payment ID: {payload.razorpay_payment_id})",
        "timestamp": now,
        "performed_by": "Razorpay Gateway"
    })

    db.orders.update_one(
        {"order_id": payload.order_id},
        {
            "$set": {
                "payment_status": "PAID",
                "order_status": "PAYMENT_CONFIRMED",
                "payment_id": payload.razorpay_payment_id,
                "payment_verified_at": now,
                "timeline": timeline,
                "updated_at": now
            }
        }
    )

    # Record payment transaction
    db.payments.insert_one({
        "order_id": payload.order_id,
        "payment_gateway": "Razorpay",
        "razorpay_order_id": payload.razorpay_order_id,
        "razorpay_payment_id": payload.razorpay_payment_id,
        "amount": order["final_amount"],
        "currency": "INR",
        "status": "CAPTURED",
        "created_at": now
    })

    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="PAYMENT_CONFIRMED",
        resource_type="ORDER",
        resource_id=payload.order_id,
        user_id=order.get("user_id"),
        user_email=order.get("customer_email"),
        details={"payment_id": payload.razorpay_payment_id, "amount": order["final_amount"]}
    )

    return {
        "success": True,
        "message": "Payment verified and order confirmed",
        "order_id": payload.order_id,
        "payment_id": payload.razorpay_payment_id
    }

@router.post("/webhook")
async def razorpay_webhook(request: Request, db = Depends(get_db)):
    """Idempotent webhook listener for Razorpay payment lifecycle events."""
    body_bytes = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    # In real production, verify against webhook secret
    try:
        event_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_id = event_data.get("id")
    event_type = event_data.get("event")

    # Check idempotency
    if event_id and db.webhook_events.find_one({"event_id": event_id}):
        return {"status": "already_processed"}

    now = datetime.now(timezone.utc)
    db.webhook_events.insert_one({
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": event_type,
        "payload": event_data,
        "created_at": now
    })
    db_manager.persist_to_disk()

    logger.info(f"Razorpay Webhook event received: {event_type} ({event_id})")
    return {"status": "ok"}
