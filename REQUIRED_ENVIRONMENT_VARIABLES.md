# Sree Sai Krishna Collections – Required Production Environment Variables

This document provides a comprehensive configuration guide for all environment variables used across Sree Sai Krishna Collections (SSK). Configure these variables in `backend/.env` on the production server.

---

## 1. Complete Environment Reference (`backend/.env`)

```ini
# ==============================================================================
# 1. CORE APPLICATION & SECURITY CONFIGURATION
# ==============================================================================
ENVIRONMENT=production
PROJECT_NAME="Sree Sai Krishna Collections"
API_V1_STR=/api/v1
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_SECRET=generate_with_openssl_rand_hex_32
JWT_REFRESH_SECRET=generate_with_openssl_rand_hex_32
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=14
BACKEND_CORS_ORIGINS=["https://sreesaikrishnacollections.com","https://admin.sreesaikrishnacollections.com"]
FRONTEND_URL=https://sreesaikrishnacollections.com

# ==============================================================================
# 2. DATABASE CONFIGURATION (MONGODB)
# ==============================================================================
# For Docker or MongoDB Atlas:
MONGODB_URI=mongodb://ssk_user:STRONG_SECURE_PASSWORD@127.0.0.1:27017/ssk_collections_db?authSource=admin
DATABASE_NAME=ssk_collections_db
FORCE_MOCK_DB=false

# ==============================================================================
# 3. RAZORPAY PAYMENT GATEWAY
# ==============================================================================
# Switch to rzp_live_ keys only when live bank account activation is authorized.
RAZORPAY_KEY_ID=rzp_test_SSK1234567890
RAZORPAY_KEY_SECRET=YOUR_RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET=YOUR_RAZORPAY_WEBHOOK_SECRET
ALLOW_MOCK_PAYMENTS=false

# ==============================================================================
# 4. GST & INVOICE GENERATION CONFIGURATION
# ==============================================================================
SELLER_GSTIN=36AAECS1234F1Z5               # Official 15-digit GSTIN (Telangana: 36)
SELLER_PAN=AAECS1234F                      # 10-digit Permanent Account Number
SELLER_STATE=Telangana
SELLER_STATE_CODE=36
DEFAULT_JEWELLERY_GST_RATE=0.03            # 3% GST for Gold & Imitation Jewellery (HSN 7113/7117)
DEFAULT_ACCESSORIES_GST_RATE=0.18          # 18% GST for Hair Clips & Fashion Accessories (HSN 9615)
INVOICE_PREFIX=SSK-INV
CREDIT_NOTE_PREFIX=SSK-CN

# ==============================================================================
# 5. TRANSACTIONAL EMAIL (SMTP GATEWAY)
# ==============================================================================
# Works with AWS SES, SendGrid, Mailgun, or Google Workspace SMTP Relay:
SMTP_HOST=email-smtp.ap-south-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=YOUR_SMTP_USERNAME
SMTP_PASSWORD=YOUR_SMTP_PASSWORD
SMTP_FROM_EMAIL=orders@sreesaikrishnacollections.com
SMTP_FROM_NAME="Sree Sai Krishna Collections"
SMTP_TLS=true

# ==============================================================================
# 6. OFFICIAL META WHATSAPP BUSINESS PLATFORM CLOUD API (v19.0)
# ==============================================================================
# Set to true once Meta WhatsApp Business account and System User token are ready:
WHATSAPP_ENABLED=false
WHATSAPP_PHONE_NUMBER_ID=YOUR_META_PHONE_NUMBER_ID
WHATSAPP_BUSINESS_ACCOUNT_ID=YOUR_META_WABA_ID
WHATSAPP_ACCESS_TOKEN=YOUR_PERMANENT_SYSTEM_USER_ACCESS_TOKEN
WHATSAPP_API_VERSION=v19.0
WHATSAPP_WEBHOOK_VERIFY_TOKEN=YOUR_CUSTOM_RANDOM_VERIFY_TOKEN_FOR_META
WHATSAPP_APP_SECRET=YOUR_META_APP_SECRET
SUPPORT_PHONE="+91 98480 22338"

# ==============================================================================
# 7. LOGISTICS & COURIER WEBHOOK CONFIGURATION
# ==============================================================================
LOGISTICS_WEBHOOK_SECRET=YOUR_LOGISTICS_WEBHOOK_HMAC_SECRET
```

---

## 2. Meta WhatsApp Business Cloud API Setup Instructions

To obtain the required Meta credentials:

1. **Meta for Developers Account:**
   - Log into [developers.facebook.com](https://developers.facebook.com).
   - Create an app of type **Business** named `SSK Notifications`.
2. **Add WhatsApp Product:**
   - From the app dashboard, add **WhatsApp** &rarr; **Quickstart**.
   - Note your **Phone Number ID** and **WhatsApp Business Account ID (WABA ID)**.
3. **Generate Permanent System User Token:**
   - In **Meta Business Manager** (`business.facebook.com`), navigate to **Business Settings &rarr; System Users**.
   - Create a System User with role `Admin`.
   - Generate an access token with permissions:
     - `whatsapp_business_messaging`
     - `whatsapp_business_management`
   - Store this token securely as `WHATSAPP_ACCESS_TOKEN`.
4. **Register Webhook:**
   - In App Settings &rarr; WhatsApp &rarr; Configuration &rarr; **Webhook**:
     - Callback URL: `https://api.sreesaikrishnacollections.com/api/v1/webhooks/whatsapp`
     - Verify Token: Enter the value defined in `WHATSAPP_WEBHOOK_VERIFY_TOKEN`.
   - Subscribe to the `messages` field to receive delivery and read status updates.
5. **Register Templates:**
   - Submit the 10 templates listed in `WHATSAPP_INTEGRATION_REPORT.md` under the **Utility** category for instant Meta approval.

---

## 3. Production Frontend Environment (`frontend/.env.production`)

```ini
VITE_API_URL=https://api.sreesaikrishnacollections.com/api/v1
VITE_BRAND_NAME="Sree Sai Krishna Collections"
VITE_RAZORPAY_KEY_ID=rzp_live_YOUR_LIVE_KEY_ID
```
