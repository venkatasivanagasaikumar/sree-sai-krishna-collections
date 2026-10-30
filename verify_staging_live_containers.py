#!/usr/bin/env python3
"""
SSK Staging Live Container End-to-End Verification Script
Runs Phase 3, Phase 4, Phase 5, and Phase 6 against the live Docker containers on http://localhost:8080
"""

import sys
import time
import json
import io
import os
import subprocess
import requests

BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api/v1"

results = []

def record(step: str, status: str, details: str):
    print(f"[{status}] {step}: {details}")
    results.append({
        "step": step,
        "status": status,
        "details": details
    })

def main():
    print("=" * 80)
    print("SSK STAGING LIVE CONTAINER VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 80)

    # ---------------------------------------------------------
    # PHASE 3: Base HTTP & Gateway Verification
    # ---------------------------------------------------------
    print("\n--- PHASE 3: Base Gateway & Health Checks ---")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200 and r.json().get("status") == "healthy":
            record("Phase 3.1: Health Probe", "PASS", f"HTTP {r.status_code} - {r.json()}")
        else:
            record("Phase 3.1: Health Probe", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 3.1: Health Probe", "FAIL", str(e))

    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=5)
        data = r.json()
        if r.status_code == 200 and data.get("status") == "ready" and data.get("database", {}).get("type") == "mongodb_live":
            record("Phase 3.2: Readiness & Live MongoDB Probe", "PASS", f"HTTP {r.status_code} - DB: {data.get('database')}")
        else:
            record("Phase 3.2: Readiness & Live MongoDB Probe", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 3.2: Readiness & Live MongoDB Probe", "FAIL", str(e))

    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        if r.status_code == 200 and '<div id="root">' in r.text:
            record("Phase 3.3: Frontend SPA Routing", "PASS", f"HTTP {r.status_code} - React SPA root rendered ({len(r.text)} bytes)")
        else:
            record("Phase 3.3: Frontend SPA Routing", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 3.3: Frontend SPA Routing", "FAIL", str(e))

    # ---------------------------------------------------------
    # PHASE 4: End-to-End Business Flow Verification
    # ---------------------------------------------------------
    print("\n--- PHASE 4: End-to-End Business Flow ---")
    # Step 4.1: Storefront Catalog Listing
    try:
        r = requests.get(f"{API_BASE}/products", timeout=5)
        if r.status_code == 200:
            products_data = r.json()
            items = products_data.get("products", [])
            total = products_data.get("total", len(items))
            record("Phase 4.1: Storefront Catalog Listing", "PASS", f"HTTP {r.status_code} - {len(items)} active products returned (Total: {total})")
        else:
            record("Phase 4.1: Storefront Catalog Listing", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.1: Storefront Catalog Listing", "FAIL", str(e))

    # Step 4.2: Customer Registration
    cust_ts = int(time.time())
    cust_email = f"staging_shopper_{cust_ts}@sskstaging.internal"
    cust_password = f"CustomerPass{cust_ts}!"
    cust_token = None
    cust_id = None
    try:
        reg_payload = {
            "email": cust_email,
            "password": cust_password,
            "full_name": f"Staging Customer {cust_ts}",
            "phone": "+91 98480 99999"
        }
        r = requests.post(f"{API_BASE}/auth/register", json=reg_payload, timeout=5)
        if r.status_code in [200, 201]:
            data = r.json()
            cust_token = data.get("access_token")
            cust_id = data.get("user", {}).get("id")
            record("Phase 4.2: Customer Registration", "PASS", f"HTTP {r.status_code} - Created customer: {cust_email} (ID: {cust_id})")
        else:
            record("Phase 4.2: Customer Registration", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.2: Customer Registration", "FAIL", str(e))

    # Step 4.3: Customer Login
    try:
        login_payload = {
            "email": cust_email,
            "password": cust_password
        }
        r = requests.post(f"{API_BASE}/auth/login", json=login_payload, timeout=5)
        if r.status_code == 200:
            data = r.json()
            cust_token = data.get("access_token")
            record("Phase 4.3: Customer Login", "PASS", f"HTTP {r.status_code} - JWT Access Token issued")
        else:
            record("Phase 4.3: Customer Login", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.3: Customer Login", "FAIL", str(e))

    # Step 4.4: Admin Login
    admin_token = None
    try:
        admin_login_payload = {
            "email": "admin@sskcollections.com",
            "password": "Admin@SSK2026!"
        }
        r = requests.post(f"{API_BASE}/auth/login", json=admin_login_payload, timeout=5)
        if r.status_code == 200:
            data = r.json()
            admin_token = data.get("access_token")
            record("Phase 4.4: Admin Authentication", "PASS", f"HTTP {r.status_code} - Super Admin authenticated")
        else:
            record("Phase 4.4: Admin Authentication", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.4: Admin Authentication", "FAIL", str(e))

    # Step 4.5: Image Upload (Admin)
    uploaded_image_url = None
    uploaded_filename = None
    try:
        # Generate 1x1 PNG image
        fake_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x03\x00\x08\xfc\x02\xfe\xa79\x84\x9a\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {"file": ("test_choker.png", io.BytesIO(fake_png), "image/png")}
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{API_BASE}/upload", files=files, headers=headers, timeout=5)
        if r.status_code in [200, 201]:
            data = r.json()
            uploaded_image_url = data.get("url")
            uploaded_filename = uploaded_image_url.split("/")[-1]
            record("Phase 4.5: Admin Image Upload", "PASS", f"HTTP {r.status_code} - Saved to {uploaded_image_url}")
        else:
            record("Phase 4.5: Admin Image Upload", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.5: Admin Image Upload", "FAIL", str(e))

    # Step 4.6: Verify Uploaded Image over HTTP Nginx
    try:
        r = requests.get(f"{BASE_URL}{uploaded_image_url}", timeout=5)
        if r.status_code == 200 and len(r.content) > 0 and r.headers.get("content-type") == "image/png":
            record("Phase 4.6: Nginx Static Upload Proxy", "PASS", f"HTTP {r.status_code} - Successfully served {len(r.content)} bytes from disk via /uploads/")
        else:
            record("Phase 4.6: Nginx Static Upload Proxy", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 4.6: Nginx Static Upload Proxy", "FAIL", str(e))

    # Step 4.7: Product Creation (Admin)
    new_product_id = None
    test_sku = f"SSK-STG-E2E-{cust_ts % 10000}"
    initial_stock = 25
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        prod_payload = {
            "name": "Staging Verified Emerald Temple Choker",
            "sku": test_sku,
            "category": "Necklaces & Chains",
            "price": 1899.0,
            "mrp": 2999.0,
            "stock": initial_stock,
            "description": "Premium 1-gram micro gold plated temple choker set with hydro emerald stones.",
            "materials_and_finish": "Brass alloy with micro gold-plating finish (Imitation)",
            "jewelry_type": "1-Gram Gold Finish",
            "images": [uploaded_image_url or "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=600&q=80"],
            "status": "active"
        }
        r = requests.post(f"{API_BASE}/products", json=prod_payload, headers=headers, timeout=5)
        if r.status_code in [200, 201]:
            data = r.json()
            new_product_id = data.get("id") or str(data.get("_id"))
            record("Phase 4.7: Product Creation", "PASS", f"HTTP {r.status_code} - SKU: {test_sku} (ID: {new_product_id})")
        else:
            record("Phase 4.7: Product Creation", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.7: Product Creation", "FAIL", str(e))

    # Step 4.8: Add Item to Cart (Customer)
    cart_qty = 2
    try:
        headers = {"Authorization": f"Bearer {cust_token}"}
        cart_payload = {
            "product_id": new_product_id,
            "quantity": cart_qty
        }
        r = requests.post(f"{API_BASE}/cart/items", json=cart_payload, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            record("Phase 4.8: Customer Cart Add Item", "PASS", f"HTTP {r.status_code} - Added {cart_qty} units of {test_sku} to customer cart")
        else:
            record("Phase 4.8: Customer Cart Add Item", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.8: Customer Cart Add Item", "FAIL", str(e))

    # Step 4.9: Retrieve Cart
    try:
        headers = {"Authorization": f"Bearer {cust_token}"}
        r = requests.get(f"{API_BASE}/cart", headers=headers, timeout=5)
        if r.status_code == 200:
            cart_data = r.json()
            subtotal = cart_data.get("subtotal", 0.0)
            items_count = len(cart_data.get("items", []))
            record("Phase 4.9: Customer Cart Retrieval", "PASS", f"HTTP {r.status_code} - Cart items: {items_count}, Subtotal: Rs. {subtotal}")
        else:
            record("Phase 4.9: Customer Cart Retrieval", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.9: Customer Cart Retrieval", "FAIL", str(e))

    # Step 4.10: COD Checkout & Order Creation
    created_order_id = None
    created_final_amount = None
    try:
        headers = {"Authorization": f"Bearer {cust_token}"}
        order_payload = {
            "shipping_address": {
                "name": f"Staging Customer {cust_ts}",
                "phone": "+91 98480 99999",
                "address_line1": "Flat 402, Sai Krishna Enclave",
                "address_line2": "Beside Temple Road",
                "city": "Hyderabad",
                "state": "Telangana",
                "pincode": "500081",
                "landmark": "Near SSK Collections"
            },
            "payment_method": "COD",
            "notes": "Staging E2E Container Verification Order"
        }
        r = requests.post(f"{API_BASE}/orders", json=order_payload, headers=headers, timeout=5)
        if r.status_code in [200, 201]:
            data = r.json()
            created_order_id = data.get("order_id")
            created_final_amount = data.get("final_amount")
            init_status = data.get("order_status")
            record("Phase 4.10: COD Checkout & Order Placement", "PASS", f"HTTP {r.status_code} - Order: {created_order_id}, Amount: Rs. {created_final_amount}, Status: {init_status}")
        else:
            record("Phase 4.10: COD Checkout & Order Placement", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.10: COD Checkout & Order Placement", "FAIL", str(e))

    # Step 4.11: Inventory Stock Decrement Verification
    try:
        r = requests.get(f"{API_BASE}/products/{test_sku}", timeout=5)
        if r.status_code == 200:
            prod_data = r.json()
            remaining_stock = prod_data.get("stock")
            expected_stock = initial_stock - cart_qty
            if remaining_stock == expected_stock:
                record("Phase 4.11: Atomic Stock Decrement", "PASS", f"Initial: {initial_stock}, Ordered: {cart_qty}, Remaining: {remaining_stock}")
            else:
                record("Phase 4.11: Atomic Stock Decrement", "FAIL", f"Expected stock {expected_stock}, found {remaining_stock}")
        else:
            record("Phase 4.11: Atomic Stock Decrement", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.11: Atomic Stock Decrement", "FAIL", str(e))

    # Step 4.12: Invoice PDF Retrieval & Validation
    invoice_id_to_check = None
    try:
        headers = {"Authorization": f"Bearer {cust_token}"}
        r = requests.get(f"{API_BASE}/invoices/my-invoices", headers=headers, timeout=5)
        if r.status_code == 200:
            invoices = r.json()
            if len(invoices) > 0:
                inv = invoices[0]
                invoice_id_to_check = inv.get("invoice_id") or inv.get("invoice_number")
                # Now download PDF
                r_pdf = requests.get(f"{API_BASE}/invoices/{invoice_id_to_check}/download", headers=headers, timeout=10)
                if r_pdf.status_code == 200 and r_pdf.headers.get("content-type") == "application/pdf" and r_pdf.content.startswith(b"%PDF"):
                    record("Phase 4.12: Invoice PDF Generation & Download", "PASS", f"HTTP 200 - Downloaded valid PDF ({len(r_pdf.content)} bytes) for Invoice: {invoice_id_to_check}")
                else:
                    record("Phase 4.12: Invoice PDF Generation & Download", "FAIL", f"HTTP {r_pdf.status_code} - CT: {r_pdf.headers.get('content-type')}")
            else:
                record("Phase 4.12: Invoice PDF Generation & Download", "FAIL", "No invoices found for customer")
        else:
            record("Phase 4.12: Invoice PDF Generation & Download", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.12: Invoice PDF Generation & Download", "FAIL", str(e))

    # Step 4.13: Customer Order Tracking
    try:
        headers = {"Authorization": f"Bearer {cust_token}"}
        r = requests.get(f"{API_BASE}/orders/{created_order_id}", headers=headers, timeout=5)
        if r.status_code == 200:
            ord_data = r.json()
            ord_status = ord_data.get("order_status") or ord_data.get("status")
            record("Phase 4.13: Customer Order Tracking", "PASS", f"HTTP {r.status_code} - Order {created_order_id} status: {ord_status}")
        else:
            record("Phase 4.13: Customer Order Tracking", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.13: Customer Order Tracking", "FAIL", str(e))

    # Step 4.14: Admin Order Management (Update to Shipped)
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        status_payload = {
            "status": "Shipped",
            "carrier_name": "BlueDart Express",
            "tracking_number": "BLU-STG-998877",
            "internal_notes": "Staging dispatched via express air"
        }
        r = requests.put(f"{API_BASE}/orders/admin/{created_order_id}/status", json=status_payload, headers=headers, timeout=5)
        if r.status_code == 200:
            resp_data = r.json()
            msg = resp_data.get("message")
            record("Phase 4.14: Admin Order Management", "PASS", f"HTTP {r.status_code} - {msg}")
        else:
            record("Phase 4.14: Admin Order Management", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 4.14: Admin Order Management", "FAIL", str(e))

    # Step 4.15: MongoDB Real Document Verification via Mongosh
    try:
        cmd = f'docker exec ssk-mongodb-staging mongosh --quiet ssk_staging_db --eval "db.orders.findOne({{order_id: \'{created_order_id}\'}}, {{_id: 1, order_id: 1, order_status: 1, final_amount: 1}})"'
        out = subprocess.check_output(cmd, shell=True, text=True)
        if created_order_id and created_order_id in out and "Shipped" in out:
            record("Phase 4.15: MongoDB Live Document Verification", "PASS", f"Found live document in MongoDB: {out.strip()}")
        else:
            record("Phase 4.15: MongoDB Live Document Verification", "FAIL", f"Output: {out}")
    except Exception as e:
        record("Phase 4.15: MongoDB Live Document Verification", "FAIL", str(e))

    # ---------------------------------------------------------
    # PHASE 5: Container Restart & Persistence Verification
    # ---------------------------------------------------------
    print("\n--- PHASE 5: Container Restart & Persistence Verification ---")
    print(f"Recorded state before restarts: SKU={test_sku}, Order={created_order_id}, Image={uploaded_filename}")

    # Restart backend-staging and frontend-staging
    print("Restarting backend-staging and frontend-staging containers...")
    subprocess.run("docker compose -f docker-compose.staging.yml restart backend-staging frontend-staging", shell=True, check=True)
    time.sleep(15) # Wait for health checks

    # Verify backend and frontend recovered
    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=5)
        if r.status_code == 200 and r.json().get("status") == "ready":
            record("Phase 5.1: App Gateway Recovery After App Restart", "PASS", f"HTTP 200 - App ready after restarting backend & frontend")
        else:
            record("Phase 5.1: App Gateway Recovery After App Restart", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 5.1: App Gateway Recovery After App Restart", "FAIL", str(e))

    # Verify product persistence
    try:
        r = requests.get(f"{API_BASE}/products/{test_sku}", timeout=5)
        if r.status_code == 200 and r.json().get("sku") == test_sku and r.json().get("stock") == (initial_stock - cart_qty):
            record("Phase 5.2: Product & Stock Persistence Across Restart", "PASS", f"HTTP 200 - Product {test_sku} still present with stock {r.json().get('stock')}")
        else:
            record("Phase 5.2: Product & Stock Persistence Across Restart", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 5.2: Product & Stock Persistence Across Restart", "FAIL", str(e))

    # Verify uploaded image persistence on volume
    try:
        r = requests.get(f"{BASE_URL}{uploaded_image_url}", timeout=5)
        if r.status_code == 200 and len(r.content) > 0 and r.headers.get("content-type") == "image/png":
            record("Phase 5.3: Uploaded Image Persistence Across Restart", "PASS", f"HTTP 200 - Uploaded image {uploaded_filename} served cleanly ({len(r.content)} bytes)")
        else:
            record("Phase 5.3: Uploaded Image Persistence Across Restart", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 5.3: Uploaded Image Persistence Across Restart", "FAIL", str(e))

    # Verify invoice PDF persistence on volume
    try:
        headers = {"Authorization": f"Bearer {cust_token}"}
        r = requests.get(f"{API_BASE}/invoices/{invoice_id_to_check}/download", headers=headers, timeout=10)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            record("Phase 5.4: Invoice PDF Persistence Across Restart", "PASS", f"HTTP 200 - Downloaded invoice {invoice_id_to_check} PDF ({len(r.content)} bytes)")
        else:
            record("Phase 5.4: Invoice PDF Persistence Across Restart", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 5.4: Invoice PDF Persistence Across Restart", "FAIL", str(e))

    # Restart mongodb-staging container
    print("Restarting mongodb-staging container...")
    subprocess.run("docker compose -f docker-compose.staging.yml restart mongodb-staging", shell=True, check=True)
    time.sleep(15) # Wait for MongoDB to become healthy and backend to reconnect

    # Verify database persistence across DB restart
    try:
        r = requests.get(f"{BASE_URL}/ready", timeout=5)
        if r.status_code == 200 and r.json().get("status") == "ready":
            record("Phase 5.5: Database Recovery After MongoDB Restart", "PASS", f"HTTP 200 - Database reconnected cleanly")
        else:
            record("Phase 5.5: Database Recovery After MongoDB Restart", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 5.5: Database Recovery After MongoDB Restart", "FAIL", str(e))

    try:
        r = requests.get(f"{API_BASE}/products/{test_sku}", timeout=5)
        if r.status_code == 200 and r.json().get("sku") == test_sku:
            record("Phase 5.6: MongoDB Named Volume Data Persistence", "PASS", f"HTTP 200 - Product {test_sku} persisted on named volume 'staging_mongo_data'")
        else:
            record("Phase 5.6: MongoDB Named Volume Data Persistence", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 5.6: MongoDB Named Volume Data Persistence", "FAIL", str(e))

    # ---------------------------------------------------------
    # PHASE 6: Backup and Restore Verification
    # ---------------------------------------------------------
    print("\n--- PHASE 6: Staging Backup & Restore Verification ---")
    backup_filename = None
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{API_BASE}/settings/backups/create?tag=staging_e2e_verification", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            backup_filename = data.get("backup", {}).get("filename")
            b_size = data.get("backup", {}).get("size_bytes")
            b_checksum = data.get("backup", {}).get("checksum")
            record("Phase 6.1: Staging Backup Creation", "PASS", f"HTTP 200 - Snapshot created: {backup_filename} ({b_size} bytes, SHA256: {b_checksum[:12]}...)")
        else:
            record("Phase 6.1: Staging Backup Creation", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 6.1: Staging Backup Creation", "FAIL", str(e))

    # Verify backup file on host filesystem
    backup_host_path = os.path.join("backend", "backups", backup_filename or "")
    if os.path.exists(backup_host_path) and os.path.getsize(backup_host_path) > 1000:
        record("Phase 6.2: Host Filesystem Backup Verification", "PASS", f"File exists on host: {backup_host_path} ({os.path.getsize(backup_host_path)} bytes)")
    else:
        record("Phase 6.2: Host Filesystem Backup Verification", "FAIL", f"Backup file not found or empty: {backup_host_path}")

    # Insert sentinel product into MongoDB
    sentinel_sku = f"SENTINEL-RESTORE-{cust_ts % 10000}"
    try:
        cmd = f'docker exec ssk-mongodb-staging mongosh --quiet ssk_staging_db --eval "db.products.insertOne({{sku: \'{sentinel_sku}\', name: \'Sentinel Restore Verification Product\', status: \'active\', price: 999, stock: 1}})"'
        subprocess.check_output(cmd, shell=True, text=True)
        # Check it exists
        r = requests.get(f"{API_BASE}/products/{sentinel_sku}", timeout=5)
        if r.status_code == 200:
            record("Phase 6.3: Sentinel Record Injection Pre-Restore", "PASS", f"Injected sentinel product {sentinel_sku} into live database")
        else:
            record("Phase 6.3: Sentinel Record Injection Pre-Restore", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 6.3: Sentinel Record Injection Pre-Restore", "FAIL", str(e))

    # Perform restore from backup snapshot
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = requests.post(f"{API_BASE}/settings/backups/restore", json={"filename": backup_filename}, headers=headers, timeout=60)
        if r.status_code == 200:
            rest_data = r.json()
            details = rest_data.get("details", {})
            cols = details.get("collections_restored", len(details.get("stats", {})))
            record("Phase 6.4: Controlled Database Restore Execution", "PASS", f"HTTP 200 - Restored from {backup_filename} ({cols} collections restored)")
        else:
            record("Phase 6.4: Controlled Database Restore Execution", "FAIL", f"HTTP {r.status_code} - {r.text}")
    except Exception as e:
        record("Phase 6.4: Controlled Database Restore Execution", "FAIL", str(e))

    # Verify sentinel product is purged by restore
    try:
        r = requests.get(f"{API_BASE}/products/{sentinel_sku}", timeout=5)
        if r.status_code == 404:
            record("Phase 6.5: Post-Restore State Integrity Verification", "PASS", f"HTTP 404 - Sentinel {sentinel_sku} correctly absent after restore")
        else:
            record("Phase 6.5: Post-Restore State Integrity Verification", "FAIL", f"HTTP {r.status_code} - Sentinel still exists!")
    except Exception as e:
        record("Phase 6.5: Post-Restore State Integrity Verification", "FAIL", str(e))

    # Verify original product survives restore
    try:
        r = requests.get(f"{API_BASE}/products/{test_sku}", timeout=5)
        if r.status_code == 200:
            record("Phase 6.6: Original Catalog Integrity After Restore", "PASS", f"HTTP 200 - Product {test_sku} intact with stock {r.json().get('stock')}")
        else:
            record("Phase 6.6: Original Catalog Integrity After Restore", "FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        record("Phase 6.6: Original Catalog Integrity After Restore", "FAIL", str(e))

    # Summary
    print("\n" + "=" * 80)
    print("COMPLETE VERIFICATION SUMMARY:")
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    print(f"Total Steps: {total_count} | Passed: {pass_count} | Failed: {total_count - pass_count}")
    print("=" * 80)
    for r in results:
        print(f"[{r['status']}] {r['step']}: {r['details']}")
    print("=" * 80)

    # Save detailed evidence json
    report_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_url": BASE_URL,
        "total_steps": total_count,
        "passed_steps": pass_count,
        "failed_steps": total_count - pass_count,
        "results": results
    }
    with open("staging_e2e_evidence.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

if __name__ == "__main__":
    main()
