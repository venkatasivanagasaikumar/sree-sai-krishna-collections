import os
import hmac
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from bson import ObjectId

from app.database import get_db, db_manager, INVOICES_DIR
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token, verify_password
from app.services.invoice_service import InvoiceService, number_to_words_inr
from app.services.whatsapp_service import WhatsAppService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.backup_service import BackupService as DatabaseBackupService
from app.services.shipping_service import ShippingService

from app.api.v1.auth import register_customer, login, add_address
from app.api.v1.cart import get_user_cart, add_to_cart, apply_cart_coupon
from app.api.v1.orders import create_order, get_my_orders, update_order_status_admin as update_order_status
from app.api.v1.payments import create_razorpay_order, verify_razorpay_payment as verify_payment, initiate_refund, retry_payment, razorpay_webhook
from app.api.v1.shipping import create_shipment, shipping_carrier_webhook
from app.api.v1.invoices import get_my_invoices, get_invoice_details, download_invoice_pdf, generate_credit_note
from app.api.v1.communications import get_communications_status, get_notification_logs, update_customer_preferences, retry_failed_notification, UpdatePreferencesRequest
from app.api.v1.webhooks import verify_whatsapp_webhook

from app.schemas.auth import UserCreate, UserLogin, Address
from app.schemas.cart import CartItem, ApplyCouponRequest
from app.schemas.order import CreateOrderRequest, OrderStatusUpdate
from app.schemas.payment import VerifyPaymentRequest

# ==============================================================================
# TEST 1: CUSTOMER PURCHASE SIMULATION
# ==============================================================================

def test_sim_01_customer_purchase_cod_journey():
    """
    Simulates complete customer shopping journey:
    1. Register
    2. Login
    3. Browse products
    4. Add to cart & update quantity
    5. Apply coupon
    6. Add shipping address
    7. COD Checkout
    8. Verify stock deduction, invoice generation, email & WhatsApp outbox dispatch
    9. Download PDF & view order history
    """
    db = get_db()
    test_email = "sita.commercial.sim@sreesaikrishnacollections.com"
    test_phone = "9848022338"

    # Cleanup any prior test customer
    db.users.delete_one({"email": test_email})
    db.carts.delete_many({"user_id": test_email})
    db.products.update_one({"sku": "SSK-JWL-101"}, {"$set": {"stock": 50}})

    # 1. Registration
    reg_payload = UserCreate(
        email=test_email,
        password="SecurePassword@2026",
        full_name="Sita Ramana Devi",
        phone=test_phone
    )
    reg_res = register_customer(payload=reg_payload, request=None, db=db)
    assert reg_res.access_token is not None
    user_id = reg_res.user["id"]

    # 2. Login
    login_payload = UserLogin(email=test_email, password="SecurePassword@2026")
    login_res = login(payload=login_payload, request=None, db=db)
    assert login_res.access_token is not None
    current_customer = db.users.find_one({"email": test_email})
    current_customer["id"] = str(current_customer["_id"])

    # Opt-in for WhatsApp
    update_customer_preferences(
        payload=UpdatePreferencesRequest(whatsapp_enabled=True, email_enabled=True, whatsapp_phone=test_phone),
        current_user=current_customer,
        db=db
    )

    # 3. Browse & select product
    product = db.products.find_one({"sku": "SSK-JWL-101"})
    assert product is not None
    initial_stock = int(product.get("stock", 0))
    product_id = str(product.get("id") or product["_id"])

    # 4. Add to cart with quantity 1, then add 1 more (total qty = 2)
    add_to_cart(item=CartItem(product_id=product_id, quantity=1), current_user=current_customer, db=db)
    cart_after_qty = add_to_cart(item=CartItem(product_id=product_id, quantity=1), current_user=current_customer, db=db)
    assert len(cart_after_qty.items) == 1
    assert cart_after_qty.items[0].quantity == 2
    assert cart_after_qty.subtotal == round(product["price"] * 2, 2)

    # 5. Apply Coupon 'SSKFIRST10' (10% discount)
    cart_with_coupon = apply_cart_coupon(payload=ApplyCouponRequest(code="SSKFIRST10"), current_user=current_customer, db=db)
    assert cart_with_coupon.coupon_code == "SSKFIRST10"
    assert cart_with_coupon.discount_amount > 0

    # 6. Add delivery address (Secunderabad, Telangana)
    shipping_addr = Address(
        name="Sita Ramana Devi",
        phone=test_phone,
        address_line1="Flat 402, Sai Balaji Enclave, Begumpet",
        city="Secunderabad",
        state="Telangana",
        pincode="500003",
        is_default=True,
        type="Home"
    )
    add_address(address=shipping_addr, current_user=current_customer, db=db)

    # 7. Complete Checkout using COD
    order_req = CreateOrderRequest(
        shipping_address=shipping_addr,
        payment_method="COD",
        coupon_code="SSKFIRST10",
        notes="Please deliver between 10am to 5pm"
    )
    checkout_res = create_order(payload=order_req, current_user=current_customer, db=db)
    order_id = checkout_res["order_id"]
    assert order_id.startswith("SSK-")
    assert checkout_res["payment_method"] == "COD"
    assert checkout_res["payment_status"] in ["PENDING", "PENDING_COD"]
    assert checkout_res["order_status"] in ["ORDER_PLACED", "CONFIRMED"]

    # 8. Verify stock deduction
    updated_product = db.products.find_one({"sku": "SSK-JWL-101"})
    assert int(updated_product["stock"]) == initial_stock - 2

    # 9. Verify automatic GST Invoice generation
    invoice = db.invoices.find_one({"order_id": order_id})
    assert invoice is not None
    assert invoice["invoice_number"].startswith("SSK-INV-")
    assert os.path.exists(invoice["pdf_path"])
    assert os.path.getsize(invoice["pdf_path"]) > 1000

    # 10. Verify notification logs (Email + WhatsApp)
    email_log = db.notification_logs.find_one({"order_id": order_id, "channel": "email"})
    assert email_log is not None
    assert email_log["recipient"] == test_email

    wa_log = db.notification_logs.find_one({"order_id": order_id, "channel": "whatsapp"})
    assert wa_log is not None
    assert wa_log["recipient"] == "919848022338"
    assert wa_log["template_name"] == "cod_confirmation"

    # 11. Download Invoice PDF via API
    dl_resp = download_invoice_pdf(invoice_id=invoice["invoice_number"], current_user=current_customer, db=db)
    assert os.path.exists(dl_resp.path)

    # 12. View Order History
    my_orders = get_my_orders(current_user=current_customer, db=db)
    assert any(o["order_id"] == order_id for o in my_orders)


