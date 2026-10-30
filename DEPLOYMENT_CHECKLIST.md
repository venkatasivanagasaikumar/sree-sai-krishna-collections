# PRODUCTION DEPLOYMENT & LAUNCH CHECKLIST

**Target Environment:** Linux VPS / Cloud VM (Ubuntu 22.04 LTS / 24.04 LTS) or Container Service (AWS ECS, DigitalOcean App Platform, Render)  
**Architecture:** Docker Compose (MongoDB, FastAPI ASGI Backend, Nginx + React Frontend)  
**Domain:** `sreesaikrishnacollections.com`  

---

## 1. PRE-DEPLOYMENT ENVIRONMENT VARIABLES

Create a secure `.env` file in `/backend/.env` with the following production values:

```ini
# Core Configuration
ENVIRONMENT=production
PROJECT_NAME="Sree Sai Krishna Collections API"
BRAND_NAME="Sree Sai Krishna Collections"
BRAND_SHORT_NAME="SSK"
SECRET_KEY="<GENERATE_64_CHAR_HEX_ENTROPY_KEY>"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database Configuration (MongoDB Atlas or Replica Set)
MONGODB_URI="mongodb+srv://<DB_USER>:<DB_PASS>@ssk-cluster.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME="ssk_collections_prod"
FORCE_MOCK_DB=false

# Payments (Live Razorpay Merchant Keys)
RAZORPAY_KEY_ID="rzp_live_xxxxxxxxxxxxxx"
RAZORPAY_KEY_SECRET="xxxxxxxxxxxxxxxxxxxxxxxx"
ALLOW_MOCK_PAYMENTS=false
ENABLE_COD=true
COD_MIN_ORDER_AMOUNT=299.0
COD_MAX_ORDER_AMOUNT=50000.0
FREE_SHIPPING_THRESHOLD=999.0
STANDARD_SHIPPING_FEE=79.0

# Store Contact & Registration
SUPPORT_EMAIL="support@sreesaikrishnacollections.com"
SUPPORT_PHONE="+91 98480 22338"
BUSINESS_ADDRESS="Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003, India"
```

In `/frontend/.env.production`:
```ini
VITE_API_URL="https://sreesaikrishnacollections.com/api/v1"
```

---

## 2. PRODUCTION LAUNCH STEP-BY-STEP PROCEDURE

### Step 1: Server Provisioning
- Update Ubuntu system packages: `sudo apt update && sudo apt upgrade -y`
- Install Docker & Docker Compose: `sudo apt install docker.io docker-compose -y`
- Configure firewall (UFW):
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```

### Step 2: SSL / TLS Certificate (Let's Encrypt / Certbot)
- Issue Let's Encrypt certificate for `sreesaikrishnacollections.com` and `www.sreesaikrishnacollections.com`.
- Configure automated auto-renewal cronjob (`certbot renew --quiet`).

### Step 3: Container Deployment
- Clone the production branch:
  ```bash
  git clone https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections.git
  cd sree-sai-krishna-collections
  ```
- Build and spin up containers:
  ```bash
  docker-compose up -d --build
  ```
- Verify health check:
  ```bash
  curl -I https://sreesaikrishnacollections.com/api/v1/health
  ```
  Expected output: `HTTP/1.1 200 OK` with JSON `{"status": "healthy", "database": "mongodb_live"}`.

### Step 4: Initial Super Admin Setup
- Check that seed data has populated the default categories and products.
- Log in to `/admin/login` using the initial credentials.
- **IMMEDIATE POST-DEPLOY ACTION:** Navigate to `/account` or `/admin/settings` and change the initial administrative password to a unique, non-shared enterprise passphrase.

---

## 3. ROLLBACK PROCEDURE

In the event of an unrecoverable failure during deployment:

1. **Revert to Previous Docker Tag:**
   ```bash
   docker-compose down
   git checkout tags/v1.0.0-stable
   docker-compose up -d --build
   ```
2. **Restore Database from Backup:**
   ```bash
   mongorestore --uri="$MONGODB_URI" --drop /backups/latest/
   ```
3. **Verify Integrity:**
   - Execute health check and run `python -m pytest tests -v`.
