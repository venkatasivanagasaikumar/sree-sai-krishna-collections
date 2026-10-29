from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class StockAdjustment(BaseModel):
    product_id: str
    sku: str
    variant_id: Optional[str] = None
    adjustment_type: str # "RESTOCK", "DAMAGED", "AUDIT_CORRECTION", "SALE", "RETURN"
    quantity_change: int # Positive for additions, negative for deductions
    reason: str

class InventoryMovementRecord(BaseModel):
    id: Optional[str] = None
    product_id: str
    sku: str
    product_name: str
    previous_stock: int
    quantity_change: int
    new_stock: int
    adjustment_type: str
    reason: str
    performed_by: str
    created_at: datetime
