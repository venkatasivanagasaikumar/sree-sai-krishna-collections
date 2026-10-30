from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime, timezone
import io
import csv
from bson import ObjectId
from app.database import get_db, db_manager
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.permissions import Role
from app.core.logging import AuditLogger
from app.api.dependencies import require_roles, get_optional_current_user

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("")
def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    jewelry_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: Optional[bool] = False,
    sort_by: Optional[str] = "recommended", # recommended, newest, price_asc, price_desc, popularity, discount
    page: int = 1,
    limit: int = 12,
    db = Depends(get_db)
):
    query = {"status": "active"}

    if category:
        query["category"] = category
    if subcategory:
        query["subcategory"] = subcategory
    if jewelry_type:
        query["jewelry_type"] = jewelry_type
    if in_stock_only:
        query["stock"] = {"$gt": 0}
    
    price_q = {}
    if min_price is not None:
        price_q["$gte"] = min_price
    if max_price is not None:
        price_q["$lte"] = max_price
    if price_q:
        query["price"] = price_q

    if search:
        # regex search for flexibility
        reg = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"name": reg},
            {"description": reg},
            {"sku": reg},
            {"category": reg},
            {"subcategory": reg},
            {"tags": reg}
        ]

    # Sorting
    sort_field = [("created_at", -1)]
    if sort_by == "newest":
        sort_field = [("created_at", -1)]
    elif sort_by == "price_asc":
        sort_field = [("price", 1)]
    elif sort_by == "price_desc":
        sort_field = [("price", -1)]
    elif sort_by == "popularity":
        sort_field = [("sales_count", -1), ("rating", -1)]
    elif sort_by == "discount":
        sort_field = [("discount_percent", -1)]
    elif sort_by == "recommended":
        sort_field = [("is_featured", -1), ("is_bestseller", -1), ("rating", -1)]

    total_count = db.products.count_documents(query)
    skip = (page - 1) * limit
    cursor = db.products.find(query).sort(sort_field).skip(skip).limit(limit)

    products = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        # Compute discount percentage if not present
        if doc.get("mrp") and doc["mrp"] > doc.get("price", 0):
            doc["discount_percent"] = round(((doc["mrp"] - doc["price"]) / doc["mrp"]) * 100)
            doc["discount_amount"] = round(doc["mrp"] - doc["price"], 2)
        else:
            doc["discount_percent"] = 0
            doc["discount_amount"] = 0
        products.append(doc)

    return {
        "products": products,
        "total": total_count,
        "page": page,
        "pages": (total_count + limit - 1) // limit,
        "limit": limit
    }

@router.get("/featured")
def get_featured_products(limit: int = 8, db = Depends(get_db)):
    cursor = db.products.find({"status": "active", "is_featured": True}).limit(limit)
    items = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        items.append(doc)
    return items

@router.get("/bestsellers")
def get_bestseller_products(limit: int = 8, db = Depends(get_db)):
    cursor = db.products.find({"status": "active", "is_bestseller": True}).limit(limit)
    items = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        items.append(doc)
    return items

@router.get("/trending")
def get_trending_products(limit: int = 8, db = Depends(get_db)):
    cursor = db.products.find({"status": "active", "is_trending": True}).limit(limit)
    items = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        items.append(doc)
    return items

@router.get("/{id_or_sku}")
def get_product_details(id_or_sku: str, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(id_or_sku)}
    except Exception:
        query = {"$or": [{"sku": id_or_sku}, {"id": id_or_sku}]}
    
    product = db.products.find_one(query)
    if not product:
        # Check by id string
        product = db.products.find_one({"_id": id_or_sku})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product["id"] = str(product["_id"])
    product.pop("_id", None)
    
    # Compute discount
    if product.get("mrp") and product["mrp"] > product.get("price", 0):
        product["discount_percent"] = round(((product["mrp"] - product["price"]) / product["mrp"]) * 100)
        product["discount_amount"] = round(product["mrp"] - product["price"], 2)

    # Fetch reviews
    reviews = list(db.reviews.find({"product_id": product["id"], "is_approved": True}).sort("created_at", -1))
    for r in reviews:
        r["id"] = str(r["_id"])
        r.pop("_id", None)
    product["reviews"] = reviews

    # Fetch related products
    related = list(db.products.find({
        "category": product.get("category"),
        "id": {"$ne": product["id"]},
        "status": "active"
    }).limit(4))
    for rel in related:
        rel["id"] = str(rel["_id"])
        rel.pop("_id", None)
    product["related_products"] = related

    return product

# Admin routes
@router.post("", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def create_product(payload: ProductCreate, db = Depends(get_db)):
    # Check duplicate SKU
    if db.products.find_one({"sku": payload.sku.upper()}):
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    doc = payload.model_dump()
    doc["sku"] = payload.sku.upper()
    doc["sales_count"] = 0
    doc["rating"] = 5.0
    doc["rating_count"] = 0
    doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = datetime.now(timezone.utc)
    
    res = db.products.insert_one(doc)
    doc_id = str(res.inserted_id)
    db.products.update_one({"_id": res.inserted_id}, {"$set": {"id": doc_id}})
    db_manager.persist_to_disk()
    
    AuditLogger.log_event(
        db,
        action="PRODUCT_CREATED",
        resource_type="PRODUCT",
        resource_id=doc_id,
        details={"sku": doc["sku"], "name": doc["name"]}
    )
    return {"message": "Product created successfully", "id": doc_id}

@router.put("/{product_id}", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def update_product(product_id: str, payload: ProductUpdate, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(product_id)}
    except Exception:
        query = {"_id": product_id}
    
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        return {"message": "Nothing to update"}
    
    if "sku" in update_data:
        update_data["sku"] = update_data["sku"].upper()
    update_data["updated_at"] = datetime.now(timezone.utc)

    res = db.products.update_one(query, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    db_manager.persist_to_disk()
    
    AuditLogger.log_event(
        db,
        action="PRODUCT_UPDATED",
        resource_type="PRODUCT",
        resource_id=product_id,
        details={"updated_keys": list(update_data.keys())}
    )
    return {"message": "Product updated successfully"}

@router.delete("/{product_id}", dependencies=[Depends(require_roles([Role.ADMIN]))])
def delete_or_archive_product(product_id: str, hard_delete: bool = False, db = Depends(get_db)):
    query = {}
    try:
        query = {"_id": ObjectId(product_id)}
    except Exception:
        query = {"_id": product_id}

    if hard_delete:
        res = db.products.delete_one(query)
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
    else:
        # Soft delete / Archive
        res = db.products.update_one(query, {"$set": {"status": "archived", "updated_at": datetime.now(timezone.utc)}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

    db_manager.persist_to_disk()
    return {"message": "Product archived/deleted successfully"}

@router.get("/admin/export/csv", dependencies=[Depends(require_roles([Role.ADMIN, Role.INVENTORY_MANAGER]))])
def export_products_csv(db = Depends(get_db)):
    products = list(db.products.find({}))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["SKU", "Name", "Category", "Subcategory", "MRP", "Price", "Stock", "Status", "Jewelry_Type"])
    for p in products:
        writer.writerow([
            p.get("sku", ""),
            p.get("name", ""),
            p.get("category", ""),
            p.get("subcategory", ""),
            p.get("mrp", 0),
            p.get("price", 0),
            p.get("stock", 0),
            p.get("status", "active"),
            p.get("jewelry_type", "")
        ])
    return {
        "csv_content": output.getvalue(),
        "filename": f"ssk_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    }
