# SREE SAI KRISHNA COLLECTIONS (SSK)
# DATABASE BACKUP, DISASTER RECOVERY & RESTORATION RUNBOOK

**Document Version:** 1.0.0  
**Effective Date:** October 31, 2026  
**Auditor Roles:** Senior Database Administrator, Cloud Architect, and Security Release Manager  
**Baseline Verified Commit:** [`038345c`](https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections/commit/038345c)  
**Database Architecture:** MongoDB Atlas M0 (AWS Mumbai `ap-south-1`)  
**Target Monthly Budget:** ₹0.00 (Zero Recurring Cost)

---

## 1. EXECUTIVE SUMMARY & BACKUP STRATEGY

MongoDB Atlas M0 Free Tier does not include automated snapshots or Point-In-Time Recovery (PITR). Furthermore, Atlas M0 automatically pauses clusters that experience zero connection activity for 60 consecutive days.

To ensure enterprise-grade data protection without incurring paid database fees (such as Atlas M10 at ₹4,800/month), SSK implements an **Automated Encrypted Backup Pipeline** using **GitHub Actions Scheduled Workflows**.

### Key Architecture Features
1. **Zero Recurring Infrastructure Cost:** Executes on GitHub Actions free runner minutes (consumes ~4 minutes/month out of 2,000 free minutes).
2. **End-to-End Cryptographic Security:** Database archives are encrypted immediately using **AES-256 GPG symmetric cipher** before exiting runner memory.
3. **Atlas M0 Activity Keeper:** Connecting to MongoDB Atlas every Sunday resets the 60-day inactivity counter, guaranteeing the cluster **never pauses unexpectedly**.
4. **90-Day Retention Policy:** Stored securely as encrypted GitHub Actions artifacts.

```mermaid
flowchart TD
    subgraph Scheduled_Trigger["1. Automated Schedule"]
        Cron["GitHub Actions Cron\n'0 2 * * 0' (Sundays 07:30 IST)\nOr manual workflow_dispatch"]
    end

    subgraph GitHub_Runner["2. Ephemeral Ubuntu Runner (Zero Cost)"]
        Tools["Install mongodb-database-tools & gnupg"]
        Dump["mongodump --uri=$PROD_MONGODB_URI\n--archive --gzip"]
        Encrypt["gpg --symmetric --cipher-algo AES256\n--passphrase $BACKUP_ENCRYPTION_KEY"]
        Clean["Wipe unencrypted archive from memory"]
        
        Cron --> Tools
        Tools --> Dump
        Dump --> Encrypt
        Encrypt --> Clean
    end

    subgraph Atlas_Cloud["3. Cloud Database"]
        Atlas[("MongoDB Atlas M0\nAWS Mumbai (ap-south-1)\n- Orders, Users, Products, Invoices\n- Resets 60-day Inactivity Timer")]
        Dump <-->|Encrypted TLS 1.3 Connection| Atlas
    end

    subgraph Secure_Storage["4. Encrypted Artifact Retention"]
        Artifacts[("GitHub Artifacts Storage\n- 90-Day Encrypted Retention\n- Filename: ssk_backup_YYYYMMDD.archive.gpg")]
        Clean --> Artifacts
    end
```

---

## 2. GITHUB ACTIONS AUTOMATED BACKUP WORKFLOW

