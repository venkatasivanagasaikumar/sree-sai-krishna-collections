from app.database import get_db
from app.api.v1.products import list_products, get_product_details, create_product
from app.schemas.product import ProductCreate
import pytest
from fastapi import HTTPException

def test_list_and_search_products():
    db = get_db()
    res = list_products(search=None, category=None, page=1, limit=10, db=db)
    assert res["total"] >= 8
    assert len(res["products"]) >= 1

    # Category filter
    jhumkas = list_products(category="Earrings & Jhumkas", page=1, limit=10, db=db)
    assert len(jhumkas["products"]) >= 1
    for p in jhumkas["products"]:
        assert p["category"] == "Earrings & Jhumkas"

    # Search filter
    search_res = list_products(search="Matte", page=1, limit=10, db=db)
    assert len(search_res["products"]) >= 1

def test_product_detail():
    db = get_db()
    prod = get_product_details("SSK-JWL-101", db=db)
    assert prod["sku"] == "SSK-JWL-101"
    assert "Royal Lakshmi" in prod["name"]
    assert prod["price"] == 1899.0
    assert "care_instructions" in prod

def test_create_duplicate_sku_rejected():
    db = get_db()
    dto = ProductCreate(
        name="Duplicate Test",
        sku="SSK-JWL-101", # Existing
        category="1-Gram Gold Jewellery",
        description="Test description",
        mrp=2000.0,
        price=1000.0,
        stock=10,
        materials_and_finish="Brass"
    )
    with pytest.raises(HTTPException) as exc:
        create_product(payload=dto, db=db)
    assert exc.value.status_code == 400
