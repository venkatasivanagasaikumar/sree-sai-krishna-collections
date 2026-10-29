from pydantic import BaseModel, Field
from typing import List, Optional

class CartItem(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(..., ge=1)

class CartItemDetail(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    name: str
    sku: str
    image: str
    mrp: float
    price: float
    quantity: int
    total_price: float
    stock: int
    in_stock: bool

class CartResponse(BaseModel):
    items: List[CartItemDetail] = []
    subtotal: float = 0.0
    discount_amount: float = 0.0
    coupon_code: Optional[str] = None
    shipping_fee: float = 0.0
    final_amount: float = 0.0
    free_shipping_eligible: bool = False
    amount_needed_for_free_shipping: float = 0.0

class ApplyCouponRequest(BaseModel):
    code: str
