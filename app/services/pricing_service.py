"""
Authoritative Pricing Service for MediApp.
Uses exact Decimal arithmetic with explicit rounding rules to calculate subtotals,
taxes, delivery fees, discounts, and authoritative order totals.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence, Mapping, Any

# Tax rate on medicines: 5% (standard GST on essential pharmaceuticals)
TAX_RATE = Decimal("0.05")
# Standard delivery fee in INR
STANDARD_DELIVERY_FEE = Decimal("30.00")
# Threshold for free delivery
FREE_DELIVERY_THRESHOLD = Decimal("500.00")

def quantize_money(amount: Decimal | float | int | str) -> Decimal:
    """Rounds an amount to 2 decimal places using ROUND_HALF_UP."""
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class PricingService:
    @staticmethod
    def calculate_item_total(unit_price: float | Decimal, quantity: int) -> Decimal:
        """Calculates item line total = unit_price * quantity."""
        price = Decimal(str(unit_price))
        qty = Decimal(str(quantity))
        return quantize_money(price * qty)

    @classmethod
    def calculate_order_totals(
        cls,
        items: Sequence[Mapping[str, Any]],
        discount_amount: float | Decimal = 0.0,
        custom_delivery_fee: float | Decimal | None = None
    ) -> dict[str, float]:
        """
        Authoritative backend calculation of order financial totals.
        
        Args:
            items: Iterable of dicts, each with 'unit_price' and 'quantity'
            discount_amount: Validated promotional discount
            custom_delivery_fee: Explicit delivery fee override if provided
            
        Returns:
            Dictionary containing exact float representations for API responses:
            'subtotal', 'tax', 'delivery_fee', 'discount', 'total'
        """
        subtotal = Decimal("0.00")
        for item in items:
            line_total = cls.calculate_item_total(item["unit_price"], item["quantity"])
            subtotal += line_total
        subtotal = quantize_money(subtotal)

        # Calculate 5% tax on subtotal
        tax = quantize_money(subtotal * TAX_RATE)

        # Calculate delivery fee
        if custom_delivery_fee is not None:
            delivery_fee = quantize_money(custom_delivery_fee)
        elif subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == Decimal("0.00"):
            delivery_fee = Decimal("0.00")
        else:
            delivery_fee = STANDARD_DELIVERY_FEE

        # Discount
        discount = quantize_money(discount_amount)
        if discount > subtotal:
            discount = subtotal

        # Authoritative Grand Total
        grand_total = quantize_money(subtotal + tax + delivery_fee - discount)

        return {
            "subtotal": float(subtotal),
            "tax": float(tax),
            "delivery_fee": float(delivery_fee),
            "discount": float(discount),
            "total": float(grand_total)
        }
