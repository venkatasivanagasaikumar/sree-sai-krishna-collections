import pytest
import json
from app.services.shipping_service import ShippingService
from app.database import get_db
from app.api.v1.shipping import (
    check_pincode_serviceability,
    create_shipment,
    get_shipping_label,
    shipping_carrier_webhook,
    get_cod_reconciliation
)

def test_pincode_validation_and_serviceability():
    # Valid Metro (Secunderabad / Hyderabad 500xxx)
    res_metro = ShippingService.check_serviceability("500003")
    assert res_metro["serviceable"] is True
    assert res_metro["zone"] == "Metro"
    assert res_metro["cod_available"] is True
    assert "2-4" in res_metro["estimated_delivery"]

    # Valid Non-metro (Warangal 506xxx)
    res_non_metro = ShippingService.check_serviceability("506001")
    assert res_non_metro["serviceable"] is True
    assert res_non_metro["zone"] == "Standard Domestic"
    assert res_non_metro["cod_available"] is True

    # Valid Remote (Northeast Assam / Manipur 795xxx)
    res_remote = ShippingService.check_serviceability("795001")
    assert res_remote["serviceable"] is True
    assert "Remote" in res_remote["zone"]
    assert res_remote["cod_available"] is False # Prepaid only

    # Invalid PIN codes
    res_invalid_len = ShippingService.check_serviceability("50003")
    assert res_invalid_len["serviceable"] is False
    res_invalid_char = ShippingService.check_serviceability("50000A")
    assert res_invalid_char["serviceable"] is False
    res_zero = ShippingService.check_serviceability("012345")
    assert res_zero["serviceable"] is False

def test_shipping_fee_calculation():
    assert ShippingService.calculate_shipping_fee(999.0) == 0.0
    assert ShippingService.calculate_shipping_fee(1500.0) == 0.0
    assert ShippingService.calculate_shipping_fee(998.0) == 79.0
    assert ShippingService.calculate_shipping_fee(399.0) == 79.0

def test_shipping_label_generator():
    order = {
        "order_id": "SSK-20261030-9999",
        "payment_method": "COD",
        "final_amount": 1499.0,
        "shipping_address": {
            "name": "Sunita Reddy",
            "phone": "+91 99887 76655",
            "address_line1": "Flat 402, Sai Nilayam",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500034"
        },
        "items": [
            {"sku": "SSK-JHM-001", "name": "Temple Jhumka Earrings", "quantity": 1}
        ]
    }
    tracking = {"awb": "BD9928374", "carrier": "Blue Dart Express"}
    html = ShippingService.generate_shipping_label_html(order, tracking)
    assert "SREE SAI KRISHNA COLLECTIONS" in html
    assert "BD9928374" in html
    assert "Sunita Reddy" in html
    assert "500034" in html
    assert "COLLECT CASH ON DELIVERY: ₹1499.00" in html

import asyncio

def test_shipping_api_endpoints():
    db = get_db()

    # 1. Public serviceability endpoint
    pub_res = check_pincode_serviceability("500003")
    assert pub_res["serviceable"] is True

    # 2. Create shipment for existing order
    ship_res = create_shipment(
        order_id="SSK-20261028-4412",
        payload={"carrier": "Blue Dart Express", "awb": "BLUEDART8831"},
        db=db
    )
    assert ship_res["tracking"]["awb"] == "BLUEDART8831"

    # 3. Fetch label
    lbl_res = get_shipping_label(order_id="SSK-20261028-4412", db=db)
    content = lbl_res.body.decode("utf-8")
    assert "BLUEDART8831" in content
    assert "SREE SAI KRISHNA COLLECTIONS" in content

    # 4. Tracking webhook updates order status
    hook_res = shipping_carrier_webhook(payload={"awb": "BLUEDART8831", "status": "DELIVERED"}, db=db)
    assert hook_res["new_status"] == "DELIVERED"

    # 5. COD reconciliation report
    recon = get_cod_reconciliation(db=db)
    assert "total_cod_orders" in recon
    assert "currency" in recon
