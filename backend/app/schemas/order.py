from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.auth import Address

class OrderItem(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    name: str
    sku: str
    image: str
    unit_price: float
    mrp: float
    quantity: int
    total_price: float

class TimelineEvent(BaseModel):
    status: str
    message: str
    timestamp: datetime
    performed_by: Optional[str] = None

class CreateOrderRequest(BaseModel):
    shipping_address: Address
    payment_method: str = "Razorpay" # "Razorpay", "COD"
    coupon_code: Optional[str] = None
    notes: Optional[str] = None
    guest_email: Optional[str] = None
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None
    cart_items: Optional[List[Dict[str, Any]]] = None # For guest checkout

class OrderStatusUpdate(BaseModel):
    status: str
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    internal_notes: Optional[str] = None

class ReturnRequestCreate(BaseModel):
    reason: str
    comments: Optional[str] = None
    images: List[str] = []
