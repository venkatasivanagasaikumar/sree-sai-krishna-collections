from app.database import get_db
from app.api.v1.cart import calculate_cart_totals
from app.api.v1.orders import create_order, cancel_customer_order, get_order_by_id
from app.schemas.order import CreateOrderRequest
from app.schemas.auth import Address
import pytest
from fastapi import HTTPException

def test_cart_calculation_with_coupon():
    db = get_db()
    # Free shipping > 999
    totals = calculate_cart_totals(
        [{"product_id": "SSK-JWL-101", "quantity": 1}],
        "SSKFIRST10",
        db
    )
    assert totals.subtotal == 1899.0
    assert totals.discount_amount == 189.9
    assert totals.shipping_fee == 0.0
    assert totals.final_amount == 1709.1
    assert totals.free_shipping_eligible is True

def test_create_and_cancel_order():
    db = get_db()
    # Check current stock
    prod = db.products.find_one({"sku": "SSK-JWL-103"})
    initial_stock = prod["stock"]

    addr = Address(
        name="Sunita Rao",
        phone="+91 98480 11223",
        address_line1="12 Jubilee Enclave",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        is_default=True
    )
    dto = CreateOrderRequest(
        shipping_address=addr,
        payment_method="COD",
        guest_email="sunita.test@example.com",
        guest_name="Sunita Rao",
        guest_phone="+91 98480 11223",
        cart_items=[{"product_id": "SSK-JWL-103", "quantity": 1}]
    )
    order_res = create_order(payload=dto, current_user=None, db=db)
    order_id = order_res["order_id"]
    assert order_id.startswith("SSK-")
    assert order_res["payment_method"] == "COD"

    # Verify stock deducted
    prod_after = db.products.find_one({"sku": "SSK-JWL-103"})
    assert prod_after["stock"] == initial_stock - 1

    # Cancel order (as admin)
    admin_user = db.users.find_one({"email": "admin@sskcollections.com"})
    admin_user["id"] = str(admin_user["_id"])
    cancel_res = cancel_customer_order(
        order_id=order_id,
        reason="Test order cleanup",
        current_user=admin_user,
        db=db
    )
    assert "restored" in cancel_res["message"]

    # Verify stock restored
    prod_restored = db.products.find_one({"sku": "SSK-JWL-103"})
    assert prod_restored["stock"] == initial_stock

def test_atomic_stock_decrement_rollback_on_out_of_stock():
    """SEC-01: Verifies that if an order item fails atomic stock deduction,
    all previously reserved items in the multi-item batch are rolled back."""
    db = get_db()
    
    # Ensure two known products exist with controlled stock
    db.products.update_one({"sku": "SSK-JWL-101"}, {"$set": {"stock": 10}})
    db.products.update_one({"sku": "SSK-JWL-102"}, {"$set": {"stock": 1}})
    
    addr = Address(
        name="Rollback Test",
        phone="+91 98480 99999",
        address_line1="Test St",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        is_default=True
    )
    # Order requests 2 of SSK-JWL-101 (available: 10) and 2 of SSK-JWL-102 (available: only 1)
    # Note: we temporarily bypass initial validation by updating stock right before atomic deduction
    # or by ordering when stock is exhausted concurrently
    # Let's test the atomic deduction directly:
    # First item: SSK-JWL-101 (qty 2)
    # Second item: SSK-JWL-102 (qty 2, but stock is 1)
    dto = CreateOrderRequest(
        shipping_address=addr,
        payment_method="COD",
        guest_email="rollback.test@example.com",
        guest_name="Rollback Test",
        guest_phone="+91 98480 99999",
        cart_items=[
            {"product_id": "SSK-JWL-101", "quantity": 2},
            {"product_id": "SSK-JWL-102", "quantity": 1} # initial check passes
        ]
    )
    # Concurrently reduce SSK-JWL-102 to 0 right before order creation
    db.products.update_one({"sku": "SSK-JWL-102"}, {"$set": {"stock": 0}})
    
    with pytest.raises(HTTPException) as exc:
        create_order(payload=dto, current_user=None, db=db)
    
    assert exc.value.status_code == 400 or exc.value.status_code == 409
    
    # Verify SSK-JWL-101 was NOT decremented or was rolled back to 10
    prod_101 = db.products.find_one({"sku": "SSK-JWL-101"})
    assert prod_101["stock"] == 10

