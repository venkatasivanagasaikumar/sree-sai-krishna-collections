# Sree Sai Krishna Collections (SSK) – Payment Activation Guide

This guide provides step-by-step instructions for activating live Razorpay payments, generating credentials, setting up webhooks, and performing verification transactions for Sree Sai Krishna Collections.

---

## 1. Current Payment Gateway Status

- **Status:** **LIVE-READY / SANDBOX VERIFIED**
- **Test Results:** 4/4 passing automated payment integration tests (`test_razorpay_full.py`).
- **Signature Verification:** Constant-time SHA-256 HMAC cryptographic comparison active.
- **Mock Bypass:** Strictly disabled when `ENVIRONMENT=production`.
- **Default Mode:** Sandboxed until the business owner supplies verified live credentials.

---

## 2. Merchant Account Setup & KYC Verification

To accept real payments via UPI, Credit/Debit Cards, Net Banking, and Wallets in India, the business owner must complete Razorpay merchant onboarding.

### Step-by-Step KYC Checklist:

1. **Sign Up / Log In:**
   - Visit [https://dashboard.razorpay.com](https://dashboard.razorpay.com) and log in using the official business email (`saikumaryenduri7@gmail.com` or `orders@sreesaikrishnacollections.com`).
2. **Business Profile:**
   - **Business Type:** Sole Proprietorship or Partnership / Private Limited.
   - **Business Category:** Retail / E-commerce.
   - **Sub-Category:** Jewellery & Accessories / Fashion Accessories.
   - **Website URL:** `https://sreesaikrishnacollections.com`.
3. **Required Documentation:**
   - Business Owner PAN Card.
   - Aadhaar Card (front and back).
   - Business Registration Proof (GST Certificate, MSME Udyam Registration, or Trade License).
   - Cancelled Cheque / Bank Statement showing Account Holder Name, Account Number, and IFSC code for settlement.
4. **Website Compliance Verification:**
   Razorpay requires live compliance pages before activating payments. SSK Collections already provides all required legal pages:
   - Contact Us (`/contact`): Phone number, email address, physical address.
   - Terms & Conditions (`/terms`): Governing law, acceptable use.
   - Privacy Policy (`/privacy`): Data collection and protection disclosures.
   - Return & Refund Policy (`/returns-policy`): 7-day return window, damaged goods protocol, 5-7 day refund settlement.
   - Shipping Policy (`/policies`): Delivery timelines (2-4 days metro, 4-7 days domestic, ₹79 or free $\ge$ ₹999).

---

## 3. Generating Live API Credentials

Once KYC is approved (typically 24–48 hours):

1. In the Razorpay Dashboard, switch the top toggle from **Test Mode** to **Live Mode**.
2. Navigate to **Settings** &rarr; **API Keys**.
3. Click **Generate Key**.
4. Securely copy:
   - **Key ID:** Starts with `rzp_live_` (e.g., `rzp_live_X1Y2Z3A4B5C6`).
   - **Key Secret:** 24+ character secret string (shown only once).
5. **Never commit these keys to Git.** Store them directly in your production server's `backend/.env` file:
   ```ini
   RAZORPAY_KEY_ID="rzp_live_YOUR_ACTUAL_KEY_ID"
   RAZORPAY_KEY_SECRET="YOUR_ACTUAL_KEY_SECRET"
   ```

---

## 4. Setting Up Live Webhooks

Webhooks guarantee that orders are updated immediately if a customer closes their browser before the redirect completes.

1. Navigate to **Settings** &rarr; **Webhooks** in the Razorpay Dashboard.
2. Click **Add New Webhook**.
3. **Webhook URL:** `https://api.sreesaikrishnacollections.com/api/v1/payments/webhook`
4. **Secret:** Generate a random 32-character secret string (e.g., `SSKLiveWebhookSecret2026`) and paste it in `RAZORPAY_WEBHOOK_SECRET` in `backend/.env`.
5. **Alert Email:** `orders@sreesaikrishnacollections.com`.
6. **Active Events to Subscribe:**
   - `order.paid`
   - `payment.authorized`
   - `payment.captured`
   - `payment.failed`
   - `refund.processed`
7. Click **Create Webhook**.

---

## 5. First Live Verification Transaction (The ₹10 Test)

Before public announcement, conduct a live end-to-end verification order:

1. In the SSK Admin Panel, create a temporary product:
   - Name: "Live Payment Test Item"
   - Price: ₹10
   - SKU: "SSK-TEST-LIVE-001"
2. Visit the public storefront as an incognito user.
3. Add the test product to bag and proceed to checkout.
4. Pay ₹10 using UPI (Google Pay, PhonePe, or Paytm).
5. Verify that:
   - The Razorpay checkout modal shows "Sree Sai Krishna Collections" and verified green badge.
   - Payment succeeds and redirects to `/order-success/{orderId}`.
   - Order confirmation email arrives in the buyer's inbox.
   - The transaction appears in Razorpay Dashboard under **Transactions**.
   - The order appears in the SSK Admin Orders panel (`/admin/orders`) with status `PAYMENT_CONFIRMED`.
6. From the Admin Panel, process a refund for the ₹10 test order and confirm the refund receipt email arrives.
7. Archive the test product.

---

## 6. Settlement Cycles & Payouts in India

- **Standard Settlement Cycle:** $T + 2$ business days (Transactions settled on Monday are transferred to the business bank account on Wednesday morning).
- **Razorpay Early / Instant Settlements:** Available upon request to Razorpay once consistent daily volume is established.
- **GST Invoices for Fees:** Razorpay charges 2% + 18% GST on transactions. Monthly GST invoices can be downloaded under **Reports** &rarr; **Invoices** for input tax credit (ITC).
