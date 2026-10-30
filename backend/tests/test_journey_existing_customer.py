"""
Journey 2: Existing Customer Automated Journey Test
Covers: Login, multi-product cart addition, item removal, quantity sync,
payment order creation, payment gateway verification, and packing slip invoice verification.
"""
import pytest
from app.database import get_db
from app.api.v1.auth import login
from app.api.v1.cart import add_to_cart, remove_from_cart, update_cart_quantity, get_user_cart
from app.api.v1.orders import create_order, get_order_by_id, get_packing_slip
from app.api.v1.payments import create_razorpay_order, verify_razorpay_payment
from app.schemas.auth import UserLogin, Address
from app.schemas.cart import CartItem
from app.schemas.order import CreateOrderRequest
from app.schemas.payment import VerifyPaymentRequest

def test_existing_customer_multi_item_and_payment_journey():
    db = get_db()
    
    # Step 1: Login Existing Seed Customer (Priya Sharma)
    login_dto = UserLogin(email="priya.sharma@example.com", password="Customer@123")
    login_res = login(payload=login_dto, request=None, db=db)
    user_id = login_res.user["id"]
    assert login_res.access_token is not None

    current_user = {
        "id": user_id,
        "_id": user_id,
        "email": "priya.sharma@example.com",
        "full_name": "Priya Sharma",
        "role": "Customer"
    }

    # Step 2: Clear any leftover cart items
    db.carts.delete_one({"user_id": user_id})

    # Step 3: Add Multiple Products to Cart
    prod1_sku = "SSK-JWL-102" # Matte Finish Temple Jhumkas (₹799)
    prod2_sku = "SSK-HAIR-201" # French Matte Acrylic Claw Clips Set (₹349)
    
    add_to_cart(item=CartItem(product_id=prod1_sku, quantity=2), current_user=current_user, db=db)
    cart2 = add_to_cart(item=CartItem(product_id=prod2_sku, quantity=1), current_user=current_user, db=db)
    assert len(cart2.items) == 2
    assert cart2.subtotal == (799 * 2) + 349 # 1598 + 349 = 1947.0

    # Step 4: Remove Product 2 from Cart
    cart_after_remove = remove_from_cart(product_id=prod2_sku, current_user=current_user, db=db)
    assert len(cart_after_remove.items) == 1
    assert cart_after_remove.subtotal == 1598.0

    # Step 5: Update Quantity of Product 1
    cart_after_qty = update_cart_quantity(product_id=prod1_sku, quantity=1, current_user=current_user, db=db)
    assert cart_after_qty.subtotal == 799.0
    # Less than 999 threshold -> standard shipping fee applies
    assert cart_after_qty.shipping_fee == 79.0
    assert cart_after_qty.final_amount == 799.0 + 79.0 # 878.0

    # Step 6: Checkout with Online Payment (Razorpay)
    addr = Address(
        name="Priya Sharma",
        phone="+91 98765 43210",
        address_line1="Flat 402, Sai Balaji Residency",
        address_line2="Banjara Hills",
        city="Hyderabad",
        state="Telangana",
        pincode="500034",
        is_default=True
    )
    order_dto = CreateOrderRequest(
        shipping_address=addr,
        payment_method="Razorpay"
    )
    order_res = create_order(payload=order_dto, current_user=current_user, db=db)
    order_id = order_res["order_id"]
    assert order_res["payment_status"] == "PENDING"
    assert order_res["order_status"] == "PAYMENT_PENDING"

    # Step 7: Create Razorpay Order
    rzp_order = create_razorpay_order(payload={"order_id": order_id}, current_user=current_user, db=db)
    assert rzp_order.order_id == order_id
    assert rzp_order.razorpay_order_id.startswith("order_")
    assert rzp_order.amount_in_paise == int(round(878.0 * 100))

    # Step 8: Verify Razorpay Payment (in sandbox test mode)
    verify_payload = VerifyPaymentRequest(
        order_id=order_id,
        razorpay_order_id=rzp_order.razorpay_order_id,
        razorpay_payment_id="pay_test_existing_cust_123",
        razorpay_signature="sandbox_success"
    )
    verify_res = verify_razorpay_payment(payload=verify_payload, request=None, db=db)
    assert verify_res["success"] is True

    # Step 9: Confirm Order Status Transitioned to PAID
    paid_order = get_order_by_id(order_id=order_id, current_user=current_user, db=db)
    assert paid_order["payment_status"] == "PAID"
    assert paid_order["order_status"] == "PAYMENT_CONFIRMED"

    # Step 10: Packing Slip Generation
    slip = get_packing_slip(order_id=order_id, db=db)
    assert slip["order"]["order_id"] == order_id
    assert slip["brand_short"] == "SSK"

    # Cleanup
    db.orders.delete_one({"order_id": order_id})
    db.payments.delete_one({"order_id": order_id})
