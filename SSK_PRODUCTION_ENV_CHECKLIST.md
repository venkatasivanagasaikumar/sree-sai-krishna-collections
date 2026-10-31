# SREE SAI KRISHNA COLLECTIONS (SSK)
# PRODUCTION ENVIRONMENT VARIABLE CHECKLIST & CONFIGURATION RUNBOOK

**Document Version:** 1.0.0  
**Effective Date:** October 31, 2026  
**Auditor Roles:** Senior DevOps Engineer, Cloud Architect, and Security Release Manager  
**Baseline Verified Commit:** [`038345c`](https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections/commit/038345c)  
**Target Architecture:** Cloudflare Pages (Frontend) + Render.com Free Web Service (Backend) + MongoDB Atlas M0 (AWS Mumbai)

---

## 1. CRITICAL SECURITY GUARDRAILS

> [!CAUTION]
> **STRICT SECRETS GOVERNANCE:**
> 1. **ZERO SECRETS IN GIT:** Real production passwords, database URIs, JWT secret keys, and SMTP credentials must **NEVER** be committed to source code or pushed to any Git branch.
> 2. **CONSOLE-ONLY CONFIGURATION:** All variables listed in this document must be configured exclusively in the official cloud provider web consoles:
>    - Frontend variables &rarr; **Cloudflare Dashboard &rarr; Pages &rarr; Settings &rarr; Environment variables**
>    - Backend variables &rarr; **Render Dashboard &rarr; Services &rarr; ssk-backend &rarr; Environment**
> 3. **STAGING ISOLATION:** Never reuse staging database connection strings, credentials, or keys in the production environment.
> 4. **MINIMUM ENTROPY STANDARDS:** Secret keys must be minimum 32 random characters (generated via `python -c "import secrets; print(secrets.token_urlsafe(48))"`).

---

## 2. FRONTEND PRODUCTION ENVIRONMENT VARIABLES (Cloudflare Pages)

Configure these variables in **Cloudflare Dashboard** &rarr; **Workers & Pages** &rarr; **Overview** &rarr; **Your Project (`ssk-collections-frontend`)** &rarr; **Settings** &rarr; **Environment variables** &rarr; **Production**:

| Variable Name | Required? | Production Value / Pattern | Description & Validation Rules |
| :--- | :---: | :--- | :--- |
| **`VITE_API_URL`** | **MANDATORY** | `https://api.sreesaikrishnacollections.com/api/v1` *(or Render backend URL)* | **CRITICAL (PRE-01):** Must point to the backend API base. Do NOT use `VITE_API_BASE_URL`. Must include `/api/v1` suffix and omit trailing slash. |
| `VITE_STORE_NAME` | Optional | `Sree Sai Krishna Collections` | Brand display name rendered in storefront navigation and page titles. |
| `VITE_STORE_TAGLINE` | Optional | `Exquisite 1-Gram Gold & Bridal Imitation Jewellery` | Hero headline and metadata description. |
| `VITE_CURRENCY_SYMBOL` | Optional | `₹` | Currency symbol rendered in product cards, cart, and checkout. |
| `VITE_ENABLE_ONLINE_PAYMENTS`| Mandatory | `false` *(initially for pure COD)* or `true` *(once Razorpay KYC approved)* | Feature flag controlling visibility of online credit card/UPI checkout option. |
| `VITE_ENABLE_COD` | Mandatory | `true` | Enables Cash on Delivery payment option at checkout. |
| `VITE_WHATSAPP_SUPPORT_PHONE`| Mandatory | `919848022338` | Merchant WhatsApp phone number (Country code 91 + 10 digits; NO plus sign or spaces). |
| `VITE_WHATSAPP_WELCOME_MESSAGE`| Optional | `Hi SSK Collections, I would like to inquire about jewellery order.` | Pre-filled URL-encoded message for customer click-to-chat concierge link. |
| `VITE_CLOUDINARY_CLOUD_NAME`| Optional | `ssk-jewellery` | Public Cloudinary cloud name for direct asset transformations. |

---

## 3. BACKEND PRODUCTION ENVIRONMENT VARIABLES (Render.com)

Configure these variables in **Render Dashboard** &rarr; **Web Services** &rarr; **`ssk-backend`** &rarr; **Environment** tab:

### Category A: Core Application & Security Settings

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Security Impact |
| :--- | :---: | :--- | :--- |
| **`ENVIRONMENT`** | **MANDATORY** | `production` | **STRICT SECURITY REQUIREMENT:** Setting to `production` disables Swagger `/docs`, `/redoc`, and `/openapi.json` routes, and enables strict HMAC validation. |
| `PROJECT_NAME` | Optional | `Sree Sai Krishna Collections API` | Display name for system logs and audit headers. |
| **`SECRET_KEY`** | **MANDATORY** | *Random 48-char string* | Cryptographic signing key for customer and admin JWT tokens. Must NOT contain default test values (`ssk-royal-navy-gold`). |
| `ALGORITHM` | Mandatory | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Mandatory | `1440` | JWT token validity window in minutes (1440 = 24 hours). |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Mandatory | `30` | Refresh token lifespan in days. |
| **`BACKEND_CORS_ORIGINS`** | **MANDATORY** | `["https://sreesaikrishnacollections.com","https://www.sreesaikrishnacollections.com"]` | **CRITICAL (PRE-05):** JSON string array of allowed storefront origins. Must match `config.py`. No wildcards (`*`) permitted in production. |

