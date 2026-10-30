# SECURITY AUDIT REPORT (OWASP TOP 10) – SREE SAI KRISHNA COLLECTIONS

**Audit Scope:** Full Application Stack (FastAPI Backend, React Storefront, MongoDB / MongoMock, JWT Auth, Razorpay Payment Gateway, Google Sheets Integration).  
**Methodology:** OWASP Top 10 (2021/2026), OWASP API Security Top 10, Dynamic & Static Code Analysis.  
**Auditor:** Senior E-Commerce Security Auditor  

---

## 1. OWASP TOP 10 EVALUATION MATRIX

| OWASP Category | Vulnerability / Control Checked | Pre-Audit Rating | Post-Remediation Status |
|---|---|---|---|
| **A01: Broken Access Control** | IDOR on order details (`/api/v1/orders/{order_id}`) | **CRITICAL** | **RESOLVED** (Mandatory verification challenge implemented) |
| **A01: Broken Access Control** | Google Apps Script secret key template endpoint | **HIGH** | **RESOLVED** (Enforced `Super Admin` / `Admin` dependency) |
| **A01: Broken Access Control** | Cross-customer address & cart modification | **PASS** | **RESOLVED** (Enforced by JWT subject checks) |
| **A02: Cryptographic Failures** | Password storage algorithm | **PASS** | **RESOLVED** (Argon2id hashing with salt) |
| **A02: Cryptographic Failures** | Secret key leakage in frontend bundle | **PASS** | **RESOLVED** (Zero private keys found in React build) |
| **A02: Cryptographic Failures** | Payment signature comparison | **MEDIUM** | **RESOLVED** (Constant-time `hmac.compare_digest` implemented) |
| **A03: Injection** | NoSQL / MongoDB Operator Injection | **LOW** | **RESOLVED** (Pydantic schema validation blocks raw dictionary inputs) |
| **A03: Injection** | Cross-Site Scripting (XSS) via SVG Uploads | **HIGH** | **RESOLVED** (SVG format removed; raster images only) |
| **A04: Insecure Design** | Client-side cart price tampering | **PASS** | **RESOLVED** (Backend strictly recalculates all prices) |
| **A04: Insecure Design** | Negative stock and inventory race conditions | **PASS** | **RESOLVED** (Atomic `$inc` operations with $\ge 0$ boundary) |
| **A05: Security Misconfiguration** | CORS wildcard `"*"` with `allow_credentials=True` | **MEDIUM** | **RESOLVED** (Replaced with explicit trusted origins) |
| **A05: Security Misconfiguration** | Unbounded file upload size | **HIGH** | **RESOLVED** (Streamed 10MB chunked size limiter enforced) |
| **A06: Vulnerable Components** | Outdated third-party packages | **LOW** | **RESOLVED** (FastAPI 0.110+, PyJWT 2.8+, Argon2-cffi 23.1+) |
| **A07: Identification & Auth** | Pre-filled admin credentials in DOM | **HIGH** | **RESOLVED** (Demo switcher excised; state cleared) |
| **A07: Identification & Auth** | Public registration role escalation | **PASS** | **RESOLVED** (Hardcoded `Role.CUSTOMER` assignment) |
| **A08: Software & Data Integrity** | Payment verification bypass in production | **HIGH** | **RESOLVED** (Sandbox signatures gated behind environment check) |
| **A09: Logging & Monitoring** | Audit logging of critical administrative operations | **PASS** | **RESOLVED** (`AuditLogger` captures logins, stock, and orders) |
| **A10: Server-Side Request Forgery** | Google Apps Script webhook trigger | **LOW** | **RESOLVED** (Restricted to configured HTTPS webhook URLs) |

---

## 2. DETAILED VULNERABILITY ASSESSMENTS & EVIDENCE

