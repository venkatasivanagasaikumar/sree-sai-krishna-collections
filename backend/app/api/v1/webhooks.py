from fastapi import APIRouter, Request, Response, HTTPException, status, Query
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger
from app.database import get_db, db_manager
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.get("/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Official Meta WhatsApp Business Cloud API webhook verification.
    Meta sends a GET request with hub.mode, hub.challenge, and hub.verify_token.
    """
    logger.info(f"Received WhatsApp webhook verification request: mode={hub_mode}")
    configured_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN

    if hub_mode == "subscribe" and hub_verify_token == configured_token:
        logger.info("WhatsApp webhook verified successfully.")
        # Return hub_challenge as plain text
        return Response(content=hub_challenge or "", media_type="text/plain")

    logger.warning("WhatsApp webhook verification token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp")
async def receive_whatsapp_status(request: Request):
    """
    Receives WhatsApp message status updates (sent, delivered, read, failed) from Meta Cloud API.
    Updates notification_logs idempotently.
    """
    try:
        payload = await request.json()
        logger.info(f"Received WhatsApp webhook event: {payload.get('object', 'unknown')}")
        WhatsAppService.process_webhook_payload(payload)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        # Always return 200 to acknowledge webhook so Meta does not retry incessantly
        return {"status": "error", "message": str(e)}


@router.post("/email-status")
async def receive_email_status(request: Request):
    """
    Receives delivery/bounce callbacks from transactional email providers.
    """
    try:
        payload = await request.json()
        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        event_type = payload.get("event") or payload.get("type", "delivered")
        recipient = payload.get("email") or payload.get("recipient")
        message_id = payload.get("message_id") or payload.get("sg_message_id")

        if message_id:
            db.notification_logs.update_one(
                {"external_id": message_id},
                {"$set": {"status": event_type, "webhook_updated_at": datetime.now(timezone.utc)}}
            )
            db_manager.persist_to_disk()

        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing email status webhook: {e}")
        return {"status": "error", "message": str(e)}
