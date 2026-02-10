from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

ALLOWED_CATEGORIES = {"book", "food", "electronics", "other"}
MEMBERSHIP_DISCOUNTS = {"gold": 0.03, "platinum": 0.05}
SHIPPING_RULES = {
    "TH": [(500, 60.0)],
    "JP": [(4000, 600.0)],
    "US": [(100, 15.0), (300, 8.0)],
    "DEFAULT": [(200, 25.0)],
}
TAX_RATES = {"TH": 0.07, "JP": 0.10, "US": 0.08, "DEFAULT": 0.05}

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    def _calc_shipping(self, country: str, subtotal: float) -> float:
        rules = SHIPPING_RULES.get(country, SHIPPING_RULES["DEFAULT"])
        for threshold, fee in rules:
            if subtotal < threshold:
                return fee
        return 0.0

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            problems.append("Invoice is missing")
            return problems
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ALLOWED_CATEGORIES:
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def _calc_subtotal_and_fragile(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = 0.0
        fragile_fee = 0.0
        for it in items:
            line = it.unit_price * it.qty
            subtotal += line
            if it.fragile:
                fragile_fee += 5.0 * it.qty
        return subtotal, fragile_fee

    def _calc_discount(self, inv: Invoice, subtotal: float, warnings: List[str]) -> float:
        discount = 0.0
        if inv.membership in MEMBERSHIP_DISCOUNTS:
            discount += subtotal * MEMBERSHIP_DISCOUNTS[inv.membership]
        elif subtotal > 3000:
            discount += 20

        coupon = inv.coupon.strip() if inv.coupon else ""
        if coupon:
            if coupon in self._coupon_rate:
                discount += subtotal * self._coupon_rate[coupon]
            else:
                warnings.append("Unknown coupon")
        return min(discount, subtotal)

    def _calc_tax(self, country: str, taxable_base: float) -> float:
        tax_rate = TAX_RATES.get(country, TAX_RATES["DEFAULT"])
        return taxable_base * tax_rate

    def _maybe_add_upgrade_warning(self, subtotal: float, membership: str, warnings: List[str]) -> None:
        if subtotal > 10000 and membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal, fragile_fee = self._calc_subtotal_and_fragile(inv.items)
        shipping = self._calc_shipping(inv.country, subtotal)
        discount = self._calc_discount(inv, subtotal, warnings)
        taxable_base = max(0.0, subtotal - discount)
        tax = self._calc_tax(inv.country, taxable_base)

        total = subtotal + shipping + fragile_fee + tax - discount
        if total < 0:
            total = 0

        self._maybe_add_upgrade_warning(subtotal, inv.membership, warnings)
        return total, warnings
