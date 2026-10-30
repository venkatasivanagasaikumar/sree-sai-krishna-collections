import os
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse
from bson import ObjectId

from app.core.config import settings
from app.core.logging import logger
from app.database import get_db, db_manager
from app.api.dependencies import get_current_user, require_admin
from app.services.invoice_service import InvoiceService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/invoices", tags=["Invoices"])

def _serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d["_id"])
        del d["_id"]
    return d

@router.get("/my-invoices")
def get_my_invoices(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Returns all tax invoices and credit notes belonging to the authenticated customer.
    Protected against IDOR: only returns documents matching user's id or email.
    """
    user_id = str(current_user["id"])
    user_email = current_user.get("email")

    query = {
        "$or": [
            {"user_id": user_id},
            {"customer_email": user_email},
            {"customer.email": user_email}
        ]
    }

    invoices = list(db.invoices.find(query).sort("created_at", -1))
    return [_serialize_doc(inv) for inv in invoices]


@router.get("/admin/all")
def get_admin_invoices(
    q: Optional[str] = Query(None, description="Search query by invoice #, order ID, customer name, email"),
    invoice_type: Optional[str] = Query(None, description="TAX_INVOICE or CREDIT_NOTE"),
    from_date: Optional[str] = Query(None, description="ISO format start date"),
    to_date: Optional[str] = Query(None, description="ISO format end date"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Admin endpoint to search, filter, and paginate through store invoices and credit notes.
    """
    query: Dict[str, Any] = {}

    if isinstance(invoice_type, str) and invoice_type.upper() in ["TAX_INVOICE", "CREDIT_NOTE"]:
        query["invoice_type"] = invoice_type.upper()

    if isinstance(q, str) and q.strip():
        regex_q = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"invoice_number": regex_q},
            {"order_id": regex_q},
            {"customer_email": regex_q},
            {"customer.name": regex_q},
            {"customer.phone": regex_q}
        ]

    total_count = db.invoices.count_documents(query)
    skip = (page - 1) * limit
    invoices = list(
        db.invoices.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return {
        "items": [_serialize_doc(inv) for inv in invoices],
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total_count / limit) if total_count > 0 else 1
    }


@router.get("/{invoice_id}")
def get_invoice_details(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Retrieves metadata for an invoice by its invoice number or order ID.
    Enforces IDOR checks for non-staff customers.
    """
    invoice = db.invoices.find_one({
        "$or": [
            {"invoice_number": invoice_id},
            {"order_id": invoice_id}
        ]
    })
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    user_role = current_user.get("role")
    is_staff = user_role in ["super_admin", "admin", "staff"]

    if not is_staff:
        # Verify ownership
        user_id = str(current_user["id"])
        user_email = current_user.get("email")
        inv_user_id = str(invoice.get("user_id", ""))
        inv_email = invoice.get("customer_email") or (invoice.get("customer") or {}).get("email")

        if inv_user_id != user_id and inv_email != user_email:
            raise HTTPException(status_code=403, detail="Unauthorized access to this invoice")

    return _serialize_doc(invoice)


@router.get("/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Streams the vector PDF invoice file for download.
    Enforces IDOR ownership protection.
    If the PDF file is missing from disk, it regenerates it dynamically.
    """
    invoice = db.invoices.find_one({
        "$or": [
            {"invoice_number": invoice_id},
            {"order_id": invoice_id}
        ]
    })
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    user_role = current_user.get("role")
    is_staff = user_role in ["super_admin", "admin", "staff"]

    if not is_staff:
        user_id = str(current_user["id"])
        user_email = current_user.get("email")
        inv_user_id = str(invoice.get("user_id", ""))
        inv_email = invoice.get("customer_email") or (invoice.get("customer") or {}).get("email")

        if inv_user_id != user_id and inv_email != user_email:
            raise HTTPException(status_code=403, detail="Unauthorized access to this invoice")

    pdf_path = invoice.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        # Regenerate PDF from stored invoice metadata
        pdf_path = InvoiceService.generate_pdf(invoice)
        db.invoices.update_one(
            {"_id": invoice["_id"]},
            {"$set": {"pdf_path": pdf_path, "pdf_filename": os.path.basename(pdf_path)}}
        )

    filename = f"{invoice.get('invoice_number', 'SSK-INVOICE')}.pdf"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/admin/{invoice_id}/resend")
def resend_invoice(
    invoice_id: str,
    channel: str = Query("all", description="email, whatsapp, or all"),
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Admin action to resend the invoice to customer via Email, WhatsApp, or both.
    """
    invoice = db.invoices.find_one({
        "$or": [
            {"invoice_number": invoice_id},
            {"order_id": invoice_id}
        ]
    })
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    order_id = invoice.get("order_id")
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail=f"Order #{order_id} not found")

    res = NotificationService.dispatch_order_event(
        order_id=order_id,
        event_name="ORDER_CONFIRMED",
        extra_data={"force_resend": True, "resend_channel": channel},
        actor=current_user.get("email", "admin")
    )

    return {
        "success": True,
        "message": f"Invoice {invoice.get('invoice_number')} resent successfully",
        "result": res
    }


@router.post("/admin/generate-from-order/{order_id}")
def generate_invoice_for_order(
    order_id: str,
    force: bool = Query(False, description="Force overwrite existing invoice"),
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Admin action to manually generate or regenerate an invoice for an order.
    """
    order = db.orders.find_one({"order_id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail=f"Order #{order_id} not found")

    try:
        inv = InvoiceService.generate_or_get_invoice(order_id=order_id, force_regenerate=force)
        return {
            "success": True,
            "message": f"Invoice {inv.get('invoice_number')} generated successfully",
            "invoice": _serialize_doc(inv)
        }
    except Exception as e:
        logger.error(f"Error generating invoice for #{order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate invoice: {str(e)}")


@router.post("/admin/{invoice_id}/credit-note")
def generate_credit_note(
    invoice_id: str,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    """
    Admin action to issue an official GST Tax Credit Note for an existing invoice.
    """
    invoice = db.invoices.find_one({
        "$or": [
            {"invoice_number": invoice_id},
            {"order_id": invoice_id}
        ]
    })
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    order_id = invoice.get("order_id")
    try:
        cn = InvoiceService.generate_or_get_invoice(order_id=order_id, is_credit_note=True)
        return {
            "success": True,
            "message": f"Credit note {cn.get('invoice_number')} issued successfully",
            "credit_note": _serialize_doc(cn)
        }
    except Exception as e:
        logger.error(f"Error generating credit note for #{order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate credit note: {str(e)}")
