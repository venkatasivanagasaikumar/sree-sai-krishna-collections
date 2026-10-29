from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from app.database import get_db, db_manager
from app.schemas.product import CategoryBase, CategoryCreate, CategoryUpdate
from app.core.permissions import Role
from app.api.dependencies import require_roles

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("")
def list_categories(db = Depends(get_db)):
    cats = list(db.categories.find({"is_active": True}).sort("display_order", 1))
    for c in cats:
        c["id"] = str(c["_id"])
        c.pop("_id", None)
    return cats

@router.get("/admin/all", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def list_all_categories_admin(db = Depends(get_db)):
    cats = list(db.categories.find({}).sort("display_order", 1))
    for c in cats:
        c["id"] = str(c["_id"])
        c.pop("_id", None)
    return cats

@router.post("", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def create_category(payload: CategoryCreate, db = Depends(get_db)):
    existing = db.categories.find_one({"slug": payload.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    doc = payload.model_dump()
    res = db.categories.insert_one(doc)
    db_manager.persist_to_disk()
    return {"message": "Category created", "id": str(res.inserted_id)}

@router.put("/{cat_id}", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def update_category(cat_id: str, payload: CategoryUpdate, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(cat_id)}
    except Exception:
        query = {"_id": cat_id}
    
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        return {"message": "Nothing to update"}
    
    res = db.categories.update_one(query, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    db_manager.persist_to_disk()
    return {"message": "Category updated"}

@router.delete("/{cat_id}", dependencies=[Depends(require_roles([Role.ADMIN]))])
def delete_category(cat_id: str, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(cat_id)}
    except Exception:
        query = {"_id": cat_id}
    
    res = db.categories.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    db_manager.persist_to_disk()
    return {"message": "Category deleted"}
