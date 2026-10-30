import os
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.database import db_manager, MongoJSONEncoder, BACKUP_DIR
from app.core.logging import logger

class BackupService:
    @staticmethod
    def create_backup(tag: Optional[str] = None) -> Dict[str, Any]:
        """Creates a timestamped snapshot of the current database state."""
        os.makedirs(BACKUP_DIR, exist_ok=True)
        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        tag_str = f"_{tag.strip().replace(' ', '_')}" if tag else ""
        filename = f"ssk_backup_{timestamp_str}{tag_str}.json"
        filepath = os.path.join(BACKUP_DIR, filename)

        state = db_manager.export_state()
        summary = {col: len(docs) for col, docs in state.items()}

        backup_payload = {
            "metadata": {
                "created_at": now.isoformat(),
                "brand": "Sree Sai Krishna Collections",
                "tag": tag or "manual_snapshot",
                "collections_count": len(state),
                "summary": summary
            },
            "data": state
        }

        content_str = json.dumps(backup_payload, cls=MongoJSONEncoder, indent=2)
        checksum = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        backup_payload["metadata"]["checksum"] = checksum

        # Write with checksum
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_payload, f, cls=MongoJSONEncoder, indent=2)

        file_size_bytes = os.path.getsize(filepath)
        logger.info(f"Database backup created: {filename} ({file_size_bytes} bytes)")

        return {
            "filename": filename,
            "filepath": filepath,
            "size_bytes": file_size_bytes,
            "created_at": now.isoformat(),
            "checksum": checksum,
            "summary": summary
        }

    @staticmethod
    def list_backups() -> List[Dict[str, Any]]:
        """Lists all existing backup files in the backup directory."""
        if not os.path.exists(BACKUP_DIR):
            return []

        backups = []
        for fname in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if fname.endswith(".json"):
                fpath = os.path.join(BACKUP_DIR, fname)
                try:
                    stat = os.stat(fpath)
                    created_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    # Peek metadata
                    metadata = {}
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "metadata" in data:
                            metadata = data["metadata"]
                        elif isinstance(data, dict):
                            metadata = {"summary": {k: len(v) for k, v in data.items() if isinstance(v, list)}}
                    
                    backups.append({
                        "filename": fname,
                        "size_bytes": stat.st_size,
                        "created_at": metadata.get("created_at", created_at),
                        "tag": metadata.get("tag", "snapshot"),
                        "checksum": metadata.get("checksum"),
                        "summary": metadata.get("summary", {})
                    })
                except Exception as e:
                    logger.warning(f"Error inspecting backup file {fname}: {e}")

        return backups

    @staticmethod
    def restore_backup(filename_or_path: str) -> Dict[str, Any]:
        """Restores database collections from a designated backup snapshot."""
        if os.path.isabs(filename_or_path):
            fpath = filename_or_path
        else:
            fpath = os.path.join(BACKUP_DIR, filename_or_path)

        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Backup file not found at {fpath}")

        with open(fpath, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if isinstance(payload, dict) and "data" in payload:
            state = payload["data"]
            meta = payload.get("metadata", {})
        elif isinstance(payload, dict):
            state = payload
            meta = {}
        else:
            raise ValueError("Invalid backup structure.")

        stats = db_manager.import_state(state)
        logger.info(f"Database successfully restored from {fpath}: {stats}")

        return {
            "restored_from": os.path.basename(fpath),
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "collections_restored": len(stats),
            "stats": stats
        }
