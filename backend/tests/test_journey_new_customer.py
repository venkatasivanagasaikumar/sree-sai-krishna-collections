"""
Journey 1: New Customer Automated End-to-End Journey Test
Covers: Registration, login, catalog browse, search, product detail, wishlist simulation,
cart add & quantity adjustment, coupon application, address setup, checkout, order placement,
and order tracking.
"""
import pytest
from app.database import get_db
from app.api.v1.auth import register_customer, login, add_address
from app.api.v1.products import list_products, get_product_details
from app.api.v1.cart import add_to_cart, update_cart_quantity, apply_cart_coupon, get_user_cart
from app.api.v1.orders import create_order, get_order_by_id
from app.schemas.auth import UserCreate, UserLogin, Address
from app.schemas.cart import CartItem, ApplyCouponRequest
from app.schemas.order import CreateOrderRequest

def test_new_customer_full_journey():
    db = get_db()
    test_email = "ananya.newcustomer@example.com"
    db.users.delete_one({"email": test_email})
    db.carts.delete_one({"user_id": test_email})

    # Step 1: Register Account
    reg_dto = UserCreate(
        email=test_email,
        full_name="Ananya Reddy",
        phone="+91 99887 71122",
        password="SecurePass2026!"
    )
    reg_res = register_customer(payload=reg_dto, request=None, db=db)
    user_id = reg_res.user["id"]
    assert reg_res.access_token is not None
    assert reg_res.user["email"] == test_email

    # Step 2: Log In
    login_dto = UserLogin(email=test_email, password="SecurePass2026!")
    login_res = login(payload=login_dto, request=None, db=db)
    assert login_res.access_token is not None

    current_user = {
        "id": user_id,
        "_id": user_id,
        "email": test_email,
        "full_name": "Ananya Reddy",
        "role": "Customer"
    }

    # Step 3: Browse Jewellery Catalog
    catalog = list_products(category="1-Gram Gold Jewellery", db=db)
    assert catalog["total"] > 0
    assert len(catalog["products"]) > 0

    # Step 4: Search for Product
    search_res = list_products(search="Jhumka", db=db)
    assert search_res["total"] > 0

    # Step 5: Open Product Details
    prod_sku = "SSK-JWL-101" # 1-Gram Gold Lakshmi Temple Necklace Set
    product = get_product_details(id_or_sku=prod_sku, db=db)
    assert product["name"] is not None
    assert product["price"] == 1899.0

    # Step 6: Add to Cart
    cart_item = CartItem(product_id=prod_sku, quantity=1)
    cart_totals = add_to_cart(item=cart_item, current_user=current_user, db=db)
    assert len(cart_totals.items) == 1
    assert cart_totals.subtotal == 1899.0

    # Step 7: Increase Quantity
    cart_updated = update_cart_quantity(
        product_id=prod_sku,
        quantity=2,
        current_user=current_user,
        db=db
    )
    assert cart_updated.subtotal == 3798.0

    # Step 8: Apply Coupon SSKFIRST10 (10% off)
    coupon_res = apply_cart_coupon(
        payload=ApplyCouponRequest(code="SSKFIRST10"),
        current_user=current_user,
        db=db
    )
    assert coupon_res.coupon_code == "SSKFIRST10"
    # Max discount is capped at ₹300 for this coupon
    assert coupon_res.discount_amount == 300.0
    assert coupon_res.free_shipping_eligible is True
    assert coupon_res.final_amount == round(3798.0 - 300.0, 2)

    # Step 9: Add Delivery Address
    addr_dto = Address(
        name="Ananya Reddy",
        phone="+91 99887 71122",
        address_line1="Plot 45, Madhapur Main Road",
        address_line2="Near Durgam Cheruvu",
        city="Hyderabad",
        state="Telangana",
        pincode="500081",
        is_default=True,
        type="Home"
    )
    add_addr_res = add_address(address=addr_dto, current_user=current_user, db=db)
    assert add_addr_res["message"] == "Address added successfully"

    # Step 10: Complete Checkout (Cash on Delivery)
    order_dto = CreateOrderRequest(
        shipping_address=addr_dto,
        payment_method="COD",
        coupon_code="SSKFIRST10"
    )
    order_res = create_order(payload=order_dto, current_user=current_user, db=db)
    order_id = order_res["order_id"]
    assert order_id.startswith("SSK-")
    assert order_res["payment_method"] == "COD"
    assert order_res["order_status"] == "ORDER_PLACED"

    # Step 11: View and Track Order
    fetched_order = get_order_by_id(order_id=order_id, current_user=current_user, db=db)
    assert fetched_order["order_id"] == order_id
    assert fetched_order["user_id"] == user_id
    assert len(fetched_order["items"]) == 1
    assert fetched_order["items"][0]["quantity"] == 2
    assert len(fetched_order["timeline"]) >= 1

    # Clean up test user
    db.users.delete_one({"email": test_email})
    db.orders.delete_one({"order_id": order_id})
