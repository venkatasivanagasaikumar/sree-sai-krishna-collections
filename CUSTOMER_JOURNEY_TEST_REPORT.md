# CUSTOMER JOURNEY & AUTOMATED E2E TEST REPORT

**Test Suite:** Pytest + FastAPI Test Runner  
**Total Tests:** 22 Automated Tests  
**Passing:** 22 (100% Pass Rate)  
**Execution Duration:** 7.81s  
**Test Coverage:** Customer Storefront, Existing Customer Account, Admin Seller Operations, and OWASP Security Controls.  

---

## 1. AUTOMATED TEST EXECUTION SUMMARY

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.7.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\saiku\.gemini\antigravity\scratch\ssk-collections\backend
plugins: anyio-4.12.1
collecting ... collected 22 items

tests/test_admin.py::test_admin_dashboard_kpis PASSED                    [  4%]
tests/test_admin.py::test_order_status_progression PASSED                [  9%]
tests/test_admin.py::test_inventory_adjustment PASSED                    [ 13%]
tests/test_auth.py::test_customer_registration_and_login PASSED          [ 18%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 22%]
tests/test_auth.py::test_address_management PASSED                       [ 27%]
tests/test_journey_admin.py::test_admin_staff_operations_journey PASSED  [ 31%]
tests/test_journey_existing_customer.py::test_existing_customer_multi_item_and_payment_journey PASSED [ 36%]
tests/test_journey_new_customer.py::test_new_customer_full_journey PASSED [ 40%]
tests/test_journey_security.py::test_security_idor_order_access_blocked_for_unauthenticated_stranger PASSED [ 45%]
tests/test_journey_security.py::test_security_idor_order_access_blocked_for_wrong_verification PASSED [ 50%]
tests/test_journey_security.py::test_security_cross_customer_order_access_blocked PASSED [ 54%]
tests/test_journey_security.py::test_security_role_escalation_on_public_registration_prevented PASSED [ 59%]
tests/test_journey_security.py::test_security_customer_cannot_access_admin_role_checker PASSED [ 63%]
tests/test_journey_security.py::test_security_cart_price_tampering_prevented PASSED [ 68%]
tests/test_journey_security.py::test_security_invalid_payment_signature_rejected PASSED [ 72%]
tests/test_journey_security.py::test_security_inventory_negative_stock_prevented PASSED [ 77%]
tests/test_orders.py::test_cart_calculation_with_coupon PASSED           [ 81%]
tests/test_orders.py::test_create_and_cancel_order PASSED                [ 86%]
tests/test_products.py::test_list_and_search_products PASSED             [ 90%]
tests/test_products.py::test_product_detail PASSED                       [ 95%]
tests/test_products.py::test_create_duplicate_sku_rejected PASSED        [100%]

============================= 22 passed in 7.81s ==============================
```

---

## 2. DETAILED USER JOURNEY BREAKDOWN

### Journey 1: New Customer Onboarding to Order Completion (`test_journey_new_customer.py`)
1. **Registration:** Customer account created with valid email, phone number, and password hashed with Argon2id.
2. **Authentication:** Valid credentials exchange for JWT access and refresh token.
3. **Catalog Exploration:** Customer filters catalogue by "1-Gram Gold Jewellery" and retrieves active items.
4. **Search Verification:** Queries "Jhumka" and receives accurate keyword-matched products.
5. **Product Detail View:** Retrieves SKU `SSK-JWL-101`, verifying price (₹1899), images, reviews, and related items.
6. **Cart Add & Increment:** Adds 1 item, then increments quantity to 2; subtotal properly updates to ₹3798.
7. **Coupon Application:** Applies `SSKFIRST10` (10% discount). Server correctly enforces ₹300 maximum cap.
8. **Free Shipping Meter:** Since subtotal ($3798) exceeds ₹999, shipping fee is evaluated to ₹0.00.
9. **Address Creation:** Adds delivery address in Hyderabad, Telangana (PIN 500081).
10. **Order Creation (COD):** Submits order with Cash on Delivery; stock atomically decrements by 2.
11. **Order Tracking:** Fetches order timeline, verifying status `ORDER_PLACED` and payment status `PENDING_COD`.
- **Verdict:** **PASS (100% Verified)**

---

### Journey 2: Existing Customer Multi-Product & Online Payment (`test_journey_existing_customer.py`)
1. **Existing User Login:** Logs in seed customer Priya Sharma (`priya.sharma@example.com`).
2. **Multi-Item Add:** Adds 2 Temple Jhumkas (`SSK-JWL-102` @ ₹799) and 1 Hair Claw Clip (`SSK-HAIR-201` @ ₹349).
3. **Subtotal Calculation:** Subtotal accurately computes to $1598 + 349 = ₹1947.00.
4. **Item Removal:** Removes Hair Claw Clip; cart subtotal automatically drops to ₹1598.00.
5. **Quantity Decrement & Shipping Fee:** Decrements Jhumkas to 1 ($799); subtotal drops below ₹999, so standard ₹79 shipping fee is automatically applied (Final: ₹878.00).
6. **Razorpay Order Creation:** Backend generates Razorpay order for 87,800 paise (₹878.00).
7. **Payment Signature Verification:** Simulates successful gateway capture with valid signature; status transitions to `PAID` / `PAYMENT_CONFIRMED`.
8. **Packing Slip Generation:** Admin packing slip renders brand address, item details, and customer shipping notes.
- **Verdict:** **PASS (100% Verified)**

---

### Journey 3: Admin Catalog, Inventory & Logistics Operations (`test_journey_admin.py`)
1. **Administrative Login:** Super Admin logs in and receives administrative JWT token.
2. **Dashboard KPIs:** Verifies gross sales, net sales, order counts, and 7-day sales trend series.
3. **Product Creation:** Creates new 1-Gram Gold Emerald Bridal Choker (`SSK-TEST-JWL-999`).
4. **Storefront Reflection:** Product is immediately searchable and visible on customer storefront.
5. **Inventory Movement:** Adjusts stock by +5 consignment units; logged in `db.inventory_movements`.
6. **Order Dispatch & Logistics:** Fulfills incoming order, assigns Delhivery carrier name and AWB tracking number (`DEL9848022338IN`).
7. **CSV Export:** Generates standardized CSV export of complete store catalog.
8. **Google Sheets Sync Payload:** Exports unified JSON containing products, orders, customers, and inventory movements.
- **Verdict:** **PASS (100% Verified)**

---

### Journey 4: OWASP Security & Access Control Enforcement (`test_journey_security.py`)
1. **IDOR Block:** Unauthenticated stranger cannot query orders without verification token (HTTP 401).
2. **Verification Mismatch Block:** Supplying incorrect email/phone returns HTTP 403 Forbidden.
3. **Cross-Customer Isolation:** Customer A cannot view Customer B's order.
4. **Privilege Escalation Prevention:** Public registration cannot inject staff or admin roles.
5. **RBAC Guard:** Regular customer calling administrative functions is rejected with HTTP 403.
6. **Price Tampering Prevention:** Client-modified unit prices in cart payload are discarded; server calculates actual prices from MongoDB.
7. **Cryptographic Signature Verification:** Tampered Razorpay signatures are rejected with HTTP 400.
8. **Negative Stock Prevention:** Manual inventory adjustments cannot drive product stock below 0.
- **Verdict:** **PASS (100% Verified)**
