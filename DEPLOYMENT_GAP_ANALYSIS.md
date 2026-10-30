# SREE SAI KRISHNA COLLECTIONS (SSK)
## PRODUCTION DEPLOYMENT GAP ANALYSIS

**Evaluation Date:** October 30, 2026  
**Auditor:** Senior DevOps Engineer, Cloud Architect & E-Commerce Security Auditor  
**Repository Branch:** `main`  
**Inspected Commit:** `1ce2836`  
**Current Commercial Status:** `CONDITIONAL GO`  

---

## 1. EXECUTIVE GAP OVERVIEW

An exhaustive audit of the Sree Sai Krishna Collections (SSK) repository was conducted across frontend source files, FastAPI backend services, database orchestration layers, Docker container configurations, and Nginx reverse proxies.

The application software, business logic, cart total calculations, and internal mock simulation engines are **100% complete and verified** (64/64 automated tests passing, 0 TypeScript/Vite errors). However, **commercial launch to live paying consumers requires resolving 8 specific operational and infrastructure gaps** that require merchant action or external service provisioning.

```
+------------------------------------+----------------+--------------------+------------------------+
| Audit Domain                       | Findings Count | Critical Blockers  | Commercial Readiness   |
+------------------------------------+----------------+--------------------+------------------------+
| Database (MongoDB Atlas)           | 1 Finding      | 1 Critical         | Code Ready / Live Block|
| Payment Gateway (Razorpay)         | 1 Finding      | 1 Critical         | Code Ready / KYC Block |
| Domain, DNS & SSL Certificates     | 1 Finding      | 1 Critical         | Nginx Ready / DNS Block|
| Transactional Email (SMTP Relay)   | 1 Finding      | 1 High             | Code Ready / Creds Blk |
| WhatsApp Cloud API (Meta v19.0)    | 1 Finding      | 1 High             | Code Ready / Meta Blk  |
| Legal & Chartered Accountant (GST) | 1 Finding      | 1 High             | Engine Ready / CA Blk  |
| Security & Secret Management       | 1 Finding      | 1 High             | Script Ready / Ops Blk |
| Media Storage & Cloud CDN (S3)     | 1 Finding      | 1 Medium           | Local Volume Functional|
+------------------------------------+----------------+--------------------+------------------------+
```

---

## 2. DETAILED GAP FINDINGS MATRIX

### FINDING GAP-01: Live MongoDB Atlas Cluster Provisioning & Connection String
- **File and Location:** `backend/app/database.py` (Lines 32–75), `backend/app/core/config.py` (Line 19), `backend/.env.production.example` (Lines 16–25).
- **Current State:** The backend codebase fully supports `mongodb+srv://` connection strings, TLS encryption, and connection pooling (`maxPoolSize=50-100`, `minPoolSize=10`, `maxIdleTimeMS=45000`). Strict fail-safes are active (`RuntimeError` if production boots without a live database). However, no live MongoDB Atlas connection string is configured in `.env`; local port 27017 is not listening on the host machine.
- **Severity:** **CRITICAL**
- **Business Impact:** High-concurrency commercial launches cannot rely on file-backed disk dumps (`db_dump.json`) or single-instance local containers without high-availability clustering and point-in-time recovery.
- **Required Fix:** Provision an Atlas M10+ replica set in AWS ap-south-1 (Mumbai), create user `ssk_app_user`, whitelist the production server IP, and inject `MONGODB_URI` into `backend/.env` with `FORCE_MOCK_DB=false`.
- **Verification Method:** Invoke `GET /ready` and verify response `{"status": "ready", "database": {"status": "connected", "type": "mongodb_live"}}`.

---

### FINDING GAP-02: Public Domain DNS Cutover and SSL/TLS Termination
- **File and Location:** `frontend/nginx.conf` (Lines 1–65), `frontend/public/robots.txt` (Line 17), `frontend/public/sitemap.xml` (Lines 1–53), `frontend/index.html` (Line 10).
- **Current State:** Nginx reverse proxy directives, security headers (`X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`), and static asset caching are configured. The canonical domain is set to `https://sreesaikrishnacollections.com`. However, public DNS records have not yet been pointed to the production IP, and SSL certificates are not yet issued.
- **Severity:** **CRITICAL**
- **Business Impact:** Customers attempting to access the site over unencrypted HTTP will receive browser security warnings; payments and authentication cookies cannot be transmitted securely without HTTPS.
- **Required Fix:** Configure DNS A records for `@` and `admin` pointing to the production server IP; execute Certbot (`certbot --nginx -d sreesaikrishnacollections.com -d admin.sreesaikrishnacollections.com`) to generate free Let's Encrypt certificates.
- **Verification Method:** Inspect SSL handshake via `curl -I https://sreesaikrishnacollections.com` and verify HTTP 200 with valid TLS 1.3 certificate.

