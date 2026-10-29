from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db, db_manager
from app.schemas.inventory import StockAdjustment, InventoryMovementRecord
from app.core.permissions import Role
from app.core.logging import AuditLogger
from app.api.dependencies import require_roles, get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def get_inventory_status(
    search: Optional[str] = None,
    low_stock_only: bool = False,
    page: int = 1,
    limit: int = 20,
    db = Depends(get_db)
):
    query = {"status": {"$ne": "archived"}}
    if low_stock_only:
        # Stock <= low_stock_threshold or stock <= 5
        query["stock"] = {"$lte": 5}
    if search:
        reg = {"$regex": search, "$options": "i"}
        query["$or"] = [{"name": reg}, {"sku": reg}, {"category": reg}]

    total = db.products.count_documents(query)
    cursor = db.products.find(query).sort("stock", 1).skip((page - 1) * limit).limit(limit)

    items = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        doc["is_low_stock"] = doc.get("stock", 0) <= doc.get("low_stock_threshold", 5)
        items.append(doc)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "limit": limit
    }

@router.post("/adjust", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def adjust_stock(
    payload: StockAdjustment,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    p = db.products.find_one({"sku": payload.sku})
    if not p:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{payload.sku}' not found")

    prev_stock = int(p.get("stock", 0))
    new_stock = prev_stock + payload.quantity_change
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock adjustment cannot result in negative stock")

    now = datetime.now(timezone.utc)
    db.products.update_one(
        {"sku": payload.sku},
        {"$set": {"stock": new_stock, "updated_at": now}}
    )

    movement = {
        "product_id": str(p.get("id", p.get("_id"))),
        "sku": payload.sku,
        "product_name": p.get("name"),
        "previous_stock": prev_stock,
        "quantity_change": payload.quantity_change,
        "new_stock": new_stock,
        "adjustment_type": payload.adjustment_type,
        "reason": payload.reason,
        "performed_by": f"{current_user.get('full_name')} ({current_user.get('role')})",
        "created_at": now
    }
    db.inventory_movements.insert_one(movement)
    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="INVENTORY_ADJUSTMENT",
        resource_type="INVENTORY",
        resource_id=payload.sku,
        user_id=current_user.get("id"),
        user_email=current_user.get("email"),
        details={
            "sku": payload.sku,
            "change": payload.quantity_change,
            "new_stock": new_stock,
            "type": payload.adjustment_type,
            "reason": payload.reason
        }
    )

    return {
        "message": f"Stock adjusted for {payload.sku}",
        "previous_stock": prev_stock,
        "new_stock": new_stock
    }

@router.get("/movements", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def get_inventory_movements(
    sku: Optional[str] = None,
    limit: int = 50,
    db = Depends(get_db)
):
    query = {}
    if sku:
        query["sku"] = sku
    
    cursor = db.inventory_movements.find(query).sort("created_at", -1).limit(limit)
    movements = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        movements.append(doc)
    return movements
