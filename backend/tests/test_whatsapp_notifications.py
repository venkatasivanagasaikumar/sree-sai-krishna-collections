import pytest
from fastapi import HTTPException
from app.services.whatsapp_service import WhatsAppService
from app.api.v1.webhooks import verify_whatsapp_webhook
from app.api.v1.communications import get_communications_status, get_notification_logs, retry_failed_notification
from app.core.config import settings
from app.database import get_db

def test_whatsapp_phone_number_normalization():
    assert WhatsAppService.normalize_indian_phone("9848022338") == "919848022338"
    assert WhatsAppService.normalize_indian_phone("+91 98480 22338") == "919848022338"
    assert WhatsAppService.normalize_indian_phone("098480-22338") == "919848022338"
    assert WhatsAppService.normalize_indian_phone("919848022338") == "919848022338"
    assert WhatsAppService.normalize_indian_phone("12345") is None

def test_whatsapp_template_payload_builder():
    payload = WhatsAppService.build_meta_payload(
        to_phone="9848022338",
        template_name="ssk_order_placed_v1",
        body_params=["Radha Krishna", "SSK-20261030-1001", "₹1,899.00", "Prepaid"]
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "919848022338"
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "ssk_order_placed_v1"
    assert payload["template"]["language"]["code"] == "en"
    parameters = payload["template"]["components"][0]["parameters"]
    assert len(parameters) == 4
    assert parameters[0]["text"] == "Radha Krishna"
    assert parameters[1]["text"] == "SSK-20261030-1001"

def test_whatsapp_customer_opt_out_enforcement():
    db = get_db()
    test_phone = "9988776655"
    norm_phone = "919988776655"

    # Set user preference to opted-out
    db.communication_preferences.update_one(
        {"whatsapp_phone": test_phone},
        {"$set": {"whatsapp_enabled": False, "whatsapp_phone": test_phone}},
        upsert=True
    )

    res = WhatsAppService.send_template_notification(
        to_phone=test_phone,
        template_key="order_placed",
        template_params={"customer_name": "Test User", "order_id": "SSK-OPT-1", "amount": "999.00", "payment_method": "COD"}
    )
    assert res["status"] == "opted_out"
    assert "opted out" in res["message"]

    # Now opt-in
    db.communication_preferences.update_one(
        {"whatsapp_phone": test_phone},
        {"$set": {"whatsapp_enabled": True}}
    )
    res_opt_in = WhatsAppService.send_template_notification(
        to_phone=test_phone,
        template_key="order_placed",
        template_params={"customer_name": "Test User", "order_id": "SSK-OPT-2", "amount": "999.00", "payment_method": "COD"}
    )
    assert res_opt_in["status"] in ["simulated", "simulated_sent", "sent"]

def test_whatsapp_webhook_verification():
    # Valid verification
    valid_resp = verify_whatsapp_webhook(
        hub_mode="subscribe",
        hub_challenge="1158201444",
        hub_verify_token=settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    )
    assert valid_resp.body.decode("utf-8") == "1158201444"

    # Invalid token raises 403
    with pytest.raises(HTTPException) as exc:
        verify_whatsapp_webhook(
            hub_mode="subscribe",
            hub_challenge="1158201444",
            hub_verify_token="wrong_token"
        )
    assert exc.value.status_code == 403

def test_whatsapp_webhook_status_callback_processing():
    db = get_db()
    # Insert a dummy notification record
    notif_id = "wa_status_test_99"
    external_msg_id = "wamid.HBgMOTE5ODQ4MDIyMzM4FQIAERgSRjQ1"
    db.notification_logs.delete_one({"notification_id": notif_id})
    db.notification_logs.insert_one({
        "notification_id": notif_id,
        "channel": "whatsapp",
        "external_id": external_msg_id,
        "recipient": "919848022338",
        "order_id": "SSK-STATUS-TEST",
        "status": "sent"
    })

    # Simulate Meta Cloud API webhook delivery receipt
    mock_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "100200300",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15551234567", "phone_number_id": "100200300"},
                            "statuses": [
                                {
                                    "id": external_msg_id,
                                    "status": "delivered",
                                    "timestamp": "1730300000",
                                    "recipient_id": "919848022338"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    WhatsAppService.process_webhook_payload(mock_payload)

    # Check updated record in DB
    updated = db.notification_logs.find_one({"notification_id": notif_id})
    assert updated["status"] == "delivered"

def test_admin_communications_endpoints():
    db = get_db()
    admin_user = {"id": "usr_admin_1", "email": "admin@sskcollections.com", "role": "admin"}
    status = get_communications_status(current_user=admin_user, db=db)
    assert "email" in status
    assert "whatsapp" in status
    assert len(status["whatsapp"]["verified_templates"]) >= 10

    logs_res = get_notification_logs(page=1, limit=10, current_user=admin_user, db=db)
    assert "items" in logs_res
    assert "total" in logs_res
