# BUGS AND FIXES REGISTER – SREE SAI KRISHNA COLLECTIONS (SSK)

This document provides a technical log of every bug, functional defect, and security vulnerability discovered during the production readiness audit, along with the precise fix implemented, affected files, code diffs, and verification status.

---

### BUG-01: Insecure Direct Object Reference (IDOR) on Order Endpoint
- **Severity:** CRITICAL (CVSS 8.6)
- **Module:** Orders API (`backend/app/api/v1/orders.py`)
- **Description:** `GET /api/v1/orders/{order_id}` permitted unauthenticated visitors to fetch complete order details without authorization checks because `current_user` was optional and the permission block `if current_user:` was skipped entirely when `current_user` was null. Any anonymous actor could harvest customer names, delivery addresses, phone numbers, and purchased jewellery items.
- **Affected Files:** `backend/app/api/v1/orders.py`, `frontend/src/pages/account/OrderTrackingPage.tsx`, `frontend/src/pages/checkout/OrderSuccessPage.tsx`
- **Fix Implemented:**
  1. Updated `get_order_by_id` to strictly mandate customer verification:
     - Authenticated users must own the order or have an administrative role (`Super Admin`, `Admin`, `Order Manager`, `Customer Support`).
     - Unauthenticated/guest callers must supply a matching verification token (`guest_token`, customer email, or customer telephone number) via query parameter `?verification=`.
  2. Implemented `guest_token` generation on order creation and passed it to `OrderSuccessPage`.
  3. Added interactive verification challenge form on `OrderTrackingPage.tsx` for anonymous tracking inquiries.
- **Verification Result:** PASS (`test_journey_security.py::test_security_idor_order_access_blocked_for_unauthenticated_stranger` and `test_security_idor_order_access_blocked_for_wrong_verification`).

---

### BUG-02: Private Google Apps Script Security Token Disclosure
- **Severity:** HIGH (CVSS 7.5)
- **Module:** Google Sheets Sync (`backend/app/api/v1/sheets_sync.py`)
- **Description:** Endpoint `GET /api/v1/sheets/appscript-template` lacked authentication guards (`dependencies=[Depends(require_roles([...]))]`). Any external internet crawler could query the endpoint and retrieve the business owner's private `SECRET_SECURITY_KEY`, allowing unauthorized actors to forge fake sync transactions to the owner's Google Spreadsheet.
- **Affected Files:** `backend/app/api/v1/sheets_sync.py`
- **Fix Implemented:**
  - Added strict administrative authorization:
    ```python
    @router.get("/appscript-template", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
    def get_appscript_template(db = Depends(get_db)):
    ```
- **Verification Result:** PASS (Unauthenticated access returns HTTP 401 Unauthorized).

---

### BUG-03: Hardcoded Admin 1-Click Role Switcher & Pre-filled Credentials
- **Severity:** HIGH (CVSS 7.4)
- **Module:** Admin Authentication (`frontend/src/pages/authentication/AdminLoginPage.tsx`)
- **Description:** The staff login portal included interactive buttons labeled "Quick Demo Role Switcher" that automatically injected Super Admin and Order Manager credentials into the browser DOM, and initialized component state with pre-filled administrative passwords (`useState('Admin@SSK2026!')`).
- **Affected Files:** `frontend/src/pages/authentication/AdminLoginPage.tsx`
- **Fix Implemented:**
  - Completely removed the demo role switcher button grid.
  - Cleared default credentials from React state to `email: ''`, `password: ''`.
  - Added enterprise security disclaimer and standard credential inputs.
- **Verification Result:** PASS (Clean login form confirmed; verified in build).

---

### BUG-04: Unrestricted File Size & Stored XSS Risk in Media Uploads
- **Severity:** HIGH (CVSS 7.2)
- **Module:** Uploads API (`backend/app/api/v1/upload.py`)
- **Description:**
  1. `MAX_FILE_SIZE = 10 * 1024 * 1024` was defined in code but never evaluated during file streaming. An attacker could stream gigabytes of data, causing disk exhaustion.
  2. `.svg` was included in `ALLOWED_EXTENSIONS`. Because `/uploads` was statically served, SVGs containing `<script>` or `onload` handlers could execute arbitrary JavaScript within the domain's origin (Stored XSS).
