import pytest
from datetime import datetime, timezone
from app.services.notification_service import NotificationService
from app.database import get_db

def test_centralized_notification_dispatch_and_invoice_issuance():
    db = get_db()
    order_id = "SSK-EVT-TEST-001"
    db.orders.delete_one({"order_id": order_id})
    db.invoices.delete_one({"order_id": order_id})
    db.notification_events.delete_many({"order_id": order_id})

    # Create test order
    db.orders.insert_one({
        "order_id": order_id,
        "user_id": "usr_evt_1",
        "customer_name": "Priya Sharma",
        "customer_email": "priya@example.com",
        "customer_phone": "9848099881",
        "items": [
            {
                "product_id": "prod_1",
                "name": "Gold Plated Temple Bangles (Set of 4)",
                "sku": "SSK-BG-01",
                "category": "Bangles",
                "quantity": 1,
                "price": 1499.0
            }
        ],
        "final_amount": 1499.0,
        "payment_method": "PREPAID",
        "payment_status": "PAID",
        "shipping_address": {
            "state": "Telangana",
            "pincode": "500003"
        }
    })

    # 1. Dispatch PAYMENT_CONFIRMED
    res = NotificationService.dispatch_order_event(
        order_id=order_id,
        event_name="PAYMENT_CONFIRMED",
        actor="razorpay_gateway"
    )

    assert res["success"] is True
    assert res["order_id"] == order_id
    assert res["invoice_number"] is not None
    assert res["invoice_number"].startswith("SSK-INV-")

    # Verify Invoice was created in database
    inv_doc = db.invoices.find_one({"order_id": order_id})
    assert inv_doc is not None
    assert inv_doc["invoice_number"] == res["invoice_number"]

    # Verify outbox record exists and was marked completed
    outbox_doc = db.notification_outbox.find_one({"order_id": order_id, "event_type": "PAYMENT_CONFIRMED"})
    assert outbox_doc is not None
    assert outbox_doc["status"] == "completed"

    # 2. Idempotency test: calling the exact same event without force_resend does not regenerate
    dup_res = NotificationService.dispatch_order_event(
        order_id=order_id,
        event_name="PAYMENT_CONFIRMED",
        actor="razorpay_gateway"
    )
    assert dup_res["success"] is True
    assert dup_res["status"] == "already_dispatched"

def test_credit_note_on_refund():
    db = get_db()
    order_id = "SSK-EVT-REFUND-002"
    db.orders.delete_one({"order_id": order_id})
    db.invoices.delete_many({"order_id": order_id})
    db.notification_events.delete_many({"order_id": order_id})

    # Create paid order
    db.orders.insert_one({
        "order_id": order_id,
        "customer_name": "Anita Rao",
        "customer_email": "anita@example.com",
        "customer_phone": "9848077665",
        "items": [
            {
                "product_id": "p2",
                "name": "Bridal Matha Patti",
                "sku": "SSK-MP-02",
                "category": "Hair Accessories",
                "quantity": 1,
                "price": 1899.0
            }
        ],
        "final_amount": 1899.0,
        "payment_method": "PREPAID",
        "payment_status": "PAID",
        "shipping_address": {"state": "Andhra Pradesh", "pincode": "530001"}
    })

    # Dispatch REFUND_INITIATED
    res = NotificationService.dispatch_order_event(
        order_id=order_id,
        event_name="REFUND_INITIATED",
        extra_data={"amount": 1899.0, "reason": "Customer cancellation"},
        actor="admin"
    )

    assert res["success"] is True
    assert res["invoice_number"] is not None
    assert res["invoice_number"].startswith("SSK-CN-")

    # Verify Credit Note doc in database
    cn_doc = db.invoices.find_one({"order_id": order_id, "invoice_type": "CREDIT_NOTE"})
    assert cn_doc is not None
    assert cn_doc["invoice_number"].startswith("SSK-CN-")

def test_notification_retry_mechanism():
    db = get_db()
    notif_id = "notif_retry_test_88"
    db.notification_logs.delete_one({"notification_id": notif_id})

    # Seed a simulated/failed record
    db.notification_logs.insert_one({
        "notification_id": notif_id,
        "channel": "whatsapp",
        "recipient": "9848012345",
        "template_name": "order_placed",
        "order_id": "SSK-RETRY-001",
        "status": "failed",
        "created_at": datetime.now(timezone.utc)
    })

    retry_res = NotificationService.retry_notification(notif_id)
    assert retry_res is not None
    assert retry_res["status"] in ["simulated", "simulated_sent", "sent"]

    # Check updated status
    updated = db.notification_logs.find_one({"notification_id": notif_id})
    assert updated["status"] in ["simulated", "simulated_sent", "sent"]
    assert "retry_at" in updated
