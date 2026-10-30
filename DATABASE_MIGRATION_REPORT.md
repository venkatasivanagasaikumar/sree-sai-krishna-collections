# Sree Sai Krishna Collections (SSK) – Database Migration & Persistence Report

This report documents the database architecture, schema definitions, compound indexes, migration mechanisms, and disaster recovery procedures for the Sree Sai Krishna Collections platform.

---

## 1. Database Architecture & Operational Modes

The SSK platform features an adaptive, dual-mode persistence architecture:

```
+-------------------------------------------------------------------------+
|                           SSK Database Engine                           |
+-------------------------------------------------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
+-----------------------------+               +-----------------------------+
|    MongoMock (Offline/Dev)  |               |  Production MongoDB Cluster |
|   - Zero native daemon req  |               |   - WiredTiger Storage      |
|   - Syncs to data/db_dump   |               |   - Replica Set Enabled     |
|   - Fast pytest automation  |               |   - Automated Failover      |
+-----------------------------+               +-----------------------------+
```

### Automatic Cluster Detection & Seeding
In `backend/app/database.py`, when `FORCE_MOCK_DB=false`:
1. The engine attempts a connection to `MONGODB_URI` with a 2000ms timeout.
2. If the live cluster is connected and contains 0 products (a fresh empty database), it automatically parses `backend/data/db_dump.json` and loads all existing product catalogs, categories, settings, and historical orders.
3. It rebuilds all production indexes immediately.
4. If the live database fails to connect, it logs a warning and falls back to local file-persisted mock mode, ensuring zero customer downtime.

---

## 2. Collections & Schema Architecture

The database persists 10 core collections:

| Collection | Description | Document Count (Baseline) | Primary Index / Constraints |
| :--- | :--- | :---: | :--- |
| **`users`** | Staff and customer profiles | 4 | `email` (Unique), `role` |
| **`products`** | Jewellery and fashion catalog | 8 | `sku` (Unique), `category`, `status`, `[category, price]` |
| **`categories`** | Hierarchy & metadata | 5 | `slug` (Unique), `is_active` |
| **`orders`** | Customer purchases & lifecycle | 14 | `order_id` (Unique), `customer_email`, `order_status`, `created_at` (-1) |
| **`inventory_movements`**| Stock audit trail | 8 | `sku`, `created_at` |
| **`coupons`** | Promotional discount rules | 2 | `code` (Unique), `is_active` |
| **`carts`** | User shopping bags | 2 | `user_id` (Unique) |
| **`webhook_events`** | Gateway idempotency records | 5 | `event_id` (Unique) |
| **`password_reset_tokens`**| Single-use account recovery | 2 | `token` (Unique), `expires_at` |
| **`audit_logs`** | Security and admin activity | 45+ | `created_at` (-1), `action` |

---

## 3. Production Index Verification

Compound and unique indexes are automatically applied via `_create_indexes()` upon startup:

```python
# Unique Identity Indexes
self.db.users.create_index("email", unique=True)
self.db.products.create_index("sku", unique=True)
self.db.categories.create_index("slug", unique=True)
self.db.orders.create_index("order_id", unique=True)
self.db.coupons.create_index("code", unique=True)
self.db.webhook_events.create_index("event_id", unique=True)
self.db.password_reset_tokens.create_index("token", unique=True)

# Performance & Filtering Compound Indexes
self.db.products.create_index([("category", 1), ("price", 1)])
self.db.products.create_index("is_featured")
self.db.products.create_index("is_bestseller")
self.db.orders.create_index([("created_at", -1)])
self.db.orders.create_index("order_status")
self.db.orders.create_index("payment_status")
self.db.inventory_movements.create_index("sku")
self.db.audit_logs.create_index([("created_at", -1)])
```

---

## 4. Disaster Recovery & Backup Verification

A automated backup and restore subsystem has been implemented in `BackupService` (`app/services/backup_service.py`):

1. **Snapshot Creation (`BackupService.create_backup`):**
   - Serializes all collections with ISO-8601 timestamps and ObjectId translation.
   - Calculates a cryptographic SHA-256 checksum of the backup archive.
   - Saves to `backend/backups/ssk_backup_<TIMESTAMP>_<TAG>.json`.
2. **Disaster Restoration (`BackupService.restore_backup`):**
   - Safely parses and validates the archive structure.
   - Drops stale collections and inserts restored documents preserving original ObjectIds.
   - Re-applies all compound and unique indexes.
3. **Automated Test Results:**
   - Test `test_database_backup_and_restore_service`: **PASSED** (created snapshot, verified checksum, dropped/restored documents with 100% integrity).
   - Test `test_admin_backup_endpoints`: **PASSED** (verified `/settings/database/status`, `/settings/backups`, and `/settings/backups/restore`).

---

## 5. Live Cluster Migration Runbook

To migrate from the current file-persisted mock to a live MongoDB Atlas / AWS DocumentDB cluster:

1. **Provision Cluster:** Create a M10+ replica set cluster on MongoDB Atlas in the AWS `ap-south-1` (Mumbai) region for minimal latency to Indian shoppers.
2. **Configure Database User:** Create a dedicated user `ssk_app_user` with `readWrite` role on `ssk_collections_db`.
3. **IP Whitelist:** Add the production server's static IP to the Atlas Network Access list.
4. **Update `.env`:**
   ```ini
   FORCE_MOCK_DB=false
   MONGODB_URI="mongodb+srv://ssk_app_user:<PASSWORD>@cluster0.mongodb.net/ssk_collections_db?retryWrites=true&w=majority"
   DATABASE_NAME="ssk_collections_db"
   ```
5. **Restart Service:** Restart the backend container (`docker compose restart ssk-backend-api`).
6. **Verify:** Check `GET /api/v1/health` and verify `"database": "mongodb_live"`. All 8 products and catalog categories will automatically seed into the live cluster.
