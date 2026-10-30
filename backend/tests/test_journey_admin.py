"""
Journey 3: Admin & Staff Automated Operations Test
Covers: Staff authentication, dashboard KPIs, product creation, stock adjustment,
order dispatch with carrier & AWB tracking, analytics, and Google Sheets export.
"""
import pytest
from app.database import get_db
from app.api.v1.auth import login
from app.api.v1.analytics import get_dashboard_kpis
from app.api.v1.products import create_product, list_products, delete_or_archive_product, export_products_csv
from app.api.v1.inventory import adjust_stock, get_inventory_status
from app.api.v1.orders import create_order, list_orders_admin, update_order_status_admin
from app.api.v1.sheets_sync import export_all_for_sheets
from app.schemas.auth import UserLogin, Address
from app.schemas.product import ProductCreate
from app.schemas.inventory import StockAdjustment
from app.schemas.order import CreateOrderRequest, OrderStatusUpdate

def test_admin_staff_operations_journey():
    db = get_db()

    # Step 1: Admin Login
    admin_login = login(payload=UserLogin(email="admin@sskcollections.com", password="Admin@SSK2026!"), request=None, db=db)
    assert admin_login.access_token is not None
    assert admin_login.user["role"] == "Super Admin"

    admin_user = {
        "id": admin_login.user["id"],
        "_id": admin_login.user["id"],
        "email": "admin@sskcollections.com",
        "full_name": "Sree Sai Krishna Admin",
        "role": "Super Admin"
    }

    # Step 2: Open Dashboard & Verify KPI Calculations
    kpis = get_dashboard_kpis(days=30, db=db)
    assert kpis["kpis"]["gross_sales"] >= 0
    assert kpis["kpis"]["total_orders"] >= 0
    assert "sales_trend" in kpis
    assert len(kpis["sales_trend"]) == 7

    # Step 3: Create a New Jewellery Product
    test_sku = "SSK-TEST-JWL-999"
    db.products.delete_one({"sku": test_sku})

    new_prod_dto = ProductCreate(
        name="1-Gram Gold Emerald Floral Bridal Choker",
        sku=test_sku,
        category="1-Gram Gold Jewellery",
        subcategory="Bridal Chokers",
        price=2499.0,
        mrp=3499.0,
        stock=15,
        description="Handcrafted micro-gold plated bridal choker with simulated emeralds.",
        materials_and_finish="High grade brass core, 1-gram gold tone micro electroplate",
        images=["/uploads/sample-emerald.jpg"],
        is_featured=True
    )
    prod_create_res = create_product(payload=new_prod_dto, db=db)
    assert prod_create_res["id"] is not None

    # Step 4: Verify Product Visible in Catalog
    catalog_check = list_products(search="Emerald Floral", db=db)
    assert catalog_check["total"] >= 1
    found_prod = next(p for p in catalog_check["products"] if p["sku"] == test_sku)
    assert found_prod["price"] == 2499.0

    # Step 5: Adjust Stock
    adjust_dto = StockAdjustment(
        product_id=str(prod_create_res["id"]),
        sku=test_sku,
        quantity_change=5,
        adjustment_type="RESTOCK",
        reason="Fresh artisan workshop consignment"
    )
    adj_res = adjust_stock(payload=adjust_dto, current_user=admin_user, db=db)
    assert adj_res["new_stock"] == 20

    # Step 6: Create Customer Order for This Item
    addr = Address(
        name="Ramesh Babu",
        phone="+91 98480 33445",
        address_line1="4-56 Temple Street",
        city="Secunderabad",
        state="Telangana",
        pincode="500003",
        is_default=True
    )
    order_res = create_order(
        payload=CreateOrderRequest(
            shipping_address=addr,
            payment_method="COD",
            guest_email="ramesh.babu@example.com",
            guest_name="Ramesh Babu",
            guest_phone="+91 98480 33445",
            cart_items=[{"product_id": test_sku, "quantity": 2}]
        ),
        current_user=None,
        db=db
    )
    created_order_id = order_res["order_id"]

    # Step 7: Order Fulfilment - Update to SHIPPED with Delhivery AWB
    ship_dto = OrderStatusUpdate(
        status="SHIPPED",
        carrier_name="Delhivery Express",
        tracking_number="DEL9848022338IN",
        internal_notes="Double bubbled protective packaging with SSK warranty tag"
    )
    ship_res = update_order_status_admin(order_id=created_order_id, payload=ship_dto, current_user=admin_user, db=db)
    assert "SHIPPED" in ship_res["message"]

    # Verify status in database
    shipped_order = db.orders.find_one({"order_id": created_order_id})
    assert shipped_order["order_status"] == "SHIPPED"
    assert shipped_order["carrier_name"] == "Delhivery Express"
    assert shipped_order["tracking_number"] == "DEL9848022338IN"

    # Step 8: Export Products to CSV
    csv_res = export_products_csv(db=db)
    assert "SKU,Name,Category" in csv_res["csv_content"]
    assert test_sku in csv_res["csv_content"]

    # Step 9: Export Data for Google Sheets Sync
    sheets_payload = export_all_for_sheets(db=db)
    assert "products" in sheets_payload
    assert "orders" in sheets_payload
    assert "inventory" in sheets_payload
    assert sheets_payload["store"] == "Sree Sai Krishna Collections"

    # Cleanup test records
    delete_or_archive_product(product_id=str(found_prod["id"]), hard_delete=True, db=db)
    db.orders.delete_one({"order_id": created_order_id})
    db.inventory_movements.delete_many({"sku": test_sku})
