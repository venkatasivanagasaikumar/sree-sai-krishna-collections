# SREE SAI KRISHNA COLLECTIONS (SSK)
# ULTRA-LOW-COST PRODUCTION ENVIRONMENT TEMPLATES & SECRET MANAGEMENT

**Document Version:** 1.0.0  
**Effective Date:** October 31, 2026  
**Auditor Roles:** Senior DevOps Engineer, Cloud Architect, and Security Release Manager  
**Baseline Verified Commit:** [`89f020c`](https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections/commit/89f020c)  
**Target Architecture:** Cloudflare Pages (Frontend) + Render.com (Backend) + MongoDB Atlas M0 + Brevo SMTP + Cloudinary

---

## 1. SECRET MANAGEMENT & SECURITY GUARDRAILS

> [!CAUTION]
> **CRITICAL SECURITY RULES:**
> 1. **NEVER COMMIT REAL SECRETS TO GIT:** Production passwords, secret keys, SMTP tokens, and database credentials must NEVER be committed to GitHub or hardcoded into source code.
> 2. **INJECT SECRETS ONLY VIA PROVIDER CONSOLES:** All variables below must be entered exclusively in the **Render.com Environment Dashboard** and **Cloudflare Pages Settings**.
> 3. **STAGING VS. PRODUCTION ISOLATION:** Staging credentials (`.env.staging`) must never be used in production, and production credentials must never be configured in staging.
> 4. **GENERATE HIGH-ENTROPY PASSWORDS:** Secret keys and admin passwords must be minimum 32 characters long, generated via cryptographic random generators.

---

## 2. FRONTEND PRODUCTION ENVIRONMENT TEMPLATE

Configure these variables in **Cloudflare Pages** &rarr; **Settings** &rarr; **Environment variables** (Production):

```bash
# ==============================================================================
# SSK FRONTEND PRODUCTION CONFIGURATION (Cloudflare Pages)
# ==============================================================================

# Public API Gateway URL (Points to your custom backend domain or Render service)
VITE_API_BASE_URL=https://api.sreesaikrishnacollections.com/api/v1

# Storefront Branding & Metadata
VITE_STORE_NAME="Sree Sai Krishna Collections"
VITE_STORE_TAGLINE="Exquisite 1-Gram Gold & Bridal Imitation Jewellery"
VITE_CURRENCY_SYMBOL="₹"

# Feature Toggles
VITE_ENABLE_ONLINE_PAYMENTS=true
VITE_ENABLE_COD=true

# Manual WhatsApp Business Customer Concierge Link
# (Formatted without + or spaces: Country code 91 followed by 10-digit mobile number)
VITE_WHATSAPP_SUPPORT_PHONE=919848022338
VITE_WHATSAPP_WELCOME_MESSAGE="Hi SSK Collections, I would like to inquire about jewellery order."

# Cloudinary Public Delivery Base URL (Optional - if using Cloudinary folder shortcuts)
VITE_CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
```

---

## 3. BACKEND PRODUCTION ENVIRONMENT TEMPLATE

Configure these variables in **Render.com** &rarr; **Your Web Service (`ssk-backend-prod`)** &rarr; **Environment** tab:

