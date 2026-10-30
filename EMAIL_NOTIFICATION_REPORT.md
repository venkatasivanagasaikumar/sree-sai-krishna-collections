# SSK Transactional Email Notification Subsystem Report

**Brand:** Sree Sai Krishna Collections (SSK)  
**Implementation Date:** October 2026  
**Status:** FULLY OPERATIONAL & TESTED (SMTP Gateway + Jinja2 Responsive Templates + PDF Attachments)

---

## 1. Subsystem Overview

The transactional email subsystem for Sree Sai Krishna Collections provides automated, branded customer communications across the entire order, fulfillment, and account lifecycles. It supports standard SMTP transport (AWS SES, SendGrid, Mailgun, or Google Workspace SMTP Relay), TLS encryption, dual-format delivery (responsive HTML + plaintext fallback), dynamic invoice PDF attachments, and dual logging into `email_logs` and `notification_logs`.

When live SMTP credentials are not configured, the engine operates in **Simulation Mode**, logging the complete payload without disrupting customer orders or checkout.

---

## 2. Event & Template Catalog

The transactional email engine supports 17 distinct operational templates:

```
+----------------------------+-----------------------------------+---------------------------------------------------+
| Event Key                  | Target Recipient                  | Content & Attachments                             |
+----------------------------+-----------------------------------+---------------------------------------------------+
| ORDER_PLACED               | Customer                          | Order summary, item list, tracking link           |
| PAYMENT_CONFIRMED          | Customer                          | Payment receipt, **Attached Tax Invoice PDF**     |
| COD_CONFIRMED              | Customer                          | Cash on Delivery guidance, **Tax Invoice PDF**    |
| ORDER_PACKED               | Customer                          | Quality check confirmation, dispatch preparation  |
| ORDER_SHIPPED              | Customer                          | Courier partner, AWB tracking number, link        |
| OUT_FOR_DELIVERY           | Customer                          | Real-time delivery alert, contact guidelines      |
| ORDER_DELIVERED            | Customer                          | Delivery confirmation, review & feedback invite   |
| ORDER_CANCELLED            | Customer                          | Cancellation explanation, refund notification     |
| REFUND_INITIATED           | Customer                          | Refund amount, bank transfer timeline             |
| REFUND_COMPLETED           | Customer                          | Bank reference ID, closing statement              |
| USER_REGISTRATION          | Customer                          | Welcome message, account verification link        |
| PASSWORD_RESET             | Customer                          | Expiring single-use reset token link (15m expiry) |
| ADMIN_LOW_STOCK_ALERT      | Store Admin                       | SKU inventory threshold trigger notice            |
| ADMIN_DAILY_SALES_DIGEST   | Store Admin                       | Revenue, total orders, COD balance summary        |
| ADMIN_NEW_ORDER_ALERT      | Store Staff                       | Immediate notification of incoming paid orders    |
| ADMIN_TEST_EMAIL           | Administrator                     | Diagnostics verifying SMTP socket connectivity    |
| RETRY_DISPATCH             | Customer                          | Idempotent re-dispatch of previous notification   |
+----------------------------+-----------------------------------+---------------------------------------------------+
```

---

## 3. Styling & Mobile Responsiveness

Templates are constructed using inline CSS for cross-client compatibility (Gmail, Apple Mail, Outlook, Android Mail):
- **Brand Palette:** Royal Navy Blue (`#123F7A`) header banners, Gold (`#C89A43`) buttons and badges, Slate (`#1E293B`) text, and Soft Gray (`#F8FAFC`) background.
- **Card-Based Hierarchy:** Product thumbnails, itemized line tables, order progress timelines, and prominent CTA buttons (*"Track Your Order"*, *"Download Invoice"*).
- **Security & Privacy:** Expiring tokens, masked sensitive data, and official legal disclaimers.

---

## 4. PDF Attachment Handling

When an order reaches a confirmed state (`PAYMENT_CONFIRMED` or `COD_CONFIRMED`):
1. `InvoiceService.generate_or_get_invoice(order_id)` builds the vector PDF invoice file (`SSK-INV-YYYY-XXXX.pdf`).
2. `EmailService.send_order_confirmation` attaches the file using `MIMEApplication(pdf_bytes, _subtype="pdf")` with header `Content-Disposition: attachment; filename="SSK-INV-YYYY-XXXX.pdf"`.
3. The email body also contains a direct authenticated link to view and re-download the invoice from the customer’s SSK account portal.

---

## 5. Security & Deliverability Controls

- **No Credential Exposure:** SMTP credentials and passwords are stored strictly in environment variables and are never surfaced in API responses or frontend bundles.
- **Single-Use Expiring Tokens:** Password reset and email verification tokens expire within 15 minutes and become invalid immediately upon first use.
- **Rate Limiting:** Public endpoints requesting emails (forgot password, test dispatches) are rate-limited to avoid SMTP provider throttling.
- **Webhook Status Synchronization:** Endpoint `/api/v1/webhooks/email-status` ingests bounce and delivery callbacks to mark `notification_logs` accordingly.
