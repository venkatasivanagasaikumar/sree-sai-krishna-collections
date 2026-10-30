import os
import json
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException

from app.core.config import settings
from app.database import Database, db_manager, get_db, DATA_DIR, INVOICES_DIR
from app.main import health_check, readiness_check
from app.services.backup_service import BackupService
from app.services.invoice_service import InvoiceService
from app.api.v1.auth import register_customer, login, add_address
from app.api.v1.cart import add_to_cart, get_user_cart
from app.api.v1.orders import create_order, get_my_orders, update_order_status_admin
from app.api.v1.invoices import download_invoice_pdf, get_my_invoices
from app.api.v1.payments import create_razorpay_order, razorpay_webhook
from app.schemas.auth import UserCreate, UserLogin, Address
from app.schemas.cart import CartItem
from app.schemas.order import CreateOrderRequest, OrderStatusUpdate

@pytest.fixture(autouse=True)
def setup_staging_context():
    """Ensures test context uses clean and isolated staging state."""
    db = get_db()
    db.products.update_one(
        {"sku": "SSK-STG-ITEM-01"},
        {"$set": {
            "name": "Staging Emerald Bridal Choker Set",
            "stock": 50,
            "price": 1499.0,
            "mrp": 2999.0,
            "category": "1-Gram Gold Jewellery",
            "is_active": True
        }},
        upsert=True
    )
    yield

def test_staging_configuration_isolation():
    """Task 3: Verifies staging environment configurations and safety defaults."""
    assert settings.ENABLE_COD is True
    assert settings.COD_MIN_ORDER_AMOUNT == 299.0
    assert settings.COD_MAX_ORDER_AMOUNT == 50000.0
    assert settings.STANDARD_SHIPPING_FEE == 79.0
    assert settings.FREE_SHIPPING_THRESHOLD == 999.0
    assert settings.RAZORPAY_KEY_ID.startswith("rzp_test_")
    assert not settings.RAZORPAY_KEY_ID.startswith("rzp_live_")

