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
os.makedirs(DATA_DIR, exist_ok=True)
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
                    serverSelectionTimeoutMS=1000,
                    connectTimeoutMS=1000
                )
                real_client.server_info()
                self.client = real_client
                self.db = real_client[settings.DATABASE_NAME]
                self.is_mock = False
                logger.info(f"Connected to live MongoDB at {settings.MONGODB_URI}/{settings.DATABASE_NAME}")
                self._create_indexes()
                return self.db
            except Exception as e:
                logger.warning(f"Live MongoDB connection failed ({e}). Falling back to MongoMock.")

        # Fallback to mongomock
        self.client = mongomock.MongoClient()
        self.db = self.client[settings.DATABASE_NAME]
        self.is_mock = True
        logger.info(f"Using MongoMock database '{settings.DATABASE_NAME}'.")
        self._load_from_disk()
        self._create_indexes()
        return self.db

    def _create_indexes(self):
        try:
            self.db.users.create_index("email", unique=True)
            self.db.products.create_index("sku", unique=True)
            self.db.categories.create_index("slug", unique=True)
            self.db.orders.create_index("order_id", unique=True)
            self.db.coupons.create_index("code", unique=True)
        except Exception as e:
            logger.debug(f"Index creation note: {e}")

    def persist_to_disk(self):
        """Persists current state to JSON file so data survives restarts in mock mode."""
        if not self.is_mock:
            return
        try:
            state = {}
            for col_name in self.db.list_collection_names():
                docs = list(self.db[col_name].find({}))
                state[col_name] = docs
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
            logger.info("Loaded previous MongoMock state from disk.")
        except Exception as e:
            logger.warning(f"Could not load state from disk: {e}")

db_manager = Database()

def get_db():
    if db_manager.db is None:
        db_manager.connect()
    return db_manager.db
