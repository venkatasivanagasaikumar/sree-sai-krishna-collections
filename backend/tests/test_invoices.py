import os
import pytest
from app.services.invoice_service import InvoiceService, number_to_words_inr
from app.database import get_db, INVOICES_DIR
from app.api.v1.invoices import (
    get_my_invoices,
    get_admin_invoices,
    get_invoice_details,
    download_invoice_pdf,
    resend_invoice,
    generate_invoice_for_order,
    generate_credit_note
)
from fastapi import HTTPException

def test_number_to_words_inr():
    assert number_to_words_inr(0) == "Zero Rupees Only"
    assert number_to_words_inr(1500) == "One Thousand Five Hundred Rupees Only"
    assert number_to_words_inr(25499.50) == "Twenty Five Thousand Four Hundred Ninety Nine Rupees and Fifty Paise Only"
    assert number_to_words_inr(125000) == "One Lakh Twenty Five Thousand Rupees Only"

def test_tax_calculation_intrastate_telangana():
    """
    Intrastate delivery (Telangana) should split GST 50/50 into CGST and SGST.
    HSN 7117 (Jewellery) at 3% (1.5% CGST + 1.5% SGST).
    HSN 9615 (Hair clips) at 18% (9% CGST + 9% SGST).
    """
    order = {
        "order_id": "SSK-TEST-INTRA",
        "shipping_address": {
            "state": "Telangana",
            "pincode": "500003"
        },
        "items": [
            {
                "name": "1 Gram Gold Plated Royal Haar",
                "category": "Necklaces",
                "sku": "SSK-NK-001",
                "quantity": 1,
                "price": 2060.0 # Tax inclusive 3% -> Taxable ~2000, Tax ~60
            },
            {
                "name": "Gold Pearl Luxury Hair Clip",
                "category": "Hair Accessories",
                "sku": "SSK-HC-002",
                "quantity": 1,
                "price": 1180.0 # Tax inclusive 18% -> Taxable ~1000, Tax ~180
            }
        ],
        "discount_amount": 0.0,
        "shipping_fee": 0.0,
        "final_amount": 3240.0
    }

    tax_info = InvoiceService.calculate_taxes(order)
    assert tax_info["is_intrastate"] is True
    assert "Telangana" in tax_info["place_of_supply"]
    assert tax_info["total_igst"] == 0.0
    assert tax_info["total_cgst"] > 0
    assert tax_info["total_sgst"] > 0
    # CGST and SGST must be equal
    assert round(tax_info["total_cgst"], 2) == round(tax_info["total_sgst"], 2)

    # Check item 1 (Jewellery)
    item1 = tax_info["items"][0]
    assert item1["hsn_code"] == "7117"
    assert item1["gst_rate"] == 0.03
    assert item1["cgst_rate"] == 0.015
    assert item1["sgst_rate"] == 0.015

    # Check item 2 (Hair Accessories)
    item2 = tax_info["items"][1]
    assert item2["hsn_code"] == "9615"
    assert item2["gst_rate"] == 0.18
    assert item2["cgst_rate"] == 0.09
    assert item2["sgst_rate"] == 0.09

def test_tax_calculation_interstate():
    """
    Interstate delivery (e.g. Bangalore, Karnataka) should apply full IGST.
    """
    order = {
        "order_id": "SSK-TEST-INTER",
        "shipping_address": {
            "state": "Karnataka",
            "pincode": "560001"
        },
        "items": [
            {
                "name": "Traditional Temple Jhumkas",
                "category": "Earrings",
                "sku": "SSK-ER-003",
                "quantity": 2,
                "price": 1030.0 # 2060 total (tax inclusive 3%)
            }
        ],
        "discount_amount": 0.0,
        "shipping_fee": 0.0,
        "final_amount": 2060.0
    }

    tax_info = InvoiceService.calculate_taxes(order)
    assert tax_info["is_intrastate"] is False
    assert tax_info["total_cgst"] == 0.0
    assert tax_info["total_sgst"] == 0.0
    assert tax_info["total_igst"] > 0
    assert round(tax_info["total_taxable_value"] + tax_info["total_igst"], 2) == 2060.0

