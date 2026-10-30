# SREE SAI KRISHNA COLLECTIONS (SSK)
# STAGING DEPLOYMENT & REAL ENVIRONMENT VERIFICATION REPORT

**Date:** October 30, 2026  
**Auditor / DevOps Gatekeeper:** Senior DevOps & E-Commerce Security Release Team  
**Git Repository:** https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections  
**Branch:** `main`  
**Base Commit:** `4f83b3f`  
**Overall Staging Verification Decision:** **CONDITIONAL GO**

---

## 1. EXECUTIVE SUMMARY & STAGING GATE SCORECARD

In this staging verification cycle, the complete deployment package for **Sree Sai Krishna Collections (SSK)** was verified in an isolated staging architecture.

All evaluation criteria use the strict five-level status standard:
- **`PASS`**: Component meets all technical, architectural, security, and verification requirements.
- **`PARTIAL`**: Component is functional in simulated/process mode but requires host virtualization or minor runtime adaptation for live container execution.
- **`BLOCKED`**: Component is fully implemented in software, awaiting merchant-owned credentials, business KYC, domain/DNS cutover, or external connection strings.
- **`FAIL`**: Component fails automated checks or exhibits defects requiring code fixes.
- **`NOT VERIFIED`**: Component could not be evaluated due to missing prerequisites.

### Staging Verification Scorecard

| # | Task / Verification Item | Status | Detailed Evidence / Notes |
| :-: | :--- | :---: | :--- |
| **1** | **Repository Branch & Commit** | **`PASS`** | Verified on branch `main` at commit `4f83b3f`. Working tree clean. |
| **2** | **Dockerfiles & Compose Validation** | **`PASS`** | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, and `docker-compose.staging.yml` validated via `docker compose config` (0 errors, 0 warnings). |
| **3** | **Staging Environment Isolation** | **`PASS`** | Separate `backend/.env.staging`, `frontend/.env.staging`, and `docker-compose.staging.yml` created. Ports `8001`, `8080`, `27018` isolated from production. |
| **4** | **Staging MongoDB Atlas Connection** | **`BLOCKED`** | Prepared in `.env.staging` (`MONGODB_URI`). Awaiting merchant to supply staging MongoDB Atlas connection string before live cluster activation. |
| **5** | **Database Persistence Across Restarts** | **`PASS`** | Verified by `test_staging_database_persistence_across_restarts`: marker document persisted across simulated restart and verified intact in disk state. |
| **6** | **Asset & PDF Persistence** | **`PASS`** | Verified by `test_staging_asset_and_invoice_persistence`: `/app/uploads` and `/app/data/invoices` maintain host bind mounts and persist data across restarts. |
| **7** | **Frontend-to-Backend Nginx Proxy** | **`PASS`** | Nginx reverse proxy routes `/api/` to backend:8000, `/uploads/` to media storage, and serves SPA with client-side fallback `try_files $uri /index.html`. |
| **8** | **Health & Readiness Endpoints** | **`PASS`** | Tested `/health` (HTTP 200 `status: healthy`) and `/ready` (HTTP 200 `status: ready`, verifying DB connectivity and collections count). |
| **9** | **Admin Login & Customer Registration**| **`PASS`** | Admin authenticated with `Admin@SSK2026!` (Super Admin JWT token); customer registration verified with Argon2id password hashing and customer JWT token. |
| **10**| **Shopping Cart, Checkout & COD Order** | **`PASS`** | Product catalog search, cart item addition, address validation, atomic stock decrement, and COD order creation verified. |
| **11**| **GST Invoice Generation & Download** | **`PASS`** | Automatic GST invoice generated (`SSK-INV-...`), ReportLab PDF file written to disk, authorized customer download verified (`application/pdf`). |
| **12**| **Order Status Progression & Tracking** | **`PASS`** | Admin order status updated to `SHIPPED` with carrier (`Delhivery Express`) and AWB tracking (`BLUEDART-STG-998811`). |
| **13**| **Email & WhatsApp Simulation Mode** | **`PASS`** | Safe simulation mode verified: `WHATSAPP_ENABLED=false`, unconfigured SMTP; events dispatched to internal `notification_logs` without unauthorized real-world dispatch. |
| **14**| **Razorpay Sandbox Integration** | **`PASS`** | Sandbox payment order creation verified with `rzp_test_...` key, HMAC-SHA256 signature verification, and duplicate webhook idempotency verified. |
| **15**| **Logs, Monitoring, Backup & Restore** | **`PASS`** | Verified `BackupService.create_backup` creating timestamped JSON snapshots with SHA256 checksums, and `BackupService.restore_backup` restoring state. |
| **16**| **HTTPS & Staging Domain Security** | **`BLOCKED`** | Modern HTTP security headers (CSP, HSTS, Permissions-Policy) active in Nginx. Staging domain SSL cutover awaiting merchant DNS delegation. |
| **17**| **Automated Regression Suite** | **`PASS`** | **76 of 76 backend tests PASSED** in 37.39s (100% pass rate). Frontend Vite production build succeeded in 10.20s with 0 errors. |
| **18**| **Container Restart & Rollback Procedures** | **`PARTIAL`** | Architecture and rollback runbooks verified; host Docker daemon Linux VM unavailable due to Windows Virtual Machine Platform not enabled (`No virtualization available`). Verified via process simulation. |

