from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CouponBase(BaseModel):
    code: str
    description: str
    discount_type: str = "percentage" # "percentage" or "fixed"
    discount_value: float
    min_order_value: float = 0.0
    max_discount_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    usage_limit_total: Optional[int] = None
    usage_limit_per_user: int = 1
    is_active: bool = True

class CouponCreate(CouponBase):
    pass

class CouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_value: Optional[float] = None
    max_discount_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    usage_limit_total: Optional[int] = None
    usage_limit_per_user: Optional[int] = None
    is_active: Optional[bool] = None
