# SREE SAI KRISHNA COLLECTIONS (SSK)
## MONGODB ATLAS PRODUCTION DEPLOYMENT & DATABASE ARCHITECTURE GUIDE

**Target Environment:** Production Managed Database (MongoDB Atlas)  
**Database Name:** `ssk_collections_db`  
**Compliance & SLA:** High Availability Multi-AZ Replica Set, Continuous Point-in-Time Recovery, TLS 1.3  

---

## 1. CLUSTER PROVISIONING SPECIFICATIONS

### Recommended Cluster Tier
- **Tier:** **M10** (General Purpose) or higher.
  - *RAM:* 2 GB.
  - *Storage:* 10 GB to 80 GB Auto-expanding NVMe SSD.
  - *vCPU:* 1 vCPU (burstable to 2).
  - *Backups:* Continuous Cloud Backups (7-day point-in-time recovery).
- *Free Tier (M0) Note:* M0 Sandbox tier lacks VPC peering, custom network isolation, and point-in-time restores; it is strictly disallowed for commercial transactions in production.

### Cloud Provider & Region Selection
- **Cloud Provider:** **Amazon Web Services (AWS)**.
- **Region:** **`ap-south-1` (Asia Pacific - Mumbai)**.
- **Latency Advantage:** Placing the database in Mumbai delivers single-digit millisecond latency (< 15ms) to Indian consumers across Hyderabad, Secunderabad, Bengaluru, Chennai, Mumbai, and Delhi.

---

## 2. STEP-BY-STEP ATLAS SETUP PROCEDURE

