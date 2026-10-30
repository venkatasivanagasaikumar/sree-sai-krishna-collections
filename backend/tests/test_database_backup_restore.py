import pytest
import os
from app.services.backup_service import BackupService
from app.database import get_db, db_manager
from app.api.v1.settings import get_database_status, list_database_backups, create_database_backup, restore_database_backup

def test_database_backup_and_restore_service():
    db = get_db()
    # 1. Create a snapshot backup
    backup = BackupService.create_backup(tag="test_suite_snapshot")
    assert backup["filename"].startswith("ssk_backup_")
    assert os.path.exists(backup["filepath"])
    assert "checksum" in backup
    assert backup["summary"]["products"] > 0

    # 2. List backups
    backups = BackupService.list_backups()
    assert len(backups) >= 1
    assert any(b["filename"] == backup["filename"] for b in backups)

    # 3. Modify something, then restore
    initial_count = db.products.count_documents({})
    # Insert a temporary product
    temp_res = db.products.insert_one({"name": "Temp Test Item", "sku": "TEMP-999", "price": 100})
    assert db.products.count_documents({}) == initial_count + 1

    # Restore from snapshot
    restore_res = BackupService.restore_backup(backup["filename"])
    assert restore_res["collections_restored"] > 0
    # The temporary product should be gone after restore
    assert db.products.count_documents({}) == initial_count

def test_admin_backup_endpoints():
    db = get_db()

    # 1. Check database status
    data = get_database_status(db=db)
    assert data["status"] == "healthy"
    assert "collections" in data
    assert data["collections"]["products"] > 0

    # 2. Create backup via endpoint
    create_res = create_database_backup(tag="api_test")
    created = create_res["backup"]
    assert "filename" in created

    # 3. List backups
    list_res = list_database_backups()
    assert len(list_res["backups"]) > 0

    # 4. Restore backup
    restore_res = restore_database_backup(payload={"filename": created["filename"]})
    assert "Database restored successfully" in restore_res["message"]