```bash
# ==============================================================================
# SSK BACKEND PRODUCTION CONFIGURATION (Render.com Free Web Service)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. CORE APPLICATION & ENVIRONMENT
# ------------------------------------------------------------------------------
# Set strictly to 'production' to automatically lock down Swagger /docs and /openapi.json
ENVIRONMENT=production
PROJECT_NAME="Sree Sai Krishna Collections"

# Cryptographic Secret Key for JWT signing (Minimum 32 random characters)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=GENERATE_RANDOM_48_CHAR_SECRET_KEY_HERE
ALGORITHM=HS256

# JWT Access Token Expiration (in minutes: 1440 = 24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ------------------------------------------------------------------------------
# 2. CORS DOMAIN ALLOWLIST
# ------------------------------------------------------------------------------
# Comma-separated list of allowed origins (No trailing slashes; NO wildcard *)
CORS_ORIGINS=["https://sreesaikrishnacollections.com","https://www.sreesaikrishnacollections.com"]

# ------------------------------------------------------------------------------
# 3. PRODUCTION DATABASE (MongoDB Atlas M0 Cluster)
# ------------------------------------------------------------------------------
# Connection string from Atlas M0 cluster in AWS Mumbai (ap-south-1)
MONGODB_URI=mongodb+srv://ssk_app_user:REPLACE_WITH_STRONG_DB_PASSWORD@ssk-cluster.xxxx.mongodb.net/ssk_production_db?retryWrites=true&w=majority
DATABASE_NAME=ssk_production_db

# Enforce live database connection (Refuses startup if set to true in production)
FORCE_MOCK_DB=false
DB_TLS=true

# Atlas Connection Pool Optimization (Tuned for M0 500-connection limit)
DB_MIN_POOL_SIZE=5
DB_MAX_POOL_SIZE=25
DB_MAX_IDLE_TIME_MS=45000
DB_CONNECT_TIMEOUT_MS=10000
DB_SERVER_SELECTION_TIMEOUT_MS=10000

# ------------------------------------------------------------------------------
# 4. INITIAL SUPER ADMIN ACCOUNT (Automated Provisioning on First Boot)
# ------------------------------------------------------------------------------
# Initial admin credentials used to seed the first administrative user
INITIAL_ADMIN_EMAIL=admin@sreesaikrishnacollections.com
INITIAL_ADMIN_PASSWORD=REPLACE_WITH_MINIMUM_20_CHAR_ADMIN_PASSWORD!@#
INITIAL_ADMIN_NAME="Venkata Siva Naga Sai Kumar"
INITIAL_ADMIN_PHONE="+91 98480 22338"

# ------------------------------------------------------------------------------
# 5. TRANSACTIONAL EMAIL (Brevo / Sendinblue Free SMTP)
# ------------------------------------------------------------------------------
# Brevo SMTP Relay credentials (300 free emails/day)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=REPLACE_WITH_YOUR_BREVO_LOGIN_EMAIL@example.com
SMTP_PASSWORD=REPLACE_WITH_BREVO_SMTP_KEY_xsmtpsib-...
SMTP_FROM=orders@sreesaikrishnacollections.com
SMTP_FROM_NAME="Sree Sai Krishna Collections"
SMTP_USE_TLS=true

# ------------------------------------------------------------------------------
# 6. WHATSAPP NOTIFICATIONS (Manual Boutique Concierge Mode)
# ------------------------------------------------------------------------------
# Disabled for zero-cost operation; customer communication routed via WhatsApp Business App
WHATSAPP_ENABLED=false
WHATSAPP_PHONE_NUMBER_ID=""
WHATSAPP_BUSINESS_ACCOUNT_ID=""
WHATSAPP_ACCESS_TOKEN=""
WHATSAPP_DEFAULT_PHONE="919848022338"

# ------------------------------------------------------------------------------
# 7. PAYMENTS CONFIGURATION (Razorpay Live & Cash on Delivery)
# ------------------------------------------------------------------------------
# Disallow mock payments in production
ALLOW_MOCK_PAYMENTS=false

# Cash on Delivery (COD) Settings
ENABLE_COD=true
COD_MIN_ORDER_AMOUNT=299
COD_MAX_ORDER_AMOUNT=15000

# Razorpay Live Credentials (Obtain from Razorpay Dashboard -> Settings -> API Keys)
# Keep empty or insert live keys when online payments are desired
RAZORPAY_KEY_ID=rzp_live_REPLACE_WITH_LIVE_KEY_ID
RAZORPAY_KEY_SECRET=REPLACE_WITH_LIVE_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET=REPLACE_WITH_LIVE_WEBHOOK_SECRET

# ------------------------------------------------------------------------------
# 8. SHIPPING & TAX ENGINE SETTINGS
# ------------------------------------------------------------------------------
DEFAULT_JEWELLERY_GST_RATE=0.03
DEFAULT_ACCESSORIES_GST_RATE=0.18
STORE_ORIGIN_STATE=Telangana
STORE_ORIGIN_PINCODE=500081
FREE_SHIPPING_THRESHOLD=999
STANDARD_SHIPPING_FEE=70.0
EXPRESS_SHIPPING_FEE=150.0

# ------------------------------------------------------------------------------
# 9. PRODUCT MEDIA CDN (Cloudinary Free Tier)
# ------------------------------------------------------------------------------
# Optional: Used if integrating Cloudinary direct server-side uploads
CLOUDINARY_CLOUD_NAME=REPLACE_WITH_CLOUDINARY_NAME
CLOUDINARY_API_KEY=REPLACE_WITH_CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET=REPLACE_WITH_CLOUDINARY_API_SECRET
```

---

## 4. SECURE VALUE GENERATION COMMANDS

Run the following quick PowerShell or Python commands locally to generate cryptographically secure values before entering them in your cloud consoles:

```powershell
# 1. Generate 48-character Secret Key for JWT
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 2. Generate 24-character Super Admin Password
python -c "import secrets, string; alphabet = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(alphabet) for _ in range(24)))"

# 3. Generate 32-character Webhook Secret
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## 5. ENVIRONMENT VERIFICATION CHECKLIST

Before accepting public traffic, verify that:
- [ ] `ENVIRONMENT` is set to `production` (Confirm `GET /docs` returns `404 Not Found`).
- [ ] `FORCE_MOCK_DB` is `false` and backend connects to MongoDB Atlas M0 cluster.
- [ ] `CORS_ORIGINS` contains only your exact custom domain (`https://sreesaikrishnacollections.com`).
- [ ] Brevo test email succeeds upon customer registration or password reset.
- [ ] Razorpay webhook URL is configured in Razorpay Dashboard pointing to `https://api.sreesaikrishnacollections.com/api/v1/payments/webhook`.