def test_atomic_sequence_numbering():
    seq1 = InvoiceService.get_next_invoice_number(year_prefix="2026")
    seq2 = InvoiceService.get_next_invoice_number(year_prefix="2026")
    assert seq1.startswith("SSK-INV-2026-")
    assert seq2.startswith("SSK-INV-2026-")
    num1 = int(seq1.split("-")[-1])
    num2 = int(seq2.split("-")[-1])
    assert num2 == num1 + 1

    # Credit Note sequence
    cn1 = InvoiceService.get_next_invoice_number(year_prefix="2026", is_credit_note=True)
    assert cn1.startswith("SSK-CN-2026-")

def test_generate_invoice_pdf_and_verification():
    db = get_db()
    order_id = "SSK-TEST-PDF-001"
    db.orders.delete_one({"order_id": order_id})
    db.invoices.delete_one({"order_id": order_id})

    db.orders.insert_one({
        "order_id": order_id,
        "user_id": "usr_test_123",
        "customer_name": "Sita Devi",
        "customer_email": "sita@example.com",
        "customer_phone": "9848011223",
        "shipping_address": {
            "name": "Sita Devi",
            "address_line1": "Flat 302, Sai Residency, Begumpet",
            "city": "Secunderabad",
            "state": "Telangana",
            "pincode": "500003"
        },
        "items": [
            {
                "product_id": "p1",
                "name": "1 Gram Gold Royal Choker",
                "sku": "SSK-CH-01",
                "category": "Necklaces",
                "quantity": 1,
                "price": 2499.0
            }
        ],
        "final_amount": 2499.0,
        "payment_method": "PREPAID",
        "payment_status": "PAID"
    })

    invoice = InvoiceService.generate_or_get_invoice(order_id)
    assert invoice is not None
    assert invoice["invoice_number"].startswith("SSK-INV-")
    assert os.path.exists(invoice["pdf_path"])
    assert os.path.getsize(invoice["pdf_path"]) > 1000 # Valid non-empty PDF

    # Idempotent check
    invoice2 = InvoiceService.generate_or_get_invoice(order_id)
    assert invoice2["invoice_number"] == invoice["invoice_number"]

def test_invoice_api_endor_and_security():
    db = get_db()
    current_customer = {"id": "usr_test_123", "email": "sita@example.com", "role": "customer"}
    attacker = {"id": "usr_attacker_999", "email": "attacker@evil.com", "role": "customer"}
    admin_user = {"id": "usr_admin_1", "email": "admin@sskcollections.com", "role": "admin"}

    # 1. Customer can view their own invoices
    my_invs = get_my_invoices(current_user=current_customer, db=db)
    assert len(my_invs) >= 1
    target_inv = my_invs[0]

    # 2. Attacker attempting to access customer's invoice is blocked with 403
    with pytest.raises(HTTPException) as exc:
        get_invoice_details(invoice_id=target_inv["invoice_number"], current_user=attacker, db=db)
    assert exc.value.status_code == 403

    # 3. Attacker attempting to download customer's invoice PDF is blocked with 403
    with pytest.raises(HTTPException) as exc_dl:
        download_invoice_pdf(invoice_id=target_inv["invoice_number"], current_user=attacker, db=db)
    assert exc_dl.value.status_code == 403

    # 4. Admin can list all invoices
    admin_list = get_admin_invoices(page=1, limit=10, current_user=admin_user, db=db)
    assert admin_list["total"] >= 1
    assert len(admin_list["items"]) >= 1

    # 5. Admin can issue a credit note
    cn_res = generate_credit_note(invoice_id=target_inv["invoice_number"], current_user=admin_user, db=db)
    assert cn_res["success"] is True
    assert cn_res["credit_note"]["invoice_number"].startswith("SSK-CN-")