---

### FINDING GAP-03: Razorpay Live Merchant Account KYC & Live Credentials
- **File and Location:** `backend/app/api/v1/payments.py` (Lines 19–80, Lines 346–380), `backend/app/core/config.py` (Lines 36–38), `backend/.env.production.example` (Lines 30–35).
- **Current State:** Razorpay Sandbox integration is 100% functional and tested. Webhook signature authentication (`X-Razorpay-Signature`) is active and validated with HMAC-SHA256. Unpaid online orders cannot be marked paid via admin shortcuts. However, credentials remain set to sandbox test keys (`rzp_test_...`).
- **Severity:** **CRITICAL**
- **Business Impact:** The store cannot accept real currency payments from credit cards, debit cards, UPI, or Net Banking from Indian shoppers until live merchant credentials are authenticated.
- **Required Fix:** Complete business KYC on the Razorpay Dashboard, generate live keys (`rzp_live_...`), register the webhook URL `https://sreesaikrishnacollections.com/api/v1/payments/webhook` with secret, and populate `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` in `backend/.env`.
- **Verification Method:** Perform a live micro-transaction (₹1.00 via UPI) and verify settlement, payment status transition, and automated GST invoice issuance.

---

### FINDING GAP-04: Production SMTP Relay Provisioning (AWS SES or SendGrid)
- **File and Location:** `backend/app/services/email_service.py` (Lines 42–115), `backend/app/core/config.py` (Lines 51–60), `backend/.env.production.example` (Lines 48–55).
- **Current State:** Transactional email engine is fully implemented with 17 HTML/text templates, TLS port 587 support, and automatic ReportLab PDF invoice attachments. When unconfigured, it logs to `email_logs` without failing checkout. However, `SMTP_USER` and `SMTP_PASSWORD` are unconfigured.
- **Severity:** **HIGH**
- **Business Impact:** Real customers will not receive automated order confirmation emails, invoice PDFs, shipping updates, or password reset tokens in their inboxes.
- **Required Fix:** Provision an Amazon Simple Email Service (SES) or SendGrid account, verify domain DNS records (SPF, DKIM, DMARC) for `sreesaikrishnacollections.com`, and set `SMTP_HOST`, `SMTP_PORT=587`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL` in `backend/.env`.
- **Verification Method:** Trigger test password reset via `POST /api/v1/auth/forgot-password` and verify delivery in external inbox.

---

### FINDING GAP-05: Meta WhatsApp Business Platform Permanent System User Token
- **File and Location:** `backend/app/services/whatsapp_service.py` (Lines 10–62, Lines 130–255), `backend/app/api/v1/webhooks.py` (Lines 12–49), `backend/.env.production.example` (Lines 57–67).
- **Current State:** Official Meta WhatsApp Business Cloud API v19.0 client is implemented. Phone normalization to E.164 (`919848022338`), customer opt-out preferences, and webhook `hub.mode=subscribe` verification handshakes are verified. However, `WHATSAPP_ACCESS_TOKEN` is unset.
- **Severity:** **HIGH**
- **Business Impact:** WhatsApp order confirmation and dispatch alerts are logged to internal database collections but not delivered to real customer WhatsApp handsets.
- **Required Fix:** In Meta Business Manager, verify the business entity, register the 10 utility message templates in English, generate a permanent System User Access Token with `whatsapp_business_messaging` permissions, and set `WHATSAPP_ENABLED=true` and `WHATSAPP_ACCESS_TOKEN` in `backend/.env`.
- **Verification Method:** Trigger test dispatch via `POST /api/v1/communications/admin/test-whatsapp` and verify receipt on registered test phone.

---

### FINDING GAP-06: Legal Verification of GSTIN and Product HSN Classifications
- **File and Location:** `backend/app/services/invoice_service.py` (Lines 120–170), `backend/app/core/config.py` (Lines 63–70), `backend/.env.production.example` (Lines 40–46).
- **Current State:** The automated invoicing subsystem reverse-calculates taxes and applies dual HSN classifications: HSN 7117 (3% GST) for imitation jewellery and HSN 9615 (18% GST) for hair accessories. Sequential numbering (`SSK-INV-YYYY-XXXX`) and intrastate (50/50 Telangana CGST+SGST) vs interstate (100% IGST) rules are implemented. However, the configured GSTIN (`36AAECS1234F1Z5`) is a demo placeholder.
- **Severity:** **HIGH**
- **Business Impact:** Issuing commercial tax invoices with a placeholder GSTIN or unverified HSN rates violates Section 31 of the Central Goods and Services Tax (CGST) Act, 2017.
- **Required Fix:** Consult the business Chartered Accountant to confirm the official 15-digit GSTIN, PAN, and specific HSN classifications for 1-gram gold vs imitation pieces, and update `SELLER_GSTIN` and `SELLER_PAN` in `backend/.env`.
- **Verification Method:** Generate an invoice for order `SSK-INV-2026-0001` and verify that the printed legal header matches the registered GST Certificate.

---

### FINDING GAP-07: Production Cryptographic Secret Generation
- **File and Location:** `backend/app/core/config.py` (Line 10), `backend/.env.production.example` (Line 10).
- **Current State:** The backend has a fallback development secret `ssk-royal-navy-gold-super-secure-jwt-secret-key-2026-prod`. The startup pre-flight validator (`validate_production_readiness()`) flags this default key as insecure in production mode.
- **Severity:** **HIGH**
- **Business Impact:** Using predictable or public development secrets allows attackers to forge valid JWT authentication tokens and impersonate customers or store administrators.
- **Required Fix:** Generate a cryptographically secure 256-bit secret on the production server using `openssl rand -hex 32` and assign it to `SECRET_KEY` in `backend/.env`.
- **Verification Method:** Inspect backend logs during startup and ensure no `[PRODUCTION CONFIG ALERT] SECRET_KEY is using insecure default development value` warning appears.

---

### FINDING GAP-08: Product Uploads Stored Locally vs Cloud Object Storage (S3 / Cloudflare R2)
- **File and Location:** `backend/app/api/v1/upload.py` (Lines 10–25), `frontend/nginx.conf` (Lines 52–59), `docker-compose.yml` (Line 27).
- **Current State:** Uploaded product images are stored locally in `backend/uploads/` and served via Nginx reverse proxy. Volume mounts in `docker-compose.yml` guarantee data persistence across container restarts. However, local storage is bounded by server disk space and does not leverage a global Content Delivery Network (CDN).
- **Severity:** **MEDIUM**
- **Business Impact:** While fully functional for initial commercial launch (< 1,000 product images), scaling to tens of thousands of customer visits and catalog images will consume local SSD storage and server bandwidth.
- **Required Fix:** For Day 1 Go-Live, the existing persistent Docker volume mount (`./backend/uploads:/app/uploads`) is sufficient. For post-launch scaling (Phase 2), configure an S3-compatible bucket (AWS S3 or Cloudflare R2 with free egress).
- **Verification Method:** Upload an image via Seller Panel (`/admin/products`), restart the Docker container (`docker compose restart backend`), and verify image URL remains accessible.

---

## 3. SUMMARY OF ACTIONABLE ITEMS

```
================================================================================
PRIORITY 1 (MUST RESOLVE BEFORE PUBLIC TRAFFIC):
  [ ] Provision MongoDB Atlas M10+ Replica Set in Mumbai (ap-south-1).
  [ ] Configure DNS A records for sreesaikrishnacollections.com.
  [ ] Issue Let's Encrypt SSL/TLS Certificate via Certbot.
  [ ] Activate Razorpay Live Account and set rzp_live_ keys & webhook secret.
  [ ] Generate random 64-character SECRET_KEY with openssl rand -hex 32.

PRIORITY 2 (MUST RESOLVE FOR FULL STORE AUTOMATION):
  [ ] Configure Transactional SMTP Relay (AWS SES or SendGrid).
  [ ] Setup Meta WhatsApp Cloud API System User Token and approve 10 templates.
  [ ] Insert official 15-digit GSTIN verified by business Chartered Accountant.

PRIORITY 3 (POST-LAUNCH ENHANCEMENTS):
  [ ] Migrate product upload storage from local Docker volume to Cloudflare R2 / AWS S3.
================================================================================
```
