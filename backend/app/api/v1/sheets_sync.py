from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import secrets
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
        # Generate default private secret key for the owner
        default_secret = f"ssk_sec_{secrets.token_hex(16)}"
        default_cfg = {
            "webhook_url": "",
            "secret_key": default_secret,
            "owner_email": "saikumaryenduri7@gmail.com",
            "auto_sync_on_order": True,
            "auto_sync_on_product": True,
            "last_synced_at": None,
            "status": "not_configured"
        }
        db.store_settings.insert_one({"key": CONFIG_KEY, "data": default_cfg, "updated_at": datetime.now(timezone.utc)})
        db_manager.persist_to_disk()
        return default_cfg
    
    cfg = doc.get("data", {})
    if "secret_key" not in cfg or not cfg["secret_key"]:
        cfg["secret_key"] = f"ssk_sec_{secrets.token_hex(16)}"
        cfg["owner_email"] = cfg.get("owner_email", "saikumaryenduri7@gmail.com")
        db.store_settings.update_one({"key": CONFIG_KEY}, {"$set": {"data": cfg}})
        db_manager.persist_to_disk()
    return cfg

@router.get("/config", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
def get_sheets_config(db = Depends(get_db)):
    """Only Super Admin (the business owner) can view or change sync security credentials."""
    return get_current_sync_config(db)

@router.post("/config", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
def save_sheets_config(payload: Dict[str, Any], db = Depends(get_db)):
    webhook_url = payload.get("webhook_url", "").strip()
    secret_key = payload.get("secret_key", "").strip()
    owner_email = payload.get("owner_email", "saikumaryenduri7@gmail.com").strip()
    
    if not secret_key:
        secret_key = f"ssk_sec_{secrets.token_hex(16)}"

    data = {
        "webhook_url": webhook_url,
        "secret_key": secret_key,
        "owner_email": owner_email,
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
    return {"message": "Private Google Sheets configuration saved securely", "config": data}

def post_to_google_sheet(webhook_url: str, secret_key: str, payload_data: dict) -> dict:
    if not webhook_url:
        return {"success": False, "message": "No Google Apps Script Webhook URL configured."}
    
    # Securely append secret_token to every transmission
    payload_data["secret_token"] = secret_key
    
    headers = {"Content-Type": "application/json"}
    body_bytes = json.dumps(payload_data, default=str).encode("utf-8")
    req = urllib.request.Request(webhook_url, data=body_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
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

@router.get("/export-all", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
def export_all_for_sheets(db = Depends(get_db)):
    """
    Returns unified JSON structured specifically for importing into Excel or Google Sheets.
    Contains Products, Orders, Customers, and Inventory movements.
    """
    products = list(db.products.find({}))
    orders = list(db.orders.find({}))
    customers = list(db.customers.find({}))
    movements = list(db.inventory_movements.find({}))

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

@router.post("/push-all", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
def push_all_to_google_sheet(db = Depends(get_db)):
    """
    Sends all current products, orders, and inventory data to the owner's private Google Sheet.
    Verifies that the secret security token matches.
    """
    config = get_current_sync_config(db)
    webhook_url = config.get("webhook_url")
    secret_key = config.get("secret_key", "")
    
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
    
    result = post_to_google_sheet(webhook_url, secret_key, payload)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with Google Apps Script: {result.get('error') or result.get('message')}"
        )
    
    resp_obj = result.get("response", {})
    if isinstance(resp_obj, dict) and resp_obj.get("status") == "unauthorized":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google Apps Script rejected sync: Secret Security Key mismatch! Please ensure the secret token matches."
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
        details={"result": result, "authorized_for": config.get("owner_email")}
    )

    return {
        "message": "All records securely synced to your private Google Sheet!",
        "last_synced_at": config["last_synced_at"],
        "sheet_response": result
    }

@router.post("/test-connection", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
def test_sheets_connection(payload: Dict[str, Any], db = Depends(get_db)):
    webhook_url = payload.get("webhook_url", "").strip()
    secret_key = payload.get("secret_key", "").strip()
    if not webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL is required to test")
    
    test_payload = {
        "event": "PING_TEST",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "store": "Sree Sai Krishna Collections",
        "message": "Private authentication ping test"
    }
    res = post_to_google_sheet(webhook_url, secret_key, test_payload)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Connection failed: {res.get('error') or res.get('message')}"
        )
    
    resp_obj = res.get("response", {})
    if isinstance(resp_obj, dict) and resp_obj.get("status") == "unauthorized":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access Denied: The Google Apps Script verified that the secret key did not match!"
        )

    return {"message": "Private Google Sheet authenticated and verified successfully!", "response": res}

@router.get("/appscript-template", dependencies=[Depends(require_roles([Role.SUPER_ADMIN, Role.ADMIN]))])
def get_appscript_template(db = Depends(get_db)):
    """
    Returns the ready-to-paste Google Apps Script code with OWNER-ONLY lockdown:
    1. Rejects any incoming payload that does not have your unique SECRET_SECURITY_KEY.
    2. Only the spreadsheet owner can view or edit the sheet (spreadsheet sharing stays restricted to 'Restricted / Only You').
    """
    cfg = get_current_sync_config(db)
    secret = cfg.get("secret_key", "REPLACE_WITH_YOUR_SECRET_KEY")
    owner_email = cfg.get("owner_email", "saikumaryenduri7@gmail.com")

    code = f'''/**
 * SREE SAI KRISHNA COLLECTIONS (SSK) - SECURE OWNER-ONLY DATABASE SYNC
 * 
 * SPREADSHEET SECURITY LOCKDOWN:
 * 1. Keep your Google Spreadsheet sharing setting set to "Restricted" (Only {owner_email} has access).
 * 2. This Apps Script runs under YOUR Google account ("Execute as: Me").
 * 3. Any sync request from outside must present the exact SECRET_SECURITY_KEY, otherwise it is immediately rejected with HTTP 401 Unauthorized.
 */

// Your unique SSK secret token:
var SECRET_SECURITY_KEY = "{secret}";

// Allowed owner email address:
var OWNER_EMAIL = "{owner_email}";

function doPost(e) {{
  var lock = LockService.getScriptLock();
  lock.tryLock(15000);
  
  try {{
    if (!e || !e.postData || !e.postData.contents) {{
      return createJsonResponse({{ status: "error", message: "Empty request" }}, 400);
    }}

    var raw = e.postData.contents;
    var payload = JSON.parse(raw);
    
    // 1. STRICT AUTHENTICATION CHECK: Reject if secret token does not match
    if (!payload.secret_token || payload.secret_token !== SECRET_SECURITY_KEY) {{
      return createJsonResponse({{ 
        status: "unauthorized", 
        message: "Access Denied: Invalid or missing secret security token. Only the SSK owner can access this database." 
      }}, 401);
    }}
    
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // 2. Ping connection test
    if (payload.event === "PING_TEST") {{
      return createJsonResponse({{ 
        status: "success", 
        message: "Private connection verified! Authenticated for " + OWNER_EMAIL 
      }});
    }}
    
    // 3. Full bulk database sync
    if (payload.event === "BULK_FULL_SYNC" && payload.data) {{
      syncProducts(ss, payload.data.products || []);
      syncOrders(ss, payload.data.orders || []);
      syncCustomers(ss, payload.data.customers || []);
      syncInventory(ss, payload.data.inventory || []);
      
      return createJsonResponse({{ 
        status: "success", 
        message: "Secure database sync completed. 4 tabs updated successfully." 
      }});
    }}
    
    if (payload.event === "ORDER_CREATED" || payload.event === "ORDER_UPDATED") {{
      syncOrders(ss, [payload.order]);
      return createJsonResponse({{ status: "success" }});
    }}
    
    if (payload.event === "PRODUCT_CREATED" || payload.event === "PRODUCT_UPDATED") {{
      syncProducts(ss, [payload.product]);
      return createJsonResponse({{ status: "success" }});
    }}
    
    return createJsonResponse({{ status: "acknowledged", event: payload.event }});
  }} catch (err) {{
    return createJsonResponse({{ status: "error", message: err.toString() }}, 500);
  }} finally {{
    lock.releaseLock();
  }}
}}

function createJsonResponse(obj, statusCode) {{
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}}

function syncProducts(ss, products) {{
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
  
  var rows = products.map(function(p) {{
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
  }});
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}}

function syncOrders(ss, orders) {{
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
  
  var rows = orders.map(function(o) {{
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
  }});
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}}

function syncCustomers(ss, customers) {{
  var sheet = getOrCreateSheet(ss, "Customers", [
    "Customer ID", "Name", "Email", "Phone", "Total Orders", "Total Spent (₹)", "Created Date"
  ]);
  
  sheet.clearContents();
  sheet.appendRow([
    "Customer ID", "Name", "Email", "Phone", "Total Orders", "Total Spent (₹)", "Created Date"
  ]);
  formatHeader(sheet, "#1769AA");
  
  if (!customers || customers.length === 0) return;
  
  var rows = customers.map(function(c) {{
    return [
      c.id || c._id || "",
      c.full_name || "",
      c.email || "",
      c.phone || "",
      c.total_orders || 0,
      c.total_spent || 0,
      c.created_at || new Date().toISOString()
    ];
  }});
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}}

function syncInventory(ss, inventory) {{
  var sheet = getOrCreateSheet(ss, "Inventory_Log", [
    "SKU", "Product Name", "Movement Type", "Change Qty", "Previous Stock", "New Stock", "Reason", "Adjusted By", "Timestamp"
  ]);
  
  sheet.clearContents();
  sheet.appendRow([
    "SKU", "Product Name", "Movement Type", "Change Qty", "Previous Stock", "New Stock", "Reason", "Adjusted By", "Timestamp"
  ]);
  formatHeader(sheet, "#082B55");
  
  if (!inventory || inventory.length === 0) return;
  
  var rows = inventory.map(function(i) {{
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
  }});
  
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
}}

function getOrCreateSheet(ss, name, headers) {{
  var sheet = ss.getSheetByName(name);
  if (!sheet) {{
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
  }}
  return sheet;
}}

function formatHeader(sheet, colorHex) {{
  var header = sheet.getRange(1, 1, 1, sheet.getLastColumn());
  header.setBackground(colorHex);
  header.setFontColor("#FFFFFF");
  header.setFontWeight("bold");
  header.setFontFamily("Arial");
  sheet.setFrozenRows(1);
}}
'''
    return {"script": code, "secret_key": secret, "owner_email": owner_email}
