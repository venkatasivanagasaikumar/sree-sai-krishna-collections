from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.database import get_db, db_manager
from app.core.config import settings
from app.core.permissions import Role
from app.api.dependencies import require_roles
from app.services.backup_service import BackupService

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

@router.get("/database/status", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def get_database_status(db = Depends(get_db)):
    """Returns database operational mode, collection statistics, and health."""
    col_counts = {}
    for col in db.list_collection_names():
        col_counts[col] = db[col].count_documents({})
    
    return {
        "status": "healthy",
        "engine": "mongomock (file-persisted)" if db_manager.is_mock else "mongodb-cluster",
        "is_mock": db_manager.is_mock,
        "database_name": settings.DATABASE_NAME,
        "collections_count": len(col_counts),
        "collections": col_counts,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/backups", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def list_database_backups():
    """Lists all stored database snapshots."""
    return {"backups": BackupService.list_backups()}

@router.post("/backups/create", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def create_database_backup(tag: Optional[str] = None):
    """Creates an immediate snapshot backup with sha256 checksum."""
    res = BackupService.create_backup(tag=tag)
    return {"message": "Database backup created successfully", "backup": res}

@router.post("/backups/restore", dependencies=[Depends(require_roles([Role.SUPER_ADMIN]))])
def restore_database_backup(payload: Dict[str, str]):
    """Restores database from a specific snapshot filename."""
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Backup filename is required.")
    try:
        res = BackupService.restore_backup(filename)
        return {"message": "Database restored successfully", "details": res}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

