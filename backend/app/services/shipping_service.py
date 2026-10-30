import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.database import db_manager

# Major Indian Metro prefixes
METRO_PREFIXES = ("500", "501", "400", "401", "560", "110", "600", "700", "411", "380")
REMOTE_PREFIXES = ("79", "19", "74", "73")

class ShippingService:
    @staticmethod
    def validate_pincode(pincode: str) -> bool:
        """Validates that a PIN code is a 6-digit Indian postal code."""
        if not pincode:
            return False
        clean = pincode.strip()
        return bool(re.match(r"^[1-9][0-9]{5}$", clean))

    @classmethod
    def check_serviceability(cls, pincode: str) -> Dict[str, Any]:
        """Checks delivery timeline, COD availability, and partner courier for an Indian PIN code."""
        if not cls.validate_pincode(pincode):
            return {
                "serviceable": False,
                "pincode": pincode,
                "message": "Invalid Indian postal code. Must be a 6-digit number starting with 1-9."
            }

        pincode_clean = pincode.strip()
        prefix3 = pincode_clean[:3]
        prefix2 = pincode_clean[:2]

        if prefix3 in METRO_PREFIXES:
            zone = "Metro"
            estimated_days = "2-4 Business Days"
            couriers = ["Blue Dart Express", "Delhivery Direct", "DTDC Air"]
            cod_available = True
        elif prefix2 in REMOTE_PREFIXES:
            zone = "Remote / Special Territory"
            estimated_days = "6-9 Business Days"
            couriers = ["India Post Speed Post", "Delhivery Surface"]
            cod_available = False # Pre-paid only for high-risk remote zones
        else:
            zone = "Standard Domestic"
            estimated_days = "4-7 Business Days"
            couriers = ["Delhivery Surface", "Blue Dart Surface", "Ekart Logistics"]
            cod_available = True

        return {
            "serviceable": True,
            "pincode": pincode_clean,
            "zone": zone,
            "estimated_delivery": estimated_days,
            "cod_available": cod_available,
            "free_shipping_threshold": settings.FREE_SHIPPING_THRESHOLD,
            "standard_shipping_fee": settings.STANDARD_SHIPPING_FEE,
            "courier_partners": couriers
        }

    @staticmethod
    def calculate_shipping_fee(order_subtotal: float) -> float:
        """Returns ₹0 for orders >= ₹999; otherwise ₹79 standard shipping."""
        if order_subtotal >= settings.FREE_SHIPPING_THRESHOLD:
            return 0.0
        return settings.STANDARD_SHIPPING_FEE

    @classmethod
    def generate_shipping_label_html(cls, order: Dict[str, Any], tracking_info: Dict[str, Any]) -> str:
        """Generates a standard 4x6 thermal printable shipping label and packing slip."""
        order_id = order.get("order_id", "SSK-ORDER")
        awb = tracking_info.get("awb", f"AWB{order_id.replace('-', '')}")
        carrier = tracking_info.get("carrier", "Blue Dart Express")
        shipping_addr = order.get("shipping_address", {})
        
        customer_name = shipping_addr.get("name", order.get("customer_name", "Customer"))
        customer_phone = shipping_addr.get("phone", order.get("customer_phone", ""))
        line1 = shipping_addr.get("address_line1", "")
        line2 = shipping_addr.get("address_line2", "")
        city = shipping_addr.get("city", "")
        state = shipping_addr.get("state", "")
        pincode = shipping_addr.get("pincode", "")

        is_cod = order.get("payment_method") == "COD"
        final_amt = order.get("final_amount", 0.0)

        items_rows = ""
        for itm in order.get("items", []):
            items_rows += f"""
            <tr>
                <td style="padding: 4px; border: 1px solid #cbd5e1;">{itm.get('sku', 'SKU')}</td>
                <td style="padding: 4px; border: 1px solid #cbd5e1;">{itm.get('name', 'Product')[:32]}</td>
                <td style="padding: 4px; border: 1px solid #cbd5e1; text-align: center;">{itm.get('quantity', 1)}</td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Shipping Label - {order_id}</title>
    <style>
        @media print {{ body {{ margin: 0; }} }}
        body {{ font-family: 'Courier New', monospace, sans-serif; margin: 20px; font-size: 13px; color: #000; }}
        .label-card {{ width: 384px; border: 2px solid #000; padding: 12px; margin: 0 auto; box-sizing: border-box; }}
        .header {{ border-bottom: 2px solid #000; padding-bottom: 8px; text-align: center; }}
        .awb-box {{ border: 2px dashed #000; padding: 8px; text-align: center; margin: 10px 0; font-size: 16px; font-weight: bold; }}
        .section {{ margin-bottom: 10px; font-size: 12px; line-height: 1.4; }}
        .cod-badge {{ background: #000; color: #fff; padding: 6px; text-align: center; font-weight: bold; font-size: 14px; margin: 8px 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 6px; }}
    </style>
</head>
<body onload="window.print()">
    <div class="label-card">
        <div class="header">
            <h2 style="margin: 0; font-size: 16px;">SREE SAI KRISHNA COLLECTIONS</h2>
            <div style="font-size: 10px;">Precious Traditional Jewellery & Accessories</div>
        </div>
        <div class="awb-box">
            <div>CARRIER: {carrier.upper()}</div>
            <div style="letter-spacing: 2px; margin-top: 4px;">AWB: {awb}</div>
        </div>
        {f'<div class="cod-badge">COLLECT CASH ON DELIVERY: ₹{final_amt:.2f}</div>' if is_cod else '<div style="border: 1px solid #000; padding: 4px; text-align: center; font-weight: bold;">PREPAID - DO NOT COLLECT CASH</div>'}
        <div class="section" style="border-bottom: 1px solid #000; padding-bottom: 8px;">
            <strong>DELIVER TO:</strong><br>
            {customer_name}<br>
            {line1}{', ' + line2 if line2 else ''}<br>
            {city}, {state} - <strong>{pincode}</strong><br>
            Tel: {customer_phone}
        </div>
        <div class="section" style="border-bottom: 1px solid #000; padding-bottom: 8px;">
            <strong>SHIPPED FROM:</strong><br>
            {settings.BRAND_NAME}<br>
            {settings.BUSINESS_ADDRESS}<br>
            Helpline: {settings.SUPPORT_PHONE}
        </div>
        <div class="section">
            <strong>MANIFEST (Order #{order_id}):</strong>
            <table>
                <thead>
                    <tr style="background: #f1f5f9;">
                        <th style="padding: 4px; border: 1px solid #cbd5e1;">SKU</th>
                        <th style="padding: 4px; border: 1px solid #cbd5e1;">Item</th>
                        <th style="padding: 4px; border: 1px solid #cbd5e1;">Qty</th>
                    </tr>
                </thead>
                <tbody>
                    {items_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
        return html
