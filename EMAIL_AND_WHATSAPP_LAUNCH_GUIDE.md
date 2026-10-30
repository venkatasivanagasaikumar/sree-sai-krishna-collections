# SREE SAI KRISHNA COLLECTIONS (SSK)
## TRANSACTIONAL EMAIL & OFFICIAL WHATSAPP CLOUD API LAUNCH GUIDE

**Target Channels:**  
1. **Transactional Email:** Amazon Simple Email Service (SES) / SendGrid SMTP Relay (Port 587, TLS)  
2. **Instant Messaging:** Official Meta WhatsApp Business Platform Cloud API (v19.0)  
**Regulatory Compliance:** TRAI Commercial Communication Customer Preference Regulations (TCCCPR), India DPDP Act 2023, RFC 5321  

---

## PART 1: TRANSACTIONAL EMAIL SETUP (AMAZON SES / SENDGRID)

### 1. DNS Record Configuration for High Deliverability (Anti-Spam)
To prevent order confirmation emails from landing in customer spam or promotional tabs, the business owner must configure SPF, DKIM, and DMARC records on the DNS provider (Cloudflare / Namecheap / GoDaddy):

```
+-----------+--------------------+---------------------------------------------------------------+
| Record    | Host / Name        | Value / Content                                               |
+-----------+--------------------+---------------------------------------------------------------+
| TXT (SPF) | @                  | v=spf1 include:amazonses.com include:sendgrid.net ~all        |
| CNAME     | ssk._domainkey     | ssk.domainkey.u123456.wl.sendgrid.net (or AWS SES DKIM tokens)|
| TXT (DMARC| _dmarc             | v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@ssk.com    |
+-----------+--------------------+---------------------------------------------------------------+
```

### 2. Generating SMTP Credentials
1. **In Amazon SES (Mumbai `ap-south-1`):**
   - Navigate to **Verified Identities** &rarr; Verify Domain `sreesaikrishnacollections.com`.
   - Navigate to **Account Dashboard** &rarr; Click **Create SMTP Credentials**.
   - Copy the generated **SMTP Username** and **SMTP Password**.
2. **In SendGrid (Alternative):**
   - Navigate to **Settings &rarr; API Keys** &rarr; Create Key with *Full Access to Mail Send*.
   - Username is `apikey`; Password is the generated 69-character API key.

### 3. Server Configuration (`backend/.env`)
```ini
SMTP_HOST=email-smtp.ap-south-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=REPLACE_WITH_YOUR_SMTP_USERNAME
SMTP_PASSWORD=REPLACE_WITH_YOUR_SMTP_PASSWORD
SMTP_FROM_EMAIL=orders@sreesaikrishnacollections.com
SMTP_FROM_NAME="Sree Sai Krishna Collections"
SMTP_TLS=true
```

### 4. Lifecycle Templates Active in Application
The backend automatically triggers styled, responsive HTML emails for:
- `ORDER_PLACED`: Order received & payment instructions.
- `PAYMENT_CONFIRMED`: Official confirmation with vector PDF invoice attached.
- `COD_CONFIRMED`: Cash on Delivery verification with PDF invoice attached.
- `ORDER_PACKED`: Quality check completed, parcel boxed in Secunderabad.
- `ORDER_SHIPPED`: Dispatch alert with courier name, tracking AWB, and live link.
- `OUT_FOR_DELIVERY`: Same-day courier alert.
- `ORDER_DELIVERED`: Delivery confirmation and review request.
- `ORDER_CANCELLED`: Cancellation notice.
- `REFUND_INITIATED`: Bank transfer notice with Credit Note PDF attached.
- `PASSWORD_RESET`: Single-use 15-minute expiring recovery link.

---

## PART 2: META WHATSAPP BUSINESS CLOUD API SETUP

### 1. Architecture & Compliance Principles
- **Direct Cloud API Exclusively:** Integrated directly with Meta Graph API v19.0 (`https://graph.facebook.com/v19.0/{phone_number_id}/messages`).
- **Zero Third-Party Middlemen:** Direct server-to-Meta communication eliminates recurring per-message aggregator fees.
- **Opt-Out Compliance:** The system verifies `db.communication_preferences` before sending. If a customer opts out in their Account Portal, notifications are skipped and logged as `opted_out`.
- **E.164 Normalization:** Customer input numbers (`+91`, `0`, spaces) are normalized automatically to `91XXXXXXXXXX`.

### 2. Generating Permanent Meta System User Token
Temporary user access tokens expire after 24 hours. A **permanent System User Access Token** must be generated:

