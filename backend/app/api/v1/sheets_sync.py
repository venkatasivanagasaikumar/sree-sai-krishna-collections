from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import urllib.request
import urllib.error
from bson import ObjectId
from app.database import get_db, db_manager
from app.core.permissions import Role
from app.core.logging import AuditLogger
from app.api.dependencies import require_roles

router = APIRouter(prefix="/sheets", tags=["Google Sheets / Excel Sync"])

CONFIG_KEY = "google_sheets_sync_config"

def get_current_sync_config(db):
    doc = db.store_settings.find_one({"key": CONFIG_KEY})
    if not doc:
        return {
            "webhook_url": "",
            "auto_sync_on_order": True,
            "auto_sync_on_product": True,
            "last_synced_at": None,
            "status": "not_configured"
        }
    return doc.get("data", {})

@router.get("/config", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def get_sheets_config(db = Depends(get_db)):
    return get_current_sync_config(db)

@router.post("/config", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def save_sheets_config(payload: Dict[str, Any], db = Depends(get_db)):
    webhook_url = payload.get("webhook_url", "").strip()
    data = {
        "webhook_url": webhook_url,
        "auto_sync_on_order": bool(payload.get("auto_sync_on_order", True)),
        "auto_sync_on_product": bool(payload.get("auto_sync_on_product", True)),
        "last_synced_at": payload.get("last_synced_at"),
        "status": "connected" if webhook_url else "not_configured"
    }
    db.store_settings.update_one(
        {"key": CONFIG_KEY},
        {"$set": {"data": data, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    db_manager.persist_to_disk()
    return {"message": "Google Sheets configuration saved", "config": data}

def post_to_google_sheet(webhook_url: str, payload_data: dict) -> dict:
    if not webhook_url:
        return {"success": False, "message": "No Google Apps Script Webhook URL configured."}
    
    headers = {"Content-Type": "application/json"}
    body_bytes = json.dumps(payload_data, default=str).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=body_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode("utf-8")
            try:
                parsed = json.loads(res_body)
                return {"success": True, "response": parsed}
            except Exception:
                return {"success": True, "raw": res_body}
    except urllib.error.HTTPError as e:
        return {"success": False, "status_code": e.code, "error": str(e.read().decode('utf-8', errors='ignore'))}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/export-all", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def export_all_for_sheets(db = Depends(get_db)):
    """
    Returns unified JSON structured specifically for importing into Excel or Google Sheets.
    Contains Products, Orders, Customers, and Inventory movements.
    """
    products = list(db.products.find({}))
    orders = list(db.orders.find({}))
    customers = list(db.customers.find({}))
    movements = list(db.inventory_movements.find({}))

    # Clean ObjectIds
    def clean_docs(docs):
        clean = []
        for d in docs:
            copy = dict(d)
            if "_id" in copy:
                copy["_id"] = str(copy["_id"])
            if "id" not in copy and "_id" in copy:
                copy["id"] = copy["_id"]
            clean.append(copy)
        return clean

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "store": "Sree Sai Krishna Collections",
        "products": clean_docs(products),
        "orders": clean_docs(orders),
        "customers": clean_docs(customers),
        "inventory": clean_docs(movements)
    }

@router.post("/push-all", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def push_all_to_google_sheet(db = Depends(get_db)):
    """
    Sends all current products, orders, and inventory data to the configured Google Sheet via Apps Script Webhook.
    """
    config = get_current_sync_config(db)
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Apps Script Webhook URL is not configured. Please paste your deployed Web App URL in settings."
        )

    all_data = export_all_for_sheets(db)
    payload = {
        "event": "BULK_FULL_SYNC",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": all_data
    }
    
    result = post_to_google_sheet(webhook_url, payload)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with Google Apps Script: {result.get('error') or result.get('message')}"
        )
    
    # Update last synced time
    config["last_synced_at"] = datetime.now(timezone.utc).isoformat()
    config["status"] = "synced"
    db.store_settings.update_one(
        {"key": CONFIG_KEY},
        {"$set": {"data": config, "updated_at": datetime.now(timezone.utc)}}
    )
    db_manager.persist_to_disk()

    AuditLogger.log_event(
        db,
        action="SHEETS_FULL_SYNC",
        resource_type="GOOGLE_SHEET",
        resource_id="webhook",
        details={"result": result}
    )

    return {
        "message": "All database records (products, orders, customers, inventory) pushed to Google Sheet successfully!",
        "last_synced_at": config["last_synced_at"],
        "sheet_response": result
    }

@router.post("/test-connection", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def test_sheets_connection(payload: Dict[str, Any], db = Depends(get_db)):
    webhook_url = payload.get("webhook_url", "").strip()
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL is required to test")
    
    test_payload = {
        "event": "PING_TEST",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "store": "Sree Sai Krishna Collections",
        "message": "Connection test from SSK Admin Panel"
    }
    res = post_to_google_sheet(webhook_url, test_payload)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Connection failed: {res.get('error') or res.get('message')}"
        )
    return {"message": "Google Sheet Webhook responded successfully!", "response": res}

@router.get("/appscript-template")
def get_appscript_template():
    """
    Returns the ready-to-paste Google Apps Script code for the user to deploy in Google Sheets.
    """
    code = '''/**
 * SREE SAI KRISHNA COLLECTIONS (SSK) - GOOGLE SHEETS LIVE SYNC SCRIPT
 * 
 * Instructions:
 * 1. Open Google Sheets (create a new blank spreadsheet).
 * 2. In Google Sheets menu, click: Extensions -> Apps Script.
 * 3. Delete any default code and PASTE this entire code.
 * 4. Click "Deploy" (top right) -> "New deployment".
 * 5. Select type: "Web app".
 * 6. Under "Execute as": select "Me".
 * 7. Under "Who has access": select "Anyone".
 * 8. Click "Deploy" and authorize the script when prompted.
 * 9. Copy the "Web app URL" and paste it into the SSK Admin -> Google Sheets Sync page!
 */

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(15000);
  
  try {
    var raw = e.postData.contents;
    var payload = JSON.parse(raw);
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    if (payload.event === "PING_TEST") {
      return ContentService.createTextOutput(JSON.stringify({ status: "success", message: "Connected to SSK Sheet successfully!" })).setMimeType(ContentService.MimeType.JSON);
    }
    
    if (payload.event === "BULK_FULL_SYNC" && payload.data) {
      syncProducts(ss, payload.data.products || []);
      syncOrders(ss, payload.data.orders || []);
      syncCustomers(ss, payload.data.customers || []);
      syncInventory(ss, payload.data.inventory || []);
      
      return ContentService.createTextOutput(JSON.stringify({ 
        status: "success", 
        message: "Full synchronization complete: Products, Orders, Customers, and Inventory updated." 
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    if (payload.event === "ORDER_CREATED" || payload.event === "ORDER_UPDATED") {
      appendOrUpdateOrder(ss, payload.order);
      return ContentService.createTextOutput(JSON.stringify({ status: "success" })).setMimeType(ContentService.MimeType.JSON);
    }
    
    if (payload.event === "PRODUCT_CREATED" || payload.event === "PRODUCT_UPDATED") {
      appendOrUpdateProduct(ss, payload.product);
      return ContentService.createTextOutput(JSON.stringify({ status: "success" })).setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({ status: "acknowledged", event: payload.event })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function syncProducts(ss, products) {
  var sheet = getOrCreateSheet(ss, "Products", [
    "SKU", "Product Name", "Category", "Subcategory", "Jewelry Type", 
    "Selling Price (₹)", "MRP (₹)", "Stock Quantity", "Materials & Finish", "Status", "Last Updated"
  ]);
  
  sheet.clearContents();
  sheet.appendRow([
    "SKU", "Product Name", "Category", "Subcategory", "Jewelry Type", 
    "Selling Price (₹)", "MRP (₹)", "Stock Quantity", "Materials & Finish", "Status", "Last Updated"
  ]);
  formatHeader(sheet, "#123F7A");
  
  if (!products || products.length === 0) return;
  
  var rows = products.map(function(p) {
    return [
      p.sku || "",
      p.name || "",
      p.category || "",
      p.subcategory || "",
      p.jewelry_type || "",
      p.price || 0,
      p.mrp || 0,
      p.stock || 0,
      p.materials_and_finish || "",
      p.status || "active",
      p.updated_at || p.created_at || new Date().toISOString()
    ];
  });
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}

function syncOrders(ss, orders) {
  var sheet = getOrCreateSheet(ss, "Orders", [
    "Order ID", "Customer Name", "Phone", "Email", "Total (₹)", 
    "Payment Method", "Payment Status", "Order Status", "Tracking / AWB", "Items Count", "Date"
  ]);
  
  sheet.clearContents();
  sheet.appendRow([
    "Order ID", "Customer Name", "Phone", "Email", "Total (₹)", 
    "Payment Method", "Payment Status", "Order Status", "Tracking / AWB", "Items Count", "Date"
  ]);
  formatHeader(sheet, "#C89A43");
  
  if (!orders || orders.length === 0) return;
  
  var rows = orders.map(function(o) {
    return [
      o.order_id || "",
      o.customer_name || "",
      o.customer_phone || "",
      o.customer_email || "",
      o.final_amount || 0,
      o.payment_method || "",
      o.payment_status || "",
      o.order_status || "",
      o.tracking_number || "Unassigned",
      (o.items && o.items.length) ? o.items.length : 0,
      o.created_at || new Date().toISOString()
    ];
  });
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}

function syncCustomers(ss, customers) {
  var sheet = getOrCreateSheet(ss, "Customers", [
    "Customer ID", "Name", "Email", "Phone", "Total Orders", "Total Spent (₹)", "Created Date"
  ]);
  
  sheet.clearContents();
  sheet.appendRow([
    "Customer ID", "Name", "Email", "Phone", "Total Orders", "Total Spent (₹)", "Created Date"
  ]);
  formatHeader(sheet, "#1769AA");
  
  if (!customers || customers.length === 0) return;
  
  var rows = customers.map(function(c) {
    return [
      c.id || c._id || "",
      c.full_name || "",
      c.email || "",
      c.phone || "",
      c.total_orders || 0,
      c.total_spent || 0,
      c.created_at || new Date().toISOString()
    ];
  });
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}

function syncInventory(ss, inventory) {
  var sheet = getOrCreateSheet(ss, "Inventory_Log", [
    "SKU", "Product Name", "Movement Type", "Change Qty", "Previous Stock", "New Stock", "Reason", "Adjusted By", "Timestamp"
  ]);
  
  sheet.clearContents();
  sheet.appendRow([
    "SKU", "Product Name", "Movement Type", "Change Qty", "Previous Stock", "New Stock", "Reason", "Adjusted By", "Timestamp"
  ]);
  formatHeader(sheet, "#082B55");
  
  if (!inventory || inventory.length === 0) return;
  
  var rows = inventory.map(function(i) {
    return [
      i.sku || "",
      i.product_name || "",
      i.movement_type || "",
      i.change_qty || 0,
      i.previous_stock || 0,
      i.new_stock || 0,
      i.reason || "",
      i.adjusted_by || "",
      i.timestamp || new Date().toISOString()
    ];
  });
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}

function getOrCreateSheet(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
  }
  return sheet;
}

function formatHeader(sheet, colorHex) {
  var header = sheet.getRange(1, 1, 1, sheet.getLastColumn());
  header.setBackground(colorHex);
  header.setFontColor("#FFFFFF");
  header.setFontWeight("bold");
  header.setFontFamily("Arial");
  sheet.setFrozenRows(1);
}
'''
    return {"script": code}
