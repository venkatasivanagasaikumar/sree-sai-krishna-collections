# SREE SAI KRISHNA COLLECTIONS (SSK)
## RAZORPAY LIVE ACTIVATION & PAYMENT GATEWAY PRODUCTION RUNBOOK

**Target Gateway:** Razorpay Payment Gateway (Standard Checkout + Server-to-Server Webhooks)  
**Supported Methods:** UPI (Google Pay, PhonePe, Paytm), Credit/Debit Cards (Visa, MasterCard, RuPay), Net Banking, Cash on Delivery (COD)  
**Currency:** Indian Rupee (`INR`)  
**Compliance:** RBI e-Mandate & Tokenization Guidelines, Section 31 CGST Act  

---

## 1. PRE-FLIGHT MERCHANT KYC & ACCOUNT ACTIVATION

Before live credentials can be issued, the business owner must complete legal merchant onboarding on the [Razorpay Dashboard](https://dashboard.razorpay.com/):

```
+-------------------------------------------------------------------------------+
| REQUIRED MERCHANT ONBOARDING DOCUMENTS (INDIA)                                |
+-------------------------------------------------------------------------------+
| 1. Business Registration Certificate / Sole Proprietorship Registration / GST |
| 2. Business PAN Card (Matching SELLER_PAN in backend configuration)           |
| 3. Authorized Signatory / Owner PAN & Aadhaar                                 |
| 4. Bank Account Verification (Cancelled Cheque or Bank Statement)             |
| 5. Operational Website URLs containing mandatory legal policies:              |
|    - About Us & Contact Info: https://sreesaikrishnacollections.com/contact   |
|    - Terms of Service: https://sreesaikrishnacollections.com/policies         |
|    - Privacy Policy: https://sreesaikrishnacollections.com/policies           |
|    - Return & Refund Policy: https://sreesaikrishnacollections.com/policies   |
|    - Shipping & Delivery Policy: https://sreesaikrishnacollections.com/policies
+-------------------------------------------------------------------------------+
```

---

## 2. GENERATING LIVE API KEYS

1. Log into [Razorpay Dashboard](https://dashboard.razorpay.com/).
2. In the top navigation bar, toggle the mode switch from **Test Mode** to **Live Mode**.
3. Navigate to **Settings &rarr; API Keys**.
4. Click **Generate Key**.
5. Save both values securely:
   - **Key ID:** Starts with `rzp_live_` (e.g. `rzp_live_1A2B3C4D5E6F7G`).
   - **Key Secret:** 24–32 character alphanumeric string.
6. **SECURITY WARNING:** The Key Secret is displayed **only once**. Store it in a secure password manager. **Never commit the Key Secret to Git.**

---

## 3. CONFIGURING THE LIVE WEBHOOK

Razorpay sends asynchronous server-to-server HTTP POST notifications for critical payment events. Configuring this webhook is mandatory to ensure that orders are marked paid even if the customer accidentally closes their mobile browser after completing a UPI pin payment.

1. In Razorpay Dashboard (Live Mode), navigate to **Settings &rarr; Webhooks**.
2. Click **Add New Webhook**.
3. **Webhook URL:**
   ```
   https://sreesaikrishnacollections.com/api/v1/payments/webhook
   ```
4. **Secret:** Generate a 24-character random alphanumeric secret (e.g., `ssk_live_wh_sec_2026_x9a8b7`).
5. **Active Events to Select:**
   - [x] `payment.captured` *(Triggered when customer payment successfully settles)*
   - [x] `payment.failed` *(Triggered when bank/UPI server rejects transaction)*
   - [x] `order.paid` *(Triggered when order amount is fully satisfied)*
   - [x] `refund.processed` *(Triggered when admin refund completes)*
6. Click **Save Webhook**.

---

## 4. SERVER CONFIGURATION (`backend/.env`)

Update the production `backend/.env` with live credentials:

```ini
# ==============================================================================
# RAZORPAY LIVE PRODUCTION CONFIGURATION
# ==============================================================================
RAZORPAY_KEY_ID=rzp_live_REPLACE_WITH_YOUR_ACTUAL_KEY_ID
RAZORPAY_KEY_SECRET=REPLACE_WITH_YOUR_ACTUAL_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET=REPLACE_WITH_THE_WEBHOOK_SECRET_YOU_ENTERED_IN_RAZORPAY
ALLOW_MOCK_PAYMENTS=false

# Cash on Delivery Configuration
ENABLE_COD=true
COD_MIN_ORDER_AMOUNT=299.0
COD_MAX_ORDER_AMOUNT=50000.0
FREE_SHIPPING_THRESHOLD=999.0
STANDARD_SHIPPING_FEE=79.0
```

---

## 5. CONTROLLED LIVE TRANSACTION VERIFICATION PROCEDURE

Once live keys are saved and the backend is restarted (`docker compose restart backend`), execute this exact single-transaction test to verify live processing before opening the store to the public:

### Step 1: Create a Low-Value Test Product
In the Admin Dashboard (`/admin/products`), create a temporary hidden item:
- **Title:** `Live Payment Test Item`
- **SKU:** `SSK-TEST-LIVE-01`
- **Price:** ₹1.00 (Minimum allowable Razorpay transaction)
- **Stock:** 5

### Step 2: Complete Checkout via UPI
1. Open the storefront on a mobile smartphone: `https://sreesaikrishnacollections.com`.
2. Add `Live Payment Test Item` to cart and proceed to Checkout.
3. Select **Online Payment (Cards / UPI / Net Banking)**.
4. When the Razorpay popup opens, select **UPI** and complete the ₹1.00 payment via Google Pay or PhonePe.

### Step 3: Verify Automated Order Mechanics
Verify the following 6 actions occur automatically in real time:
1. Razorpay displays the green success checkmark and redirects to `/order-success/{order_id}`.
2. In the Admin Panel (`/admin/orders`), the order status is **`PAYMENT_CONFIRMED`** and payment status is **`PAID`**.
3. Sourced item stock is decremented from 5 to 4.
4. Tax invoice `SSK-INV-2026-XXXX` is generated automatically and downloadable as a vector PDF.
5. The order confirmation email is received with the invoice PDF attached.
6. The customer receives a WhatsApp confirmation message.

### Step 4: Verify Live Refund
1. In the Admin Dashboard (`/admin/orders`), open the test order details.
2. Click **Process Refund**. Enter amount: `1.00`, Reason: `Live cutover test refund`.
3. Confirm refund.
4. Verify that:
   - Order payment status transitions to **`REFUNDED`**.
   - An official GST Credit Note `SSK-CN-2026-XXXX` is issued.
   - The ₹1.00 is refunded back to the customer's UPI account.

### Step 5: Clean Up
Deactivate the `SSK-TEST-LIVE-01` product in the admin catalog. The payment gateway is now certified for full commercial launch.
