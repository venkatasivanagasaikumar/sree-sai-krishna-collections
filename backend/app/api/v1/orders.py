from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from bson import ObjectId
from app.database import get_db, db_manager
from app.core.config import settings
from app.core.permissions import Role
from app.core.logging import AuditLogger
from app.schemas.order import CreateOrderRequest, OrderStatusUpdate, ReturnRequestCreate
from app.schemas.inventory import StockAdjustment
from app.api.dependencies import get_current_user, get_optional_current_user, require_roles

router = APIRouter(prefix="/orders", tags=["Orders"])

def generate_order_id() -> str:
    now_str = datetime.now().strftime("%Y%m%d")
    rnd = random.randint(1000, 9999)
    return f"SSK-{now_str}-{rnd}"

@router.post("")
def create_order(
    payload: CreateOrderRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user),
    db = Depends(get_db)
):
    # Determine user identity or guest details
    user_id = current_user["id"] if current_user else None
    customer_email = current_user.get("email") if current_user else payload.guest_email
    customer_name = current_user.get("full_name") if current_user else payload.guest_name
    customer_phone = current_user.get("phone") if current_user else payload.guest_phone

    if not customer_email:
        raise HTTPException(status_code=400, detail="Customer email is required")

    # Fetch items from user's cart or guest payload
    raw_items = []
    coupon_code = payload.coupon_code

    if current_user:
        cart = db.carts.find_one({"user_id": current_user["id"]})
        if not cart or not cart.get("items"):
            raise HTTPException(status_code=400, detail="Cart is empty")
        raw_items = cart.get("items", [])
        if not coupon_code:
            coupon_code = cart.get("coupon_code")
    else:
        if not payload.cart_items:
            raise HTTPException(status_code=400, detail="Cart items required for guest checkout")
        raw_items = payload.cart_items

    # Validate items and stock, recalculate prices
    order_items = []
    subtotal = 0.0

    for item in raw_items:
        p_id = item.get("product_id")
        q = int(item.get("quantity", 1))
        v_id = item.get("variant_id")

        p = None
        try:
            p = db.products.find_one({"_id": ObjectId(p_id)})
        except Exception:
            pass
        if not p:
            p = db.products.find_one({"_id": p_id}) or db.products.find_one({"id": p_id}) or db.products.find_one({"sku": p_id})

        if not p:
            raise HTTPException(status_code=400, detail=f"Product {p_id} no longer exists")

        unit_price = float(p.get("price", 0.0))
        mrp = float(p.get("mrp", unit_price))
        stock = int(p.get("stock", 0))

        if v_id and "variants" in p:
            for v in p["variants"]:
                if v.get("variant_id") == v_id:
                    unit_price = float(v.get("price", unit_price))
                    mrp = float(v.get("mrp", mrp))
                    stock = int(v.get("stock", stock))
                    break

        if stock < q:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for '{p.get('name')}'. Available: {stock}")

        total_price = round(unit_price * q, 2)
        subtotal += total_price

        order_items.append({
            "product_id": str(p.get("id", p.get("_id"))),
            "variant_id": v_id,
            "name": p.get("name"),
            "sku": p.get("sku"),
            "image": p.get("images", [""])[0] if p.get("images") else "",
            "unit_price": unit_price,
            "mrp": mrp,
            "quantity": q,
            "total_price": total_price
        })

    # Validate coupon and calculate discount
    discount_amount = 0.0
    applied_coupon = None

    if coupon_code:
        coupon = db.coupons.find_one({"code": coupon_code.upper().strip(), "is_active": True})
        if coupon and subtotal >= float(coupon.get("min_order_value", 0)):
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
    shipping_fee = 0.0 if free_shipping else settings.STANDARD_SHIPPING_FEE
    final_amount = max(0.0, round(subtotal - discount_amount + shipping_fee, 2))

    # Payment validation for COD
    if payload.payment_method == "COD":
        if not settings.ENABLE_COD:
            raise HTTPException(status_code=400, detail="Cash on Delivery is currently disabled")
        if final_amount < settings.COD_MIN_ORDER_AMOUNT or final_amount > settings.COD_MAX_ORDER_AMOUNT:
            raise HTTPException(
                status_code=400,
                detail=f"COD is only available for orders between ₹{settings.COD_MIN_ORDER_AMOUNT} and ₹{settings.COD_MAX_ORDER_AMOUNT}"
            )

    order_id = generate_order_id()
    now = datetime.now(timezone.utc)

    # Status determination
    initial_order_status = "ORDER_PLACED" if payload.payment_method == "COD" else "PAYMENT_PENDING"
    initial_payment_status = "PENDING_COD" if payload.payment_method == "COD" else "PENDING"

    timeline = [
        {
            "status": "ORDER_PLACED",
            "message": f"Order {order_id} created with payment method {payload.payment_method}",
            "timestamp": now,
            "performed_by": customer_name or "Customer"
        }
    ]

    order_doc = {
        "order_id": order_id,
        "user_id": user_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "items": order_items,
        "subtotal": round(subtotal, 2),
        "discount_amount": round(discount_amount, 2),
        "coupon_code": applied_coupon,
        "shipping_fee": round(shipping_fee, 2),
        "final_amount": round(final_amount, 2),
        "currency": "INR",
        "shipping_address": payload.shipping_address.model_dump(),
        "payment_method": payload.payment_method,
        "payment_status": initial_payment_status,
        "order_status": initial_order_status,
        "fulfilment_status": "UNFULFILLED",
        "carrier_name": None,
        "tracking_number": None,
        "notes": payload.notes,
        "timeline": timeline,
        "created_at": now,
        "updated_at": now
    }

    # Atomically deduct stock
    for item in order_items:
        db.products.update_one(
            {"sku": item["sku"]},
            {
                "$inc": {"stock": -item["quantity"], "sales_count": item["quantity"]},
                "$set": {"updated_at": now}
            }
        )
        # Log inventory movement
        db.inventory_movements.insert_one({
            "product_id": item["product_id"],
            "sku": item["sku"],
            "product_name": item["name"],
            "quantity_change": -item["quantity"],
            "adjustment_type": "SALE",
            "reason": f"Order #{order_id}",
            "performed_by": customer_email,
            "created_at": now
        })

    res = db.orders.insert_one(order_doc)
    doc_id = str(res.inserted_id)

    # Clear user's cart if authenticated
    if current_user:
        db.carts.update_one(
            {"user_id": current_user["id"]},
            {"$set": {"items": [], "coupon_code": None, "updated_at": now}}
        )

    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="ORDER_CREATED",
        resource_type="ORDER",
        resource_id=order_id,
        user_id=user_id,
        user_email=customer_email,
        details={"final_amount": final_amount, "items_count": len(order_items)}
    )

    return {
        "order_id": order_id,
        "id": doc_id,
        "final_amount": final_amount,
        "payment_method": payload.payment_method,
        "order_status": initial_order_status,
        "payment_status": initial_payment_status,
        "message": "Order created successfully"
    }

