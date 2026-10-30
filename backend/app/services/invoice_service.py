import os
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager, INVOICES_DIR

# Currency formatting & number to words for Indian Rupees
ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
        "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

def _num_to_words_below_1000(num: int) -> str:
    parts = []
    if num >= 100:
        parts.append(ONES[num // 100] + " Hundred")
        num %= 100
    if num >= 20:
        parts.append(TENS[num // 10])
        num %= 10
    if num > 0:
        parts.append(ONES[num])
    return " ".join(parts)

def number_to_words_inr(amount: float) -> str:
    """Converts a monetary amount into words according to the Indian numbering system."""
    amount = round(amount, 2)
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    if rupees == 0 and paise == 0:
        return "Zero Rupees Only"

    parts = []
    crores = rupees // 10000000
    rupees %= 10000000
    lakhs = rupees // 100000
    rupees %= 100000
    thousands = rupees // 1000
    rupees %= 1000

    if crores > 0:
        parts.append(_num_to_words_below_1000(crores) + " Crore")
    if lakhs > 0:
        parts.append(_num_to_words_below_1000(lakhs) + " Lakh")
    if thousands > 0:
        parts.append(_num_to_words_below_1000(thousands) + " Thousand")
    if rupees > 0:
        parts.append(_num_to_words_below_1000(rupees))

    rupees_str = " ".join(parts).strip() + " Rupees" if parts else ""
    paise_str = f" and {_num_to_words_below_1000(paise)} Paise" if paise > 0 else ""
    return f"{rupees_str}{paise_str} Only".strip()


class InvoiceService:
    @staticmethod
    def get_next_invoice_number(year_prefix: Optional[str] = None, is_credit_note: bool = False) -> str:
        """Generates an atomic, unique sequential invoice or credit note number."""
        now = datetime.now(timezone.utc)
        prefix = settings.CREDIT_NOTE_PREFIX if is_credit_note else settings.INVOICE_PREFIX
        yp = year_prefix or str(now.year)
        key = f"{prefix}-{yp}"

        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        seq_doc = db.invoice_sequences.find_one({"year_prefix": key})
        if not seq_doc:
            next_val = 1
            db.invoice_sequences.insert_one({"year_prefix": key, "current_seq": 1})
        else:
            next_val = seq_doc.get("current_seq", 0) + 1
            db.invoice_sequences.update_one({"year_prefix": key}, {"$set": {"current_seq": next_val}})
        db_manager.persist_to_disk()

        return f"{key}-{next_val:04d}"

    @classmethod
    def calculate_taxes(cls, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates item-level and order-level GST, determining Place of Supply.
        Intra-state (Telangana): CGST + SGST (split equally).
        Inter-state: IGST (full rate).
        """
        shipping_addr = order.get("shipping_address") or {}
        dest_state = (shipping_addr.get("state") or "").strip().title()
        pincode = (shipping_addr.get("pincode") or "").strip()

        # Place of supply evaluation
        is_intrastate = (
            dest_state.lower() == settings.SELLER_STATE.lower() or
            pincode.startswith("500") or pincode.startswith("501") or
            pincode.startswith("502") or pincode.startswith("503")
        )
        place_of_supply = f"{settings.SELLER_STATE} (Code 36)" if is_intrastate else f"{dest_state or 'Other State'} (Inter-state)"

        items_breakdown = []
        total_taxable_value = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        total_igst = 0.0

        for idx, itm in enumerate(order.get("items", []), start=1):
            category = (itm.get("category") or "").lower()
            name = (itm.get("name") or "").lower()
            sku = itm.get("sku", "")
            qty = int(itm.get("quantity", 1))
            unit_price = float(itm.get("unit_price") or itm.get("price", 0.0))
            line_total = unit_price * qty

            # HSN and GST rate classification
            if any(term in name or term in category for term in ["hair", "clip", "claw", "band", "scrunchie"]):
                hsn = "9615" # Hair slides, clips, hairpins
                gst_rate = settings.DEFAULT_ACCESSORIES_GST_RATE # 18%
            else:
                hsn = "7117" # Imitation jewellery
                gst_rate = settings.DEFAULT_JEWELLERY_GST_RATE # 3%

            # Reverse calculate taxable value from inclusive retail price
            taxable_val = round(line_total / (1.0 + gst_rate), 2)
            tax_amount = round(line_total - taxable_val, 2)

            if is_intrastate:
                cgst = round(tax_amount / 2.0, 2)
                sgst = round(tax_amount - cgst, 2)
                igst = 0.0
            else:
                cgst = 0.0
                sgst = 0.0
                igst = tax_amount

            total_taxable_value += taxable_val
            total_cgst += cgst
            total_sgst += sgst
            total_igst += igst

            items_breakdown.append({
                "item_index": idx,
                "name": itm.get("name", "Product Item"),
                "sku": sku,
                "hsn": hsn,
                "hsn_code": hsn,
                "quantity": qty,
                "unit_price": unit_price,
                "discount": 0.0,
                "taxable_value": taxable_val,
                "gst_rate": gst_rate,
                "cgst_rate": round(gst_rate / 2.0, 4) if is_intrastate else 0.0,
                "sgst_rate": round(gst_rate / 2.0, 4) if is_intrastate else 0.0,
                "gst_percentage": f"{int(gst_rate * 100)}%",
                "cgst": cgst,
                "sgst": sgst,
                "igst": igst,
                "line_total": line_total
            })

        shipping_fee = float(order.get("shipping_fee", 0.0))
        final_total = float(order.get("final_amount", order.get("total_amount", 0.0)))

        return {
            "place_of_supply": place_of_supply,
            "is_intrastate": is_intrastate,
            "items": items_breakdown,
            "total_taxable_value": round(total_taxable_value, 2),
            "total_cgst": round(total_cgst, 2),
            "total_sgst": round(total_sgst, 2),
            "total_igst": round(total_igst, 2),
            "total_tax": round(total_cgst + total_sgst + total_igst, 2),
            "shipping_fee": shipping_fee,
            "final_amount": final_total,
            "amount_in_words": number_to_words_inr(final_total)
        }

    @classmethod
    def generate_pdf(cls, invoice_data: Dict[str, Any]) -> str:
        """Renders vector PDF invoice matching SSK brand guidelines and saves to disk."""
        os.makedirs(INVOICES_DIR, exist_ok=True)
        inv_no = invoice_data["invoice_number"]
        filename = f"{inv_no.replace('/', '_')}.pdf"
        filepath = os.path.join(INVOICES_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        NAVY = colors.HexColor("#123F7A")
        GOLD = colors.HexColor("#C89A43")
        DARK = colors.HexColor("#1E293B")
        MUTED = colors.HexColor("#64748B")
        LIGHT_BG = colors.HexColor("#F8FAFC")
        BORDER_GRAY = colors.HexColor("#E2E8F0")

        styles = getSampleStyleSheet()

        brand_title_style = ParagraphStyle(
            "BrandTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY
        )
        sub_style = ParagraphStyle(
            "SubStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED
        )
        inv_type_style = ParagraphStyle(
            "InvoiceTypeStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_RIGHT,
            textColor=NAVY
        )
        header_meta_style = ParagraphStyle(
            "HeaderMetaStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            alignment=TA_RIGHT,
            textColor=DARK
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=NAVY
        )
        body_style = ParagraphStyle(
            "InvoiceBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=DARK
        )
        table_hdr = ParagraphStyle(
            "TableHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=colors.white
        )
        table_hdr_right = ParagraphStyle(
            "TableHdrR",
            parent=table_hdr,
            alignment=TA_RIGHT
        )
        table_cell = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=DARK
        )
        table_cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=table_cell,
            fontName="Helvetica-Bold"
        )
        table_cell_right = ParagraphStyle(
            "TableCellR",
            parent=table_cell,
            alignment=TA_RIGHT
        )

        elements = []

        # Top Header Table (Seller Info on Left, Invoice Meta on Right)
        is_cn = invoice_data.get("invoice_type") == "CREDIT_NOTE"
        doc_type_title = "TAX CREDIT NOTE" if is_cn else "TAX INVOICE"
        
        seller_html = f"""
        <b>{settings.BRAND_NAME}</b><br/>
        {settings.BUSINESS_ADDRESS}<br/>
        <b>GSTIN:</b> {settings.SELLER_GSTIN or 'Pending Verification'} | <b>PAN:</b> {settings.SELLER_PAN}<br/>
        <b>Helpline:</b> {settings.SUPPORT_PHONE} | <b>Email:</b> {settings.SUPPORT_EMAIL}
        """
        meta_html = f"""
        <b>{doc_type_title}</b><br/>
        <b>Invoice #:</b> {invoice_data['invoice_number']}<br/>
        <b>Invoice Date:</b> {invoice_data['invoice_date']}<br/>
        <b>Order ID:</b> {invoice_data['order_id']}<br/>
        <b>Payment Mode:</b> {invoice_data.get('payment_method', 'Prepaid')} ({invoice_data.get('payment_status', 'PAID')})<br/>
        <b>Place of Supply:</b> {invoice_data.get('place_of_supply', 'Telangana')}
        """
        header_table = Table(
            [[Paragraph(seller_html, sub_style), Paragraph(meta_html, header_meta_style)]],
            colWidths=[3.25 * inch, 4.0 * inch]
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8, spaceBefore=4))

        # Billing & Shipping Block
        cust = invoice_data.get("customer", {})
        shipping = cust.get("shipping_address", {})
        billing = cust.get("billing_address") or shipping

        bill_html = f"""
        <b>BILL TO:</b><br/>
        <b>{cust.get('name', 'Valued Customer')}</b><br/>
        {billing.get('address_line1', '')} {billing.get('address_line2', '')}<br/>
        {billing.get('city', '')}, {billing.get('state', '')} - {billing.get('pincode', '')}<br/>
        Phone: {cust.get('phone', '')} | Email: {cust.get('email', '')}
        """
        ship_html = f"""
        <b>SHIP TO:</b><br/>
        <b>{cust.get('name', 'Valued Customer')}</b><br/>
        {shipping.get('address_line1', '')} {shipping.get('address_line2', '')}<br/>
        {shipping.get('city', '')}, {shipping.get('state', '')} - {shipping.get('pincode', '')}<br/>
        Phone: {shipping.get('phone', cust.get('phone', ''))}
        """
        addr_table = Table(
            [[Paragraph(bill_html, body_style), Paragraph(ship_html, body_style)]],
            colWidths=[3.6 * inch, 3.65 * inch]
        )
        addr_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(addr_table)
        elements.append(Spacer(1, 10))

        # Products Table
        table_data = [[
            Paragraph("Sl.", table_hdr),
            Paragraph("Item & SKU", table_hdr),
            Paragraph("HSN", table_hdr),
            Paragraph("Qty", table_hdr_right),
            Paragraph("Unit Price", table_hdr_right),
            Paragraph("Taxable", table_hdr_right),
            Paragraph("GST", table_hdr_right),
            Paragraph("Total (₹)", table_hdr_right),
        ]]

        items = invoice_data.get("items", [])
        for itm in items:
            item_desc = f"<b>{itm['name']}</b><br/><font color='#64748B'>SKU: {itm.get('sku', 'N/A')}</font>"
            table_data.append([
                Paragraph(str(itm.get("item_index", 1)), table_cell),
                Paragraph(item_desc, table_cell),
                Paragraph(str(itm.get("hsn", "7117")), table_cell),
                Paragraph(str(itm.get("quantity", 1)), table_cell_right),
                Paragraph(f"₹{itm.get('unit_price', 0.0):.2f}", table_cell_right),
                Paragraph(f"₹{itm.get('taxable_value', 0.0):.2f}", table_cell_right),
                Paragraph(itm.get("gst_percentage", "3%"), table_cell_right),
                Paragraph(f"₹{itm.get('line_total', 0.0):.2f}", table_cell_right),
            ])

        prod_table = Table(
            table_data,
            colWidths=[0.35 * inch, 2.5 * inch, 0.65 * inch, 0.45 * inch, 0.9 * inch, 0.85 * inch, 0.6 * inch, 0.95 * inch]
        )
        prod_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ]))
        elements.append(prod_table)
        elements.append(Spacer(1, 8))

        # Financial Breakdown & Tax Split Table
        tax_info = invoice_data.get("tax_breakdown", {})
        is_intra = tax_info.get("is_intrastate", True)

        summary_rows = [
            [Paragraph("Taxable Subtotal:", body_style), Paragraph(f"₹{tax_info.get('total_taxable_value', 0.0):.2f}", table_cell_right)],
        ]
        if is_intra:
            summary_rows.append([Paragraph("CGST (Central Tax):", body_style), Paragraph(f"₹{tax_info.get('total_cgst', 0.0):.2f}", table_cell_right)])
            summary_rows.append([Paragraph("SGST (State Tax):", body_style), Paragraph(f"₹{tax_info.get('total_sgst', 0.0):.2f}", table_cell_right)])
        else:
            summary_rows.append([Paragraph("IGST (Integrated Tax):", body_style), Paragraph(f"₹{tax_info.get('total_igst', 0.0):.2f}", table_cell_right)])

        shipping_fee = tax_info.get("shipping_fee", 0.0)
        summary_rows.append([Paragraph("Shipping Charges:", body_style), Paragraph(f"₹{shipping_fee:.2f}" if shipping_fee > 0 else "FREE", table_cell_right)])

        discount_val = invoice_data.get("discount_amount", 0.0)
        if discount_val > 0:
            summary_rows.append([Paragraph("Coupon / Discount:", body_style), Paragraph(f"-₹{discount_val:.2f}", table_cell_right)])

        final_amt = tax_info.get("final_amount", 0.0)
        summary_rows.append([Paragraph("<b>TOTAL INVOICE AMOUNT:</b>", section_heading), Paragraph(f"<b>₹{final_amt:.2f}</b>", ParagraphStyle("BigTot", parent=table_cell_right, fontName="Helvetica-Bold", fontSize=9, textColor=NAVY))])

        summary_table = Table(summary_rows, colWidths=[1.8 * inch, 1.2 * inch])
        summary_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, -1), (-1, -1), 1, NAVY),
        ]))

        # Bottom Box: Amount in words + Bank Info on Left, Summary on Right
        bank_html = f"""
        <b>Amount in Words:</b><br/>
        <i>{tax_info.get('amount_in_words', '')}</i><br/><br/>
        <b>Remittance & Support Details:</b><br/>
        Bank: State Bank of India | Account: Sree Sai Krishna Collections<br/>
        Account No: 40992817263 | IFSC: SBIN0000847<br/>
        Terms: 7-day hassle-free return window for unused items in original jewellery box.
        """
        bottom_table = Table(
            [[Paragraph(bank_html, body_style), summary_table]],
            colWidths=[4.25 * inch, 3.0 * inch]
        )
        bottom_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(KeepTogether(bottom_table))
        elements.append(Spacer(1, 14))

        # Signatory Section
        sig_html = f"""
        <table width="100%">
            <tr>
                <td width="60%" style="font-size: 7.5pt; color: #64748B;">
                    This is a computer-generated tax invoice issued in accordance with Section 31 of the CGST Act, 2017.<br/>
                    All disputes subject to Hyderabad / Secunderabad jurisdiction.
                </td>
                <td width="40%" align="right" style="font-size: 8pt; color: #123F7A;">
                    <b>For Sree Sai Krishna Collections</b><br/><br/><br/>
                    ____________________________<br/>
                    <b>Authorized Signatory</b>
                </td>
            </tr>
        </table>
        """
        elements.append(Paragraph(sig_html, body_style))

        doc.build(elements)
        logger.info(f"Generated invoice PDF at {filepath}")
        return filepath

    @classmethod
    def generate_or_get_invoice(
        cls,
        order_id: str,
        force_regenerate: bool = False,
        is_credit_note: bool = False
    ) -> Dict[str, Any]:
        """
        Creates an immutable, GST-compliant invoice for an order.
        Idempotent: If an invoice exists and force_regenerate is False, returns existing invoice.
        """
        db = db_manager.db
        if db is None:
            db_manager.connect()
            db = db_manager.db

        inv_type = "CREDIT_NOTE" if is_credit_note else "TAX_INVOICE"
        existing = db.invoices.find_one({"order_id": order_id, "invoice_type": inv_type})
        if existing and not force_regenerate:
            return existing

        order = db.orders.find_one({"order_id": order_id})
        if not order:
            raise ValueError(f"Order #{order_id} not found.")

        invoice_number = existing.get("invoice_number") if (existing and force_regenerate) else cls.get_next_invoice_number(is_credit_note=is_credit_note)
        now = datetime.now(timezone.utc)
        tax_info = cls.calculate_taxes(order)

        customer_info = {
            "name": order.get("customer_name") or "Valued Customer",
            "email": order.get("customer_email") or "",
            "phone": order.get("customer_phone") or "",
            "shipping_address": order.get("shipping_address") or {},
            "billing_address": order.get("billing_address") or order.get("shipping_address") or {},
            "customer_gstin": order.get("customer_gstin") or ""
        }

        invoice_data = {
            "invoice_number": invoice_number,
            "invoice_type": inv_type,
            "invoice_date": now.strftime("%d-%b-%Y"),
            "order_id": order_id,
            "user_id": str(order.get("user_id", "")),
            "customer_email": order.get("customer_email", ""),
            "customer": customer_info,
            "items": tax_info["items"],
            "tax_breakdown": tax_info,
            "payment_method": order.get("payment_method", "Prepaid"),
            "payment_status": order.get("payment_status", "PAID"),
            "place_of_supply": tax_info["place_of_supply"],
            "discount_amount": float(order.get("discount_amount", 0.0)),
            "created_at": now
        }

        # Render PDF
        pdf_path = cls.generate_pdf(invoice_data)
        invoice_data["pdf_path"] = pdf_path
        invoice_data["pdf_filename"] = os.path.basename(pdf_path)

        # Upsert in database
        db.invoices.update_one(
            {"invoice_number": invoice_number},
            {"$set": invoice_data},
            upsert=True
        )
        # Update order with invoice reference
        db.orders.update_one(
            {"order_id": order_id},
            {"$set": {"invoice_number": invoice_number, "invoiced_at": now, "invoice_path": pdf_path}}
        )
        db_manager.persist_to_disk()

        logger.info(f"Invoice {invoice_number} successfully registered for Order #{order_id}")
        return invoice_data