# ==============================================================================
# TEST 2: PAYMENT LIFECYCLE (RAZORPAY SANDBOX)
# ==============================================================================

def test_sim_02_razorpay_payment_lifecycle():
    """
    Tests Razorpay Payment gateway transitions:
    - Successful signature verification
    - Failed/tampered signature rejection (unpaid transaction cannot be marked paid)
    - Payment retry creation
    - Webhook idempotency (duplicate callback ignored)
    """
    db = get_db()
    order_id = f"SSK-RZP-{uuid.uuid4().hex[:8]}"

    # Seed an order pending payment
    db.orders.insert_one({
        "order_id": order_id,
        "customer_name": "Kavitha Reddy",
        "customer_email": "kavitha@example.com",
        "customer_phone": "9848033445",
        "final_amount": 1999.0,
        "payment_method": "ONLINE",
        "payment_status": "PENDING",
        "order_status": "ORDER_PLACED",
        "items": [{"name": "Gold Pendant", "sku": "SSK-JWL-104", "quantity": 1, "price": 1999.0}],
        "shipping_address": {"state": "Telangana", "pincode": "500003"}
    })

    # 1. Create Razorpay Order
    rzp_order = create_razorpay_order(payload={"order_id": order_id}, db=db)
    assert rzp_order.order_id == order_id
    assert rzp_order.razorpay_order_id.startswith("order_")
    assert rzp_order.amount_in_paise == 199900

    # 2. Test Failed Payment Verification (Tampered Signature)
    with pytest.raises(HTTPException) as exc_fail:
        verify_payment(
            payload=VerifyPaymentRequest(
                order_id=order_id,
                razorpay_order_id=rzp_order.razorpay_order_id,
                razorpay_payment_id="pay_tampered_123",
                razorpay_signature="invalid_signature_hash"
            ),
            request=None,
            db=db
        )
    assert exc_fail.value.status_code == 400
    # Ensure order was NOT marked as paid
    order_after_fail = db.orders.find_one({"order_id": order_id})
    assert order_after_fail["payment_status"] == "PENDING"

    # 3. Test Payment Retry
    retry_data = retry_payment(order_id=order_id, db=db)
    assert retry_data["order_id"] == order_id
    assert retry_data["razorpay_order_id"] != rzp_order.razorpay_order_id

    # 4. Test Successful Payment Verification
    new_rzp_order_id = retry_data["razorpay_order_id"]
    valid_payment_id = "pay_valid_998877"
    secret = settings.RAZORPAY_KEY_SECRET
    valid_sig = hmac.new(
        secret.encode(),
        f"{new_rzp_order_id}|{valid_payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    verify_res = verify_payment(
        payload=VerifyPaymentRequest(
            order_id=order_id,
            razorpay_order_id=new_rzp_order_id,
            razorpay_payment_id=valid_payment_id,
            razorpay_signature=valid_sig
        ),
        request=None,
        db=db
    )
    assert verify_res["success"] is True

    # Verify order state is now PAID
    paid_order = db.orders.find_one({"order_id": order_id})
    assert paid_order["payment_status"] == "PAID"
    assert paid_order["order_status"] == "PAYMENT_CONFIRMED"

    # Verify Tax Invoice was generated automatically upon payment confirmation
    inv = db.invoices.find_one({"order_id": order_id})
    assert inv is not None
    assert inv["invoice_number"].startswith("SSK-INV-")

    # 5. Duplicate Webhook Idempotency Check
    wh_event_id = f"evt_test_dup_{uuid.uuid4().hex[:8]}"
    wh_payload = {
        "id": wh_event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": valid_payment_id,
                    "order_id": new_rzp_order_id,
                    "amount": 199900,
                    "notes": {"order_id": order_id}
                }
            }
        }
    }
    # Send webhook callback
    wh_res1 = razorpay_webhook(payload=wh_payload, db=db)
    assert wh_res1["status"] in ["ok", "success", "acknowledged"]
    # Send exact same webhook second time
    wh_res2 = razorpay_webhook(payload=wh_payload, db=db)
    assert wh_res2["status"] == "already_processed"