### Category B: Database Configuration (MongoDB Atlas M0)

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Operational Impact |
| :--- | :---: | :--- | :--- |
| **`MONGODB_URI`** | **MANDATORY** | `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority` | Atlas M0 connection string. Must use TLS (`+srv://`). Must NOT contain `localhost` or `127.0.0.1`. |
| `DATABASE_NAME` | Mandatory | `ssk_production_db` | Target MongoDB database name. |
| **`FORCE_MOCK_DB`** | **MANDATORY** | `false` | Must be `false`. If set to `true` when `ENVIRONMENT=production`, backend refuses startup (`RuntimeError`). |
| `DB_TLS` | Mandatory | `true` | Enforces TLS 1.3 socket encryption for all database traffic. |
| `DB_MIN_POOL_SIZE` | Mandatory | `5` | Minimum idle connections maintained in pool. |
| `DB_MAX_POOL_SIZE` | Mandatory | `25` | Maximum connections allocated to this container (safely below Atlas M0 500-conn limit). |
| `DB_MAX_IDLE_TIME_MS` | Mandatory | `45000` | Sockets idle for >45s are recycled to prevent stale connections across cold starts. |
| `DB_CONNECT_TIMEOUT_MS` | Mandatory | `10000` | 10-second timeout for initial connection. |
| `DB_SERVER_SELECTION_TIMEOUT_MS`| Mandatory | `5000` | 5-second fail-fast timeout if cluster is unreachable. |
| `DB_SOCKET_TIMEOUT_MS` | Mandatory | `20000` | 20-second timeout for long queries. |

### Category C: Initial Super Admin Account Initialization

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Operational Impact |
| :--- | :---: | :--- | :--- |
| **`INITIAL_ADMIN_EMAIL`** | **MANDATORY** | `admin@sreesaikrishnacollections.com` | Primary administrative email account seeded on first database boot. |
| **`INITIAL_ADMIN_PASSWORD`** | **MANDATORY** | *Minimum 24-character random password* | High-entropy password. Must NOT be default passwords (`Admin@SSK2026!`, `AdminPassword123!`). |

### Category D: Transactional Email (Brevo / Sendinblue Free SMTP)

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Operational Impact |
| :--- | :---: | :--- | :--- |
| `SMTP_HOST` | Optional | `smtp-relay.brevo.com` | Brevo SMTP server address. If empty, emails are logged in simulated mode. |
| `SMTP_PORT` | Optional | `587` | Standard SMTP STARTTLS port. |
| `SMTP_USER` | Optional | `your_brevo_account_login@email.com` | Brevo SMTP account identifier. |
| `SMTP_PASSWORD` | Optional | `xsmtpsib-...` | Brevo SMTP master key. |
| `SMTP_FROM_EMAIL` | Optional | `orders@sreesaikrishnacollections.com` | Verified sender email address matching authenticated domain. |
| `SMTP_FROM_NAME` | Optional | `Sree Sai Krishna Collections` | Friendly sender name displayed to recipient. |
| `SMTP_TLS` | Optional | `true` | Enforces STARTTLS encryption during SMTP handshake. |
| `FRONTEND_URL` | Mandatory | `https://sreesaikrishnacollections.com` | Production URL used in password reset email links. |

### Category E: Customer Messaging (WhatsApp Business Concierge Mode)

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Operational Impact |
| :--- | :---: | :--- | :--- |
| `WHATSAPP_ENABLED` | Mandatory | `false` | Disabled for zero-cost operation; customer support is handled manually via WhatsApp Business mobile app. |
| `WHATSAPP_PHONE_NUMBER_ID` | Optional | `""` | Keep empty when `WHATSAPP_ENABLED=false`. |
| `WHATSAPP_BUSINESS_ACCOUNT_ID`| Optional | `""` | Keep empty when `WHATSAPP_ENABLED=false`. |
| `WHATSAPP_ACCESS_TOKEN` | Optional | `""` | Keep empty when `WHATSAPP_ENABLED=false`. |
| `WHATSAPP_DEFAULT_PHONE` | Optional | `919848022338` | Store owner WhatsApp phone number. |