### 2.1 IDOR on Order Endpoint (`GET /api/v1/orders/{order_id}`)
- **Vulnerability Type:** Broken Object Level Authorization (CWE-639 / BOLA)
- **Pre-Audit Behavior:**
  ```python
  # Vulnerable Code:
  @router.get("/{order_id}")
  def get_order_by_id(order_id: str, current_user: Optional[dict] = Depends(get_optional_current_user), db = Depends(get_db)):
      order = db.orders.find_one({"order_id": order_id})
      if current_user: # <--- BYPASS: If current_user is None, block was skipped!
          ...
      return order # <--- Leaked complete customer PII to anonymous requests!
  ```
- **Remediation Implemented:**
  ```python
  # Secure Code:
  if current_user:
      is_admin = current_user.get("role") in [Role.SUPER_ADMIN, Role.ADMIN, Role.ORDER_MANAGER, Role.CUSTOMER_SUPPORT]
      if not is_admin and order.get("user_id") != current_user["id"] and order.get("customer_email") != current_user.get("email"):
          raise HTTPException(status_code=403, detail="Access denied to this order")
  else:
      if not verification:
          raise HTTPException(status_code=401, detail="Authentication or customer verification required")
      # Validates verification query parameter against customer email, phone, or guest_token
      if not matches:
          raise HTTPException(status_code=403, detail="Customer verification mismatch")
  ```

### 2.2 Unauthenticated Key Disclosure in Sheets Template
- **Vulnerability Type:** Information Disclosure (CWE-200)
- **Pre-Audit Behavior:** `GET /api/v1/sheets/appscript-template` rendered the owner's `SECRET_SECURITY_KEY` without any authentication checks.
- **Remediation Implemented:** Attached `dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))]`.

### 2.3 Stored XSS via File Upload
- **Vulnerability Type:** Cross-Site Scripting (CWE-79)
- **Pre-Audit Behavior:** Allowed `.svg` files to be uploaded to `/uploads`. Statically served SVGs could embed JavaScript executed in the context of the user's session.
- **Remediation Implemented:** Excluded `.svg` from `ALLOWED_EXTENSIONS`. Allowed formats strictly limited to `{".jpg", ".jpeg", ".png", ".webp", ".gif"}`.

### 2.4 Timing Attacks on Payment Verification
- **Vulnerability Type:** Cryptographic Timing Attack (CWE-208)
- **Pre-Audit Behavior:** Evaluated string equality `generated_signature == payload.razorpay_signature`.
- **Remediation Implemented:** Replaced with Python's standard `hmac.compare_digest(generated_signature, payload.razorpay_signature)` to guarantee constant-time execution.

---

## 3. AUDIT LOGGING & SECURITY EVENT RECONCILIATION

The backend implements `AuditLogger.log_event` storing records in `db.audit_logs`:
- `CUSTOMER_REGISTRATION`: Logs timestamp, user ID, email, IP address.
- `USER_LOGIN` / `LOGIN_FAILED`: Logs authentication attempts with status and IP.
- `ORDER_CREATED`: Logs customer ID, final amount, item count.
- `ORDER_STATUS_UPDATED`: Logs staff user, old status, and new status.
- `INVENTORY_ADJUSTMENT`: Logs SKU, quantity delta, reason, and staff role.

---

## 4. SECURITY BEST PRACTICE RECOMMENDATIONS FOR HOSTING

1. **Host Environment Variables:** Never commit `.env` containing production passwords or live API keys to Git. Use Docker secrets, AWS Secrets Manager, or Doppler.
2. **Rate Limiting:** In front of the ASGI server, configure Nginx or Cloudflare WAF rate limits:
   - Max 5 failed logins per IP per 15 minutes (`/api/v1/auth/login`).
   - Max 30 requests per minute on checkout endpoints (`/api/v1/orders`).
3. **HTTP Security Headers:** Ensure the reverse proxy injects:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: SAMEORIGIN`
   - `Referrer-Policy: strict-origin-when-cross-origin`