- **Affected Files:** `backend/app/api/v1/upload.py`
- **Fix Implemented:**
  - Removed `.svg` from `ALLOWED_EXTENSIONS`, restricting uploads strictly to raster formats (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`).
  - Implemented streaming chunked byte size tracking (64KB chunks). If total bytes exceed 10MB, the stream terminates immediately, partial files are deleted, and HTTP 413 Payload Too Large is raised.
- **Verification Result:** PASS (Verified in security audit).

---

### BUG-05: Missing Legal Policy & Customer Care Pages (Indian E-Commerce Compliance)
- **Severity:** HIGH (Business & Legal Blocker)
- **Module:** Storefront Routing (`frontend/src/App.tsx`, `frontend/src/components/layout/Footer.tsx`)
- **Description:** Footer links for "Returns & Refunds Policy", "Shipping & Delivery Info", and "Contact Support" pointed to `/policies` and `/contact`. Neither route existed in `App.tsx`, causing all clicks to redirect users back to the homepage. This violated the Indian Consumer Protection (E-Commerce) Rules, 2020 which mandates clear display of return/refund policies, shipping terms, and grievance redressal mechanisms.
- **Affected Files:** `frontend/src/pages/storefront/PoliciesPage.tsx`, `frontend/src/pages/storefront/ContactPage.tsx`, `frontend/src/App.tsx`
- **Fix Implemented:**
  - Created `PoliciesPage.tsx` with dedicated tabs:
    1. 7-Day Return & Replacement Policy.
    2. Domestic Shipping & Delivery Policy (₹999 free shipping threshold, ₹79 flat fee).
    3. Terms of Service with material transparency (clarifying 1-gram gold imitation plating vs solid bullion).
    4. Privacy Policy adhering to the Digital Personal Data Protection Act (DPDP).
    5. Order Cancellation Policy.
    6. Official Grievance Officer details (Secunderabad registered address, phone/WhatsApp, email, 48-hour acknowledgment, 30-day resolution).
  - Created `ContactPage.tsx` connected to `POST /api/v1/customers/contact`.
  - Registered `/policies`, `/terms`, `/privacy`, `/returns-policy`, and `/contact` in `App.tsx`.
- **Verification Result:** PASS (Vite build passed with 2035 transformed modules).

---

### BUG-06: Permissive CORS Configuration with Wildcard Credentials
- **Severity:** MEDIUM (CVSS 6.5)
- **Module:** Core Configuration (`backend/app/core/config.py`, `backend/app/main.py`)
- **Description:** `BACKEND_CORS_ORIGINS` included `"*"` alongside `allow_credentials=True`. In standard web browsers, wildcard origin with credentials is either blocked or causes dynamic origin reflection, exposing authenticated customer sessions to Cross-Origin Request Forgery.
- **Affected Files:** `backend/app/core/config.py`
- **Fix Implemented:**
  - Replaced `"*"` with explicit trusted origins:
    ```python
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://sreesaikrishnacollections.com",
        "https://www.sreesaikrishnacollections.com"
    ]
    ```
- **Verification Result:** PASS.

---

### BUG-07: Uninitialized Database on Fresh Production Deployments
- **Severity:** MEDIUM (Deployment Blocker)
- **Module:** Application Startup (`backend/app/main.py`)
- **Description:** `run_seed()` was imported in `main.py` but never called. When starting a fresh MongoDB container in Docker (`FORCE_MOCK_DB=false`), the database had 0 categories, 0 products, and 0 users, preventing store operation and admin login.
- **Affected Files:** `backend/app/main.py`
- **Fix Implemented:**
  - Added startup check in `lifespan`:
    ```python
    if db.users.count_documents({}) == 0 or db.categories.count_documents({}) == 0:
        logger.info("Empty database detected. Executing initial system seeds...")
        run_seed()
    ```
- **Verification Result:** PASS (Clean databases automatically initialize initial admin account, categories, and inventory).

---

### BUG-08: AttributeError in Hard Product Deletion
- **Severity:** MEDIUM (Functional Defect)
- **Module:** Product Admin API (`backend/app/api/v1/products.py:246`)
- **Description:** In `delete_or_archive_product`, code executed:
  `if res.matched_count == 0 and res.deleted_count == 0:`
  When `hard_delete=True`, PyMongo returns a `DeleteResult` object which has `deleted_count` but NOT `matched_count`, triggering an `AttributeError`.
- **Affected Files:** `backend/app/api/v1/products.py`
- **Fix Implemented:**
  - Separated `hard_delete` and soft-archive checks:
    ```python
    if hard_delete:
        res = db.products.delete_one(query)
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
    else:
        res = db.products.update_one(query, {"$set": {"status": "archived", "updated_at": datetime.now(timezone.utc)}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
    ```
- **Verification Result:** PASS (`test_journey_admin.py::test_admin_staff_operations_journey` passes).

---

### BUG-09: Unconditional Sandbox Payment Signature Bypass
- **Severity:** HIGH (Payment Security)
- **Module:** Payment API (`backend/app/api/v1/payments.py`)
- **Description:** `verify_razorpay_payment` unconditionally accepted `payload.razorpay_signature == "sandbox_success"`. If deployed to production without modification, anyone could mark orders as paid without transaction verification.
- **Affected Files:** `backend/app/api/v1/payments.py`, `backend/app/core/config.py`
- **Fix Implemented:**
  - Added `ENVIRONMENT: str` and `ALLOW_MOCK_PAYMENTS: bool` in `config.py`.
  - Enforced constant-time cryptographic HMAC comparison:
    ```python
    is_valid = hmac.compare_digest(generated_signature, payload.razorpay_signature)
    if not is_valid and settings.ENVIRONMENT != "production" and settings.ALLOW_MOCK_PAYMENTS:
        if payload.razorpay_signature.startswith("mock_sig_") or payload.razorpay_signature == "sandbox_success":
            is_valid = True
    ```
- **Verification Result:** PASS (`test_journey_security.py::test_security_invalid_payment_signature_rejected` passes).

---

### BUG-10: Missing SEO & Crawler Directives
- **Severity:** LOW (Marketing & Discoverability)
- **Module:** Public Web Assets (`frontend/public/`, `frontend/index.html`)
- **Description:** Missing `robots.txt` and `sitemap.xml`; `index.html` lacked meta descriptions, keywords, Open Graph social cards, and canonical links.
- **Affected Files:** `frontend/public/robots.txt`, `frontend/public/sitemap.xml`, `frontend/index.html`
- **Fix Implemented:**
  - Created standard `robots.txt` allowing public catalogue and blocking `/admin/` and `/account/`.
  - Created XML sitemap indexing all jewellery and hair accessory categories.
  - Added Open Graph / Twitter card meta tags in `index.html`.
- **Verification Result:** PASS (Verified in public build output).
