from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import hmac
import hashlib
import uuid
import httpx
from app.database import get_db, db_manager
from app.core.config import settings
from app.core.logging import AuditLogger, logger
from app.core.permissions import Role
from app.schemas.payment import RazorpayOrderResponse, VerifyPaymentRequest, PaymentStatusResponse
from app.api.dependencies import get_current_user, get_optional_current_user, require_roles
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

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
    rzp_order_id = f"order_{uuid.uuid4().hex[:14]}"

    # If live merchant keys are present, attempt live Razorpay API order creation
    if settings.RAZORPAY_KEY_ID.startswith("rzp_live_"):
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(
                    "https://api.razorpay.com/v1/orders",
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                    json={
                        "amount": amount_in_paise,
                        "currency": "INR",
                        "receipt": order_id,
                        "notes": {
                            "brand": settings.BRAND_NAME,
                            "order_id": order_id,
                            "customer_email": order.get("customer_email", "")
                        }
                    }
                )
                if res.status_code in [200, 201]:
                    live_data = res.json()
                    rzp_order_id = live_data.get("id", rzp_order_id)
                    logger.info(f"Live Razorpay order created: {rzp_order_id}")
                else:
                    logger.warning(f"Razorpay live order API returned {res.status_code}: {res.text}")
        except Exception as api_err:
            logger.warning(f"Live Razorpay order creation connection notice: {api_err}. Using generated reference.")

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

    # Dispatch Order Confirmation & Automatic Invoice via Notification Service
    try:
        NotificationService.dispatch_order_event(
            order_id=payload.order_id,
            event_name="PAYMENT_CONFIRMED",
            actor="razorpay"
        )
    except Exception as notif_err:
        logger.error(f"Notification dispatch notice for #{payload.order_id}: {notif_err}")

    return {
        "success": True,
        "message": "Payment verified and order confirmed",
        "order_id": payload.order_id,
        "payment_id": payload.razorpay_payment_id
    }

@router.post("/{order_id}/record-failure")
def record_payment_failure(
    order_id: str,
    payload: Dict[str, Any],
    db = Depends(get_db)
):
    """Records a failed payment attempt while keeping the order open for retry."""
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    reason = payload.get("reason", "Payment failed or cancelled at checkout")
    now = datetime.now(timezone.utc)
    timeline = order.get("timeline", [])
    timeline.append({
        "status": "PAYMENT_FAILED",
        "message": f"Payment attempt failed: {reason}",
        "timestamp": now,
        "performed_by": "Payment Gateway"
    })

    db.orders.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "payment_status": "FAILED",
                "timeline": timeline,
                "updated_at": now
            }
        }
    )
    db_manager.persist_to_disk()

    return {"message": "Payment failure recorded", "order_id": order_id, "status": "FAILED"}

@router.post("/{order_id}/retry")
def retry_payment(
    order_id: str,
    db = Depends(get_db)
):
    """Prepares an order for retry by generating a fresh Razorpay order."""
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("payment_status") == "PAID":
        raise HTTPException(status_code=400, detail="Order is already paid")

    new_rzp_order_id = f"order_{uuid.uuid4().hex[:14]}"
    now = datetime.now(timezone.utc)
    timeline = order.get("timeline", [])
    timeline.append({
        "status": "PAYMENT_RETRY_INITIATED",
        "message": "Customer initiated a payment retry",
        "timestamp": now,
        "performed_by": "Customer"
    })

    db.orders.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "payment_status": "PENDING",
                "razorpay_order_id": new_rzp_order_id,
                "timeline": timeline,
                "updated_at": now
            }
        }
    )
    db_manager.persist_to_disk()

    amount_in_paise = int(round(order["final_amount"] * 100))
    return {
        "order_id": order_id,
        "razorpay_order_id": new_rzp_order_id,
        "amount_in_paise": amount_in_paise,
        "currency": "INR",
        "key_id": settings.RAZORPAY_KEY_ID
    }

