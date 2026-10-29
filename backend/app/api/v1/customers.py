from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db, db_manager
from app.schemas.customer import ReviewCreate, ContactInquiry
from app.core.permissions import Role
from app.core.logging import AuditLogger
from app.api.dependencies import require_roles, get_current_user

router = APIRouter(prefix="/customers", tags=["Customers & Support"])

@router.get("/admin/all", dependencies=[Depends(require_roles([Role.ADMIN, Role.CUSTOMER_SUPPORT]))])
def list_customers_admin(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db = Depends(get_db)
):
    query = {"role": Role.CUSTOMER}
    if search:
        reg = {"$regex": search, "$options": "i"}
        query["$or"] = [{"full_name": reg}, {"email": reg}, {"phone": reg}]

    total = db.users.count_documents(query)
    cursor = db.users.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit)

    customers = []
    for u in cursor:
        uid = str(u["_id"])
        # Calculate orders count and total spend
        user_orders = list(db.orders.find({"user_id": uid}))
        total_orders = len(user_orders)
        total_spent = sum(o.get("final_amount", 0) for o in user_orders if o.get("order_status") not in ["CANCELLED", "PAYMENT_PENDING"])

        customers.append({
            "id": uid,
            "full_name": u.get("full_name", ""),
            "email": u.get("email", ""),
            "phone": u.get("phone", ""),
            "addresses_count": len(u.get("addresses", [])),
            "total_orders": total_orders,
            "total_spent": round(total_spent, 2),
            "is_active": u.get("is_active", True),
            "created_at": u.get("created_at")
        })

    return {
        "customers": customers,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "limit": limit
    }

@router.post("/contact")
def submit_contact_inquiry(payload: ContactInquiry, db = Depends(get_db)):
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    doc["status"] = "NEW"
    res = db.inquiries.insert_one(doc)
    db_manager.persist_to_disk()
    return {"message": "Thank you for contacting SSK Collections. We will get back to you shortly.", "id": str(res.inserted_id)}

@router.get("/admin/inquiries", dependencies=[Depends(require_roles([Role.ADMIN, Role.CUSTOMER_SUPPORT]))])
def list_inquiries_admin(db = Depends(get_db)):
    cursor = db.inquiries.find({}).sort("created_at", -1)
    inquiries = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        inquiries.append(doc)
    return inquiries

@router.post("/reviews")
def submit_product_review(
    payload: ReviewCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Verify product exists
    p = None
    try:
        p = db.products.find_one({"_id": ObjectId(payload.product_id)})
    except Exception:
        pass
    if not p:
        p = db.products.find_one({"_id": payload.product_id}) or db.products.find_one({"id": payload.product_id}) or db.products.find_one({"sku": payload.product_id})

    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    review_doc = {
        "product_id": str(p.get("id", p.get("_id"))),
        "user_id": current_user["id"],
        "reviewer_name": payload.reviewer_name or current_user.get("full_name") or "Verified Buyer",
        "rating": payload.rating,
        "title": payload.title,
        "comment": payload.comment,
        "images": payload.images,
        "is_verified_purchase": True,
        "is_approved": True, # Auto-approved or moderation
        "created_at": datetime.now(timezone.utc)
    }
    db.reviews.insert_one(review_doc)

    # Re-calculate product average rating
    all_revs = list(db.reviews.find({"product_id": review_doc["product_id"], "is_approved": True}))
    avg_rating = sum(r["rating"] for r in all_revs) / len(all_revs) if all_revs else 5.0
    db.products.update_one(
        {"_id": p["_id"]},
        {"$set": {"rating": round(avg_rating, 1), "rating_count": len(all_revs)}}
    )

    db_manager.persist_to_disk()
    return {"message": "Review submitted successfully!"}
