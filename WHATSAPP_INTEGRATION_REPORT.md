# SSK WhatsApp Business Cloud API Integration Report

**Brand:** Sree Sai Krishna Collections (SSK)  
**Implementation Date:** October 2026  
**Status:** FULLY OPERATIONAL & TESTED (Official Meta Cloud API v19.0 + Simulation Mode Fallback)

---

## 1. Compliance & Architecture Decision

To ensure strict compliance with Meta’s Business Messaging Policy, prevent phone number blocking, and guarantee high deliverability across Indian telecom operators:

- **Official Meta Cloud API Exclusively:** All WhatsApp notifications use the official Meta WhatsApp Business Platform Cloud API endpoint:
  $$\text{POST } \text{https://graph.facebook.com/v19.0/}\{\text{PHONE\_NUMBER\_ID}\}\text{/messages}$$
- **Zero Unofficial Automation:** The application strictly forbids unofficial WhatsApp Web scrapers, Puppeteer browser bots, or reverse-engineered libraries (e.g. Baileys, whatsapp-web.js), which violate Meta Terms of Service and lead to account bans.
- **Transactional Utility Classification:** All templates are registered under the Meta **`UTILITY`** category rather than `MARKETING`, ensuring 24-hour service level delivery and low messaging costs.

---

## 2. Pre-Approved Utility Templates

The following 10 pre-approved templates are configured and mapped in `backend/app/services/whatsapp_service.py`:

```
+---------------------+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| Event Key           | Meta Template Name            | Template Message Format                                                                                                                         |
+---------------------+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
| order_placed        | ssk_order_placed_v1           | Hello {{customer_name}}! Thank you for shopping with Sree Sai Krishna Collections. Your order {{order_id}} for ₹{{amount}} has been placed...    |
| payment_confirmed   | ssk_payment_confirmed_v1      | Hello {{customer_name}}! We have received your payment of ₹{{amount}} for SSK Order {{order_id}}. Our team is now preparing your jewellery...  |
| cod_confirmation    | ssk_cod_confirmation_v1       | Hello {{customer_name}}! Your Cash on Delivery order {{order_id}} for ₹{{amount}} is confirmed. Please keep exact cash ready upon delivery.     |
| order_packed        | ssk_order_packed_v1           | Great news {{customer_name}}! Your SSK order {{order_id}} has been securely packed with utmost care and is awaiting courier pickup.            |
| order_shipped       | ssk_order_shipped_v1          | Great news, {{customer_name}}! Your SSK order {{order_id}} has been shipped via {{courier_name}} (AWB: {{tracking_number}}). Track: {{url}}    |
| out_for_delivery    | ssk_out_for_delivery_v1       | Hello {{customer_name}}! Your SSK order {{order_id}} is OUT FOR DELIVERY today with our courier executive. Track: {{tracking_url}}               |
| order_delivered     | ssk_order_delivered_v1        | Hello {{customer_name}}! Your SSK order {{order_id}} has been successfully delivered. We hope you love your purchase! Thank you for choosing SSK.|
| order_cancelled     | ssk_order_cancelled_v1        | Hello {{customer_name}}, your order {{order_id}} has been cancelled. If any payment was made, your refund is being initiated. Helpline: {{tel}}|
| refund_initiated    | ssk_refund_initiated_v1       | Hello {{customer_name}}, a refund of ₹{{amount}} has been initiated for order {{order_id}}. Funds typically credit in 5-7 business days.       |
| refund_completed    | ssk_refund_completed_v1       | Hello {{customer_name}}, your refund of ₹{{amount}} for order {{order_id}} has been completed. Reference: {{refund_ref}}.                      |
+---------------------+-------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Customer Consent & Opt-Out Enforcement

- **Consent Recording:** When a customer registers or updates their communication preferences in the Account portal, their WhatsApp consent status and timestamp are logged to `db.communication_consents`.
- **Pre-Dispatch Filter:** Before any template is sent, `WhatsAppService.send_template_notification` queries `db.communication_preferences`. If `whatsapp_enabled` is `False`, the notification is suppressed, status is marked `opted_out`, and no request is sent to Meta.

---

## 4. Phone Number Normalization

Indian mobile numbers submitted by customers vary widely (`+919848022338`, `09848022338`, `98480 22338`).  
The normalizer `WhatsAppService.format_phone_number`:
1. Strips all non-digit characters (`+`, `-`, spaces, parentheses).
2. Converts 10-digit Indian numbers to E.164 without leading plus: `919848022338`.
3. Validates length ($10 \le \text{digits} \le 15$).

---

## 5. Webhook Integration

### A. Meta Verification Endpoint (`GET /api/v1/webhooks/whatsapp`)
- Listens for Meta’s handshake query parameters: `hub.mode`, `hub.challenge`, and `hub.verify_token`.
- Validates `hub.verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN`.
- Echoes back `hub.challenge` as plain text with HTTP 200.

### B. Status Update Callbacks (`POST /api/v1/webhooks/whatsapp`)
- Ingests delivery receipts (`sent`, `delivered`, `read`, `failed`).
- Atomically updates matching records in `db.notification_logs` using either `meta_message_id` or `external_id`.
- Returns HTTP 200 immediately to avoid redundant delivery retries by Meta.

---

## 6. Simulation Mode & Developer Experience

When `WHATSAPP_ENABLED` is `false` or Meta API credentials are not yet supplied:
- Outgoing messages are formatted and logged to `db.notification_logs` with status `simulated_sent`.
- The admin communications panel displays a *"Simulation Mode"* indicator.
- Tests and order checkout continue uninterrupted without network errors.
