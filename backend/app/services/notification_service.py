import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService
from app.services.invoice_service import InvoiceService

class NotificationService:
    @classmethod
    def dispatch_order_event(
        cls,
        order_id: str,
        event_name: str,
        extra_data: Optional[Dict[str, Any]] = None,
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Centralized event orchestrator:
        1. Validates and logs notification event (with idempotency check).
        2. Automatically generates GST Tax Invoice or Credit Note if applicable.
        3. Enqueues and processes Email and WhatsApp dispatches respecting customer preferences.
        """
        extra_data = extra_data or {}
        now = datetime.now(timezone.utc)
        event_id = f"evt_{order_id}_{event_name.lower()}_{now.strftime('%Y%m%d%H%M')}"

        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        order = db.orders.find_one({"order_id": order_id})
        if not order:
            logger.warning(f"Notification triggered for non-existent order #{order_id}")
            return {"success": False, "error": f"Order #{order_id} not found."}

        # Idempotency check: prevent duplicate event processing within short window
        existing_event = db.notification_events.find_one({"order_id": order_id, "event_type": event_name})
        if existing_event and not extra_data.get("force_resend", False):
            logger.info(f"Notification event {event_name} already dispatched for order #{order_id}. Skipping.")
            return {"success": True, "status": "already_dispatched", "event_id": existing_event.get("event_id")}

        # Record notification event
        db.notification_events.insert_one({
            "event_id": event_id,
            "order_id": order_id,
            "event_type": event_name,
            "actor": actor,
            "extra_data": extra_data,
            "created_at": now
        })

        customer_name = order.get("customer_name") or "Valued Customer"
        customer_email = order.get("customer_email") or ""
        customer_phone = order.get("customer_phone") or (order.get("shipping_address") or {}).get("phone", "")
        total_amount = float(order.get("final_amount", order.get("total_amount", 0.0)))
        tracking_url = f"{settings.FRONTEND_URL}/account/orders/{order_id}"

        # 1. Invoice Generation Trigger
        invoice_number = None
        invoice_pdf_path = None
        if event_name in ["PAYMENT_CONFIRMED", "COD_CONFIRMED", "ORDER_CONFIRMED"]:
            try:
                inv = InvoiceService.generate_or_get_invoice(order_id)
                invoice_number = inv.get("invoice_number")
                invoice_pdf_path = inv.get("pdf_path")
            except Exception as inv_err:
                logger.warning(f"Invoice generation notice for #{order_id}: {inv_err}")
        elif event_name in ["REFUND_INITIATED", "ORDER_CANCELLED"] and order.get("payment_status") == "PAID":
            try:
                cn = InvoiceService.generate_or_get_invoice(order_id, is_credit_note=True)
                invoice_number = cn.get("invoice_number")
                invoice_pdf_path = cn.get("pdf_path")
            except Exception as cn_err:
                logger.warning(f"Credit note generation notice for #{order_id}: {cn_err}")

        # Outbox Queue Record
        outbox_id = f"out_{uuid.uuid4().hex[:14]}"
        db.notification_outbox.insert_one({
            "outbox_id": outbox_id,
            "event_id": event_id,
            "order_id": order_id,
            "event_type": event_name,
            "status": "processing",
            "created_at": now
        })

        results = {"email": None, "whatsapp": None}

        # 2. Email Dispatch
        if customer_email:
            try:
                if event_name in ["ORDER_PLACED", "PAYMENT_CONFIRMED", "COD_CONFIRMED", "ORDER_CONFIRMED"]:
                    results["email"] = EmailService.send_order_confirmation(customer_email, order, invoice_number)
                elif event_name == "ORDER_PACKED":
                    results["email"] = EmailService.send_order_packed(customer_email, order)
                elif event_name == "ORDER_SHIPPED":
                    tracking_info = extra_data.get("tracking") or order.get("tracking") or {}
                    results["email"] = EmailService.send_shipment_notification(customer_email, order, tracking_info)
                elif event_name == "OUT_FOR_DELIVERY":
                    tracking_info = extra_data.get("tracking") or order.get("tracking") or {}
                    results["email"] = EmailService.send_out_for_delivery(customer_email, order, tracking_info)
                elif event_name == "ORDER_DELIVERED":
                    results["email"] = EmailService.send_order_delivered(customer_email, order)
                elif event_name == "ORDER_CANCELLED":
                    results["email"] = EmailService.send_cancellation_notification(customer_email, order, extra_data.get("reason", ""))
                elif event_name in ["REFUND_INITIATED", "REFUND_COMPLETED"]:
                    results["email"] = EmailService.send_refund_notification(
                        customer_email, order_id, extra_data.get("amount", total_amount), extra_data.get("reason", "")
                    )
            except Exception as eml_err:
                logger.error(f"Failed to dispatch email for order #{order_id}: {eml_err}")
                results["email"] = {"success": False, "error": str(eml_err)}

        # 3. WhatsApp Dispatch
        if customer_phone:
            wa_template = None
            wa_params = {
                "customer_name": customer_name,
                "order_id": order_id,
                "amount": f"{total_amount:.2f}",
                "payment_method": order.get("payment_method", "Prepaid"),
                "tracking_url": tracking_url
            }

            if event_name in ["ORDER_PLACED"]:
                wa_template = "order_placed"
            elif event_name in ["PAYMENT_CONFIRMED"]:
                wa_template = "payment_confirmed"
            elif event_name in ["COD_CONFIRMED"]:
                wa_template = "cod_confirmation"
            elif event_name == "ORDER_PACKED":
                wa_template = "order_packed"
            elif event_name == "ORDER_SHIPPED":
                wa_template = "order_shipped"
                tracking_info = extra_data.get("tracking") or order.get("tracking") or {}
                wa_params["courier_name"] = tracking_info.get("carrier", "Blue Dart Express")
                wa_params["tracking_number"] = tracking_info.get("awb", "SSK-TRACK")
            elif event_name == "OUT_FOR_DELIVERY":
                wa_template = "out_for_delivery"
            elif event_name == "ORDER_DELIVERED":
                wa_template = "order_delivered"
            elif event_name == "ORDER_CANCELLED":
                wa_template = "order_cancelled"
                wa_params["support_phone"] = settings.SUPPORT_PHONE
            elif event_name in ["REFUND_INITIATED"]:
                wa_template = "refund_initiated"
            elif event_name in ["REFUND_COMPLETED"]:
                wa_template = "refund_completed"
                wa_params["refund_ref"] = extra_data.get("refund_id", "REF-DONE")

            if wa_template:
                try:
                    results["whatsapp"] = WhatsAppService.send_template_notification(
                        to_phone=customer_phone,
                        template_key=wa_template,
                        template_params=wa_params,
                        order_id=order_id
                    )
                except Exception as wa_err:
                    logger.error(f"Failed to dispatch WhatsApp for order #{order_id}: {wa_err}")
                    results["whatsapp"] = {"success": False, "error": str(wa_err)}

        # Update outbox status to completed
        db.notification_outbox.update_one(
            {"outbox_id": outbox_id},
            {"$set": {"status": "completed", "results": results, "completed_at": datetime.now(timezone.utc)}}
        )
        db_manager.persist_to_disk()

        return {
            "success": True,
            "order_id": order_id,
            "event_name": event_name,
            "invoice_number": invoice_number,
            "results": results
        }

    @classmethod
    def retry_notification(cls, notification_id: str) -> Dict[str, Any]:
        """Retries a failed notification record."""
        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        record = db.notification_logs.find_one({"notification_id": notification_id})
        if not record:
            raise ValueError(f"Notification record {notification_id} not found.")

        channel = record.get("channel")
        order_id = record.get("order_id")
        template_name = record.get("template_name")

        now = datetime.now(timezone.utc)
        order = (db.orders.find_one({"order_id": order_id}) if order_id else None) or {}

        if channel == "whatsapp":
            res = WhatsAppService.send_template_notification(
                to_phone=record.get("recipient"),
                template_key=template_name,
                template_params={
                    "customer_name": order.get("customer_name", "Customer"),
                    "order_id": order_id or "",
                    "amount": f"{order.get('final_amount', 0.0):.2f}",
                    "tracking_url": f"{settings.FRONTEND_URL}/account/orders/{order_id}"
                },
                order_id=order_id
            )
            db.notification_logs.update_one(
                {"notification_id": notification_id},
                {"$set": {"status": res.get("status"), "retry_at": now, "error": res.get("error")}}
            )
            db_manager.persist_to_disk()
            return res
        elif channel == "email":
            res = EmailService.send_email(
                to_email=record.get("recipient"),
                subject=record.get("subject", "Order Notification - SSK Collections"),
                html_body=f"<p>{record.get('message_body', record.get('preview', ''))}</p>",
                text_body=record.get("preview", ""),
                template_name=template_name or "retry",
                order_id=order_id
            )
            db.notification_logs.update_one(
                {"notification_id": notification_id},
                {"$set": {"status": res.get("status"), "retry_at": now, "error": res.get("error")}}
            )
            db_manager.persist_to_disk()
            return res

        return {"success": False, "error": f"Unsupported channel: {channel}"}
