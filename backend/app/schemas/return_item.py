from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ReturnStatusUpdate(BaseModel):
    status: str # "APPROVED", "REJECTED", "PICKED_UP", "RECEIVED", "REFUND_INITIATED", "REFUNDED"
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_transaction_id: Optional[str] = None
