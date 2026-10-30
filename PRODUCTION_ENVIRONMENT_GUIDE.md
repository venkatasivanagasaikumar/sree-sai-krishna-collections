# Sree Sai Krishna Collections (SSK) – Production Environment Guide

This document provides a comprehensive operational manual for hosting, deploying, and maintaining the Sree Sai Krishna Collections (SSK) e-commerce platform in an enterprise production environment.

---

## 1. System Architecture Overview

```
                      +---------------------------------------+
                      |         DNS / Cloudflare CDN          |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |           Nginx Reverse Proxy         |
                      |        (SSL Termination / Gzip)       |
                      +---------------------------------------+
                                     /         \
                 /api, /docs, /uploads          Static Assets (/)
                                   /             \
                                  v               v
                +---------------------+  +---------------------+
                |   FastAPI Backend   |  |   Vite React SPA    |
                |     (Uvicorn :8000) |  |   (Dist files / Nginx)|
                +---------------------+  +---------------------+
                           |
                           v
                +---------------------+
                |   MongoDB Replica   |
                |   Set (Port 27017)  |
                +---------------------+
```

---

## 2. Server Prerequisites

- **Operating System:** Ubuntu 22.04 LTS / Debian 12 / RHEL 9 (or Windows Server 2022)
- **CPU / RAM:** Minimum 2 vCPU, 4GB RAM (Recommended: 4 vCPU, 8GB RAM)
- **Storage:** 40GB+ NVMe SSD
- **Software Dependencies:**
  - Docker Engine 24.0+ & Docker Compose v2+
  - Python 3.11+ (if running bare-metal)
  - Node.js 18+ & npm / pnpm
  - Nginx 1.22+
  - Certbot (Let's Encrypt SSL)

---

## 3. Environment Variables Reference

### Backend Configuration (`backend/.env`)

```ini
# Core Application
PROJECT_NAME="Sree Sai Krishna Collections API"
BRAND_NAME="Sree Sai Krishna Collections"
BRAND_SHORT_NAME="SSK"
ENVIRONMENT="production"                    # Set to "production" in live deployment
SECRET_KEY="<GENERATE_RANDOM_64_CHAR_HEX>"  # e.g., openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=1440            # 24 Hours
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database Configuration
FORCE_MOCK_DB=false                         # Set false for real MongoDB persistence
MONGODB_URI="mongodb://admin:SecurePass2026@mongodb:27017/ssk_collections_db?authSource=admin"
DATABASE_NAME="ssk_collections_db"

# Payment Gateway (Razorpay)
ALLOW_MOCK_PAYMENTS=false                   # Enforces strict cryptographic HMAC validation
RAZORPAY_KEY_ID="rzp_live_XXXXXXXXXXXXXX"   # Supplied from Razorpay Dashboard
RAZORPAY_KEY_SECRET="XXXXXXXXXXXXXXXXXXXX"  # Supplied from Razorpay Dashboard
RAZORPAY_WEBHOOK_SECRET="<SECURE_WEBHOOK_SECRET>"

# Transactional Email (SMTP)
SMTP_HOST="smtp.gmail.com"                  # Or smtp.sendgrid.net / email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER="orders@sreesaikrishnacollections.com"
SMTP_PASSWORD="<APP_SPECIFIC_OR_API_PASSWORD>"
SMTP_FROM_EMAIL="orders@sreesaikrishnacollections.com"
SMTP_FROM_NAME="Sree Sai Krishna Collections"
SMTP_TLS=true
FRONTEND_URL="https://sreesaikrishnacollections.com"

# Business & Logistics Rules
SUPPORT_EMAIL="support@sreesaikrishnacollections.com"
SUPPORT_PHONE="+91 98480 22338"
BUSINESS_ADDRESS="Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003, India"
FREE_SHIPPING_THRESHOLD=999.0
STANDARD_SHIPPING_FEE=79.0
ENABLE_COD=true
COD_MIN_ORDER_AMOUNT=299.0
COD_MAX_ORDER_AMOUNT=50000.0
```

### Frontend Configuration (`frontend/.env.production`)

```ini
VITE_API_URL="https://api.sreesaikrishnacollections.com/api/v1"
VITE_RAZORPAY_KEY_ID="rzp_live_XXXXXXXXXXXXXX"
VITE_BRAND_NAME="Sree Sai Krishna Collections"
VITE_STORE_TAGLINE="Exquisite 1-Gram Gold Jewellery & Bridal Accessories"
```

---

## 4. Production Deployment Using Docker Compose

The repository includes a ready-to-run multi-container setup in `docker-compose.yml`.

### Step 1: Clone & Configure
```bash
git clone https://github.com/saikumar-ssk/ssk-collections.git /var/www/ssk-collections
cd /var/www/ssk-collections
cp backend/.env.example backend/.env
# Edit backend/.env with production secrets
```

### Step 2: Build and Launch Containers
```bash
docker compose -f docker-compose.yml up -d --build
```

### Step 3: Verify Running Services
```bash
docker compose ps
```
Expected output:
```
NAME                    STATUS          PORTS
ssk-mongodb             Up (healthy)    127.0.0.1:27017->27017/tcp
ssk-backend-api         Up (healthy)    127.0.0.1:8000->8000/tcp
ssk-frontend-store      Up (healthy)    127.0.0.1:5173->80/tcp
```

---

## 5. Nginx Production Configuration & SSL Setup

Create `/etc/nginx/sites-available/sreesaikrishnacollections.com`:

```nginx
server {
    listen 80;
    server_name sreesaikrishnacollections.com www.sreesaikrishnacollections.com api.sreesaikrishnacollections.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sreesaikrishnacollections.com www.sreesaikrishnacollections.com;

    ssl_certificate /etc/letsencrypt/live/sreesaikrishnacollections.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sreesaikrishnacollections.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/www/ssk-collections/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static uploads caching
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and generate SSL certificates:
```bash
sudo ln -s /etc/nginx/sites-available/sreesaikrishnacollections.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d sreesaikrishnacollections.com -d www.sreesaikrishnacollections.com
```

---

## 6. Automated Backup & Monitoring Schedule

### Automated Nightly Database Backups
Add a cron job using `crontab -e`:

```cron
# Every night at 02:00 AM, execute snapshot backup and retain 30 days
0 2 * * * cd /var/www/ssk-collections/backend && python3 -c "from app.services.backup_service import BackupService; BackupService.create_backup(tag='nightly_auto')" >> /var/log/ssk_backup.log 2>&1
```

### Health Check Endpoint
Uptime monitoring services (e.g. BetterStack, Pingdom, UptimeRobot) should monitor:
```
GET https://sreesaikrishnacollections.com/api/v1/health
```
Expected response:
```json
{
  "status": "healthy",
  "brand": "Sree Sai Krishna Collections",
  "database": "mongodb_live",
  "products_count": 8,
  "orders_count": 14
}
```
If HTTP status is not 200 or `"status"` is not `"healthy"`, configure alert to notify engineering immediately.
