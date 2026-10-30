import re
import uuid
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager

# Standard Meta pre-approved template definitions and parameters
TEMPLATES = {
    "order_placed": {
        "name": "ssk_order_placed_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}! Thank you for shopping with Sree Sai Krishna Collections. Your order {{order_id}} for ₹{{amount}} has been placed successfully via {{payment_method}}. Track here: {{tracking_url}}"
    },
    "payment_confirmed": {
        "name": "ssk_payment_confirmed_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}! We have received your payment of ₹{{amount}} for SSK Order {{order_id}}. Our team is now preparing your exquisite jewellery pieces."
    },
    "cod_confirmation": {
        "name": "ssk_cod_confirmation_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}! Your Cash on Delivery order {{order_id}} for ₹{{amount}} is confirmed. Please keep exact cash ready upon delivery."
    },
    "order_packed": {
        "name": "ssk_order_packed_v1",
        "category": "UTILITY",
        "text": "Great news {{customer_name}}! Your SSK order {{order_id}} has been securely packed with utmost care and is awaiting courier pickup."
    },
    "order_shipped": {
        "name": "ssk_order_shipped_v1",
        "category": "UTILITY",
        "text": "Great news, {{customer_name}}! Your SSK order {{order_id}} has been shipped via {{courier_name}} (AWB: {{tracking_number}}). Track your parcel here: {{tracking_url}}"
    },
    "out_for_delivery": {
        "name": "ssk_out_for_delivery_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}! Your SSK order {{order_id}} is OUT FOR DELIVERY today with courier executive. Track: {{tracking_url}}"
    },
    "order_delivered": {
        "name": "ssk_order_delivered_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}! Your SSK order {{order_id}} has been successfully delivered. We hope you love your purchase! Thank you for choosing Sree Sai Krishna Collections."
    },
    "order_cancelled": {
        "name": "ssk_order_cancelled_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}, your order {{order_id}} has been cancelled. If any payment was made, your refund is being initiated. Helpline: {{support_phone}}"
    },
    "refund_initiated": {
        "name": "ssk_refund_initiated_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}, a refund of ₹{{amount}} has been initiated for order {{order_id}}. Funds typically credit to your bank account within 5-7 business days."
    },
    "refund_completed": {
        "name": "ssk_refund_completed_v1",
        "category": "UTILITY",
        "text": "Hello {{customer_name}}, your refund of ₹{{amount}} for order {{order_id}} has been completed. Reference: {{refund_ref}}."
    }
}

