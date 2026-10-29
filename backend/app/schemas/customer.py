from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    title: str
    comment: str
    reviewer_name: str
    images: List[str] = []

class ContactInquiry(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str
