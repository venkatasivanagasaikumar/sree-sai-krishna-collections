import os
import json
from datetime import datetime, timezone
from bson import ObjectId
import pymongo
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import mongomock
from app.core.config import settings
from app.core.logging import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
INVOICES_DIR = os.path.join(DATA_DIR, "invoices")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(INVOICES_DIR, exist_ok=True)
DUMP_FILE = os.path.join(DATA_DIR, "db_dump.json")

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

class Database:
    client = None
    db = None
    is_mock: bool = False

    def connect(self):
        if not settings.FORCE_MOCK_DB:
            try:
                real_client = pymongo.MongoClient(
                    settings.MONGODB_URI,
                    serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=2000
                )
                real_client.server_info()
                self.client = real_client
                self.db = real_client[settings.DATABASE_NAME]
                self.is_mock = False
                logger.info(f"Connected to live MongoDB cluster at {settings.MONGODB_URI}/{settings.DATABASE_NAME}")
                
                # Check for seamless live migration from dump file if live database is unpopulated
                try:
                    if self.db.products.count_documents({}) == 0 and os.path.exists(DUMP_FILE):
                        logger.info("Empty live MongoDB detected. Migrating historical data from dump file...")
                        self._load_from_disk()
                except Exception as mig_err:
                    logger.warning(f"Live database initial migration check note: {mig_err}")
                
                self._create_indexes()
                return self.db
            except Exception as e:
                logger.warning(f"Live MongoDB connection failed ({e}). Falling back to MongoMock.")

        # Fallback to MongoMock for local offline operation
        self.client = mongomock.MongoClient()
        self.db = self.client[settings.DATABASE_NAME]
        self.is_mock = True
        logger.info(f"Using MongoMock database '{settings.DATABASE_NAME}'.")
        self._load_from_disk()
        self._create_indexes()
        return self.db

    def _create_indexes(self):
        """Creates unique constraints and optimized query compound indexes across collections."""
        try:
            # Users
            self.db.users.create_index("email", unique=True)
            self.db.users.create_index("role")
            
            # Products
            self.db.products.create_index("sku", unique=True)
            self.db.products.create_index("category")
            self.db.products.create_index("status")
            self.db.products.create_index([("category", 1), ("price", 1)])
            self.db.products.create_index("is_featured")
            self.db.products.create_index("is_bestseller")
            
            # Categories
            self.db.categories.create_index("slug", unique=True)
            self.db.categories.create_index("is_active")
            
            # Orders
            self.db.orders.create_index("order_id", unique=True)
            self.db.orders.create_index("user_id")
            self.db.orders.create_index("customer_email")
            self.db.orders.create_index("order_status")
            self.db.orders.create_index("payment_status")
            self.db.orders.create_index([("created_at", -1)])
            
            # Inventory & Movements
            self.db.inventory_movements.create_index("sku")
            self.db.inventory_movements.create_index("created_at")
            
            # Coupons
            self.db.coupons.create_index("code", unique=True)
            self.db.coupons.create_index("is_active")
            
            # Webhook Events
            self.db.webhook_events.create_index("event_id", unique=True)
            
            # Carts
            self.db.carts.create_index("user_id", unique=True)
            
            # Password reset tokens
            self.db.password_reset_tokens.create_index("token", unique=True)
            self.db.password_reset_tokens.create_index("expires_at")
            
            # Audit Logs
            self.db.audit_logs.create_index("created_at")
            self.db.audit_logs.create_index("action")
            
            # Invoices & Credit Notes
            self.db.invoices.create_index("invoice_number", unique=True)
            self.db.invoices.create_index("order_id")
            self.db.invoices.create_index("customer_email")
            self.db.invoices.create_index("user_id")
            self.db.invoices.create_index("invoice_date")
            self.db.invoices.create_index("invoice_type")
            self.db.invoice_sequences.create_index("year_prefix", unique=True)
            
            # Notification Events & Logs
            self.db.notification_events.create_index("event_id", unique=True)
            self.db.notification_events.create_index("order_id")
            self.db.notification_events.create_index("event_type")
            self.db.notification_logs.create_index("notification_id", unique=True)
            self.db.notification_logs.create_index("order_id")
            self.db.notification_logs.create_index("channel")
            self.db.notification_logs.create_index("status")
            self.db.notification_logs.create_index("created_at")
            self.db.notification_outbox.create_index("outbox_id", unique=True)
            self.db.notification_outbox.create_index("status")
            self.db.notification_outbox.create_index("next_retry_at")
            
            # Communication Preferences & Consents
            self.db.communication_preferences.create_index("user_id", unique=True)
            self.db.communication_preferences.create_index("customer_email")
            self.db.communication_consents.create_index("consent_id", unique=True, sparse=True)
            self.db.communication_consents.create_index("user_id")
            
            logger.debug("Production database indexes successfully verified and applied.")
        except Exception as e:
            logger.debug(f"Index creation note: {e}")

    def export_state(self) -> dict:
        """Exports all collections and documents into a dictionary."""
        if self.db is None:
            self.connect()
        state = {}
        for col_name in self.db.list_collection_names():
            docs = list(self.db[col_name].find({}))
            state[col_name] = docs
        return state

    def import_state(self, state: dict) -> dict:
        """Imports collections and documents from dictionary into the database."""
        if self.db is None:
            self.connect()
        stats = {}
        for col_name, docs in state.items():
            if docs:
                self.db[col_name].drop()
                for d in docs:
                    if "_id" in d and isinstance(d["_id"], str) and len(d["_id"]) == 24:
                        try:
                            d["_id"] = ObjectId(d["_id"])
                        except Exception:
                            pass
                    self.db[col_name].insert_one(d)
                stats[col_name] = len(docs)
        self._create_indexes()
        self.persist_to_disk()
        return stats

    def persist_to_disk(self):
        """Persists current state to JSON file so data survives restarts in mock mode."""
        if not self.is_mock:
            return
        try:
            state = self.export_state()
            with open(DUMP_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, cls=MongoJSONEncoder, indent=2)
            logger.debug("MongoMock state persisted to disk.")
        except Exception as e:
            logger.warning(f"Error persisting mock DB to disk: {e}")

    def _load_from_disk(self):
        """Loads data from JSON file if available."""
        if not os.path.exists(DUMP_FILE):
            return
        try:
            with open(DUMP_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.import_state(state)
            logger.info("Loaded previous database state from disk.")
        except Exception as e:
            logger.warning(f"Could not load state from disk: {e}")

db_manager = Database()

def get_db():
    if db_manager.db is None:
        db_manager.connect()
    return db_manager.db