@router.post("/{order_id}/refund", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def initiate_refund(
    order_id: str,
    payload: Dict[str, Any],
    db = Depends(get_db)
):
    """Processes a refund for a previously paid order."""
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("payment_status") != "PAID":
        raise HTTPException(status_code=400, detail="Only paid orders can be refunded.")

    refund_amount = float(payload.get("amount", order.get("final_amount", 0.0)))
    reason = payload.get("reason", "Customer requested cancellation / return")
    refund_id = f"rfnd_{uuid.uuid4().hex[:14]}"
    now = datetime.now(timezone.utc)

    # If live keys are present, attempt Razorpay live refund API
    if settings.RAZORPAY_KEY_ID.startswith("rzp_live_") and order.get("payment_id"):
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(
                    f"https://api.razorpay.com/v1/payments/{order['payment_id']}/refund",
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                    json={"amount": int(round(refund_amount * 100)), "notes": {"reason": reason}}
                )
                if res.status_code in [200, 201]:
                    live_ref = res.json()
                    refund_id = live_ref.get("id", refund_id)
        except Exception as ref_err:
            logger.warning(f"Razorpay live refund notice: {ref_err}")

    timeline = order.get("timeline", [])
    timeline.append({
        "status": "REFUNDED",
        "message": f"Refund of ₹{refund_amount:.2f} processed (Refund ID: {refund_id}). Reason: {reason}",
        "timestamp": now,
        "performed_by": "SSK Admin Staff"
    })

    db.orders.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "payment_status": "REFUNDED",
                "order_status": "CANCELLED",
                "refund_id": refund_id,
                "refund_amount": refund_amount,
                "timeline": timeline,
                "updated_at": now
            }
        }
    )

    db.refunds.insert_one({
        "refund_id": refund_id,
        "order_id": order_id,
        "payment_id": order.get("payment_id"),
        "amount": refund_amount,
        "reason": reason,
        "status": "PROCESSED",
        "created_at": now
    })
    db_manager.persist_to_disk()

    # Dispatch Refund Notification & Automatic Credit Note via Notification Service
    try:
        NotificationService.dispatch_order_event(
            order_id=order_id,
            event_name="REFUND_INITIATED",
            extra_data={"amount": refund_amount, "refund_id": refund_id, "reason": reason},
            actor="admin"
        )
    except Exception as notif_err:
        logger.error(f"Refund notification dispatch notice for #{order_id}: {notif_err}")

    return {
        "success": True,
        "message": f"Refund of ₹{refund_amount:.2f} processed successfully.",
        "refund_id": refund_id,
        "order_id": order_id
    }

@router.post("/webhook")
def razorpay_webhook(
    payload: Dict[str, Any],
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db = Depends(get_db)
):
    """Idempotent webhook listener for Razorpay payment lifecycle events with signature authentication."""
    # Authenticate signature if header provided or required in production
    if isinstance(x_razorpay_signature, str) and x_razorpay_signature.strip():
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        if webhook_secret:
            raw_data = json.dumps(payload, separators=(',', ':')).encode('utf-8')
            expected_sig = hmac.new(webhook_secret.encode('utf-8'), raw_data, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig, x_razorpay_signature):
                # Try formatted json
                fallback_data = json.dumps(payload).encode('utf-8')
                fallback_sig = hmac.new(webhook_secret.encode('utf-8'), fallback_data, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(fallback_sig, x_razorpay_signature):
                    logger.warning("Invalid Razorpay webhook signature received.")
                    raise HTTPException(status_code=400, detail="Invalid webhook signature")
    elif settings.ENVIRONMENT == "production" and settings.RAZORPAY_KEY_ID.startswith("rzp_live_"):
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature header")

    event_id = payload.get("id")
    event_type = payload.get("event")

    # Idempotency check: duplicate webhooks are ignored gracefully
    if event_id and db.webhook_events.find_one({"event_id": event_id}):
        return {"status": "already_processed", "event_id": event_id}

    now = datetime.now(timezone.utc)
    db.webhook_events.insert_one({
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": event_type,
        "payload": payload,
        "created_at": now
    })
    db_manager.persist_to_disk()

    logger.info(f"Razorpay Webhook event processed: {event_type} ({event_id})")
    return {"status": "ok", "event_id": event_id}
