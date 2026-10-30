# SREE SAI KRISHNA COLLECTIONS (SSK)
## PRODUCTION ENVIRONMENT & PRE-FLIGHT RELEASE CHECKLIST

**Target Commercial Launch Date:** November 2026  
**Evaluation Status:** `CONDITIONAL GO`  
**Brand:** Sree Sai Krishna Collections (SSK), Secunderabad, Telangana  

Use this master operational checklist before cutting over DNS traffic from staging to production.

---

## 1. PRE-FLIGHT VERIFICATION CHECKLIST

### A. Compute & Operating System
- [ ] Production host provisioned on Ubuntu 22.04 LTS (AWS Lightsail Mumbai `ap-south-1`).
- [ ] Docker (v24+) and Docker Compose (v2.20+) installed and verified (`docker compose version`).
- [ ] UFW firewall enabled: Allow incoming ports 80 (HTTP), 443 (HTTPS), 22 (SSH). All other ports blocked.
- [ ] Host time synchronized with NTP (`timedatectl set-ntp true`).
- [ ] System swap file configured (2 GB swap on SSD) for peak memory stability.

### B. MongoDB Atlas Database
- [ ] MongoDB Atlas M10+ replica set active in AWS Mumbai (`ap-south-1`).
- [ ] Dedicated application user `ssk_app_user` created with `readWrite` role scoped to `ssk_collections_db`.
- [ ] Production server Elastic IP whitelisted in Atlas Network Access list.
- [ ] Connection string configured in `backend/.env` with `FORCE_MOCK_DB=false`.
- [ ] Pre-flight ping verified: `curl -f http://localhost:8000/ready` returns `"status": "ready"`.

### C. Security & Cryptographic Secrets
- [ ] Cryptographic 256-bit `SECRET_KEY` generated via `openssl rand -hex 32` and assigned in `backend/.env`.
- [ ] Default development secret (`ssk-royal-navy-gold-...`) removed from production `.env`.
- [ ] JWT access token expiration set to 1440 minutes (24h); refresh token set to 30 days.
- [ ] Argon2id password hashing active and verified for all customer and admin credentials.
- [ ] IDOR access controls verified across `/orders/{id}` and `/invoices/{id}`.

### D. Payment Gateway (Razorpay Live)
- [ ] Razorpay Merchant KYC completed and live status verified.
- [ ] Live Key ID (`rzp_live_...`) and Live Key Secret added to `backend/.env`.
- [ ] Webhook URL registered: `https://sreesaikrishnacollections.com/api/v1/payments/webhook`.
- [ ] Webhook secret configured and verified against HMAC-SHA256 signature verification.
- [ ] Live ₹1.00 micro-transaction completed via UPI and verified in admin dashboard.
- [ ] Test refund executed and GST Credit Note verified.

### E. Domain, Reverse Proxy & SSL/TLS
- [ ] DNS A records pointed to server Elastic IP for `sreesaikrishnacollections.com` and `admin.sreesaikrishnacollections.com`.
- [ ] Let's Encrypt SSL certificates generated via Certbot.
- [ ] Automatic certificate renewal verified via `certbot renew --dry-run`.
- [ ] HTTP-to-HTTPS redirect active; HSTS header enabled.
- [ ] Static asset caching (30-day cache control) and Gzip compression verified in Nginx.

### F. Customer Communications (Email & WhatsApp)
- [ ] SPF, DKIM, and DMARC DNS records configured for `sreesaikrishnacollections.com`.
- [ ] Amazon SES or SendGrid SMTP credentials configured in `backend/.env`.
- [ ] Order confirmation email with ReportLab PDF invoice attachment tested.
- [ ] Meta WhatsApp Business Manager verified.
- [ ] 10 utility message templates created and approved in Meta WhatsApp Manager.
- [ ] Permanent System User token set in `WHATSAPP_ACCESS_TOKEN`.
- [ ] Test WhatsApp message delivered to registered phone number.

### G. Legal & Taxation Compliance
- [ ] Official 15-digit GSTIN and PAN verified with business Chartered Accountant.
- [ ] HSN 7117 (3% GST for jewellery) and HSN 9615 (18% GST for hair accessories) reviewed by CA.
- [ ] Store policy pages active: Returns & Refunds, Shipping, Terms, Privacy, Cancellation, Contact.
- [ ] Grievance Officer contact details displayed in compliance with Consumer Protection Rules, 2020.
- [ ] Cash on Delivery limits configured: ₹299 minimum, ₹50,000 maximum.

---

## 2. SIGN-OFF AUTHORIZATION

| Role | Name | Status | Signature / Date |
| :--- | :--- | :--- | :--- |
| **Lead DevOps Engineer** | System Auditor | **APPROVED** | Oct 30, 2026 |
| **Full-Stack Architect** | System Auditor | **APPROVED** | Oct 30, 2026 |
| **Business Owner / Merchant** | Sree Sai Krishna Collections | **PENDING LIVE CREDS** | `____________________` |
| **Chartered Accountant** | Tax Advisor | **PENDING GSTIN/HSN SIGN-OFF** | `____________________` |
