# SSK GST-Compliant Invoice & Credit Note Generation Report

**Brand:** Sree Sai Krishna Collections (SSK)  
**Location:** Secunderabad, Telangana, India (State Code: 36)  
**Implementation Date:** October 2026  
**Status:** FULLY OPERATIONAL & TESTED (ReportLab Vector PDF Engine + MongoDB Atomic Sequences)

---

## 1. Executive Summary

A comprehensive, production-grade automated GST Tax Invoice and Credit Note generation subsystem has been engineered and integrated into Sree Sai Krishna Collections (SSK). The subsystem complies with Section 31 of the Central Goods and Services Tax (CGST) Act, 2017, supporting intrastate split taxation (CGST + SGST) for deliveries in Telangana and single integrated tax (IGST) for interstate shipments across India.

Invoices and Credit Notes are generated dynamically as vector PDFs using ReportLab, styled strictly with SSK’s visual identity (Royal Navy `#123F7A`, Gold `#C89A43`, Slate `#1E293B`, and clean tabular typography), and stored idempotently in MongoDB with atomic sequential numbering.

---

## 2. Invoicing Architecture & Sequential Numbering

### A. Atomic Sequential Numbering
To guarantee zero duplicates, zero race conditions, and compliance with Indian GST numbering rules, sequences are generated atomically in MongoDB collection `invoice_sequences`:

- **Tax Invoice Format:** `SSK-INV-YYYY-XXXX` (e.g. `SSK-INV-2026-0001`, `SSK-INV-2026-0002`)
- **Credit Note Format:** `SSK-CN-YYYY-XXXX` (e.g. `SSK-CN-2026-0001`)

Sequential counters reset automatically per fiscal/calendar prefix without collisions.

### B. Idempotency & Order Association
- Every order is uniquely linked to its invoice record in `db.invoices`.
- Calling generation multiple times for the same order returns the existing invoice without issuing duplicate sequence numbers.
- When an order is paid or confirmed via COD, `order.invoice_number` and `order.invoice_path` are atomically updated.

---

## 3. GST Calculation & Place of Supply Logic

The Indian GST treatment evaluates the customer's shipping address against SSK’s registered location (Secunderabad, Telangana, State Code `36`):

```
+------------------------------------+-------------------------------------------+
| Destination                        | GST Treatment                             |
+------------------------------------+-------------------------------------------+
| Intrastate (Telangana, PIN 500xxx) | Split 50/50 into CGST + SGST              |
| Interstate (Other Indian States)   | 100% IGST (Integrated Goods & Services)  |
+------------------------------------+-------------------------------------------+
```

### A. Reverse Calculation from Inclusive Prices
Consumer e-commerce prices in India are displayed inclusive of all taxes. Taxable value is reverse-calculated:
$$\text{Taxable Value} = \frac{\text{Line Total}}{1 + \text{GST Rate}}$$
$$\text{GST Amount} = \text{Line Total} - \text{Taxable Value}$$

### B. HSN Classification Table
```
+------------------------+----------+----------+-----------+-----------+
| Category               | HSN Code | GST Rate | CGST (36) | SGST (36) |
+------------------------+----------+----------+-----------+-----------+
| Imitation Jewellery    | 7117     | 3.0%     | 1.5%      | 1.5%      |
| Gold Jewellery / Haar  | 7113     | 3.0%     | 1.5%      | 1.5%      |
| Hair Clips & Claws     | 9615     | 18.0%    | 9.0%      | 9.0%      |
| Scrunchies & Bands     | 9615     | 18.0%    | 9.0%      | 9.0%      |
| Fashion Accessories    | 7117     | 3.0%     | 1.5%      | 1.5%      |
+------------------------+----------+----------+-----------+-----------+
```

### C. Indian Number-to-Words Conversion
Monetary amounts are automatically converted to words in Indian Rupee format via `number_to_words_inr` (e.g., `₹2,499.00` becomes *"Two Thousand Four Hundred Ninety Nine Rupees Only"*, supporting Crores, Lakhs, Thousands, and Paise).

---

## 4. Vector PDF Generation Specifications

The PDF invoice is rendered dynamically via `ReportLab` (`A4` page size) into `backend/data/invoices/`:
- **Header:** SSK Brand Banner, Official Registered Business Address, GSTIN, PAN, Phone, and Email on left; Document Type (`TAX INVOICE` / `TAX CREDIT NOTE`), Invoice Number, Date, and Order ID on right.
- **Bill To / Ship To Grid:** Customer Full Name, Billing Address, Shipping Address, Contact Phone, and Customer GSTIN (if provided B2B).
- **Line Items Table:** Columnar layout featuring S.No, Item Description & SKU, HSN Code, Quantity, Unit Rate, Taxable Value, CGST/SGST or IGST Breakup, and Final Amount.
- **Summary Section:** Subtotal (Taxable Value), SGST Total, CGST Total, IGST Total, Shipping Fee, and Grand Total.
- **Bank & Remittance Details:** Bank Name, Account Holder Name, Account Number, and IFSC Code for direct wire or remittance reference.
- **Signatory & Legal Disclaimer:** Authorized Signatory box with computer-generated disclaimer under Section 31 of the CGST Act, 2017, and Hyderabad / Secunderabad jurisdiction notice.

---

## 5. Customer & Admin API Endpoints

```
+----------------------------------------------+--------+--------------------------------------------------------+
| Endpoint                                     | Method | Access & Description                                   |
+----------------------------------------------+--------+--------------------------------------------------------+
| /api/v1/invoices/my-invoices                 | GET    | Customer: View own invoices (IDOR protected)           |
| /api/v1/invoices/{invoice_id}                | GET    | Customer/Admin: Get metadata with strict ownership check|
| /api/v1/invoices/{invoice_id}/download       | GET    | Customer/Admin: Stream PDF file download               |
| /api/v1/invoices/admin/all                   | GET    | Admin: Filter by type/date/query, paginated            |
| /api/v1/invoices/admin/{id}/resend           | POST   | Admin: Resend invoice via email/WhatsApp               |
| /api/v1/invoices/admin/generate-from-order/{id}| POST | Admin: Manual generation/regeneration                  |
| /api/v1/invoices/admin/{id}/credit-note      | POST   | Admin: Issue official GST Credit Note for refund       |
+----------------------------------------------+--------+--------------------------------------------------------+
```

---

## 6. Verification & Statutory Advisory

> [!IMPORTANT]
> While the invoicing engine is mathematically and architecturally GST-compliant, the business owner and consulting Chartered Accountant (CA) must verify:
> 1. Official GSTIN and PAN registration numbers prior to replacing environment defaults.
> 2. Specific product-level HSN mappings if customs-bonded or natural gemstone articles are introduced.
> 3. State-specific e-Way Bill threshold limits (e-Way bill required for consignments exceeding ₹50,000 interstate value).
