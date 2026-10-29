import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ssk_app")

class AuditLogger:
    @staticmethod
    def log_event(
        db,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS"
    ):
        record = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "details": details or {},
            "status": status,
            "created_at": datetime.now(timezone.utc)
        }
        try:
            db.audit_logs.insert_one(record)
        except Exception as e:
            logger.warning(f"Failed to record audit log: {e}")
        logger.info(f"AUDIT: [{status}] {action} on {resource_type} ({resource_id}) by {user_email or user_id or 'system'}")
