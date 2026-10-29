from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CategoryBase(BaseModel):
    name: str
    slug: str
    parent_category: Optional[str] = None # Jewellery, Hair Accessories, Women's Accessories
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class ProductVariant(BaseModel):
    variant_id: str
    name: str # e.g. "Size 2.4 / Ruby Red"
    sku: str
    price: float
    mrp: float
    stock: int
    color: Optional[str] = None
    size: Optional[str] = None
    image_url: Optional[str] = None

class ProductBase(BaseModel):
    name: str
    sku: str
    category: str
    subcategory: Optional[str] = None
    description: str
    short_description: Optional[str] = None
    mrp: float
    price: float # Selling price in INR
    stock: int
    low_stock_threshold: int = 5
    images: List[str] = []
    materials_and_finish: str # e.g. "Brass alloy with micro gold-plating finish (Imitation)"
    jewelry_type: str = "Fashion / Imitation" # "1-Gram Gold Finish", "Imitation Jewellery", "Hair Accessory", etc.
    genuine_gold_disclaimer: str = "This is a premium imitation / gold-finish fashion piece and contains no precious gold bullion or hallmark certification."
    colors: List[str] = []
    sizes: List[str] = []
    variants: List[ProductVariant] = []
    care_instructions: str = "Keep away from water, perfumes, and harsh chemicals. Store in an airtight pouch or box after use."
    shipping_estimate_days: str = "2-5 Business Days"
    return_eligible: bool = True
    return_window_days: int = 7
    status: str = "active" # active, draft, inactive, archived
    tags: List[str] = []
    is_featured: bool = False
    is_bestseller: bool = False
    is_trending: bool = False
    weight_grams: Optional[float] = 50.0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    mrp: Optional[float] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    images: Optional[List[str]] = None
    materials_and_finish: Optional[str] = None
    jewelry_type: Optional[str] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    variants: Optional[List[ProductVariant]] = None
    care_instructions: Optional[str] = None
    shipping_estimate_days: Optional[str] = None
    return_eligible: Optional[bool] = None
    return_window_days: Optional[int] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    is_trending: Optional[bool] = None
    weight_grams: Optional[float] = None