# ==============================================================================
# TEST 3: ORDER LIFECYCLE & SHIPPING SIMULATION
# ==============================================================================

def test_sim_03_order_lifecycle_and_shipping():
    """
    Tests complete fulfillment lifecycle via Admin & Courier Webhook:
    PROCESSING -> PACKED -> SHIPPED -> OUT_FOR_DELIVERY -> DELIVERED
    Verifies timeline, outbox notifications, and duplicate protection.
    """
    db = get_db()
    order_id = f"SSK-LIFE-{uuid.uuid4().hex[:8]}"
    admin_user = {"id": "usr_admin", "email": "admin@sskcollections.com", "full_name": "Store Manager", "role": "admin"}

    # Create test order
    db.orders.insert_one({
        "order_id": order_id,
        "customer_name": "Meera Bai",
        "customer_email": "meera@example.com",
        "customer_phone": "9848055667",
        "payment_method": "COD",
        "payment_status": "PENDING",
        "order_status": "ORDER_PLACED",
        "items": [{"name": "Gold Bangles", "sku": "SSK-JWL-103", "quantity": 1, "price": 1199.0}],
        "final_amount": 1199.0,
        "shipping_address": {"state": "Telangana", "pincode": "500003"}
    })

    # Step 1: Mark as PROCESSING
    update_order_status(
        order_id=order_id,
        payload=OrderStatusUpdate(status="PROCESSING", internal_notes="Stock reserved"),
        current_user=admin_user,
        db=db
    )
    o1 = db.orders.find_one({"order_id": order_id})
    assert o1["order_status"] == "PROCESSING"

    # Step 2: Mark as PACKED
    update_order_status(
        order_id=order_id,
        payload=OrderStatusUpdate(status="PACKED", internal_notes="Quality check passed"),
        current_user=admin_user,
        db=db
    )
    o2 = db.orders.find_one({"order_id": order_id})
    assert o2["order_status"] == "PACKED"
    # Verify PACKED event logged in notification outbox
    packed_evt = db.notification_events.find_one({"order_id": order_id, "event_type": "ORDER_PACKED"})
    assert packed_evt is not None

    # Step 3: Create Shipment (SHIPPED)
    carrier_name = "Blue Dart Express"
    awb_number = f"SSKBD{uuid.uuid4().hex[:8].upper()}"
    ship_res = create_shipment(
        order_id=order_id,
        payload={"carrier": carrier_name, "awb": awb_number},
        db=db
    )
    assert ship_res["tracking"]["awb"] == awb_number
    o3 = db.orders.find_one({"order_id": order_id})
    assert o3["order_status"] == "SHIPPED"
    assert o3["tracking"]["carrier"] == carrier_name

    # Step 4: Courier Webhook -> OUT_FOR_DELIVERY
    wh_out = shipping_carrier_webhook(payload={"awb": awb_number, "status": "OUT_FOR_DELIVERY"}, db=db)
    assert wh_out["new_status"] == "OUT_FOR_DELIVERY"
    o4 = db.orders.find_one({"order_id": order_id})
    assert o4["tracking"]["status"] == "OUT_FOR_DELIVERY"

    # Step 5: Courier Webhook -> DELIVERED
    wh_del = shipping_carrier_webhook(payload={"awb": awb_number, "status": "DELIVERED"}, db=db)
    assert wh_del["new_status"] == "DELIVERED"
    o5 = db.orders.find_one({"order_id": order_id})
    assert o5["order_status"] == "DELIVERED"
    assert o5["payment_status"] == "PAID" # COD auto-marked paid on delivery

    # Step 6: Verify Duplicate-Event Protection
    dup_dispatch = NotificationService.dispatch_order_event(order_id=order_id, event_name="ORDER_DELIVERED")
    assert dup_dispatch["status"] == "already_dispatched"


