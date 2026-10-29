"""
Unit tests for PricingService.
Asserts decimal-safe monetary calculations, rounding rules, tax, and delivery fee thresholds.
"""
from decimal import Decimal
from app.services.pricing_service import PricingService, quantize_money

def test_quantize_money():
    assert quantize_money("10.004") == Decimal("10.00")
    assert quantize_money("10.005") == Decimal("10.01")
    assert quantize_money(125.756) == Decimal("125.76")

def test_calculate_item_total():
    assert PricingService.calculate_item_total(32.00, 3) == Decimal("96.00")
    assert PricingService.calculate_item_total(25.50, 2) == Decimal("51.00")

def test_calculate_order_totals_standard_delivery():
    items = [
        {"unit_price": 100.00, "quantity": 2}, # 200.00
        {"unit_price": 50.00, "quantity": 1}   # 50.00
    ]
    # Subtotal = 250.00
    # Tax (5%) = 12.50
    # Delivery (< 500) = 30.00
    # Total = 292.50
    totals = PricingService.calculate_order_totals(items)
    assert totals["subtotal"] == 250.00
    assert totals["tax"] == 12.50
    assert totals["delivery_fee"] == 30.00
    assert totals["discount"] == 0.00
    assert totals["total"] == 292.50

def test_calculate_order_totals_free_delivery_threshold():
    items = [
        {"unit_price": 250.00, "quantity": 2} # 500.00
    ]
    # Subtotal = 500.00 -> free delivery
    # Tax (5%) = 25.00
    # Delivery = 0.00
    # Total = 525.00
    totals = PricingService.calculate_order_totals(items)
    assert totals["subtotal"] == 500.00
    assert totals["tax"] == 25.00
    assert totals["delivery_fee"] == 0.00
    assert totals["total"] == 525.00

def test_calculate_order_totals_with_discount():
    items = [{"unit_price": 100.00, "quantity": 1}]
    # Subtotal: 100, Tax: 5, Delivery: 30, Discount: 20
    # Total: 115.00
    totals = PricingService.calculate_order_totals(items, discount_amount=20.00)
    assert totals["subtotal"] == 100.00
    assert totals["tax"] == 5.00
    assert totals["delivery_fee"] == 30.00
    assert totals["discount"] == 20.00
    assert totals["total"] == 115.00
