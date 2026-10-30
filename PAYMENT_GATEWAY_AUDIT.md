# PAYMENT GATEWAY & TRANSACTION AUDIT – SREE SAI KRISHNA COLLECTIONS

**Primary Gateway:** Razorpay Payment Gateway (India)  
**Supported Currencies:** INR (₹ - Indian National Rupee)  
**Auditor:** Payment Systems & Financial QA Specialist  

---

## 1. INTEGRATION ARCHITECTURE

Sree Sai Krishna Collections employs an asynchronous, verified payment workflow to guarantee zero financial tampering:

```
[Customer Browser]
       │  1. Submit Order (COD or Razorpay)
       ▼
[SSK Backend: POST /api/v1/orders]
       │  2. Calculates subtotal, discounts, shipping server-side
       │  3. Decrements inventory atomically ($inc: -quantity)
       │  4. Sets status: PAYMENT_PENDING (or ORDER_PLACED if COD)
       ▼
[SSK Backend: POST /api/v1/payments/create-razorpay-order]
       │  5. Creates Razorpay Order with exact amount in paise (₹ * 100)
       ▼
[Razorpay Standard Checkout SDK / Modal]
       │  6. Customer completes payment via UPI / Cards / Net Banking
       │  7. Returns payment_id, order_id, signature
       ▼
[SSK Backend: POST /api/v1/payments/verify-razorpay-payment]
       │  8. HMAC-SHA256 signature verification (constant-time)
       │  9. Sets status: PAID & PAYMENT_CONFIRMED
       │ 10. Inserts transaction log into db.payments
       ▼
[Order Confirmation & Success Page]
```

---

## 2. PAYMENT METHODS AUDIT & READINESS

| Payment Method | Technical Status | Gateway Support | Commercial Readiness |
|---|---|---|---|
| **UPI Intent** (GPay, PhonePe, Paytm) | **READY** | Native Razorpay Checkout JS | Ready upon live Razorpay Key activation |
| **UPI Dynamic QR** | **READY** | Native Razorpay Checkout JS | Ready upon live Razorpay Key activation |
| **Credit & Debit Cards** | **READY** | RuPay, Visa, MasterCard, Maestro | Ready with RBI 3DS / OTP flow |
| **Net Banking** | **READY** | 50+ Indian commercial banks | Ready via Razorpay bank selector |
| **Wallets** | **READY** | Paytm, PhonePe, Mobikwik, Amazon Pay | Ready via Razorpay wallet channel |
| **Cash on Delivery (COD)** | **LIVE & ACTIVE** | In-house backend validation | **100% Production Ready** |

---

## 3. CASH ON DELIVERY (COD) CONTROL AUDIT

1. **Boundary Limits:**
   - Minimum Order Value: **₹299.00**
   - Maximum Order Limit: **₹50,000.00**
   - Evaluated and enforced server-side in `backend/app/api/v1/orders.py`. Attempts to place COD orders below ₹299 or above ₹50,000 are rejected with HTTP 400 Bad Request.
2. **Order Lifecycle for COD:**
   - Initial Order Status: `ORDER_PLACED`
   - Initial Payment Status: `PENDING_COD`
   - Automated Fulfillment: Upon status update to `DELIVERED`, payment status is automatically transitioned to `PAID`.
3. **Reconciliation:**
   - Admin orders dashboard displays payment method badges (`COD` vs `Razorpay`) and provides packing slips with explicit COD collection values.

---

## 4. PAYMENT SECURITY & INTEGRITY AUDIT

### 4.1 Server-Side Calculations (Zero Client Trust)
- The checkout payload does NOT accept item prices or totals from the frontend.
- Subtotals, coupon percentage/flat discounts, shipping eligibility, and final amounts are calculated exclusively on the backend from database records.

### 4.2 Cryptographic Signature Verification
- The signature is calculated using HMAC SHA-256:
  $$\text{Signature} = \text{HMAC-SHA256}(\text{razorpay\_order\_id} \parallel \text{"|"} \parallel \text{razorpay\_payment\_id}, \text{RAZORPAY\_KEY\_SECRET})$$
- Verified using constant-time string comparison `hmac.compare_digest` to prevent side-channel timing attacks.

### 4.3 Webhook Idempotency
- Endpoint `POST /api/v1/payments/webhook` listens for asynchronous gateway events (`payment.captured`, `payment.failed`, `refund.processed`).
- Checks `db.webhook_events` for existing `event_id` before processing, guaranteeing idempotent execution and preventing duplicate balance credits.

---

## 5. GATEWAY CONFIGURATION CHECKLIST FOR LAUNCH

Before switching the store to commercial mode:

1. **Activate Live Mode in Razorpay Dashboard:**
   - Log in to [https://dashboard.razorpay.com](https://dashboard.razorpay.com).
   - Complete business KYC, bank account linkage, and GST registration.
   - Generate **Live API Keys** (`Key Id` and `Key Secret`).
2. **Set Production Environment Variables:**
   ```bash
   RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
   ALLOW_MOCK_PAYMENTS=false
   ENVIRONMENT=production
   ```
3. **Configure Webhook Endpoint:**
   - Webhook URL: `https://sreesaikrishnacollections.com/api/v1/payments/webhook`
   - Secret: Set a dedicated webhook secret and subscribe to `order.paid`, `payment.captured`, and `refund.processed`.
