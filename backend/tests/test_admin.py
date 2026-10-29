from app.database import get_db
from app.api.v1.analytics import get_dashboard_kpis
from app.api.v1.orders import list_orders_admin, update_order_status_admin, get_order_by_id
from app.api.v1.inventory import get_inventory_status, adjust_stock
from app.schemas.order import OrderStatusUpdate
from app.schemas.inventory import StockAdjustment

def test_admin_dashboard_kpis():
    db = get_db()
    dash = get_dashboard_kpis(days=30, db=db)
    kpis = dash["kpis"]
    assert kpis["total_orders"] >= 2
    assert kpis["gross_sales"] > 0
    assert len(dash["sales_trend"]) == 7
    assert len(dash["top_selling_products"]) > 0

def test_order_status_progression():
    db = get_db()
    orders_res = list_orders_admin(page=1, limit=5, db=db)
    assert len(orders_res["orders"]) >= 1
    sample_order = orders_res["orders"][0]
    order_id = sample_order["order_id"]

    admin_user = db.users.find_one({"email": "admin@sskcollections.com"})
    admin_user["id"] = str(admin_user["_id"])

    upd_res = update_order_status_admin(
        order_id=order_id,
        payload=OrderStatusUpdate(
            status="SHIPPED",
            carrier_name="Delhivery Express",
            tracking_number="DEL-TEST-998811",
            internal_notes="Package dispatched via air cargo"
        ),
        current_user=admin_user,
        db=db
    )
    assert upd_res["order_id"] == order_id

    # Verify order timeline contains the update
    ord_doc = get_order_by_id(order_id=order_id, current_user=admin_user, db=db)
    assert ord_doc["order_status"] == "SHIPPED"
    assert ord_doc["tracking_number"] == "DEL-TEST-998811"
    assert any(t["status"] == "SHIPPED" for t in ord_doc["timeline"])

def test_inventory_adjustment():
    db = get_db()
    admin_user = db.users.find_one({"email": "inventory@sskcollections.com"})
    admin_user["id"] = str(admin_user["_id"])

    prod = db.products.find_one({"sku": "SSK-HAIR-201"})
    initial_stock = prod["stock"]

    res = adjust_stock(
        payload=StockAdjustment(
            product_id=str(prod.get("id", prod.get("_id"))),
            sku="SSK-HAIR-201",
            adjustment_type="RESTOCK",
            quantity_change=10,
            reason="Supplier shipment batch #440 received"
        ),
        current_user=admin_user,
        db=db
    )
    assert res["new_stock"] == initial_stock + 10

    # Verify inventory movement recorded
    mov = db.inventory_movements.find_one({"sku": "SSK-HAIR-201", "reason": "Supplier shipment batch #440 received"})
    assert mov is not None
    assert mov["quantity_change"] == 10