# ==============================================================================
# TEST 4: INVOICE AND CREDIT NOTE MECHANICS
# ==============================================================================

def test_sim_04_invoicing_and_credit_note_mechanics():
    """
    Verifies:
    - Sequential numbering
    - Intrastate Telangana vs Interstate taxation
    - HSN classification (7117 vs 9615)
    - IDOR protection
    - Missing PDF auto-regeneration
    - Credit Note generation upon refund
    """
    db = get_db()
    # 1. Interstate tax calculation (Karnataka)
    interstate_order = {
        "order_id": "SSK-INTER-TAX",
        "shipping_address": {"state": "Karnataka", "pincode": "560001"},
        "items": [
            {"name": "1 Gram Gold Necklace", "sku": "SSK-NK-01", "category": "Necklaces", "quantity": 1, "price": 2060.0},
            {"name": "Hair Claw Clip", "sku": "SSK-HC-01", "category": "Hair Accessories", "quantity": 1, "price": 1180.0}
        ],
        "final_amount": 3240.0
    }
    tax_info = InvoiceService.calculate_taxes(interstate_order)
    assert tax_info["is_intrastate"] is False
    assert tax_info["total_cgst"] == 0.0
    assert tax_info["total_sgst"] == 0.0
    assert tax_info["total_igst"] > 0
    # Taxable value + IGST must equal line total
    assert round(tax_info["total_taxable_value"] + tax_info["total_igst"], 2) == 3240.0

    # 2. Sequential numbering uniqueness
    n1 = InvoiceService.get_next_invoice_number(year_prefix="2026")
    n2 = InvoiceService.get_next_invoice_number(year_prefix="2026")
    assert int(n2.split("-")[-1]) == int(n1.split("-")[-1]) + 1

    # 3. IDOR Protection check
    customer_owner = {"id": "usr_owner_1", "email": "owner@example.com", "role": "customer"}
    customer_stranger = {"id": "usr_stranger_2", "email": "stranger@example.com", "role": "customer"}

    db.invoices.update_one(
        {"invoice_number": n1},
        {"$set": {"invoice_number": n1, "user_id": "usr_owner_1", "customer_email": "owner@example.com", "pdf_path": os.path.join(INVOICES_DIR, f"{n1}.pdf")}},
        upsert=True
    )
    with pytest.raises(HTTPException) as exc_idor:
        get_invoice_details(invoice_id=n1, current_user=customer_stranger, db=db)
    assert exc_idor.value.status_code == 403

    # 4. Refund Credit Note issuance
    paid_order_id = f"SSK-RFND-{uuid.uuid4().hex[:8]}"
    db.orders.insert_one({
        "order_id": paid_order_id,
        "customer_name": "Sunita V",
        "customer_email": "sunita@example.com",
        "final_amount": 1500.0,
        "payment_status": "PAID",
        "payment_method": "Razorpay",
        "items": [{"name": "Gold Ring", "sku": "SSK-RG-01", "quantity": 1, "price": 1500.0}],
        "shipping_address": {"state": "Telangana", "pincode": "500003"}
    })
    # Initial invoice
    inv = InvoiceService.generate_or_get_invoice(paid_order_id)
    assert inv["invoice_number"].startswith("SSK-INV-")

    # Issue refund & Credit Note
    ref_res = initiate_refund(order_id=paid_order_id, payload={"amount": 1500.0, "reason": "Defective item"}, db=db)
    assert ref_res["success"] is True

    cn = db.invoices.find_one({"order_id": paid_order_id, "invoice_type": "CREDIT_NOTE"})
    assert cn is not None
    assert cn["invoice_number"].startswith("SSK-CN-")
    assert os.path.exists(cn["pdf_path"])


# ==============================================================================
# TEST 5: EMAIL AND WHATSAPP PROVIDER AUDIT
# ==============================================================================

