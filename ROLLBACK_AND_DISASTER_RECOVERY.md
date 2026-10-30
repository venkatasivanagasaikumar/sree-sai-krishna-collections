# SREE SAI KRISHNA COLLECTIONS (SSK)
## ROLLBACK PROCEDURES & DISASTER RECOVERY PLAYBOOK

**Document Version:** 1.0.0  
**RTO (Recovery Time Objective):** < 15 minutes  
**RPO (Recovery Point Objective):** < 6 hours (Continuous oplog with MongoDB Atlas)  

---

## 1. INSTANT APPLICATION ROLLBACK PROCEDURE

If a newly deployed release introduces an unexpected defect, regression, or UI breakage, execute this immediate rollback procedure:

### Step 1: Identify Last Known Stable Git Commit
```bash
cd /opt/ssk-collections
git log --oneline -n 5
```
Example output:
```
1ce2836 (HEAD -> main) feat: update checkout animation
265e614 feat: complete end-to-end launch simulation  <-- [TARGET STABLE COMMIT]
1c02fb4 feat: invoice generation and whatsapp
```

### Step 2: Roll Back Source Code
```bash
git checkout 265e614
```

### Step 3: Rebuild and Restart Containers
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Step 4: Validate Restored State
```bash
# Verify health probe returns HTTP 200
curl -f http://localhost:8000/health
curl -f http://localhost:8000/ready
```
*Total Elapsed Time: < 3 minutes.*

---

## 2. DATABASE DISASTER RECOVERY SCENARIOS

### SCENARIO A: Unintended Data Corruption or Deletion
*Example: Accidental bulk deletion of products or corrupt inventory updates.*

#### Recovery Method: MongoDB Atlas Point-in-Time Restore (Recommended)
1. Log into [MongoDB Cloud](https://cloud.mongodb.com/).
2. Select Cluster **`ssk-prod-cluster`** &rarr; Navigate to **Backup**.
3. Click **Restore** &rarr; Select **Point in Time**.
4. Choose the exact timestamp (e.g. 5 minutes prior to the corrupting event).
5. Choose destination: Restore directly to production or restore to a temporary test cluster to export affected documents.

---

### SCENARIO B: Host Server Catastrophic Failure / Disk Crash
*Example: Cloud VPS crashes, terminates unexpectedly, or hardware failure occurs.*

#### Recovery Method: Restoring from Scheduled JSON Snapshot
1. Provision a new server instance (Ubuntu 22.04 LTS).
2. Clone repository:
   ```bash
   git clone https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections.git /opt/ssk-collections
   cd /opt/ssk-collections
   ```
3. Copy the latest backup snapshot file (`ssk_backup_YYYYMMDD_HHMMSS.json`) from offsite storage (S3 / backup volume) into `/opt/ssk-collections/backend/data/backups/`.
4. Execute restore:
   ```bash
   cd backend
   python -c "from app.services.backup_service import BackupService; print(BackupService.restore_backup('ssk_backup_YYYYMMDD_HHMMSS.json'))"
   ```
5. The restore script automatically:
   - Validates the backup JSON structure.
   - Computes and verifies the SHA-256 cryptographic checksum against the backup header to prevent restoring corrupted data.
   - Restores all collections (`users`, `products`, `orders`, `invoices`, `coupons`, `webhook_events`, etc.).
   - Re-applies all production compound indexes and unique constraints.

---

## 3. PAYMENT GATEWAY CONTINGENCY

### What to Do if Razorpay Experiences a Gateway Outage
1. **Customer Impact:** Razorpay popup fails to initialize or Indian banks experience UPI downtime.
2. **Built-in SSK Fallback:**
   - **Cash on Delivery (COD)** remains fully operational.
   - Customers can immediately switch to COD on the checkout screen without losing their selected jewellery items, cart quantities, applied coupons, or delivery addresses.
3. **Pending Online Payment Handling:**
   - Orders remain in `payment_status: "PENDING"`.
   - The customer can visit their **Account Portal &rarr; My Orders** (`/account`) at any time and click **Retry Payment** (`/api/v1/payments/{order_id}/retry`) to generate a fresh payment transaction without re-creating the order.