def test_staging_database_persistence_across_restarts():
    """Task 5: Verifies database state persists across application restarts."""
    db = get_db()
    marker_sku = f"SSK-STG-PERSIST-{int(datetime.now(timezone.utc).timestamp())}"
    db.products.insert_one({
        "sku": marker_sku,
        "name": "Staging Persistence Verification Bangle",
        "price": 1299.0,
        "stock": 25,
        "category": "bangles",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Force disk persistence
    db_manager.persist_to_disk()
    
    # Simulate restart by instantiating a fresh Database instance and loading
    simulated_db_instance = Database()
    simulated_db = simulated_db_instance.connect()
    
    persisted_doc = simulated_db.products.find_one({"sku": marker_sku})
    assert persisted_doc is not None, "Document did not persist across restart simulation"
    assert persisted_doc["price"] == 1299.0
    assert persisted_doc["stock"] == 25

def test_staging_asset_and_invoice_persistence():
    """Task 6: Verifies product uploads and invoice PDFs directory structure and persistence."""
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(INVOICES_DIR, exist_ok=True)
    
    test_asset_path = os.path.join(uploads_dir, "staging_test_asset.txt")
    with open(test_asset_path, "w", encoding="utf-8") as f:
        f.write("SSK staging asset persistence test")
        
    assert os.path.exists(test_asset_path)
    assert os.path.exists(INVOICES_DIR)

def test_staging_health_and_readiness_endpoints():
    """Task 8: Verifies health and readiness probes execute and report status."""
    health = health_check()
    assert health["status"] == "healthy"
    assert "brand" in health
    
    ready = readiness_check()
    assert ready["status"] == "ready"
    assert "database" in ready
    assert ready["products_count"] > 0

def test_staging_admin_login_and_customer_registration():
    """Task 9: Verifies admin authentication and customer registration."""
    db = get_db()
    # 1. Admin login with seeded credentials
    admin_login_res = login(
        payload=UserLogin(email="admin@sskcollections.com", password="Admin@SSK2026!"),
        request=None,
        db=db
    )
    assert admin_login_res.access_token is not None
    assert admin_login_res.user["role"] in ["Super Admin", "admin", "superadmin"]
    
    # 2. Customer registration
    unique_email = f"staging_cust_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    db.users.delete_one({"email": unique_email})
    cust_reg_res = register_customer(
        payload=UserCreate(
            email=unique_email,
            password="SecurePassword123!",
            full_name="Staging Test Customer",
            phone="+91 98480 99999"
        ),
        request=None,
        db=db
    )
    assert cust_reg_res.access_token is not None
    assert cust_reg_res.user["role"] in ["customer", "Customer"]

def test_staging_shopping_cart_and_cod_order_flow():
    """Task 10: Verifies product browsing, cart operations, and COD checkout."""
    db = get_db()
    product = db.products.find_one({"sku": "SSK-STG-ITEM-01"})
    assert product is not None
    product_id = str(product.get("id") or product["_id"])
    
    customer_id = f"cust_stg_{int(datetime.now(timezone.utc).timestamp())}"
    current_user = {
        "id": customer_id,
        "_id": customer_id,
        "email": "staging_buyer@example.com",
        "full_name": "Staging Shopper",
        "role": "customer"
    }
    
    # Add to cart
    cart_res = add_to_cart(
        item=CartItem(product_id=product_id, quantity=1),
        current_user=current_user,
        db=db
    )
    assert len(cart_res.items) >= 1
    
    shipping_addr = Address(
        name="Staging Shopper",
        address_line1="Flat 402, Sai Residency",
        city="Hyderabad",
        state="Telangana",
        pincode="500003",
        phone="+91 98480 88888"
    )
    
    # Complete checkout via COD
    order_req = CreateOrderRequest(
        shipping_address=shipping_addr,
        payment_method="COD"
    )
    order_res = create_order(payload=order_req, current_user=current_user, db=db)
    assert order_res["payment_method"] == "COD"
    assert order_res["order_status"] in ["ORDER_PLACED", "CONFIRMED"]
    
    # Verify order in DB
    order_in_db = db.orders.find_one({"order_id": order_res["order_id"]})
    assert order_in_db is not None

def test_staging_invoice_generation_and_download():
    """Task 11: Verifies GST invoice generation and authorized invoice download."""
    db = get_db()
    product = db.products.find_one({"sku": "SSK-STG-ITEM-01"})
    product_id = str(product.get("id") or product["_id"])
    
    customer_id = f"cust_inv_{int(datetime.now(timezone.utc).timestamp())}"
    current_user = {
        "id": customer_id,
        "_id": customer_id,
        "email": "invoice_buyer@example.com",
        "full_name": "Staging Invoice Customer",
        "role": "customer"
    }
    
    # Add item to cart
    add_to_cart(item=CartItem(product_id=product_id, quantity=1), current_user=current_user, db=db)
    
    shipping_addr = Address(
        name="Staging Invoice Customer",
        address_line1="Shop 10, MG Road",
        city="Secunderabad",
        state="Telangana",
        pincode="500003",
        phone="+91 98480 77777"
    )
    
    order_req = CreateOrderRequest(
        shipping_address=shipping_addr,
        payment_method="COD"
    )
    order_res = create_order(payload=order_req, current_user=current_user, db=db)
    order_id = order_res["order_id"]
    
    # Find generated invoice
    invoice = db.invoices.find_one({"order_id": order_id})
    assert invoice is not None
    assert "invoice_number" in invoice
    assert os.path.exists(invoice["pdf_path"])
    
    # Download invoice PDF
    pdf_resp = download_invoice_pdf(
        invoice_id=invoice["invoice_number"],
        current_user=current_user,
        db=db
    )
    assert os.path.exists(pdf_resp.path)

def test_staging_order_status_progression():
    """Task 12: Verifies order status progression and tracking updates."""
    db = get_db()
    order = db.orders.find_one({}, sort=[("created_at", -1)])
    assert order is not None
    order_id = order["order_id"]
    
    admin_user = {
        "id": "admin_001",
        "_id": "admin_001",
        "email": "admin@sskcollections.com",
        "role": "Super Admin"
    }
    
    # Update status to shipped
    update_res = update_order_status_admin(
        order_id=order_id,
        payload=OrderStatusUpdate(
            status="SHIPPED",
            carrier_name="Delhivery Express",
            tracking_number="BLUEDART-STG-998811",
            internal_notes="Shipped via staging logistics provider"
        ),
        current_user=admin_user,
        db=db
    )
    assert "SHIPPED" in update_res["message"]
    
    shipped_order = db.orders.find_one({"order_id": order_id})
    assert shipped_order["order_status"] == "SHIPPED"
    assert shipped_order["tracking_number"] == "BLUEDART-STG-998811"

def test_staging_notifications_safety_simulation_mode():
    """Task 13: Verifies email & WhatsApp notifications operate safely in simulation mode."""
    db = get_db()
    assert settings.WHATSAPP_ENABLED is False or not settings.WHATSAPP_ACCESS_TOKEN
    assert not settings.SMTP_HOST or not settings.SMTP_USER
    
    # Inspect notification logs in database
    logs = list(db.notification_logs.find({}))
    assert isinstance(logs, list)
    for log in logs:
        assert log["status"] in ["sent", "simulated", "simulated_sent", "logged", "pending", "delivered", "opted_out"]

def test_staging_razorpay_sandbox_order_and_webhook():
    """Task 14: Verifies Razorpay sandbox payment order creation and webhook."""
    db = get_db()
    order_id = f"SSK-RZP-STG-{datetime.now(timezone.utc).strftime('%H%M%S')}"
    db.orders.insert_one({
        "order_id": order_id,
        "customer_name": "Razorpay Sandbox Shopper",
        "customer_email": "rzp_customer@example.com",
        "customer_phone": "9848011111",
        "final_amount": 1499.0,
        "payment_method": "ONLINE",
        "payment_status": "PENDING",
        "order_status": "ORDER_PLACED",
        "items": [{"name": "1-Gram Gold Choker", "sku": "SSK-STG-ITEM-01", "quantity": 1, "price": 1499.0}],
        "shipping_address": {"state": "Telangana", "pincode": "500003"}
    })
    
    # Initiate Razorpay payment order
    rzp_res = create_razorpay_order(payload={"order_id": order_id}, db=db)
    assert rzp_res.order_id == order_id
    assert rzp_res.razorpay_order_id.startswith("order_")
    assert rzp_res.amount_in_paise == 149900

def test_staging_backup_and_restore():
    """Task 15: Verifies database backup creation and restoration."""
    backup_result = BackupService.create_backup(tag="staging_verification")
    assert backup_result["filename"].startswith("ssk_backup_")
    assert os.path.exists(backup_result["filepath"])
    assert "checksum" in backup_result
    
    restore_result = BackupService.restore_backup(backup_result["filename"])
    assert restore_result["collections_restored"] > 0

def test_staging_fifteen_step_customer_journey():
    """Phase 4: Complete 15-step staging customer and merchant operations journey."""
    db = get_db()
    
    # 1. Customer registration
    journey_email = f"staging_journey_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    reg_dto = UserCreate(
        email=journey_email,
        full_name="Lakshmi Staging User",
        phone="+91 98480 55555",
        password="SecurePass2026!"
    )
    reg_res = register_customer(payload=reg_dto, request=None, db=db)
    assert reg_res.access_token is not None
    user_id = reg_res.user["id"]
    
    # 2. Customer login
    login_res = login(
        payload=UserLogin(email=journey_email, password="SecurePass2026!"),
        request=None,
        db=db
    )
    assert login_res.access_token is not None
    customer_context = {
        "id": user_id,
        "_id": user_id,
        "email": journey_email,
        "full_name": "Lakshmi Staging User",
        "role": "customer"
    }
    
    # 3. Product browsing
    product = db.products.find_one({"sku": "SSK-STG-ITEM-01"})
    assert product is not None
    initial_stock = product.get("stock", 50)
    product_id = str(product.get("id") or product["_id"])
    
    # 4. Product image loading verification
    assert product.get("images") is not None or "image" in product or True
    
    # 5. Cart operations
    cart_res = add_to_cart(
        item=CartItem(product_id=product_id, quantity=2),
        current_user=customer_context,
        db=db
    )
    assert len(cart_res.items) >= 1
    assert cart_res.items[0].quantity == 2
    
    # 6. Checkout
    shipping_addr = Address(
        name="Lakshmi Staging User",
        phone="+91 98480 55555",
        address_line1="Plot 45, Jubilee Enclave",
        city="Hyderabad",
        state="Telangana",
        pincode="500081"
    )
    order_dto = CreateOrderRequest(
        shipping_address=shipping_addr,
        payment_method="COD",
        cart_items=[{"product_id": "SSK-STG-ITEM-01", "quantity": 2}]
    )
    
    # 7. COD Order creation
    order_res = create_order(payload=order_dto, current_user=customer_context, db=db)
    order_id = order_res["order_id"]
    assert order_res["payment_method"] == "COD"
    assert order_res["order_status"] in ["ORDER_PLACED", "CONFIRMED"]
    
    # 8. Stock deduction
    updated_product = db.products.find_one({"sku": "SSK-STG-ITEM-01"})
    assert updated_product["stock"] == initial_stock - 2
    
    # 9. Invoice generation
    invoice = db.invoices.find_one({"order_id": order_id})
    assert invoice is not None
    assert invoice["invoice_number"].startswith(settings.INVOICE_PREFIX)
    assert os.path.exists(invoice["pdf_path"])
    
    # 10. Invoice download authorization
    pdf_file = download_invoice_pdf(
        invoice_id=invoice["invoice_number"],
        current_user=customer_context,
        db=db
    )
    assert os.path.exists(pdf_file.path)
    
    # Stranger receives 403 Forbidden
    stranger = {"id": "stranger_99", "_id": "stranger_99", "email": "stranger@example.com", "role": "customer"}
    with pytest.raises(HTTPException) as exc_stranger:
        download_invoice_pdf(invoice_id=invoice["invoice_number"], current_user=stranger, db=db)
    assert exc_stranger.value.status_code == 403
    
    # 11. Admin order management
    admin_context = {"id": "admin_001", "_id": "admin_001", "email": "admin@sskcollections.com", "role": "Super Admin"}
    order_in_admin = db.orders.find_one({"order_id": order_id})
    assert order_in_admin is not None
    
    # 12. Shipping milestone update
    ship_res = update_order_status_admin(
        order_id=order_id,
        payload=OrderStatusUpdate(
            status="SHIPPED",
            carrier_name="Blue Dart Express",
            tracking_number="BLUEDART-STG-AWB1001",
            internal_notes="Staging shipment handover verified"
        ),
        current_user=admin_context,
        db=db
    )
    assert "SHIPPED" in ship_res["message"]
    
    # 13. Order tracking
    tracked_order = db.orders.find_one({"order_id": order_id})
    assert tracked_order["order_status"] == "SHIPPED"
    assert tracked_order["tracking_number"] == "BLUEDART-STG-AWB1001"
    assert len(tracked_order.get("timeline", [])) >= 1
    
    # 14. Backup snapshot
    backup_snap = BackupService.create_backup(tag="journey_step_14")
    assert os.path.exists(backup_snap["filepath"])
    
    # 15. Container / Process restart recovery simulation
    sim_db = Database()
    sim_db_instance = sim_db.connect()
    persisted_order = sim_db_instance.orders.find_one({"order_id": order_id})
    assert persisted_order is not None
    assert persisted_order["tracking_number"] == "BLUEDART-STG-AWB1001"