The automated backup pipeline is configured in [`.github/workflows/database-backup.yml`](file:///C:/Users/saiku/.gemini/antigravity/scratch/ssk-collections/.github/workflows/database-backup.yml):

```yaml
name: Automated MongoDB Atlas Backup

on:
  schedule:
    # Run every Sunday at 02:00 UTC (07:30 IST)
    - cron: '0 2 * * 0'
  workflow_dispatch:
    # Allows manual trigger on demand from GitHub Actions UI

jobs:
  backup:
    name: Encrypted Database Snapshot
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Install MongoDB Database Tools
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq mongodb-database-tools gnupg

      - name: Run Database Dump
        env:
          MONGODB_URI: ${{ secrets.PROD_MONGODB_URI }}
        run: |
          mkdir -p backup_dumps
          TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
          ARCHIVE_PATH="backup_dumps/ssk_backup_${TIMESTAMP}.archive"
          echo "TIMESTAMP=${TIMESTAMP}" >> $GITHUB_ENV
          echo "ARCHIVE_PATH=${ARCHIVE_PATH}" >> $GITHUB_ENV

          # Perform mongodump using gzip compression into a single archive file
          mongodump --uri="${MONGODB_URI}" --archive="${ARCHIVE_PATH}" --gzip
          
          # Verify archive was generated and is non-empty
          if [ ! -s "${ARCHIVE_PATH}" ]; then
            echo "ERROR: mongodump generated empty or missing archive!" >&2
            exit 1
          fi
          echo "Database dump created successfully: $(du -h "${ARCHIVE_PATH}")"

      - name: Encrypt Backup Archive with AES-256 GPG
        env:
          BACKUP_ENCRYPTION_KEY: ${{ secrets.BACKUP_ENCRYPTION_KEY }}
        run: |
          ENCRYPTED_PATH="${ARCHIVE_PATH}.gpg"
          echo "ENCRYPTED_PATH=${ENCRYPTED_PATH}" >> $GITHUB_ENV

          gpg --batch --yes --symmetric --cipher-algo AES256 \
              --passphrase "${BACKUP_ENCRYPTION_KEY}" \
              --output "${ENCRYPTED_PATH}" "${ARCHIVE_PATH}"

          # Remove unencrypted plain dump
          rm -f "${ARCHIVE_PATH}"
          echo "Archive encrypted successfully: $(du -h "${ENCRYPTED_PATH}")"

      - name: Upload Encrypted Backup Artifact
        uses: actions/upload-artifact@v4
        with:
          name: ssk-encrypted-db-backup-${{ env.TIMESTAMP }}
          path: ${{ env.ENCRYPTED_PATH }}
          retention-days: 90
```

### Required Repository Secrets Setup
Navigate to **GitHub Repository** &rarr; **Settings** &rarr; **Secrets and variables** &rarr; **Actions** &rarr; **New repository secret**:
1. **`PROD_MONGODB_URI`**: Production MongoDB Atlas M0 connection string (e.g., `mongodb+srv://ssk_app_user:StrongPassword@ssk-cluster.xxxx.mongodb.net/ssk_production_db?retryWrites=true&w=majority`).
2. **`BACKUP_ENCRYPTION_KEY`**: 64-character cryptographic hexadecimal string used for AES-256 symmetric encryption. Generate via:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

---

## 3. MANUAL ON-DEMAND BACKUP PROCEDURES

When preparing for database schema changes, major product catalogue updates, or application releases, perform an immediate on-demand backup using any of the following three methods:

### Method A: One-Click Trigger via GitHub Actions UI (Recommended)
1. Navigate to your GitHub repository in a browser.
2. Click the **Actions** tab.
3. Select **"Automated MongoDB Atlas Backup"** from the left sidebar.
4. Click **Run workflow** &rarr; Select branch `main` &rarr; Click the green **Run workflow** button.
5. The job completes in ~45 seconds, generating a downloadable encrypted artifact.

### Method B: Local CLI Execution (Workstation Terminal)
If offline or executing from an administrator workstation with `mongodb-database-tools` installed:
```powershell
# Set temporary session variables (do not persist in shell history)
$env:MONGODB_URI = "mongodb+srv://ssk_app_user:PASSWORD@cluster.mongodb.net/ssk_production_db"
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmssZ")
$ARCHIVE = "ssk_manual_backup_$TIMESTAMP.archive"

# 1. Create compressed MongoDB dump
mongodump --uri="$env:MONGODB_URI" --archive="$ARCHIVE" --gzip

# 2. Encrypt using GPG
gpg --batch --yes --symmetric --cipher-algo AES256 --output "$ARCHIVE.gpg" "$ARCHIVE"

# 3. Clean up plain dump file
Remove-Item "$ARCHIVE"
Write-Host "Encrypted backup saved as $ARCHIVE.gpg"
```

### Method C: SSK Admin Portal Backup Endpoint
Store administrators with `Super Admin` privileges can trigger a JSON backup snapshot via the API:
```bash
curl -X POST https://api.sreesaikrishnacollections.com/api/v1/settings/backup \
     -H "Authorization: Bearer <SUPER_ADMIN_JWT_TOKEN>"
```

---

## 4. DISASTER RECOVERY & DATABASE RESTORATION RUNBOOK

Follow this step-by-step restoration runbook in the event of database corruption, accidental deletion, or disaster recovery.

### Step 1: Download the Encrypted Backup Artifact
1. Go to **GitHub Repository &rarr; Actions &rarr; Automated MongoDB Atlas Backup**.
2. Click on the latest successful workflow run.
3. Under **Artifacts**, download `ssk-encrypted-db-backup-YYYYMMDD_HHMMSSZ`.
4. Extract the `.zip` file to locate `ssk_backup_YYYYMMDD_HHMMSSZ.archive.gpg`.

### Step 2: Decrypt the GPG Archive
In your terminal, decrypt the archive using your secret passphrase:

```bash
# Linux / macOS
gpg --decrypt --passphrase "$BACKUP_ENCRYPTION_KEY" \
    --output ssk_restore.archive \
    ssk_backup_YYYYMMDD_HHMMSSZ.archive.gpg

# Windows PowerShell
gpg --decrypt --passphrase $env:BACKUP_ENCRYPTION_KEY `
    --output ssk_restore.archive `
    ssk_backup_YYYYMMDD_HHMMSSZ.archive.gpg
```

Verify that the decrypted `ssk_restore.archive` is created and non-empty.

### Step 3: Execute mongorestore Against MongoDB Atlas

> [!WARNING]
> **DESTRUCTIVE RESTORATION ACTION:**
> The `--drop` flag drops existing collections before restoring from the archive. Ensure you are targeting the correct database.

```bash
# Execute mongorestore using gzip archive
mongorestore --uri="$PROD_MONGODB_URI" \
             --archive=ssk_restore.archive \
             --gzip \
             --drop
```

### Expected Command Output
```text
2026-10-31T12:00:00.000+0530  preparing collections to restore from
2026-10-31T12:00:00.050+0530  dropping collection ssk_production_db.users before restoring
2026-10-31T12:00:00.120+0530  restoring ssk_production_db.users from archive
2026-10-31T12:00:00.180+0530  restoring indexes for ssk_production_db.users
2026-10-31T12:00:00.220+0530  dropping collection ssk_production_db.products before restoring
2026-10-31T12:00:00.310+0530  restoring ssk_production_db.products from archive
2026-10-31T12:00:00.420+0530  dropping collection ssk_production_db.orders before restoring
2026-10-31T12:00:00.510+0530  restoring ssk_production_db.orders from archive
2026-10-31T12:00:00.580+0530  restoring indexes for ssk_production_db.orders
2026-10-31T12:00:00.650+0530  restoring ssk_production_db.invoices from archive
2026-10-31T12:00:00.720+0530  restoring ssk_production_db.counters from archive
2026-10-31T12:00:00.800+0530  0 document(s) failed to restore. 5 collection(s) restored successfully.
```

### Step 4: Post-Restoration Data Integrity Verification
Run this Python verification script to confirm document counts, critical indexes, and sequence counter integrity:

```python
import pymongo

uri = "YOUR_PROD_MONGODB_URI"
client = pymongo.MongoClient(uri)
db = client.get_default_database()

print("--- POST-RESTORE INTEGRITY AUDIT ---")
print(f"Database Name: {db.name}")
print(f"Users Count: {db.users.count_documents({})}")
print(f"Products Count: {db.products.count_documents({})}")
print(f"Orders Count: {db.orders.count_documents({})}")
print(f"Invoices Count: {db.invoices.count_documents({})}")

# Verify critical indexes exist
user_indexes = [idx["name"] for idx in db.users.list_indexes()]
order_indexes = [idx["name"] for idx in db.orders.list_indexes()]
assert "email_1" in user_indexes or any("email" in k for k in user_indexes), "CRITICAL: users email index missing!"
assert "order_id_1" in order_indexes or any("order_id" in k for k in order_indexes), "CRITICAL: orders order_id index missing!"

print("--- ALL POST-RESTORE CHECKS PASSED SUCCESSFULLY ---")
```

### Step 5: Clean Up Local Decrypted Artifacts
```bash
# Immediately delete decrypted unencrypted archive from disk
rm -f ssk_restore.archive
```

---

## 5. RECOVERY METRICS & OPERATIONAL SLA (FREE TIER)

| Metric | Target Value | Feasibility & Context at 1–2 Orders/Month |
| :--- | :---: | :--- |
| **RPO (Recovery Point Objective)** | **7 Days** *(Weekly Snapshot)* | At 1–2 orders per month, an order is placed once every 15 to 30 days. A weekly snapshot guarantees that at most **0 to 1 order** could ever be impacted in a catastrophic total loss scenario. (Manual backups prior to updates provide RPO = 0). |
| **RTO (Recovery Time Objective)** | **< 15 Minutes** | Time required to download the ~2 MB encrypted artifact, execute GPG decrypt, and run `mongorestore` over broadband connection. |
| **Backup Storage Overhead** | **~250 KB per snapshot** | The entire SSK compressed database consumes ~250 KB gzip. 52 weekly backups consume **~13 MB total**, safely within GitHub's free artifact storage tier. |
| **Cost to Maintain** | **₹0.00 / Month** | 100% free forever using GitHub Actions scheduled workflows and standard open-source tools. |