### Category F: Payments & Commerce Settings

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Operational Impact |
| :--- | :---: | :--- | :--- |
| `ALLOW_MOCK_PAYMENTS` | Mandatory | `false` | Disallows sandbox payment simulation in production. |
| `ENABLE_COD` | Mandatory | `true` | Enables Cash on Delivery order processing. |
| `COD_MIN_ORDER_AMOUNT` | Mandatory | `299.0` | Minimum order value eligible for COD. |
| `COD_MAX_ORDER_AMOUNT` | Mandatory | `15000.0` | Maximum order value eligible for COD (fraud mitigation). |
| `RAZORPAY_KEY_ID` | Optional | `rzp_live_...` *(or leave empty for COD launch)* | Live Razorpay Key ID obtained from Razorpay Dashboard. |
| `RAZORPAY_KEY_SECRET` | Optional | *Razorpay Live Secret Key* | Secret key for webhook signature and payment capture verification. |
| `RAZORPAY_WEBHOOK_SECRET` | Optional | *Razorpay Webhook Secret Key* | Webhook HMAC verification secret. |

### Category G: Taxation & Store Shipping Policies

| Variable Name | Required? | Production Value / Pattern | Validation Rule & Operational Impact |
| :--- | :---: | :--- | :--- |
| `SELLER_PAN` | Mandatory | `AAECS1234F` *(Merchant PAN)* | Permanent Account Number printed on GST invoices. |
| `SELLER_GSTIN` | Optional | `36AAECS1234F1Z5` *(or leave empty pending CA confirmation)* | Goods and Services Tax Identification Number. |
| `SELLER_STATE` | Mandatory | `Telangana` | Store origin state for CGST/SGST vs IGST calculation. |
| `SELLER_STATE_CODE` | Mandatory | `36` | 2-digit Indian State Code for Telangana. |
| `DEFAULT_JEWELLERY_GST_RATE` | Mandatory | `0.03` | 3% GST rate for imitation jewellery (HSN 7117). |
| `DEFAULT_ACCESSORIES_GST_RATE`| Mandatory | `0.18` | 18% GST rate for hair accessories (HSN 9615). |
| `FREE_SHIPPING_THRESHOLD` | Mandatory | `999.0` | Order value in INR above which shipping is complimentary. |
| `STANDARD_SHIPPING_FEE` | Mandatory | `70.0` | Flat standard shipping fee for orders below threshold. |
| `EXPRESS_SHIPPING_FEE` | Mandatory | `150.0` | Expedited shipping fee. |

---

## 4. SECURE VALUE GENERATION COMMANDS

Run the following commands in an isolated local PowerShell or Python terminal to generate cryptographically strong values prior to entering them in provider dashboards:

```powershell
# 1. Generate 48-character Secret Key for JWT (SECRET_KEY)
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 2. Generate 24-character Super Admin Password (INITIAL_ADMIN_PASSWORD)
python -c "import secrets, string; alphabet = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(alphabet) for _ in range(24)))"

# 3. Generate 32-character Webhook Secret (RAZORPAY_WEBHOOK_SECRET)
python -c "import secrets; print(secrets.token_hex(16))"

# 4. Generate AES-256 Passphrase for GitHub Actions Automated Backup (BACKUP_ENCRYPTION_KEY)
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. PRE-LAUNCH SMOKE TEST & VERIFICATION PROCEDURES

After populating environment variables and triggering the initial deployments, run this step-by-step verification checklist:

### Step 1: Verify Production Swagger Lockdown
```bash
# Must return HTTP 404 Not Found
curl -s -o /dev/null -w "%{http_code}\n" https://api.sreesaikrishnacollections.com/docs
curl -s -o /dev/null -w "%{http_code}\n" https://api.sreesaikrishnacollections.com/openapi.json
```
- [ ] Confirmed: Both endpoints return `404`.

### Step 2: Verify Health & Database Readiness
```bash
# Health probe (Liveness)
curl -s https://api.sreesaikrishnacollections.com/health | jq .

# Readiness probe (Database Connectivity)
curl -s https://api.sreesaikrishnacollections.com/ready | jq .
```
- [ ] Confirmed: `/health` returns `"status": "healthy"`, `"database": "mongodb_live"`.
- [ ] Confirmed: `/ready` returns `"status": "ready"`, `"database": {"status": "connected"}`.

### Step 3: Verify Frontend Edge CDN & API Routing
1. Open a browser in Incognito mode and navigate to `https://sreesaikrishnacollections.com`.
2. Inspect the browser Network tab:
   - [ ] Page loads in < 1 second with HTTP 200 from Cloudflare Edge.
   - [ ] API calls are routed to `https://api.sreesaikrishnacollections.com/api/v1/products` (NOT relative `/api/v1`).
   - [ ] Product catalogue renders properly with images loaded from Cloudinary CDN.

### Step 4: Verify Initial Admin Login
1. Navigate to `https://sreesaikrishnacollections.com/login`.
2. Enter `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`.
3. [ ] Confirmed: Login succeeds, redirecting to Admin Dashboard with full access to Orders, Products, and Invoices.