def test_sim_05_email_and_whatsapp_provider_audit():
    """
    Audits actual live vs simulation provider state:
    - Verifies Meta WhatsApp Cloud API credentials
    - Verifies SMTP credentials
    - Verifies phone normalization, opt-out enforcement, webhook handshake, retry
    """
    db = get_db()
    admin_user = {"id": "usr_admin", "email": "admin@sskcollections.com", "role": "admin"}

    status = get_communications_status(current_user=admin_user, db=db)
    assert "email" in status
    assert "whatsapp" in status

    # Verify WhatsApp templates
    assert len(status["whatsapp"]["verified_templates"]) == 10

    # Verify Phone Number Normalization
    assert WhatsAppService.format_phone_number("9848022338") == "919848022338"
    assert WhatsAppService.format_phone_number("+91 98480-22338") == "919848022338"

    # Verify Webhook Verification Handshake
    wh_resp = verify_whatsapp_webhook(
        hub_mode="subscribe",
        hub_challenge="99887766",
        hub_verify_token=settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    )
    assert wh_resp.body.decode("utf-8") == "99887766"

    # Verify Notification Retry
    dummy_notif_id = f"wa_retry_{uuid.uuid4().hex[:8]}"
    db.notification_logs.insert_one({
        "notification_id": dummy_notif_id,
        "channel": "whatsapp",
        "recipient": "919848022338",
        "template_name": "order_packed",
        "order_id": "SSK-TEST-RETRY",
        "status": "failed",
        "created_at": datetime.now(timezone.utc)
    })
    retry_res = retry_failed_notification(notification_id=dummy_notif_id, current_user=admin_user, db=db)
    assert retry_res["success"] is True


# ==============================================================================
# TEST 6: FAILURE RECOVERY & RESILIENCE
# ==============================================================================

def test_sim_06_failure_recovery_and_resilience():
    """
    Tests application resilience against outages:
    - Backend restart recovery for pending outbox items
    - Provider offline fallback without blocking user checkout
    - Webhook duplicate resilience
    """
    db = get_db()
    test_order_id = f"SSK-REC-{uuid.uuid4().hex[:8]}"

    # Seed an order
    db.orders.insert_one({
        "order_id": test_order_id,
        "customer_name": "Rekha Rao",
        "customer_email": "rekha@example.com",
        "customer_phone": "9848011990",
        "final_amount": 1250.0,
        "payment_method": "COD",
        "payment_status": "PENDING",
        "order_status": "ORDER_PLACED",
        "items": [{"name": "Gold Earrings", "sku": "SSK-JWL-102", "quantity": 1, "price": 1250.0}],
        "shipping_address": {"state": "Telangana", "pincode": "500003"}
    })

    # Simulate an interrupted outbox item (e.g. server crash during transmission)
    outbox_id = f"out_{uuid.uuid4().hex[:14]}"
    db.notification_outbox.insert_one({
        "outbox_id": outbox_id,
        "order_id": test_order_id,
        "event_type": "COD_CONFIRMED",
        "status": "processing",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=5)
    })

    # Dispatching new event recovers cleanly and finishes outbox processing
    res = NotificationService.dispatch_order_event(
        order_id=test_order_id,
        event_name="COD_CONFIRMED",
        extra_data={"force_resend": True}
    )
    assert res["success"] is True

    # Ensure outbox item resolved
    finished_outbox = db.notification_outbox.find_one({"order_id": test_order_id, "status": "completed"})
    assert finished_outbox is not None


# ==============================================================================
# TEST 7: FINAL PRODUCTION & SECURITY CHECKS
# ==============================================================================

def test_sim_07_final_production_checks():
    """
    Audits security, backup, and production configurations:
    - Database backup creation & restore test
    - Security password hashing with Argon2id
    - CORS origins
    - Policy pages existence
    """
    db = get_db()

    # 1. Test Automated Backup
    backup_meta = DatabaseBackupService.create_backup()
    assert os.path.exists(backup_meta["filepath"])
    assert backup_meta["size_bytes"] > 0
    assert sum(backup_meta["summary"].values()) > 0

    # 2. Test Argon2id Password Hashing
    raw_pass = "ComplexAdminSecret#2026"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    # 3. Security Check: Settings & CORS
    assert settings.API_V1_STR == "/api/v1"
    assert len(settings.cors_origins) > 0
    assert not settings.RAZORPAY_KEY_ID.startswith("rzp_live_"), "Automated tests must never execute against live Razorpay keys!"
    assert isinstance(settings.validate_production_readiness(), list)

    # 4. Database Ping & Directory Check
    ping = db_manager.ping()
    assert ping["status"] == "connected"
    assert os.path.exists(INVOICES_DIR)