1. Log into [Meta Business Manager](https://business.facebook.com/) &rarr; **Business Settings**.
2. Under **Users**, click **System Users** &rarr; Click **Add**.
3. Name: `SSK-Backend-Service`; Role: **Admin**.
4. Click **Generate New Token** &rarr; Select your Meta WhatsApp App.
5. Set Token Expiration to **Never** (Permanent).
6. Check permissions:
   - [x] `whatsapp_business_messaging`
   - [x] `whatsapp_business_management`
7. Copy the generated permanent token (`EAAG...`).

### 3. Submitting the 10 Pre-Approved Utility Templates
In Meta WhatsApp Manager (**Account Tools &rarr; Message Templates**), create these 10 exact **UTILITY** templates (Language: `en`):

```
1. ssk_order_placed_v1 (UTILITY)
   "Hello {{1}}! Thank you for shopping with Sree Sai Krishna Collections. Your order {{2}} for ₹{{3}} has been placed successfully via {{4}}. Track here: {{5}}"

2. ssk_payment_confirmed_v1 (UTILITY)
   "Hello {{1}}! We have received your payment of ₹{{2}} for SSK Order {{3}}. Our team is now preparing your exquisite jewellery pieces."

3. ssk_cod_confirmation_v1 (UTILITY)
   "Hello {{1}}! Your Cash on Delivery order {{2}} for ₹{{3}} is confirmed. Please keep exact cash ready upon delivery."

4. ssk_order_packed_v1 (UTILITY)
   "Great news {{1}}! Your SSK order {{2}} has been securely packed with utmost care and is awaiting courier pickup."

5. ssk_order_shipped_v1 (UTILITY)
   "Great news, {{1}}! Your SSK order {{2}} has been shipped via {{3}} (AWB: {{4}}). Track your parcel here: {{5}}"

6. ssk_out_for_delivery_v1 (UTILITY)
   "Hello {{1}}! Your SSK order {{2}} is OUT FOR DELIVERY today with courier executive. Track: {{3}}"

7. ssk_order_delivered_v1 (UTILITY)
   "Hello {{1}}! Your SSK order {{2}} has been successfully delivered. We hope you love your purchase! Thank you for choosing Sree Sai Krishna Collections."

8. ssk_order_cancelled_v1 (UTILITY)
   "Hello {{1}}, your order {{2}} has been cancelled. If any payment was made, your refund is being initiated. Helpline: {{3}}"

9. ssk_refund_initiated_v1 (UTILITY)
   "Hello {{1}}, a refund of ₹{{2}} has been initiated for order {{3}}. Funds typically credit to your bank account within 5-7 business days."

10. ssk_refund_completed_v1 (UTILITY)
    "Hello {{1}}, your refund of ₹{{2}} for order {{3}} has been completed. Reference: {{4}}."
```

### 4. Configuring Meta Webhook for Delivery Receipts
1. In Meta Developers Portal &rarr; Select your WhatsApp App &rarr; **WhatsApp &rarr; Configuration**.
2. **Callback URL:** `https://sreesaikrishnacollections.com/api/v1/webhooks/whatsapp`
3. **Verify Token:** Enter the value configured in `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (default: `ssk_wa_verify_token_2026`).
4. Click **Verify and Save**.
5. Under Webhook Fields, subscribe to **`messages`**.

### 5. Server Configuration (`backend/.env`)
```ini
WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=REPLACE_WITH_YOUR_PHONE_NUMBER_ID
WHATSAPP_BUSINESS_ACCOUNT_ID=REPLACE_WITH_YOUR_WABA_ID
WHATSAPP_ACCESS_TOKEN=EAAG_REPLACE_WITH_YOUR_PERMANENT_SYSTEM_USER_TOKEN
WHATSAPP_API_VERSION=v19.0
WHATSAPP_WEBHOOK_VERIFY_TOKEN=ssk_wa_verify_token_2026
WHATSAPP_APP_SECRET=REPLACE_WITH_YOUR_APP_SECRET
SUPPORT_PHONE="+91 98480 22338"
```

---

## PART 3: AUDITING DISPATCHES IN ADMIN DASHBOARD

Once live credentials are saved:
1. Log into the Seller Panel at `https://sreesaikrishnacollections.com/admin/communications`.
2. Inspect the **Live Channel Health**:
   - Transactional Email status will show **`LIVE (AWS SES / Port 587)`**.
   - WhatsApp Cloud API status will show **`LIVE (Meta Cloud API v19.0)`**.
3. Use the **Send Test Notification** tab to verify an immediate test email and WhatsApp ping to your personal phone number before opening the store to public orders.
4. Review the **Delivery Audit Log** table to track real-time message statuses (`sent`, `delivered`, `read`, `failed`).