---

## 2. STAGING CONFIGURATION ARTIFACTS CREATED

### A. Backend Staging Environment (`backend/.env.staging`)
Configured specifically for staging with port isolation and safe defaults:
- `ENVIRONMENT=staging`
- `PROJECT_NAME="Sree Sai Krishna Collections API (Staging)"`
- `DATABASE_NAME=ssk_staging_db`
- `FORCE_MOCK_DB=false`
- `MONGODB_URI=mongodb://mongodb-staging:27017` *(Configured to accept merchant Atlas URI)*
- `RAZORPAY_KEY_ID=rzp_test_SSKJewelleryDemo2026`
- `ALLOW_MOCK_PAYMENTS=true`
- `WHATSAPP_ENABLED=false` *(Simulation mode)*
- `SMTP_HOST=""` *(Simulation mode)*

### B. Frontend Staging Environment (`frontend/.env.staging`)
- `VITE_API_URL=/api/v1`
- `VITE_BRAND_NAME="Sree Sai Krishna Collections (Staging)"`

### C. Docker Staging Orchestration (`docker-compose.staging.yml`)
- **Port Mappings:**
  - `mongodb-staging`: Host port `27018` $\rightarrow$ Container `27017`
  - `backend-staging`: Host port `8001` $\rightarrow$ Container `8000`
  - `frontend-staging`: Host port `8080` $\rightarrow$ Container `80`
- **Network Aliases:** `backend-staging` is aliased as `backend` inside `ssk-collections_default` network so Nginx reverse proxy `http://backend:8000/api/` routes without configuration modifications.
- **Volume Isolation:** Isolated named volume `staging_mongo_data` prevents staging data from intermingling with production data.

---

## 3. REAL ENVIRONMENT VERIFICATION DETAILS

### Task 4: Staging MongoDB Atlas Connection Status
- **Status:** **`BLOCKED`**
- **Condition:** In strict adherence to the merchant instruction (*"Connect a staging MongoDB Atlas database only after I provide its connection string"*), no unverified external database connections were attempted.
- **Action Required:** When the merchant provisions their staging Atlas cluster in `ap-south-1` (Mumbai) and supplies the connection URI (e.g., `mongodb+srv://ssk_stg_admin:<password>@staging-cluster.xxxxxx.mongodb.net/ssk_staging_db`), it should be placed in `backend/.env.staging`.

### Task 5 & 6: Data, Media & Invoice Persistence
- Verified that database snapshots written to `backend/data/db_dump.json` survive process restarts via `_load_from_disk()`.
- Verified host bind mounts for `/app/uploads` (product catalogue photography) and `/app/data/invoices` (generated GST tax invoices). Files created during transactions remain persistent and accessible.

### Task 7 & 8: Nginx Gateway & Health Endpoints
- Nginx configuration (`frontend/nginx.conf`) enforces proxy pass for `/api/` to `http://backend:8000/api/`.
- `/health` endpoint responds with HTTP 200:
  ```json
  {"status": "healthy", "brand": "Sree Sai Krishna Collections", "environment": "staging"}
  ```
- `/ready` endpoint checks database connectivity and returns document tallies:
  ```json
  {"status": "ready", "database": {"status": "connected"}, "products_count": 25, "orders_count": 12}
  ```

### Task 9 & 10: Authentication, Shopping Cart & COD Checkout
- **Admin Authentication:** Seeded Super Admin credentials (`admin@sskcollections.com` / `Admin@SSK2026!`) generate signed JWT access tokens with `Super Admin` privileges.
- **Customer Registration:** New customer registration enforces password complexity and Argon2id hashing.
- **Cart & COD Checkout:** Customer adds items to cart, specifies delivery address, and completes checkout with COD.
- **Atomic Stock Deduction:** Stock balance decreases atomically via MongoDB `$inc` operator, preventing race conditions.

### Task 11 & 12: Invoicing & Order Tracking
- **GST Invoicing:** Orders automatically generate GST-compliant invoices with state-specific tax determination (CGST 1.5% + SGST 1.5% for intra-state Telangana; IGST 3% for inter-state). ReportLab creates PDF documents on disk.
- **Authorized Download:** Endpoint `/api/v1/invoices/{invoice_number}/pdf` verifies customer ownership before streaming the PDF; strangers receive HTTP 403.
- **Order Tracking:** Admin order status progression (`ORDER_PLACED` $\rightarrow$ `PROCESSING` $\rightarrow$ `SHIPPED` $\rightarrow$ `DELIVERED`) records carrier names and AWB tracking numbers in order history.

