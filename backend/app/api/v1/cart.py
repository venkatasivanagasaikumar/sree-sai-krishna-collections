from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db, db_manager
from app.core.config import settings
from app.schemas.cart import CartItem, CartResponse, CartItemDetail, ApplyCouponRequest
from app.api.dependencies import get_current_user, get_optional_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])

def calculate_cart_totals(raw_items: List[Dict[str, Any]], coupon_code: Optional[str], db) -> CartResponse:
    item_details: List[CartItemDetail] = []
    subtotal = 0.0

    for item in raw_items:
        p_id = item.get("product_id")
        q = item.get("quantity", 1)
        v_id = item.get("variant_id")

        p = None
        try:
            p = db.products.find_one({"_id": ObjectId(p_id)})
        except Exception:
            pass
        if not p:
            p = db.products.find_one({"_id": p_id}) or db.products.find_one({"id": p_id}) or db.products.find_one({"sku": p_id})

        if not p:
            continue

        unit_price = float(p.get("price", 0.0))
        mrp = float(p.get("mrp", unit_price))
        stock = int(p.get("stock", 0))

        # Check variant if specified
        if v_id and "variants" in p:
            for v in p["variants"]:
                if v.get("variant_id") == v_id:
                    unit_price = float(v.get("price", unit_price))
                    mrp = float(v.get("mrp", mrp))
                    stock = int(v.get("stock", stock))
                    break

        in_stock = stock >= q
        item_total = round(unit_price * q, 2)
        subtotal += item_total

        item_details.append(CartItemDetail(
            product_id=str(p.get("id", p.get("_id"))),
            variant_id=v_id,
            name=p.get("name", "Product"),
            sku=p.get("sku", ""),
            image=p.get("images", [""])[0] if p.get("images") else "",
            mrp=mrp,
            price=unit_price,
            quantity=q,
            total_price=item_total,
            stock=stock,
            in_stock=in_stock
        ))

    # Calculate discount from coupon
    discount_amount = 0.0
    applied_coupon = None

    if coupon_code:
        coupon = db.coupons.find_one({"code": coupon_code.upper().strip(), "is_active": True})
        if coupon:
            now = datetime.now(timezone.utc)
            start_ok = not coupon.get("start_date") or coupon["start_date"] <= now
            expiry_ok = not coupon.get("expiry_date") or coupon["expiry_date"] >= now
            min_ok = subtotal >= float(coupon.get("min_order_value", 0))

            if start_ok and expiry_ok and min_ok:
                applied_coupon = coupon["code"]
                if coupon.get("discount_type") == "percentage":
                    pct = float(coupon.get("discount_value", 0))
                    discount_amount = round((subtotal * pct) / 100, 2)
                    max_disc = coupon.get("max_discount_amount")
                    if max_disc and discount_amount > float(max_disc):
                        discount_amount = float(max_disc)
                else:
                    discount_amount = min(subtotal, float(coupon.get("discount_value", 0)))

    # Shipping fee calculation
    free_shipping = subtotal >= settings.FREE_SHIPPING_THRESHOLD
    shipping_fee = 0.0 if (free_shipping or subtotal == 0) else settings.STANDARD_SHIPPING_FEE
    amount_needed = max(0.0, round(settings.FREE_SHIPPING_THRESHOLD - subtotal, 2)) if not free_shipping else 0.0
    final_amount = max(0.0, round(subtotal - discount_amount + shipping_fee, 2))

    return CartResponse(
        items=item_details,
        subtotal=round(subtotal, 2),
        discount_amount=round(discount_amount, 2),
        coupon_code=applied_coupon,
        shipping_fee=round(shipping_fee, 2),
        final_amount=round(final_amount, 2),
        free_shipping_eligible=free_shipping,
        amount_needed_for_free_shipping=amount_needed
    )

@router.get("")
def get_user_cart(current_user: Optional[dict] = Depends(get_optional_current_user), db = Depends(get_db)):
    if not current_user:
        return CartResponse()
    
    cart = db.carts.find_one({"user_id": current_user["id"]})
    if not cart:
        return CartResponse()
    
    return calculate_cart_totals(cart.get("items", []), cart.get("coupon_code"), db)

@router.post("/items")
def add_to_cart(
    item: CartItem,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    cart = db.carts.find_one({"user_id": current_user["id"]})
    items = cart.get("items", []) if cart else []

    found = False
    for i in items:
        if i.get("product_id") == item.product_id and i.get("variant_id") == item.variant_id:
            i["quantity"] += item.quantity
            found = True
            break
    if not found:
        items.append(item.model_dump())

    db.carts.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    db_manager.persist_to_disk()
    return calculate_cart_totals(items, cart.get("coupon_code") if cart else None, db)

@router.put("/items/{product_id}")
def update_cart_quantity(
    product_id: str,
    quantity: int,
    variant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    cart = db.carts.find_one({"user_id": current_user["id"]})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    items = cart.get("items", [])
    if quantity <= 0:
        items = [i for i in items if not (i.get("product_id") == product_id and i.get("variant_id") == variant_id)]
    else:
        for i in items:
            if i.get("product_id") == product_id and i.get("variant_id") == variant_id:
                i["quantity"] = quantity
                break

    db.carts.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()
    return calculate_cart_totals(items, cart.get("coupon_code"), db)

@router.delete("/items/{product_id}")
def remove_from_cart(
    product_id: str,
    variant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    cart = db.carts.find_one({"user_id": current_user["id"]})
    if not cart:
        return CartResponse()

    items = [i for i in cart.get("items", []) if not (i.get("product_id") == product_id and i.get("variant_id") == variant_id)]
    db.carts.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()
    return calculate_cart_totals(items, cart.get("coupon_code"), db)

@router.post("/coupon")
def apply_cart_coupon(
    payload: ApplyCouponRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    coupon = db.coupons.find_one({"code": payload.code.upper().strip(), "is_active": True})
    if not coupon:
        raise HTTPException(status_code=400, detail="Invalid coupon code")

    cart = db.carts.find_one({"user_id": current_user["id"]})
    items = cart.get("items", []) if cart else []
    totals = calculate_cart_totals(items, payload.code, db)

    if not totals.coupon_code:
        min_v = coupon.get("min_order_value", 0)
        raise HTTPException(status_code=400, detail=f"Minimum order value for this coupon is ₹{min_v}")

    db.carts.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"coupon_code": totals.coupon_code, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    db_manager.persist_to_disk()
    return totals

@router.delete("/coupon")
def remove_cart_coupon(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    cart = db.carts.find_one({"user_id": current_user["id"]})
    items = cart.get("items", []) if cart else []
    db.carts.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"coupon_code": None, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()
    return calculate_cart_totals(items, None, db)

@router.post("/validate-guest")
def validate_guest_cart(payload: Dict[str, Any], db = Depends(get_db)):
    """Allows guest users to calculate real backend totals with coupon and stock check."""
    raw_items = payload.get("items", [])
    coupon_code = payload.get("coupon_code")
    return calculate_cart_totals(raw_items, coupon_code, db)

@router.post("/merge")
def merge_guest_cart(payload: List[CartItem], current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    cart = db.carts.find_one({"user_id": current_user["id"]})
    items = cart.get("items", []) if cart else []

    for guest_item in payload:
        matched = False
        for i in items:
            if i.get("product_id") == guest_item.product_id and i.get("variant_id") == guest_item.variant_id:
                i["quantity"] += guest_item.quantity
                matched = True
                break
        if not matched:
            items.append(guest_item.model_dump())

    db.carts.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    db_manager.persist_to_disk()
    return calculate_cart_totals(items, cart.get("coupon_code") if cart else None, db)
