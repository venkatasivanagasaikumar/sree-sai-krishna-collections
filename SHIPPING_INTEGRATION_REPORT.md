# Sree Sai Krishna Collections (SSK) – Shipping & Logistics Integration Report

This document details the domestic shipping infrastructure, Indian postal code intelligence, carrier integrations, packing slip generation, and cash-on-delivery (COD) reconciliation procedures for Sree Sai Krishna Collections.

---

## 1. Domestic Shipping Policies & Cost Model

SSK operates within the Indian domestic market, shipping imitation jewellery, 1-gram gold ornaments, and hair accessories from its primary fulfillment center in Secunderabad, Telangana.

| Rule Parameter | Configuration | Business Justification |
| :--- | :---: | :--- |
| **Free Shipping Threshold** | **₹999.00** | Encourages basket building (average order value target ₹1,400) |
| **Standard Delivery Fee** | **₹79.00** | Subsidizes domestic surface courier costs for low-value orders |
| **COD Availability** | **Enabled** | 68% of initial Indian jewellery shoppers prefer COD |
| **COD Minimum Order** | **₹299.00** | Prevents shipping costs exceeding item margins on micro-orders |
| **COD Maximum Order** | **₹50,000.00** | Manages cash transit risk; high-value bridal sets require prepaid |

---

## 2. Indian PIN Code Intelligence & Zonal Serviceability

The `ShippingService` (`backend/app/services/shipping_service.py`) validates postal codes using regular expression pattern `^[1-9][0-9]{5}$` and categorizes delivery zones:

### Zone Classifications

```
+--------------------+-------------------------------------------+---------------+---------------+
| Zone Type          | Sample Postal Code Prefixes               | Delivery Time | COD Allowed?  |
+--------------------+-------------------------------------------+---------------+---------------+
| Metro & Capital    | Hyderabad (500), Mumbai (400), Bengaluru  | 2-4 Days      | Yes           |
| Cities             | (560), Delhi (110), Chennai (600),        |               |               |
|                    | Kolkata (700), Pune (411), Ahmedabad (380)|               |               |
+--------------------+-------------------------------------------+---------------+---------------+
| Standard Domestic  | Tier 2 & Tier 3 cities across all states  | 4-7 Days      | Yes           |
| (Non-Metro)        |                                           |               |               |
+--------------------+-------------------------------------------+---------------+---------------+
| Remote / Special   | Northeast (79), Jammu & Kashmir (19),     | 6-9 Days      | No (Prepaid   |
| Territories        | Islands, high-altitude border areas       |               | Only)         |
+--------------------+-------------------------------------------+---------------+---------------+
```

### Public API Endpoint
- **URL:** `GET /api/v1/shipping/serviceability/{pincode}`
- **Usage:** Queried in real-time as the customer enters their delivery address during checkout.
- **Sample Response:**
  ```json
  {
    "serviceable": true,
    "pincode": "500003",
    "zone": "Metro",
    "estimated_delivery": "2-4 Business Days",
    "cod_available": true,
    "free_shipping_threshold": 999.0,
    "standard_shipping_fee": 79.0,
    "courier_partners": ["Blue Dart Express", "Delhivery Direct", "DTDC Air"]
  }
  ```

---

## 3. Carrier Logistics Operations: Automated vs Manual

The platform supports two operational modes:

### Mode 1: Verified Manual Logistics Mode (Default Launch Mode)
- **Primary Couriers:** Blue Dart Express, Delhivery Surface, India Post Speed Post.
- **Workflow:**
  1. Staff packs jewellery in bubble-wrap tamper-evident security envelopes.
  2. Order Manager navigates to `/admin/orders` and clicks **Create Shipment**.
  3. Enters carrier name and AWB number provided by the courier desk.
  4. The system automatically marks the order as `SHIPPED` and dispatches the customer tracking email with live tracking URL.

### Mode 2: Automated Shiprocket API Mode
- Ready for integration when daily volume exceeds 50 orders/day.
- Can be configured to automatically request pickups and download carrier labels via Shiprocket REST APIs.

---

## 4. Thermal Shipping Label & Packing Slip Generator

In compliance with Indian e-commerce standards, the platform generates 4x6 inch print-ready thermal shipping labels via `GET /api/v1/shipping/orders/{order_id}/label`.

### Key Elements on Printed Label:
1. **Brand Identity:** Sree Sai Krishna Collections banner and helpline.
2. **AWB / Tracking Number:** High-contrast carrier barcode & AWB string.
3. **Payment Badge:**
   - For COD: `COLLECT CASH ON DELIVERY: ₹XXXX.00` in solid black callout box.
   - For Prepaid: `PREPAID - DO NOT COLLECT CASH`.
4. **Delivery Address:** Clean layout with highlighted 6-digit postal code and customer mobile number.
5. **Item Manifest:** Item SKUs, titles, and quantities packed inside the parcel.

---

## 5. Webhook Milestones & Real-Time Tracking

When courier webhooks deliver milestone updates to `POST /api/v1/shipping/webhook`:
- **`IN_TRANSIT`**: Timeline appended.
- **`OUT_FOR_DELIVERY`**: Customer notified parcel is out with courier executive.
- **`DELIVERED`**: Order status transitioned to `DELIVERED`. If payment method was COD, `payment_status` is updated to `PAID` with `cod_collected_at` timestamp.
- **`RTO` (Return to Origin)**: Order status updated to `RETURNED_TO_ORIGIN`, alerting customer support.

---

## 6. COD Reconciliation Subsystem

The Cash on Delivery reconciliation endpoint (`GET /api/v1/shipping/cod-reconciliation`) provides the business owner with live settlement tracking:

```json
{
  "total_cod_orders": 8,
  "total_cod_value": 11450.0,
  "collected_orders_count": 5,
  "collected_value": 7250.0,
  "pending_collection_value": 4200.0,
  "currency": "INR"
}
```
This protects the business from courier remittance discrepancies and delayed COD payments.
