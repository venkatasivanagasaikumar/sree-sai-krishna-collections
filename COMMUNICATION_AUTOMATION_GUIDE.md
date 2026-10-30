# SSK Customer Communication Automation Guide

**Brand:** Sree Sai Krishna Collections (SSK)  
**Target Market:** India  
**System Architecture:** Event-Driven Centralized Outbox Pattern (FastAPI + MongoDB)

---

## 1. System Architecture: The Outbox Pattern

To prevent notification failures from disrupting order checkouts or database updates, Sree Sai Krishna Collections employs a resilient **Centralized Notification Engine**:

```
+---------------------------------------------------------------------------------------------------+
|                                     CUSTOMER ORDER LIFECYCLE                                      |
+---------------------------------------------------------------------------------------------------+
                                                  │
                 ┌────────────────────────────────┴────────────────────────────────┐
                 ▼                                                                 ▼
        Prepaid (Razorpay)                                                 Cash on Delivery
        `PAYMENT_CONFIRMED`                                                `COD_CONFIRMED`
                 │                                                                 │
                 └────────────────────────────────┬────────────────────────────────┘
                                                  ▼
                         NotificationService.dispatch_order_event(...)
                                                  │
            ┌─────────────────────────────────────┼─────────────────────────────────────┐
            ▼                                     ▼                                     ▼
1. Idempotency Check                  2. Automated Invoicing              3. Outbox Registration
`db.notification_events`             `InvoiceService.generate_...`        `db.notification_outbox`
(blocks duplicate triggers)          (issues GST Tax Invoice)             (persists event state)
                                                  │
                 ┌────────────────────────────────┴────────────────────────────────┐
                 ▼                                                                 ▼
      Email Service Dispatch                                            WhatsApp Service Dispatch
  - Attaches generated PDF invoice                                  - Checks customer opt-out status
  - Dispatches via SMTP Gateway                                     - Normalizes Indian phone (+91)
  - Logs to `db.notification_logs`                                  - Dispatches Meta Cloud API v19
                                                                    - Logs to `db.notification_logs`
```

---

## 2. Event Dispatching Reference

The backend exposes a single orchestration method:  
`NotificationService.dispatch_order_event(order_id, event_name, extra_data, actor)`

### Supported Events:
1. **`ORDER_PLACED`**: Dispatched immediately upon checkout completion for online orders awaiting payment.
2. **`PAYMENT_CONFIRMED`**: Dispatched when Razorpay signature verification succeeds. **Automatically triggers GST Tax Invoice creation (`SSK-INV-YYYY-XXXX`) and attaches PDF to confirmation email.**
3. **`COD_CONFIRMED`**: Dispatched when a Cash on Delivery order is placed. Triggers invoice creation and sends WhatsApp confirmation.
4. **`ORDER_PACKED`**: Dispatched when store staff marks order status as `PACKED` after quality inspection.
5. **`ORDER_SHIPPED`**: Dispatched when courier details (Carrier & AWB) are recorded. Sends tracking URL to email and WhatsApp.
6. **`OUT_FOR_DELIVERY`**: Dispatched when logistics webhook signals delivery executive is in transit.
7. **`ORDER_DELIVERED`**: Dispatched when package delivery is confirmed. Marks COD orders as `PAID`.
8. **`ORDER_CANCELLED`**: Dispatched on customer or admin cancellation. Restocks inventory movements.
9. **`REFUND_INITIATED`**: Dispatched on refund initiation. **Automatically issues official GST Tax Credit Note (`SSK-CN-YYYY-XXXX`).**
10. **`REFUND_COMPLETED`**: Dispatched when gateway confirms funds transfer.

---

## 3. Administrator Operations Guide

Staff members can manage and monitor all customer communications directly from the Seller Panel:

### A. Accessing the Communications Hub (`/admin/communications`)
Navigate to **Seller Panel &rarr; WhatsApp & Invoices**:
- **Health Indicators:** Check whether WhatsApp Cloud API and SMTP are live or running in Simulation Mode.
- **Interactive Test Tools:**
  - *Test WhatsApp:* Enter a mobile number, select a template (e.g. `order_packed`), and click **Dispatch**.
  - *Test Email:* Enter a test email address and click **Send**.
- **Audit Table & Retry Action:**
  - View real-time logs with channel badges, recipient, template name, and status (`delivered`, `read`, `sent`, `simulated`, `failed`).
  - Click the **Resend** button next to any failed notification to re-trigger transmission.

### B. Order Drawer Invoicing Actions (`/admin/orders`)
On the Orders table, each row features:
- **`Invoice` Button:** Downloads the generated GST Tax Invoice PDF immediately.
- **`Send` (Bell) Button:** Prompts to resend both WhatsApp and Email updates to the customer.
- **`Slip` Button:** Opens the print-ready thermal packing slip.

---

## 4. Customer Portal Guide

Customers have complete visibility and control over their communication preferences and documents:
- **`Account &rarr; My Orders & Invoices`**: Displays order history with a dedicated **Download Tax Invoice (PDF)** button on each order card.
- **`Account &rarr; WhatsApp & Alerts`**: Allows customers to toggle WhatsApp order notifications on/off, change their preferred 10-digit mobile number, and toggle email notifications with recorded consent timestamps.
- **`Track Order (/account/orders/{orderId})`**: Provides real-time timeline checkpoints, courier partner details, AWB tracking link, and one-click PDF invoice download.

---

## 5. Troubleshooting & FAQ

### 1. WhatsApp Notifications are showing "simulated_sent"
- **Reason:** `WHATSAPP_ENABLED` is `false` or Meta credentials are not configured in `.env`.
- **Solution:** Follow Meta Cloud API setup in `REQUIRED_ENVIRONMENT_VARIABLES.md` and set `WHATSAPP_ENABLED=true`.

### 2. Customer did not receive WhatsApp message
- Check if the customer opted out under `Account &rarr; WhatsApp & Alerts` (log will show `opted_out`).
- Verify the phone number is an active WhatsApp number formatted as a valid 10-digit Indian mobile.
- Verify the Meta access token has not expired. Use a Permanent System User Token for production.

### 3. Invoice PDF looks blank or has missing data
- Ensure `ReportLab` is installed (`pip show reportlab`).
- Invoices are stored in `backend/data/invoices/`. The system dynamically regenerates any missing PDF if deleted from disk.
