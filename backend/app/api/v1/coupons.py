from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db, db_manager
from app.schemas.coupon import CouponCreate, CouponUpdate
from app.core.permissions import Role
from app.api.dependencies import require_roles

router = APIRouter(prefix="/coupons", tags=["Coupons"])

@router.get("/active")
def get_public_active_coupons(db = Depends(get_db)):
    """Returns active coupons for banners and customer storefront checkout."""
    now = datetime.now(timezone.utc)
    coupons = list(db.coupons.find({"is_active": True}))
    valid = []
    for c in coupons:
        start_ok = not c.get("start_date") or c["start_date"] <= now
        end_ok = not c.get("expiry_date") or c["expiry_date"] >= now
        if start_ok and end_ok:
            c["id"] = str(c["_id"])
            c.pop("_id", None)
            valid.append(c)
    return valid

@router.get("/admin/all", dependencies=[Depends(require_roles([Role.ADMIN]))])
def list_all_coupons_admin(db = Depends(get_db)):
    coupons = list(db.coupons.find({}).sort("created_at", -1))
    for c in coupons:
        c["id"] = str(c["_id"])
        c.pop("_id", None)
    return coupons

@router.post("", dependencies=[Depends(require_roles([Role.ADMIN]))])
def create_coupon(payload: CouponCreate, db = Depends(get_db)):
    code_upper = payload.code.upper().strip()
    if db.coupons.find_one({"code": code_upper}):
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    doc = payload.model_dump()
    doc["code"] = code_upper
    doc["times_used"] = 0
    doc["created_at"] = datetime.now(timezone.utc)
    res = db.coupons.insert_one(doc)
    db_manager.persist_to_disk()
    return {"message": "Coupon created", "id": str(res.inserted_id)}

@router.put("/{coupon_id}", dependencies=[Depends(require_roles([Role.ADMIN]))])
def update_coupon(coupon_id: str, payload: CouponUpdate, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(coupon_id)}
    except Exception:
        query = {"_id": coupon_id}

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    res = db.coupons.update_one(query, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db_manager.persist_to_disk()
    return {"message": "Coupon updated"}

@router.delete("/{coupon_id}", dependencies=[Depends(require_roles([Role.ADMIN]))])
def delete_coupon(coupon_id: str, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(coupon_id)}
    except Exception:
        query = {"_id": coupon_id}

    res = db.coupons.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db_manager.persist_to_disk()
    return {"message": "Coupon deleted"}
