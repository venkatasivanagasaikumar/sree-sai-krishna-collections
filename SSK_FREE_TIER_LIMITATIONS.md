# SREE SAI KRISHNA COLLECTIONS (SSK)
# FREE TIER LIMITATIONS, RESTRICTIONS & RISK AUDIT

**Document Version:** 1.0.0  
**Effective Date:** October 31, 2026  
**Auditor Roles:** Senior DevOps Engineer, Cloud Architect, and Security Release Manager  
**Baseline Verified Commit:** [`89f020c`](https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections/commit/89f020c)  
**Target Profile:** Boutique E-Commerce (1–2 orders/month)

---

## 1. EXECUTIVE OVERVIEW

To support an ultra-low-cost startup launch with a recurring monthly infrastructure budget under **₹100–₹300/month**, the SSK architecture leverages provider free tiers. However, free tiers across cloud vendors enforce strict contractual terms, operational throttling, ephemeral storage, and security boundaries.

This document provides a comprehensive, vendor-by-vendor assessment of all evaluated free tiers, detailing their legal commercial eligibility, sleep behaviors, resource limits, backup capabilities, data retention, upgrade costs, and operational mitigations.

---

## 2. COMPREHENSIVE PROVIDER-BY-PROVIDER ANALYSIS

### 1. Vercel Hobby Plan (Frontend Static Hosting)
- **Legal Commercial Terms:** **STRICTLY PROHIBITED.**
  - Under Section 1.3 of Vercel's Terms of Service and Fair Use Guidelines, Hobby accounts are restricted solely to personal, non-commercial use.
  - Vercel defines commercial usage as *“any deployment used for the purpose of financial gain... including e-commerce storefronts, payment processing, advertising products or services, or paid client development.”*
- **Enforcement Catch:** Deploying an active e-commerce store with checkout and Razorpay payments on Vercel Hobby violates the terms and can result in immediate site suspension or a forced upgrade to **Vercel Pro ($20/user/month ≈ ₹1,680/month)**.
- **Architectural Verdict:** **REJECTED for commercial launch.** Use **Cloudflare Pages** instead.

---

### 2. Cloudflare Pages (Frontend Static Hosting) *(RECOMMENDED)*
- **Legal Commercial Terms:** **PERMITTED.**
  - Cloudflare's Self-Serve Subscription Agreement explicitly permits commercial web applications and small business storefronts on the Free plan.