### Step 1: Create Organization and Project
1. Log into [MongoDB Cloud](https://cloud.mongodb.com/).
2. Create an Organization named `Sree Sai Krishna Collections`.
3. Create a Project named `SSK-Production`.

### Step 2: Build the Database Cluster
1. Click **Create** &rarr; Select **Dedicated** &rarr; Tier **M10**.
2. Select **AWS** as the Cloud Provider.
3. Select Region: **Mumbai (`ap-south-1`)**.
4. Set Cluster Name: `ssk-prod-cluster`.
5. Under Additional Settings:
   - MongoDB Version: **7.0 (Current Stable)**.
   - Storage Auto-Expansion: **Enabled**.
   - Cloud Backup: **Enabled** (Continuous).
6. Click **Create Cluster** (takes ~5–7 minutes to provision).

---

## 3. SECURITY & ACCESS CONTROL

### A. Least-Privilege Database User Creation
Never connect the application as an administrative superuser (`atlasAdmin`). Create a dedicated application service user:

1. In MongoDB Atlas, navigate to **Security &rarr; Database Access**.
2. Click **Add New Database User**.
3. **Authentication Method:** Password (SCRAM-SHA-256).
4. **Username:** `ssk_app_user`.
5. **Password:** Generate a 32-character random string (e.g. `Xk9#mP2$vL7!qR4@wT8*yN1&zB5^sF3(`).
6. **Database User Privileges:**
   - Select **Built-in Role** &rarr; Select **Specific Privileges**.
   - Assign Role: `readWrite`.
   - Database: `ssk_collections_db`.
7. Click **Add User**.

### B. Network Access & IP Whitelisting
1. In MongoDB Atlas, navigate to **Security &rarr; Network Access**.
2. Click **Add IP Address**.
3. Select **Add Current IP Address** or enter the **Elastic IP** of your production Linux application server (e.g., `13.234.xx.xx/32`).
4. Set Comment: `SSK Production Application Server (AWS Mumbai)`.
5. **CRITICAL SECURITY RULE:** Never select `0.0.0.0/0` (Allow Access from Anywhere) in production. Restrict ingress strictly to the application server and authorized developer VPNs.

---

## 4. CONNECTION STRING CONFIGURATION

1. In MongoDB Atlas, navigate to **Database Deployments** &rarr; Click **Connect**.
2. Choose **Drivers** &rarr; Driver: **Python**, Version: **3.11 or later**.
3. Copy the Standard SRV connection string:
   ```
   mongodb+srv://ssk_app_user:<password>@ssk-prod-cluster.xxxxxx.mongodb.net/ssk_collections_db?retryWrites=true&w=majority
   ```
4. Configure this connection string in `backend/.env` on the production server:
   ```ini
   # Production Database Configuration
   ENVIRONMENT=production
   FORCE_MOCK_DB=false
   MONGODB_URI="mongodb+srv://ssk_app_user:REPLACE_WITH_STRONG_PASSWORD@ssk-prod-cluster.xxxxxx.mongodb.net/ssk_collections_db?retryWrites=true&w=majority"
   DATABASE_NAME=ssk_collections_db
   DB_MAX_POOL_SIZE=100
   DB_MIN_POOL_SIZE=10
   DB_MAX_IDLE_TIME_MS=45000
   DB_SERVER_SELECTION_TIMEOUT_MS=5000
   DB_CONNECT_TIMEOUT_MS=10000
   DB_SOCKET_TIMEOUT_MS=20000
   DB_TLS=true
   ```

---

## 5. CONNECTION VERIFICATION & INDEX ENFORCEMENT

Upon application startup, `backend/app/database.py` automatically initializes connection pooling, verifies cluster reachability with `ping`, and executes `_create_indexes()`.

### Automated Production Indexes Verified
The application enforces unique constraints and compound query indexes across 12 collections:

| Collection | Indexed Field(s) | Constraint Type | Purpose / Query Optimization |
| :--- | :--- | :--- | :--- |
| `users` | `email` | **Unique** | Fast authentication & duplicate prevention |
| `users` | `role` | Standard | RBAC permission filtering |
| `products` | `sku` | **Unique** | Inventory item identification |
| `products` | `category`, `status` | Standard | Catalog navigation & active item queries |
| `products` | `("category", 1), ("price", 1)` | Compound | Filtered catalog sorting by price |
| `orders` | `order_id` | **Unique** | Order lifecycle retrieval & security |
| `orders` | `user_id`, `customer_email` | Standard | Customer order history portal |
| `orders` | `created_at` (Descending) | Standard | Admin order fulfillment queue |
| `invoices` | `invoice_number` | **Unique** | GST legal document sequential numbering |
| `invoices` | `order_id`, `user_id` | Standard | Customer invoice PDF download checks |
| `coupons` | `code` | **Unique** | Promo code validation & deduplication |
| `webhook_events` | `event_id` | **Unique** | Razorpay / Carrier webhook idempotency |
| `communication_consents` | `consent_id` | **Unique, Sparse** | DPDP Act / TRAI consent compliance logs |

### Verification Command
Run the readiness probe from the production server terminal:
```bash
curl -f http://localhost:8000/ready
```
**Expected Response:**
```json
{
  "status": "ready",
  "environment": "production",
  "database": {
    "status": "connected",
    "type": "mongodb_live",
    "database": "ssk_collections_db"
  },
  "products_count": 28,
  "orders_count": 0
}
```

---

## 6. BACKUP, RESTORE & POINT-IN-TIME RECOVERY

### A. Automated Atlas Cloud Backups (Primary Recovery)
- Atlas M10+ automatically captures point-in-time snapshots every 6 hours and maintains transactional oplogs for 7 days.
- **To Restore:** Go to **Database Deployments &rarr; Backup &rarr; Restore Snapshot**, select the target timestamp, and restore directly to a staging or production cluster.

### B. Application-Level JSON Snapshot Backups (Secondary Disaster Recovery)
In addition to cloud snapshots, the SSK backend includes an automated snapshot utility `DatabaseBackupService` with SHA-256 checksum validation:

```bash
# Execute snapshot from terminal (or scheduled daily via cron):
python -c "from app.services.backup_service import BackupService; print(BackupService.create_backup(tag='daily_prod'))"
```
- Snapshots are written to `backend/data/backups/ssk_backup_YYYYMMDD_HHMMSS_daily_prod.json`.
- Backups record collections count, document counts, and SHA-256 cryptographic hashes for tamper detection.

### C. Manual Restore Command
```bash
# To restore from an application snapshot:
python -c "from app.services.backup_service import BackupService; print(BackupService.restore_backup('ssk_backup_YYYYMMDD_HHMMSS_daily_prod.json'))"
```
