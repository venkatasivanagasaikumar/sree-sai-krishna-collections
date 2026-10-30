import os
import math
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId

from app.core.config import settings
from app.core.logging import logger
from app.database import get_db, db_manager
from app.api.dependencies import get_current_user, require_admin
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/communications", tags=["Communications"])

def _serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d["_id"])
        del d["_id"]
    return d

class TestEmailRequest(BaseModel):
    recipient: EmailStr
    subject: Optional[str] = "SSK Test Notification"

class TestWhatsAppRequest(BaseModel):
    phone: str
    template: Optional[str] = "order_placed"

class UpdatePreferencesRequest(BaseModel):
    whatsapp_enabled: bool
    email_enabled: bool
    whatsapp_phone: Optional[str] = None

@router.get("/admin/status")
def get_communications_status(
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Returns live connectivity status, configuration parameters, and delivery statistics
    for both Email (SMTP) and WhatsApp Business Cloud API.
    """
    # Email stats
    email_configured = bool(settings.SMTP_USER and settings.SMTP_PASSWORD and settings.SMTP_HOST)
    
    # WhatsApp stats
    wa_configured = bool(settings.WHATSAPP_ENABLED and settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)

    # Aggregated metrics from notification logs
    pipeline = [
        {"$group": {"_id": {"channel": "$channel", "status": "$status"}, "count": {"$sum": 1}}}
    ]
    raw_stats = list(db.notification_logs.aggregate(pipeline)) if db.notification_logs else []
    
    stats_map = {
        "whatsapp": {"sent": 0, "delivered": 0, "read": 0, "failed": 0, "simulated": 0},
        "email": {"sent": 0, "delivered": 0, "failed": 0, "simulated": 0}
    }
    for item in raw_stats:
        ch = item["_id"].get("channel")
        st = item["_id"].get("status")
        cnt = item.get("count", 0)
        if ch in stats_map and st in stats_map[ch]:
            stats_map[ch][st] = cnt

    return {
        "email": {
            "is_configured": email_configured,
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT,
            "from_email": settings.EMAILS_FROM_EMAIL,
            "from_name": settings.EMAILS_FROM_NAME,
            "mode": "live_smtp" if email_configured else "simulation_logged",
            "stats": stats_map["email"]
        },
        "whatsapp": {
            "is_configured": wa_configured,
            "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID if wa_configured else "Not Set",
            "business_account_id": settings.WHATSAPP_BUSINESS_ACCOUNT_ID if wa_configured else "Not Set",
            "mode": "live_cloud_api" if wa_configured else "simulation_logged",
            "verified_templates": [
                "order_placed", "payment_confirmed", "cod_confirmation",
                "order_packed", "order_shipped", "out_for_delivery",
                "order_delivered", "order_cancelled", "refund_initiated", "refund_completed"
            ],
            "stats": stats_map["whatsapp"]
        },
        "system_time": datetime.now(timezone.utc).isoformat()
    }


@router.get("/admin/logs")
def get_notification_logs(
    channel: Optional[str] = Query(None, description="email or whatsapp"),
    status: Optional[str] = Query(None, description="sent, delivered, read, failed, simulated"),
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
    recipient: Optional[str] = Query(None, description="Filter by phone or email"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Returns paginated notification logs across Email and WhatsApp with filtering.
    """
    query: Dict[str, Any] = {}
    if isinstance(channel, str) and channel:
        query["channel"] = channel.lower()
    if isinstance(status, str) and status:
        query["status"] = status.lower()
    if isinstance(order_id, str) and order_id.strip():
        query["order_id"] = {"$regex": order_id.strip(), "$options": "i"}
    if isinstance(recipient, str) and recipient.strip():
        query["recipient"] = {"$regex": recipient.strip(), "$options": "i"}
        query["recipient"] = {"$regex": recipient.strip(), "$options": "i"}

    total_count = db.notification_logs.count_documents(query)
    skip = (page - 1) * limit
    logs = list(
        db.notification_logs.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return {
        "items": [_serialize_doc(log) for log in logs],
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total_count / limit) if total_count > 0 else 1
    }


@router.post("/admin/test-email")
def test_email_dispatch(
    payload: TestEmailRequest,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Sends a test transactional email to verify SMTP and template rendering.
    """
    res = EmailService.send_email(
        to_email=payload.recipient,
        subject=payload.subject or "SSK Collections - Test Notification",
        html_body=f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1E293B;">
            <h2 style="color: #123F7A;">Sree Sai Krishna Collections</h2>
            <p>This is a test notification confirming your transactional email subsystem is operational.</p>
            <p style="font-size: 12px; color: #64748B;">Dispatched by: {current_user.get('email')} at {datetime.now(timezone.utc).strftime('%d-%b-%Y %H:%M UTC')}</p>
        </div>
        """,
        text_body="Sree Sai Krishna Collections - Test Notification confirming your email subsystem is operational.",
        template_name="admin_test"
    )
    return res


@router.post("/admin/test-whatsapp")
def test_whatsapp_dispatch(
    payload: TestWhatsAppRequest,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Sends a test WhatsApp template notification via the Cloud API or simulator.
    """
    res = WhatsAppService.send_template_notification(
        to_phone=payload.phone,
        template_key=payload.template or "order_placed",
        template_params={
            "customer_name": "Valued Customer (Test)",
            "order_id": "SSK-TEST-9999",
            "amount": "1499.00",
            "payment_method": "Prepaid",
            "tracking_url": f"{settings.FRONTEND_URL}/account/orders/SSK-TEST-9999"
        },
        order_id="SSK-TEST-9999"
    )
    return res


@router.post("/admin/{notification_id}/retry")
def retry_failed_notification(
    notification_id: str,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Manually retries a previously failed or simulated notification.
    """
    try:
        res = NotificationService.retry_notification(notification_id)
        return {
            "success": True,
            "message": "Retry executed successfully",
            "result": res
        }
    except Exception as e:
        logger.error(f"Error retrying notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/preferences")
def get_customer_preferences(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Returns authenticated customer's communication preferences (Email & WhatsApp opt-in).
    """
    user_id = str(current_user["id"])
    pref = db.communication_preferences.find_one({"user_id": user_id})

    if not pref:
        return {
            "user_id": user_id,
            "whatsapp_enabled": True,
            "email_enabled": True,
            "whatsapp_phone": current_user.get("phone", "")
        }

    return _serialize_doc(pref)


@router.put("/customer/preferences")
def update_customer_preferences(
    payload: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Updates authenticated customer's communication preferences with audit timestamp.
    """
    user_id = str(current_user["id"])
    now = datetime.now(timezone.utc)

    pref_doc = {
        "user_id": user_id,
        "email": current_user.get("email"),
        "whatsapp_enabled": payload.whatsapp_enabled,
        "email_enabled": payload.email_enabled,
        "whatsapp_phone": payload.whatsapp_phone or current_user.get("phone", ""),
        "updated_at": now
    }

    db.communication_preferences.update_one(
        {"user_id": user_id},
        {"$set": pref_doc},
        upsert=True
    )

    # Record consent log for compliance
    db.communication_consents.insert_one({
        "consent_id": f"cns_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "channel": "whatsapp",
        "consented": payload.whatsapp_enabled,
        "phone": payload.whatsapp_phone or current_user.get("phone", ""),
        "timestamp": now,
        "source": "account_preferences"
    })
    db_manager.persist_to_disk()

    return {
        "success": True,
        "message": "Communication preferences updated successfully",
        "preferences": pref_doc
    }