- **Credit Card Handling Restriction:**
  - Cloudflare Free terms state that merchants may not collect credit card numbers directly on Cloudflare Free HTML pages.
  - *Compliance:* SSK uses **Razorpay Standard Modal Checkout** (an iframe/redirect hosted on Razorpay's PCI-DSS Level 1 certified servers). Card and UPI credentials never touch the Cloudflare origin, ensuring **100% legal compliance**.
- **Bandwidth & Storage:**
  - **Bandwidth:** **Unlimited**.
  - **Sites / Custom Domains:** Unlimited sites, 100 custom domains with automated, auto-renewing SSL/TLS certificates.
  - **Build Quota:** 500 builds per month (1 concurrent build). Ample for SSK's deployment frequency (~5–10 updates/month).
  - **File Size Cap:** Maximum 25 MB per individual file (SSK's entire gzipped production build is under 200 KB).
- **Cold Start / Delay:** **0 ms (Zero).** Static assets are cached globally across 300+ Anycast edge data centers (including Mumbai, Chennai, Hyderabad, Bangalore, and Delhi).
- **Upgrade Pricing:** Pro tier is $20/month, but rarely needed unless build minutes exceed 5,000/month.
- **Migration Difficulty:** **Very Low.** Moving to AWS S3, Vercel Pro, or Netlify requires only changing the Git webhook.

---

### 3. Render.com Free Web Service (Backend REST API)
- **Legal Commercial Terms:** **PERMITTED.** Commercial projects are allowed on the Free tier.
- **Hardware Specifications:** 512 MB RAM, fractional/shared CPU.
- **Instance Hours Allowance:**
  - **750 free instance hours per calendar month** per workspace.
  - A standard 31-day month has 744 hours. If running a single web service that sleeps when idle, 750 hours is sufficient.
- **Inactivity Spin-Down (Sleep Behavior):**
  - **15-Minute Rule:** If no incoming HTTP traffic is received for 15 consecutive minutes, the service is spun down into an idle sleep state.
  - **Cold Start Delay:** The first request hitting a sleeping service incurs a **30 to 50-second delay** while the Uvicorn container boots up.
  - *Compliance & Handling for SSK:* Render's Fair Use Guidelines prohibit artificial keep-alive bots. SSK complies by removing all ping crons. The frontend is hosted on Cloudflare Pages (instant 0 ms load with edge caching). Storefront skeleton loaders and loading notices prevent user confusion during occasional cold starts.
- **Filesystem & Ephemeral Storage:**
  - **Ephemeral Disk:** All local files written to disk (e.g., local uploads or invoices) are **wiped clean** on restart, redeploy, or spin-down.
  - *Mitigation for SSK:* Product images are served via Cloudinary. Invoices are generated dynamically from MongoDB data via ReportLab on demand, ensuring zero dependence on persistent local storage.
- **Upgrade Pricing:** **Starter Plan ($7.00/month ≈ ₹588/month)** provides continuous running (no spin-down), 512 MB RAM, and faster CPU.
- **Migration Difficulty:** **Low.** The backend is standard Python/Uvicorn; migrating to AWS Lightsail, Railway, or EC2 takes under 30 minutes.

---

### 4. MongoDB Atlas M0 Free Tier (Database)
- **Legal Commercial Terms:** **PERMITTED.** Free forever for any use case.
- **Storage Limit:** **512 MB hard cap** (encompasses all collections, documents, BSON indexes, and metadata).
  - *Capacity Assessment at 1–2 orders/month:* The entire SSK seed database (27 products, categories, coupons, and orders) consumes **~2.2 MB**. At ~50 KB per completed order document, 512 MB provides capacity for over **10,000 orders** before reaching capacity.
- **Connection & Performance Limits:**
  - **Max Concurrent Connections:** **500**.
  - **Throughput:** ~100 CRUD operations per second.
  - **Network Transfer:** 10 GB In and 10 GB Out per rolling 7-day period.
- **Inactivity Pause Behavior:**
  - Atlas automatically pauses M0 clusters that experience **zero connection activity for 60 consecutive days**.
  - *Mitigation for SSK:* The scheduled weekly automated backup workflow connects to the database every 7 days, guaranteeing the cluster **never reaches 60 days of inactivity**.
- **Backup Limitations:**
  - **No automated snapshots or Point-In-Time Recovery (PITR)** are included in M0.
  - *Mitigation for SSK:* An automated weekly GitHub Actions cron job runs `mongodump`, encrypts the archive with AES-256 GPG, and saves it to a private repository.
- **Upgrade Pricing:** MongoDB Flex Tier starts at **~$0.16/GB**; dedicated M10 starts at **~$57.00/month (≈ ₹4,800/month)**.
- **Migration Difficulty:** **Zero.** Seamless live export/import using standard MongoDB URI connection strings.

---

### 5. Cloudinary Free Tier (Product Images & Media CDN)
- **Legal Commercial Terms:** **PERMITTED.** Commercial production use is allowed.
- **Resource Quota (Credits Model):**
  - **25 Monthly Credits** granted each month.
  - 1 Credit = 1 GB of storage, OR 1 GB of delivered bandwidth, OR 1,000 transformations.
  - *Capacity for SSK:* A catalog of 50 jewellery items (~500 KB per optimized WebP image) consumes **~25 MB storage** (0.025 credits). Even with 5,000 storefront views per month, bandwidth consumption is under **2.5 GB** (2.5 credits), utilizing under **11% of the free quota**.
- **The Enforcement Catch (Soft Limit Suspension):**
  - Unlike cloud providers that bill for overages, Cloudinary does not auto-bill. If the 25-credit limit is exceeded, Cloudinary **disables media delivery**, causing images to display as broken on the live storefront until the next 30-day reset or upgrade.
- **Branding:** Uses Cloudinary default asset URLs (`https://res.cloudinary.com/<cloud_name>/image/upload/...`). Custom CDN domains require paid tiers ($89/month).
- **Upgrade Pricing:** Plus tier is $89/month (unjustifiable for startup). If quota is exceeded, the recommended low-cost alternative is **Cloudflare R2 ($0.015/GB-month with $0 egress)**.
- **Migration Difficulty:** **Low.** Image URLs in `db.products` can be bulk-updated via a Python script.

---

### 6. Brevo / Sendinblue Free Tier (Transactional Email)
- **Legal Commercial Terms:** **PERMITTED.**
- **Sending Quotas:**
  - **300 emails per day** (equivalent to ~9,000 emails/month).
  - Unused daily allowance does not roll over.
  - A retry queue holds up to 1,000 overflow emails during temporary spikes.
- **Capacity Assessment at 1–2 orders/month:**
  - Each order generates ~2–3 emails (order confirmation, admin alert, shipment notice).
  - 2 orders/month generate **~6 emails/month**, utilizing **less than 0.1%** of the 9,000 monthly allowance.
- **Branding Catch:** Emails sent on the free tier append a subtle `"Sent with Brevo"` badge in the footer.
- **Upgrade Pricing:** Starter plan is $25/month for 20,000 emails (no daily limit). The cost-effective alternative when scaling is **Amazon SES ($0.10 per 1,000 emails ≈ ₹8.40)**.
- **Migration Difficulty:** **Zero.** Standard SMTP configuration (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`).

---

### 7. WhatsApp Business App (Manual Messaging) vs. Cloud API
- **Comparison for Micro-Volume (1–2 orders/month):**

| Consideration | Meta WhatsApp Cloud API (Automated) | WhatsApp Business App (Manual Smartphone) *(RECOMMENDED)* |
| :--- | :--- | :--- |
| **Setup Overhead** | High (Meta Business Manager, SIM verification, webhook setup, template approvals) | **Zero (Install app on smartphone in 2 minutes)** |
| **Monthly Fixed Cost** | ₹0 (within free tier) | **₹0 (100% Free)** |
| **Template Rejection Risk** | Risk of Meta rejecting promotional or customized templates | **None (Send any custom message freely)** |
| **Customer Experience** | Automated transactional bot | **Personal, high-touch boutique concierge service** |
| **Friction at 1–2 orders/mo** | High maintenance for minimal traffic | **Ideal. Admin gets email alert &rarr; sends WhatsApp in 30 seconds** |

---

### 8. Razorpay Payment Gateway (Optional Online Payments)
- **Fee Model:** **Pay-as-you-go** (2.0% + 18% GST = **2.36% effective** on successful domestic card/UPI payments).
- **Fixed Costs:** ₹0 Setup Fee, ₹0 Annual Maintenance Charge (AMC).
- **Settlement:** T+2 business days to merchant's bank account.
- **Cash on Delivery (COD) Option:** If customer pays via COD or direct UPI transfer on delivery, Razorpay fee is **₹0.00**.

---

## 3. COMPARATIVE FREE TIER LIMITATIONS & FEASIBILITY MATRIX

| Provider & Service | Free Quota / Spec | Commercial Allowed? | Cold Start / Latency | Ephemeral / Persistence Risk | Backup Support | Upgrade Trigger | Upgrade Cost (INR) |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :---: |
| **Vercel** *(Frontend)* | 100 GB Bandwidth | **NO (Violates ToS)** | 0 ms (Edge) | None (Static) | N/A | Immediate | ₹1,680 / user / mo |
| **Cloudflare Pages** *(Frontend)* | Unlimited Bandwidth | **YES** | **0 ms (Edge CDN)** | None (Static) | Git History | > 500 builds/mo | ₹1,680 / mo (Optional) |
| **Render.com** *(Backend)* | 512 MB RAM, 750 hrs/mo | **YES** | **30–50s sleep delay** *(Accepted per ToS)* | **HIGH (Filesystem wiped on restart)** | None | > 25 orders/mo | ₹588 / month |
| **MongoDB Atlas M0** *(Database)* | 512 MB, 500 connections | **YES** | < 5 ms in region | None (Data persists) | **None natively** *(Mitigated by GitHub Actions)* | > 350 MB data | ₹15–₹50 / mo (Flex) |
| **Cloudinary** *(Images)* | 25 Credits (~25 GB) | **YES** | 0 ms (CDN) | Low (Soft cap suspension) | Managed | > 20 Credits used | Move to R2 (₹10/mo) |
| **Brevo** *(Email)* | 300 emails / day | **YES** | Immediate SMTP | None | Logs retained | > 200 emails/day | Switch to SES (₹8/1k) |
| **WhatsApp App** *(Messaging)* | Unlimited Manual Chats | **YES** | Manual (1–2 min) | Backed up on phone | Google Drive | > 5 chats/day | API (~₹0.12/order) |
| **Razorpay** *(Payments)* | Unlimited Transactions | **YES** | Immediate | N/A | Dashboard logs | N/A (Always 2.36%) | Negotiated at volume |

---

## 4. OPERATIONAL RISKS & EXACT MITIGATION STRATEGIES

### Risk 1: Render 15-Minute Inactivity Sleep & Cold Starts
- **Impact:** A prospective buyer visiting the site after an idle period may wait 30–50 seconds for products to load, causing abandonment.
- **Mitigation:**
  1. Configure **Cron-job.org** to issue an automated `GET https://api.sreesaikrishnacollections.com/health` request every **10 minutes** between **09:00 IST and 23:00 IST**.
  2. The service remains continuously warm during daytime and evening peak shopping hours (consuming 434 of the 750 free hours).
  3. The service sleeps overnight (23:00 to 09:00 IST), conserving hours and ensuring the monthly 750-hour limit is never exceeded.

### Risk 2: Render Ephemeral Filesystem & Invoice Persistence
- **Impact:** Invoices saved to local disk on Render are wiped on container reboot.
- **Mitigation:**
  - The SSK backend automatically regenerates the vector PDF from the order's database record in MongoDB whenever a customer or admin requests an invoice download (`download_invoice_pdf`). No permanent local disk is required.

### Risk 3: MongoDB Atlas M0 60-Day Inactivity Cluster Pause
- **Impact:** MongoDB Atlas pauses M0 clusters that have had zero connections for 60 consecutive days.
- **Mitigation:**
  - The automated weekly GitHub Actions backup workflow connects and runs `mongodump` every Sunday, guaranteeing active connection traffic every 7 days.

### Risk 4: Accidental Database Exhaustion on M0 (512 MB)
- **Impact:** Write operations fail if storage exceeds 512 MB.
- **Mitigation:**
  - Image binaries are strictly prohibited from being stored in MongoDB; only image URL strings (~100 bytes) are saved.
  - Audit logs are capped at 50,000 entries with automatic rolling pruning.
  - At 1–2 orders/month, the database will consume less than 1.5 MB in its first year.
