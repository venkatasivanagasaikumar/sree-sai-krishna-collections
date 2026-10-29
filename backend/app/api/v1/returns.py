from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db, db_manager
from app.schemas.return_item import ReturnStatusUpdate
from app.core.permissions import Role
from app.core.logging import AuditLogger
from app.api.dependencies import require_roles, get_current_user

router = APIRouter(prefix="/returns", tags=["Returns & Refunds"])

@router.get("/admin/all", dependencies=[Depends(require_roles([Role.ADMIN, Role.ORDER_MANAGER, Role.CUSTOMER_SUPPORT]))])
def list_returns_admin(status_filter: Optional[str] = None, db = Depends(get_db)):
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    cursor = db.returns.find(query).sort("created_at", -1)
    returns = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        doc.pop("_id", None)
        returns.append(doc)
    return returns

@router.put("/admin/{return_id}/status", dependencies=[Depends(require_roles([Role.ADMIN, Role.ORDER_MANAGER]))])
def update_return_status(
    return_id: str,
    payload: ReturnStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    query = {}
    try:
        query = {"_id": ObjectId(return_id)}
    except Exception:
        query = {"_id": return_id}
    
    ret = db.returns.find_one(query)
    if not ret:
        ret = db.returns.find_one({"order_id": return_id})
    if not ret:
        raise HTTPException(status_code=404, detail="Return request not found")

    now = datetime.now(timezone.utc)
    update_data = {
        "status": payload.status,
        "updated_at": now
    }
    if payload.rejection_reason:
        update_data["rejection_reason"] = payload.rejection_reason
    if payload.admin_notes:
        update_data["admin_notes"] = payload.admin_notes
    if payload.refund_amount is not None:
        update_data["refund_amount"] = payload.refund_amount
    if payload.refund_transaction_id:
        update_data["refund_transaction_id"] = payload.refund_transaction_id

    db.returns.update_one({"_id": ret["_id"]}, {"$set": update_data})

    # Update order timeline & order status
    order = db.orders.find_one({"order_id": ret["order_id"]})
    if order:
        timeline = order.get("timeline", [])
        order_status = order.get("order_status")
        if payload.status == "APPROVED":
            order_status = "RETURN_APPROVED"
            timeline.append({
                "status": "RETURN_APPROVED",
                "message": "Return request has been approved by admin. Pickup initiated.",
                "timestamp": now,
                "performed_by": current_user.get("full_name")
            })
        elif payload.status == "REJECTED":
            order_status = "RETURN_REJECTED"
            timeline.append({
                "status": "RETURN_REJECTED",
                "message": f"Return rejected: {payload.rejection_reason or 'Eligibility criteria not met'}",
                "timestamp": now,
                "performed_by": current_user.get("full_name")
            })
        elif payload.status == "REFUNDED":
            order_status = "REFUNDED"
            timeline.append({
                "status": "REFUNDED",
                "message": f"Refund of ₹{payload.refund_amount or order.get('final_amount')} processed. Reference: {payload.refund_transaction_id or 'Auto-Reversal'}",
                "timestamp": now,
                "performed_by": current_user.get("full_name")
            })
            # Also record refund in refunds collection
            db.refunds.insert_one({
                "order_id": ret["order_id"],
                "return_id": str(ret["_id"]),
                "amount": payload.refund_amount or order.get("final_amount"),
                "refund_transaction_id": payload.refund_transaction_id or f"rfnd_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "SUCCESS",
                "created_at": now
            })

        db.orders.update_one(
            {"order_id": ret["order_id"]},
            {"$set": {"order_status": order_status, "timeline": timeline, "updated_at": now}}
        )

    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="RETURN_STATUS_UPDATED",
        resource_type="RETURN",
        resource_id=str(ret["_id"]),
        user_id=current_user.get("id"),
        user_email=current_user.get("email"),
        details={"status": payload.status, "order_id": ret.get("order_id")}
    )

    return {"message": f"Return status updated to {payload.status}"}
