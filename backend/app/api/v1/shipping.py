from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from app.database import get_db, db_manager
from app.core.config import settings
from app.core.logging import AuditLogger, logger
from app.core.permissions import Role
from app.api.dependencies import get_current_user, require_roles
from app.services.shipping_service import ShippingService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/shipping", tags=["Shipping & Logistics"])

@router.get("/serviceability/{pincode}")
def check_pincode_serviceability(pincode: str):
    """Checks domestic delivery timeline and COD availability for a PIN code."""
    res = ShippingService.check_serviceability(pincode)
    return res

@router.post("/orders/{order_id}/create-shipment", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN, Role.ORDER_MANAGER]))])
def create_shipment(
    order_id: str,
    payload: Dict[str, Any],
    db = Depends(get_db)
):
    """Dispatches an order, assigns carrier and AWB tracking details, and triggers customer dispatch email."""
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    carrier = payload.get("carrier", "Blue Dart Express")
    awb = payload.get("awb", f"SSK{uuid.uuid4().hex[:10].upper()}")
    tracking_url = payload.get("tracking_url", f"https://track.sskcollections.in/{awb}")

    now = datetime.now(timezone.utc)
    tracking_info = {
        "carrier": carrier,
        "awb": awb,
        "tracking_url": tracking_url,
        "shipped_at": now,
        "status": "SHIPPED"
    }

    timeline = order.get("timeline", [])
    timeline.append({
        "status": "SHIPPED",
        "message": f"Order dispatched via {carrier} (AWB: {awb})",
        "timestamp": now,
        "performed_by": "SSK Fulfillment Center"
    })

    db.orders.update_one(
        {"order_id": order_id},
        {
            "$set": {
                "order_status": "SHIPPED",
                "tracking": tracking_info,
                "timeline": timeline,
                "updated_at": now
            }
        }
    )
    db_manager.persist_to_disk()

    # Dispatch shipment notification via Notification Service
    try:
        NotificationService.dispatch_order_event(
            order_id=order_id,
            event_name="ORDER_SHIPPED",
            extra_data={"tracking": tracking_info},
            actor="logistics"
        )
    except Exception as mail_err:
        logger.warning(f"Shipment notification notice: {mail_err}")

    return {
        "message": "Shipment created successfully",
        "order_id": order_id,
        "tracking": tracking_info
    }

@router.get("/orders/{order_id}/label", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN, Role.ORDER_MANAGER]))])
def get_shipping_label(
    order_id: str,
    db = Depends(get_db)
):
    """Generates print-ready thermal shipping label HTML."""
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tracking_info = order.get("tracking") or {
        "carrier": "Blue Dart Express",
        "awb": f"SSK{order_id.replace('-', '')}"
    }

    html = ShippingService.generate_shipping_label_html(order, tracking_info)
    return Response(content=html, media_type="text/html")

@router.post("/webhook")
def shipping_carrier_webhook(payload: Dict[str, Any], db = Depends(get_db)):
    """Receives courier milestone updates (IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, RTO)."""
    awb = payload.get("awb")
    milestone = payload.get("status", "").upper() # e.g. DELIVERED
    if not awb:
        raise HTTPException(status_code=400, detail="Missing AWB in webhook payload")

    order = db.orders.find_one({"tracking.awb": awb})
    if not order:
        return {"status": "order_not_found_ignored"}

    now = datetime.now(timezone.utc)
    new_status = order["order_status"]
    if milestone in ["DELIVERED", "COMPLETED"]:
        new_status = "DELIVERED"
        if order.get("payment_method") == "COD":
            db.orders.update_one(
                {"_id": order["_id"]},
                {"$set": {"payment_status": "PAID", "cod_collected_at": now}}
            )

    tracking = order.get("tracking") or {}
    tracking["status"] = milestone

    timeline = order.get("timeline", [])
    timeline.append({
        "status": milestone,
        "message": f"Courier tracking status updated: {milestone}",
        "timestamp": now,
        "performed_by": "Logistics Carrier Webhook"
    })

    db.orders.update_one(
        {"_id": order["_id"]},
        {
            "$set": {
                "order_status": new_status,
                "tracking": tracking,
                "timeline": timeline,
                "updated_at": now
            }
        }
    )
    db_manager.persist_to_disk()

    # Dispatch delivery or out-for-delivery notification
    try:
        if milestone in ["DELIVERED", "COMPLETED"]:
            NotificationService.dispatch_order_event(
                order_id=order["order_id"],
                event_name="ORDER_DELIVERED",
                actor="courier_webhook"
            )
        elif milestone == "OUT_FOR_DELIVERY":
            NotificationService.dispatch_order_event(
                order_id=order["order_id"],
                event_name="OUT_FOR_DELIVERY",
                extra_data={"tracking": tracking},
                actor="courier_webhook"
            )
    except Exception as notif_err:
        logger.warning(f"Carrier webhook notification notice: {notif_err}")

    return {"status": "success", "order_id": order["order_id"], "new_status": new_status}

@router.get("/cod-reconciliation", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def get_cod_reconciliation(db = Depends(get_db)):
    """Reconciles Cash on Delivery collections, delivered orders, and remittances."""
    cod_orders = list(db.orders.find({"payment_method": "COD"}))
    total_cod_orders = len(cod_orders)
    
    total_cod_value = sum(o.get("final_amount", 0.0) for o in cod_orders)
    collected_orders = [o for o in cod_orders if o.get("payment_status") == "PAID" or o.get("order_status") == "DELIVERED"]
    collected_value = sum(o.get("final_amount", 0.0) for o in collected_orders)
    pending_collection = total_cod_value - collected_value

    return {
        "total_cod_orders": total_cod_orders,
        "total_cod_value": total_cod_value,
        "collected_orders_count": len(collected_orders),
        "collected_value": collected_value,
        "pending_collection_value": pending_collection,
        "currency": "INR"
    }