class WhatsAppService:
    @staticmethod
    def format_phone_number(phone: str) -> Optional[str]:
        """Normalizes Indian phone numbers into international format without + or spaces (e.g. 919848022338)."""
        if not phone:
            return None
        # Remove non-digit characters
        digits = re.sub(r"\D", "", str(phone))
        if len(digits) == 10:
            return f"91{digits}"
        if len(digits) == 12 and digits.startswith("91"):
            return digits
        if len(digits) == 11 and digits.startswith("0"):
            return f"91{digits[1:]}"
        return digits if len(digits) >= 10 else None

    # Alias for normalization
    normalize_indian_phone = format_phone_number

    @classmethod
    def build_meta_payload(
        cls,
        to_phone: str,
        template_name: str,
        body_params: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Constructs an official Meta WhatsApp Cloud API v19.0 payload dictionary."""
        formatted = cls.format_phone_number(to_phone)
        components = []
        if body_params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": str(p)} for p in body_params]
            })
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": formatted,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": components
            }
        }

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if Meta WhatsApp Business API credentials are fully provided."""
        return bool(
            settings.WHATSAPP_ENABLED and
            settings.WHATSAPP_PHONE_NUMBER_ID and
            settings.WHATSAPP_ACCESS_TOKEN
        )

    @classmethod
    def render_template_text(cls, template_key: str, params: Dict[str, Any]) -> str:
        """Substitutes variables inside pre-approved template message text."""
        tpl = TEMPLATES.get(template_key)
        if not tpl:
            return f"Notification regarding SSK Order #{params.get('order_id', '')}"
        text = tpl["text"]
        for key, val in params.items():
            text = text.replace(f"{{{{{key}}}}}", str(val))
        return text

    @classmethod
    def send_template_notification(
        cls,
        to_phone: str,
        template_key: str,
        template_params: Dict[str, Any],
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches a WhatsApp Business template message via Meta Cloud API,
        or logs to database in simulated mode if live API credentials are unset.
        """
        formatted_phone = cls.format_phone_number(to_phone)
        if not formatted_phone:
            logger.warning(f"Invalid phone number '{to_phone}' for WhatsApp dispatch.")
            return {
                "success": False,
                "status": "failed",
                "error": f"Invalid Indian mobile number format: '{to_phone}'"
            }

        rendered_message = cls.render_template_text(template_key, template_params)
        notification_id = f"wa_msg_{uuid.uuid4().hex[:14]}"
        now = datetime.now(timezone.utc)

        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        # Check if customer has opted out of WhatsApp notifications
        pref = db.communication_preferences.find_one({
            "$or": [
                {"whatsapp_number": formatted_phone},
                {"whatsapp_phone": formatted_phone},
                {"whatsapp_phone": str(to_phone)}
            ]
        })
        if pref and (pref.get("whatsapp_enabled") is False or pref.get("whatsapp_order_updates") is False):
            logger.info(f"Customer with phone {formatted_phone} opted out of WhatsApp updates. Notification skipped.")
            log_record = {
                "notification_id": notification_id,
                "channel": "whatsapp",
                "recipient": formatted_phone,
                "order_id": order_id,
                "template_name": template_key,
                "message_body": rendered_message,
                "status": "opted_out",
                "reason": "customer_opted_out",
                "created_at": now
            }
            db.notification_logs.insert_one(log_record)
            db_manager.persist_to_disk()
            return {"success": True, "status": "opted_out", "message": "Customer opted out of WhatsApp updates"}

        dispatch_status = "simulated_sent"
        meta_message_id = None
        error_msg = None

        if cls.is_configured():
            try:
                url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
                # Construct Meta Cloud API JSON body
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": formatted_phone,
                    "type": "template",
                    "template": {
                        "name": TEMPLATES.get(template_key, {}).get("name", template_key),
                        "language": {"code": "en"},
                        "components": [
                            {
                                "type": "body",
                                "parameters": [{"type": "text", "text": str(v)} for v in template_params.values()]
                            }
                        ]
                    }
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code in [200, 201]:
                        res_json = resp.json()
                        meta_message_id = res_json.get("messages", [{}])[0].get("id")
                        dispatch_status = "sent"
                        logger.info(f"WhatsApp message {meta_message_id} sent successfully to {formatted_phone}")
                    else:
                        dispatch_status = "failed"
                        error_msg = f"Meta API HTTP {resp.status_code}: {resp.text}"
                        logger.warning(f"Meta WhatsApp API returned {resp.status_code}: {resp.text}")
            except Exception as e:
                dispatch_status = "failed"
                error_msg = str(e)
                logger.error(f"Error calling Meta WhatsApp API: {e}")
        else:
            logger.info(f"WhatsApp Meta API not configured. Notification [{template_key}] simulated for {formatted_phone}.")

        # Record in notification_logs
        log_record = {
            "notification_id": notification_id,
            "channel": "whatsapp",
            "recipient": formatted_phone,
            "order_id": order_id,
            "template_name": template_key,
            "meta_message_id": meta_message_id,
            "message_body": rendered_message,
            "status": dispatch_status,
            "error": error_msg,
            "created_at": now
        }
        db.notification_logs.insert_one(log_record)
        db_manager.persist_to_disk()

        return {
            "success": dispatch_status in ["sent", "simulated_sent"],
            "notification_id": notification_id,
            "status": dispatch_status,
            "recipient": formatted_phone,
            "meta_message_id": meta_message_id,
            "error": error_msg
        }

    @classmethod
    def process_status_webhook(cls, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes incoming Meta delivery status updates (sent, delivered, read, failed)."""
        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        entries = webhook_payload.get("entry", [])
        updated_count = 0

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                statuses = value.get("statuses", [])
                for st in statuses:
                    meta_msg_id = st.get("id")
                    status_name = st.get("status") # sent, delivered, read, failed
                    timestamp = st.get("timestamp")

                    if meta_msg_id and status_name:
                        now = datetime.now(timezone.utc)
                        res = db.notification_logs.update_one(
                            {"$or": [{"meta_message_id": meta_msg_id}, {"external_id": meta_msg_id}]},
                            {
                                "$set": {
                                    "status": status_name,
                                    "status_updated_at": now,
                                    "meta_timestamp": timestamp
                                }
                            }
                        )
                        if res.matched_count > 0:
                            updated_count += 1
                            logger.info(f"Updated WhatsApp message {meta_msg_id} status to '{status_name}'")

        db_manager.persist_to_disk()
        return {"updated_count": updated_count}

WhatsAppService.process_webhook_payload = WhatsAppService.process_status_webhook
