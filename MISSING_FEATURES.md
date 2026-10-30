# MISSING FEATURES & UPCOMING ROADMAP – SREE SAI KRISHNA COLLECTIONS

This document identifies all features, third-party integrations, and automated workflows that are either partially implemented, missing, or blocked pending external provider credentials.

---

## 1. BLOCKED CAPABILITIES (CONFIGURATION / CREDENTIALS REQUIRED)

### 1.1 Automated Password Reset via Email / SMS
- **Current State:** BLOCKED (Requires SMTP or SMS provider).
- **Behavior:** Users who forget their passwords currently must contact customer support (+91 98480 22338) for manual administrative assistance.
- **Requirements to Complete:**
  - Connect AWS Simple Email Service (SES), SendGrid, or Postmark API keys.
  - Or connect an Indian DLT-compliant SMS gateway (Fast2SMS, MSG91, Twilio) for 6-digit OTP verification.
  - Implement endpoints `POST /api/v1/auth/forgot-password` and `POST /api/v1/auth/reset-password`.

### 1.2 Live Carrier Automated AWB Generation
- **Current State:** PARTIAL (Manual AWB assignment active).
- **Behavior:** Store staff manually book parcel consignments on courier portals (Delhivery, Shiprocket, DTDC), then input the carrier name and AWB tracking number into the SSK seller panel (`/admin/orders`). Customers can view the AWB and track the parcel.
- **Requirements to Automate:**
  - Integrate Shiprocket REST API or Delhivery Express API.
  - Implement automated pickup request generation, shipping label PDF generation, and automated reverse pickup on return approvals.

### 1.3 Razorpay Live Merchant Mode
- **Current State:** BLOCKED (Sandbox test keys active).
- **Behavior:** The application loads the Razorpay Standard Checkout SDK and supports full simulation and testing.
- **Requirements to Go Live:**
  - Business KYC completion on Razorpay merchant portal.
  - Replacement of `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` with live merchant credentials in production `.env`.

---

## 2. RECOMMENDED POST-LAUNCH ENHANCEMENTS

### 2.1 WhatsApp Automated Order Notifications
- Integrate the WhatsApp Business Cloud API (Interakt, Wati, or official Meta Graph API) to send automated parcel dispatch updates and delivery confirmations directly to the customer's phone number.

### 2.2 Pincode Serviceability & Cash-On-Delivery Check Widget
- Add a PIN code validator on the single product page (`ProductDetailPage.tsx`) where shoppers can enter their 6-digit PIN code to verify delivery speed (2-4 days vs 4-7 days) and COD eligibility before adding to bag.

### 2.3 Customer Image Upload on Reviews
- Frontend review submission form currently accepts star rating, title, and comments. Enable direct image attachment for customer reviews via `POST /api/v1/upload`.

### 2.4 Multi-Factor Authentication (MFA) for Administrative Staff
- Implement TOTP (Time-Based One-Time Password) using Google Authenticator / Microsoft Authenticator for the `Super Admin` and `Order Manager` roles.