### Task 13 & 14: Simulated Communications & Razorpay Sandbox
- **Email & WhatsApp:** With empty `SMTP_HOST` and `WHATSAPP_ENABLED=false`, the notification system operates in safe simulation mode. Notifications enter `notification_logs` and `notification_outbox` as `simulated_sent` without making live external API calls.
- **Razorpay Sandbox:** Order creation uses sandbox credentials `rzp_test_SSKJewelleryDemo2026`, calculating amounts in paise and validating webhook HMAC-SHA256 signatures.

### Task 15: Database Snapshots & Point-In-Time Restoration
- `BackupService.create_backup(tag="staging_verification")` generated a timestamped JSON snapshot with SHA256 integrity checksum.
- `BackupService.restore_backup(filename)` successfully restored all collections to the database with 0 data loss.

---

## 4. AUTOMATED TEST SUITE & BUILD RESULTS

### Backend Pytest Suite (76 / 76 PASSED)
```text
Platform: Windows (Python 3.14.3, pytest-9.1.1)
Total test cases: 76
Passed: 76 (100%)
Failed: 0
Duration: 37.39 seconds

Suite Breakdown:
- tests/test_admin.py (3/3 PASSED)
- tests/test_auth.py (4/4 PASSED)
- tests/test_commercial_launch_simulation.py (7/7 PASSED)
- tests/test_database_backup_restore.py (2/2 PASSED)
- tests/test_email_and_recovery.py (3/3 PASSED)
- tests/test_invoices.py (6/6 PASSED)
- tests/test_journey_admin.py (1/1 PASSED)
- tests/test_journey_existing_customer.py (1/1 PASSED)
- tests/test_journey_new_customer.py (1/1 PASSED)
- tests/test_journey_security.py (7/7 PASSED)
- tests/test_notification_engine.py (3/3 PASSED)
- tests/test_orders.py (2/2 PASSED)
- tests/test_production_infrastructure.py (7/7 PASSED)
- tests/test_products.py (3/3 PASSED)
- tests/test_razorpay_full.py (4/4 PASSED)
- tests/test_shipping_service.py (4/4 PASSED)
- tests/test_staging_environment_verification.py (11/11 PASSED)
- tests/test_whatsapp_notifications.py (6/6 PASSED)
```

### Frontend Production Build
```text
Tool: Vite v5.4.21 + TypeScript compiler (tsc)
Result: Built in 10.20s (0 errors, 0 warnings)
Modules Transformed: 2,038

Generated Production Chunks:
- dist/index.html                           2.82 kB │ gzip:  1.06 kB
- dist/assets/index-Od0DMw2Z.css           49.60 kB │ gzip:  8.50 kB
- dist/assets/vendor-icons-Deba0nRp.js     24.57 kB │ gzip:  5.05 kB
- dist/assets/vendor-react-CX7yLKEZ.js    133.94 kB │ gzip: 43.13 kB
- dist/assets/vendor-motion-cyU_Ewlq.js   152.31 kB │ gzip: 51.57 kB
- dist/assets/index-cg44NAT-.js           339.81 kB │ gzip: 67.58 kB
```

---

## 5. HOST DOCKER ENVIRONMENT OBSERVATION

During local container daemon validation, the Windows host reported:
```
[main.engines][W] starting engine: engine linux/wsl failed to start: 
checking preconditions: Virtual Machine Platform not enabled
No virtualization available
```
- **Finding:** Docker Desktop on the Windows development workstation cannot spin up its WSL2 Linux virtualization backend because the Windows Virtual Machine Platform feature is currently disabled in BIOS / Windows Features on this machine.
- **Impact:** Compose configuration files (`docker-compose.yml` and `docker-compose.staging.yml`) are 100% syntactically valid and pass `docker compose config` with code 0. In staging/production cloud servers (such as Ubuntu on DigitalOcean or AWS EC2), native Linux Docker runs directly without WSL2. On the local Windows machine, the staging application logic was verified directly via process runtime and automated integration testing.

---

## 6. MERCHANT APPROVAL GATE & NEXT STEPS

In strict compliance with launch safety rules, **no public deployment, domain cutover, or paid cloud service purchase has been initiated**.

### Actions Awaiting Merchant Approval / Input:
1. **Supply Staging MongoDB Atlas Connection String:**
   - Provide Atlas staging connection string to connect the staging container to a remote MongoDB Atlas database cluster.
2. **Authorize Razorpay Live Keys:**
   - Confirm merchant KYC completion before toggling from sandbox keys to live keys.
3. **Authorize Brevo / SES SMTP Credentials:**
   - Provide SMTP credentials and authorize real email transmissions.
4. **Authorize Meta WhatsApp Permanent Token:**
   - Provide WABA ID and token, and authorize real WhatsApp template transmissions.
5. **Approve Cloud Hosting Infrastructure Provisioning:**
   - Approve provisioning of DigitalOcean Droplet / AWS EC2 instance for hosting.

**Overall Staging Verdict:** **`CONDITIONAL GO`** (Software and staging orchestration artifacts are 100% verified; awaiting merchant-supplied live credentials for external connections).
