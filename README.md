# Sree Sai Krishna Collections (SSK) 👑

**A Premium E-Commerce Platform & Meesho-Inspired Seller Operating System**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss)](https://tailwindcss.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Compatible-47A248?logo=mongodb)](https://www.mongodb.com)
[![Pytest](https://img.shields.io/badge/Tests-11%20Passed-success)](https://pytest.org)

---

## 1. Executive Summary & Brand System

**Sree Sai Krishna Collections (SSK)** is a modern, full-stack Indian e-commerce platform dedicated to women's jewellery, 1-gram gold tone collections, fashion jewellery, hair accessories, and traditional bridal adornments.

The platform combines two experiences:
1. **A Customer Storefront:** Royal navy blue (`#123F7A`), premium gold (`#C89A43`), and clean white aesthetic with instant search suggestions, responsive filters, quick view modals, transparent 1-gram gold purity notices, guest/authenticated shopping bags, Razorpay online payments, and timestamped order tracking.
2. **A Seller / Staff Dashboard (Meesho Supplier Panel inspired):** A persistent navy sidebar, database-backed sales and order KPIs, SKU-level inventory adjustments with mandatory audit trails, multi-stage order fulfilment (packing, dispatch with carrier and AWB tracking numbers), return/refund review workflows, promotional coupon managers, and immutable audit logs.

### Brand Color Palette
- **Primary Navy:** `#123F7A`
- **Deep Navy:** `#082B55`
- **Royal Blue:** `#1769AA`
- **Light Blue Accent:** `#EAF3FC`
- **Premium Gold:** `#C89A43`
- **Gold Light / Dark:** `#E5B963` / `#A37728`
- **Background Grid:** `#F7F9FC`
- **Borders:** `#E4EAF2`
- **Dark Text:** `#1D2939`
- **Success / Warning / Error:** `#15803D` / `#B7791F` / `#DC2626`

### Brand Asset Architecture
The official SSK logo features navy-blue monogram lettering, gold crown and filigree accents, a royal peacock feather with turquoise and gold eye motif, and blue watercolor accents. The asset configuration is centralized at `frontend/src/assets/brand.config.ts`, enabling instant logo image replacement without modifying UI components.

---

## 2. Default Seed Accounts & Credentials

The database automatically seeds with realistic test accounts, Indian jewellery items, categories, and active coupons:

| Role | Email | Password | Access Area |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@sskcollections.com` | `Admin@SSK2026!` | All Storefront + Full Seller Admin Panel |
| **Order Manager** | `orders@sskcollections.com` | `Staff@SSK2026!` | Orders, Packing Slips, AWB Shipments, Returns |
| **Inventory Manager** | `inventory@sskcollections.com` | `Staff@SSK2026!` | Catalog, Stock Adjustments, SKU Audit Trails |
| **Customer** | `priya.sharma@example.com` | `Customer@123` | Customer Storefront, Saved Addresses, Orders |

---

## 3. Architecture & Project Layout

```text
ssk-collections/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application, CORS, routers & startup seed
│   │   ├── database.py          # Dual MongoDB/File-persisted MongoMock connector
│   │   ├── core/
│   │   │   ├── config.py        # Environment settings & secrets
│   │   │   ├── security.py      # Argon2id password hasher & JWT tokens
│   │   │   ├── permissions.py   # RBAC roles & granular permission definitions
│   │   │   └── logging.py       # Structured audit logger
│   │   ├── api/v1/
│   │   │   ├── auth.py          # Register, login, refresh token, address management
│   │   │   ├── products.py      # Catalog browse, filter, search, create, CSV export
│   │   │   ├── categories.py    # Public categories & admin category manager
│   │   │   ├── cart.py          # Real-time cart calculations, guest carts, coupons
│   │   │   ├── orders.py        # Order creation, status workflow, cancellation
│   │   │   ├── payments.py      # Razorpay order generation & HMAC-SHA256 verification
│   │   │   ├── inventory.py     # SKU stock status, auditable adjustment records
│   │   │   ├── returns.py       # Customer return review & gateway refund processing
│   │   │   ├── coupons.py       # Percentage/fixed discount engine with caps
│   │   │   ├── customers.py     # Customer summaries, product reviews & inquiries
│   │   │   ├── analytics.py     # Real calculated database KPIs & sales trends
│   │   │   └── settings.py      # Business settings & policies
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   └── seeds/seed_data.py   # Initial jewellery catalog & staff accounts
│   ├── tests/                   # 11 Automated Pytest suites (100% passing)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── assets/              # Logo SVG & brand asset configuration
│   │   ├── components/
│   │   │   ├── common/          # Reusable BrandLogo component
│   │   │   ├── layout/          # AnnouncementBar, Navbar, Footer, StorefrontLayout
│   │   │   ├── products/        # ProductCard, QuickViewModal, StarRating
│   │   │   └── admin/           # Meesho-inspired AdminLayout with Navy Sidebar
│   │   ├── pages/
│   │   │   ├── storefront/      # HomePage, ShopPage, ProductDetailPage
│   │   │   ├── checkout/        # CartPage, CheckoutPage, OrderSuccessPage
│   │   │   ├── account/         # AccountPage, OrderTrackingPage, WishlistPage
│   │   │   ├── authentication/  # LoginPage, RegisterPage, AdminLoginPage
│   │   │   └── admin/           # Dashboard, Products, Orders, Inventory, Returns, etc.
│   │   ├── context/             # AuthContext, CartContext, WishlistContext
│   │   ├── services/api.ts      # Typed API client with auto-refresh tokens
│   │   └── types/index.ts       # Full TypeScript interfaces
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 4. Key Functional Highlights

### A. Customer Storefront
- **Announcement Bar:** Genuine promotional offers (`SSKFIRST10` for 10% off) and free express shipping above ₹999.
- **Search with Live Preview:** Debounced live search querying products by name, SKU, and tags.
- **Category Browsing:** 1-Gram Gold, Antique Jhumkas, Royal Chokers, Kada Bangles, French Claw Clips, Silk Scrunchies, Bridal Hair Pins, and Vaddanam.
- **Purity & Material Transparency:** Prominent consumer notice on 1-gram gold product pages clarifying that items are micro-plated brass imitation pieces and contain no bullion or BIS hallmark claims.
- **Real Backend Pricing Engine:** Prices, discounts, delivery fees, and stock are calculated on the server. Never trusts browser input.
- **Payment Gateway Integration:** Razorpay online checkout with backend signature verification + Cash on Delivery (COD) within permitted bounds.
- **Timestamped Order Tracking:** Visual timeline of the order's journey from `ORDER_PLACED` to `DELIVERED`.

### B. Meesho-Inspired Seller Dashboard
- **Live Sales & KPI Cards:** Total orders, today's orders, awaiting processing, gross sales, discounts, refunds, net sales, active products, and low-stock alerts.
- **7-Day Sales Trend Chart:** Dynamic daily sales visualization calculated from captured order records.
- **Product Management:** Searchable catalog with status toggles, structured product addition modal with image previews, and CSV export.
- **Auditable Inventory Movements:** Every stock change requires an adjustment type (`RESTOCK`, `DAMAGED`, `AUDIT_CORRECTION`) and reason.
- **Fulfilment Pipeline:** Move orders from `ORDER_PLACED` &rarr; `PACKED` &rarr; `SHIPPED` (assigning carrier like Delhivery and tracking number) &rarr; `DELIVERED`.
- **Returns & Refunds:** Review customer return requests with reason and notes, approve doorstep reverse logistics, and process gateway refunds.

---

## 5. Local Development Setup

### Prerequisites
- Node.js v18+ and npm
- Python 3.10+
- (Optional) MongoDB 6.0+ (Backend automatically falls back to persistent mock storage if MongoDB is not running locally).

### 1. Start Backend API
```powershell
cd backend
python -m pip install -r requirements.txt
python run.py
```
*API will run at `http://127.0.0.1:8000`. Swagger documentation available at `http://127.0.0.1:8000/docs`.*

### 2. Start Frontend Web Application
```powershell
cd frontend
npm install
npm run dev
```
*Frontend will run at `http://localhost:5173`.*

---

## 6. Running Automated Tests & Builds

### Backend Pytest Suite
Run the 11 automated test cases verifying auth, products, orders, cart calculations, inventory, and admin workflows:
```powershell
cd backend
python -m pytest tests -v
```

### Frontend Production Build
Run TypeScript type-checks and Vite production bundling:
```powershell
cd frontend
npm run build
```
*(Outputs optimized, minified production assets into `frontend/dist/` with zero warnings).*

---

## 7. Docker Deployment

Deploy the entire full-stack platform (MongoDB, FastAPI backend, and Nginx-served React frontend) with a single command:
```bash
docker-compose up --build -d
```
- Customer Storefront & Seller Panel: `http://localhost:5173`
- Backend API & Swagger: `http://localhost:8000/docs`