@router.get("/my-orders")
def get_my_orders(current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    cursor = db.orders.find({"user_id": current_user["id"]}).sort("created_at", -1)
    orders = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        orders.append(doc)
    return orders

@router.get("/{order_id}")
def get_order_by_id(
    order_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user),
    db = Depends(get_db)
):
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        try:
            order = db.orders.find_one({"_id": ObjectId(order_id)})
        except Exception:
            pass
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Security check: if not admin, ensure order belongs to current user
    if current_user:
        is_admin = current_user.get("role") in [Role.SUPER_ADMIN, Role.ADMIN, Role.ORDER_MANAGER, Role.CUSTOMER_SUPPORT]
        if not is_admin and order.get("user_id") != current_user["id"] and order.get("customer_email") != current_user.get("email"):
            raise HTTPException(status_code=403, detail="Access denied to this order")

    order["id"] = str(order["_id"])
    order.pop("_id", None)
    return order

@router.post("/{order_id}/cancel")
def cancel_customer_order(
    order_id: str,
    reason: str = "Customer requested cancellation",
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_admin = current_user.get("role") in [Role.SUPER_ADMIN, Role.ADMIN, Role.ORDER_MANAGER]
    if not is_admin and order.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot cancel an order that is not yours")

    # Check eligibility
    if order.get("order_status") in ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in status '{order.get('order_status')}'")

    now = datetime.now(timezone.utc)
    # Restock inventory
    for item in order.get("items", []):
        db.products.update_one(
            {"sku": item["sku"]},
            {
                "$inc": {"stock": item["quantity"], "sales_count": -item["quantity"]},
                "$set": {"updated_at": now}
            }
        )
        db.inventory_movements.insert_one({
            "product_id": item["product_id"],
            "sku": item["sku"],
            "product_name": item["name"],
            "quantity_change": item["quantity"],
            "adjustment_type": "RESTOCK",
            "reason": f"Cancellation for order #{order_id}: {reason}",
            "performed_by": current_user.get("email"),
            "created_at": now
        })

    # Update timeline
    timeline = order.get("timeline", [])
    timeline.append({
        "status": "CANCELLED",
        "message": f"Order cancelled: {reason}",
        "timestamp": now,
        "performed_by": current_user.get("full_name") or current_user.get("email")
    })

    db.orders.update_one(
        {"order_id": order_id},
        {"$set": {"order_status": "CANCELLED", "timeline": timeline, "updated_at": now}}
    )
    db_manager.persist_to_disk()
    return {"message": "Order cancelled successfully and inventory restored"}

@router.post("/{order_id}/return")
def request_order_return(
    order_id: str,
    payload: ReturnRequestCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if order.get("order_status") != "DELIVERED":
        raise HTTPException(status_code=400, detail="Returns are only eligible for delivered orders")

    now = datetime.now(timezone.utc)
    return_doc = {
        "order_id": order_id,
        "user_id": current_user["id"],
        "customer_name": current_user.get("full_name"),
        "customer_email": current_user.get("email"),
        "reason": payload.reason,
        "comments": payload.comments,
        "images": payload.images,
        "status": "RETURN_REQUESTED",
        "created_at": now,
        "updated_at": now
    }
    db.returns.insert_one(return_doc)

    timeline = order.get("timeline", [])
    timeline.append({
        "status": "RETURN_REQUESTED",
        "message": f"Return requested by customer. Reason: {payload.reason}",
        "timestamp": now,
        "performed_by": current_user.get("full_name")
    })

    db.orders.update_one(
        {"order_id": order_id},
        {"$set": {"order_status": "RETURN_REQUESTED", "timeline": timeline, "updated_at": now}}
    )
    db_manager.persist_to_disk()
    return {"message": "Return request submitted successfully. Our team will review it within 24-48 hours."}

# Admin endpoints (Meesho Supplier style)
@router.get("/admin/all", dependencies=[Depends(require_roles([Role.ADMIN, Role.ORDER_MANAGER, Role.CUSTOMER_SUPPORT]))])
def list_orders_admin(
    search: Optional[str] = None,
    order_status: Optional[str] = None,
    payment_status: Optional[str] = None,
    payment_method: Optional[str] = None,
    page: int = 1,
    limit: int = 15,
    db = Depends(get_db)
):
    query = {}
    if order_status:
        query["order_status"] = order_status
    if payment_status:
        query["payment_status"] = payment_status
    if payment_method:
        query["payment_method"] = payment_method

    if search:
        reg = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"order_id": reg},
            {"customer_name": reg},
            {"customer_email": reg},
            {"customer_phone": reg},
            {"tracking_number": reg}
        ]

    total_count = db.orders.count_documents(query)
    cursor = db.orders.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)

    orders = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        orders.append(doc)

    return {
        "orders": orders,
        "total": total_count,
        "page": page,
        "pages": (total_count + limit - 1) // limit,
        "limit": limit
    }

