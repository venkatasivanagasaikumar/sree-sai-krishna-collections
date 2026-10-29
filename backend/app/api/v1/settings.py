from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime, timezone
from app.database import get_db, db_manager
from app.core.config import settings
from app.core.permissions import Role
from app.api.dependencies import require_roles

router = APIRouter(prefix="/settings", tags=["Business Settings"])

DEFAULT_SETTINGS = {
    "brand_name": settings.BRAND_NAME,
    "brand_short_name": settings.BRAND_SHORT_NAME,
    "store_tagline": "Exclusive Women's Jewellery & Fashion Accessories",
    "support_email": settings.SUPPORT_EMAIL,
    "support_phone": settings.SUPPORT_PHONE,
    "business_address": settings.BUSINESS_ADDRESS,
    "free_shipping_threshold": settings.FREE_SHIPPING_THRESHOLD,
    "standard_shipping_fee": settings.STANDARD_SHIPPING_FEE,
    "enable_cod": settings.ENABLE_COD,
    "cod_min_order": settings.COD_MIN_ORDER_AMOUNT,
    "cod_max_order": settings.COD_MAX_ORDER_AMOUNT,
    "return_window_days": 7,
    "maintenance_mode": False,
    "announcement_bar_text": "✨ Festive Grand Launch! Free Express Delivery on orders above ₹999 | Code: SSKFIRST10 for 10% OFF",
    "primary_market": "India",
    "currency_symbol": "₹",
    "currency_code": "INR"
}

@router.get("/public")
def get_public_settings(db = Depends(get_db)):
    cfg = db.store_settings.find_one({"key": "general"})
    if not cfg:
        return DEFAULT_SETTINGS
    data = dict(DEFAULT_SETTINGS)
    data.update(cfg.get("data", {}))
    return data

@router.put("/admin", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def update_store_settings(payload: Dict[str, Any], db = Depends(get_db)):
    db.store_settings.update_one(
        {"key": "general"},
        {"$set": {"data": payload, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    db_manager.persist_to_disk()
    return {"message": "Store settings updated successfully"}
