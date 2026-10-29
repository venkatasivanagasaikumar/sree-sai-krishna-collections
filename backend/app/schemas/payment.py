from pydantic import BaseModel
from typing import Optional, Dict, Any

class RazorpayOrderResponse(BaseModel):
    order_id: str
    razorpay_order_id: str
    amount_in_paise: int
    currency: str = "INR"
    key_id: str
    business_name: str
    prefill: Dict[str, str]

class VerifyPaymentRequest(BaseModel):
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentStatusResponse(BaseModel):
    order_id: str
    payment_status: str
    payment_id: Optional[str] = None
    amount: float
    method: str