@router.put("/admin/{order_id}/status", dependencies=[Depends(require_roles([Role.ADMIN, Role.ORDER_MANAGER]))])
def update_order_status_admin(
    order_id: str,
    payload: OrderStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    now = datetime.now(timezone.utc)
    update_data: Dict[str, Any] = {
        "order_status": payload.status,
        "updated_at": now
    }

    if payload.carrier_name:
        update_data["carrier_name"] = payload.carrier_name
    if payload.tracking_number:
        update_data["tracking_number"] = payload.tracking_number

    if payload.status in ["SHIPPED", "OUT_FOR_DELIVERY"]:
        update_data["fulfilment_status"] = "SHIPPED"
    elif payload.status == "DELIVERED":
        update_data["fulfilment_status"] = "DELIVERED"
        if order.get("payment_method") == "COD":
            update_data["payment_status"] = "PAID"

    timeline = order.get("timeline", [])
    msg = f"Order status updated to {payload.status}"
    if payload.tracking_number:
        msg += f" (Carrier: {payload.carrier_name or 'Standard'}, AWB/Tracking: {payload.tracking_number})"
    if payload.internal_notes:
        msg += f" - Note: {payload.internal_notes}"

    timeline.append({
        "status": payload.status,
        "message": msg,
        "timestamp": now,
        "performed_by": f"{current_user.get('full_name')} ({current_user.get('role')})"
    })
    update_data["timeline"] = timeline

    db.orders.update_one({"order_id": order_id}, {"$set": update_data})
    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="ORDER_STATUS_UPDATED",
        resource_type="ORDER",
        resource_id=order_id,
        user_id=current_user.get("id"),
        user_email=current_user.get("email"),
        details={"new_status": payload.status}
    )

    return {"message": f"Order status updated to {payload.status}", "order_id": order_id}

@router.get("/admin/{order_id}/packing-slip", dependencies=[Depends(require_roles([Role.ADMIN, Role.ORDER_MANAGER]))])
def get_packing_slip(order_id: str, db = Depends(get_db)):
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order["id"] = str(order["_id"])
    order.pop("_id", None)
    return {
        "brand_name": settings.BRAND_NAME,
        "brand_short": settings.BRAND_SHORT_NAME,
        "business_address": settings.BUSINESS_ADDRESS,
        "support_phone": settings.SUPPORT_PHONE,
        "support_email": settings.SUPPORT_EMAIL,
        "order": order
    }
