from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.core.permissions import Role
from app.api.dependencies import require_roles

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])

def to_dt(val, fallback=None):
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    if isinstance(val, str):
        try:
            d = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d
        except Exception:
            pass
    return fallback

@router.get("/dashboard", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN, Role.ORDER_MANAGER]))])
def get_dashboard_kpis(days: int = 30, db = Depends(get_db)):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    all_orders = list(db.orders.find({}))
    period_orders = [o for o in all_orders if to_dt(o.get("created_at"), now) >= cutoff]
    today_orders = [o for o in all_orders if to_dt(o.get("created_at"), now) >= today_start]

    # Gross sales (all paid or confirmed orders)
    valid_sales_orders = [o for o in all_orders if o.get("order_status") not in ["CANCELLED", "PAYMENT_PENDING"]]
    gross_sales = sum(o.get("subtotal", 0) for o in valid_sales_orders)
    total_discounts = sum(o.get("discount_amount", 0) for o in valid_sales_orders)
    total_shipping_collected = sum(o.get("shipping_fee", 0) for o in valid_sales_orders)
    
    # Refunds
    all_refunds = list(db.refunds.find({}))
    total_refunds = sum(r.get("amount", 0) for r in all_refunds)
    
    net_sales = max(0.0, round(gross_sales - total_discounts + total_shipping_collected - total_refunds, 2))

    # Period sales
    period_valid = [o for o in period_orders if o.get("order_status") not in ["CANCELLED", "PAYMENT_PENDING"]]
    period_sales = sum(o.get("final_amount", 0) for o in period_valid)

    # Counts
    orders_awaiting_processing = sum(1 for o in all_orders if o.get("order_status") in ["ORDER_PLACED", "PAYMENT_CONFIRMED", "PROCESSING"])
    delivered_orders = sum(1 for o in all_orders if o.get("order_status") == "DELIVERED")
    return_requests = db.returns.count_documents({"status": "RETURN_REQUESTED"})
    
    # Products & Inventory
    active_products = db.products.count_documents({"status": "active"})
    low_stock_products = db.products.count_documents({"status": "active", "stock": {"$lte": 5}})

    # Order status distribution
    status_counts: Dict[str, int] = {}
    for o in all_orders:
        st = o.get("order_status", "UNKNOWN")
        status_counts[st] = status_counts.get(st, 0) + 1

    # Payment method breakdown
    payment_counts: Dict[str, int] = {}
    for o in all_orders:
        pm = o.get("payment_method", "OTHER")
        payment_counts[pm] = payment_counts.get(pm, 0) + 1

    # Top selling products
    top_products_cursor = db.products.find({"status": "active"}).sort("sales_count", -1).limit(5)
    top_products = []
    for tp in top_products_cursor:
        top_products.append({
            "id": str(tp["_id"]),
            "name": tp.get("name"),
            "sku": tp.get("sku"),
            "price": tp.get("price"),
            "sales_count": tp.get("sales_count", 0),
            "stock": tp.get("stock", 0)
        })

    # Recent orders (last 5)
    recent_orders = []
    for ro in sorted(all_orders, key=lambda x: to_dt(x.get("created_at"), now), reverse=True)[:5]:
        recent_orders.append({
            "order_id": ro.get("order_id"),
            "customer_name": ro.get("customer_name"),
            "final_amount": ro.get("final_amount"),
            "order_status": ro.get("order_status"),
            "payment_method": ro.get("payment_method"),
            "created_at": ro.get("created_at")
        })

    # Sales trends (last 7 days grouped)
    sales_trend = []
    for i in range(6, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_total = sum(
            o.get("final_amount", 0)
            for o in all_orders
            if to_dt(o.get("created_at")) and to_dt(o.get("created_at")).date() == day_date and o.get("order_status") not in ["CANCELLED", "PAYMENT_PENDING"]
        )
        sales_trend.append({
            "date": day_date.strftime("%b %d"),
            "sales": round(day_total, 2)
        })

    return {
        "kpis": {
            "total_orders": len(all_orders),
            "today_orders": len(today_orders),
            "orders_awaiting_processing": orders_awaiting_processing,
            "gross_sales": round(gross_sales, 2),
            "period_sales": round(period_sales, 2),
            "total_discounts": round(total_discounts, 2),
            "total_refunds": round(total_refunds, 2),
            "net_sales": net_sales,
            "delivered_orders": delivered_orders,
            "return_requests": return_requests,
            "active_products": active_products,
            "low_stock_products": low_stock_products
        },
        "order_status_distribution": status_counts,
        "payment_method_breakdown": payment_counts,
        "top_selling_products": top_products,
        "recent_orders": recent_orders,
        "sales_trend": sales_trend
    }

@router.get("/audit-logs", dependencies=[Depends(require_roles([Role.ADMIN, Role.SUPER_ADMIN]))])
def get_audit_logs(limit: int = 50, db = Depends(get_db)):
    cursor = db.audit_logs.find({}).sort("created_at", -1).limit(limit)
    logs = []
    for l in cursor:
        l["id"] = str(l["_id"])
        l.pop("_id", None)
        logs.append(l)
    return logs
