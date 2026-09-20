"""Build the sample project + variant prompt files for the token experiment."""
import os, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, "base")


def w(rel, body, root=BASE):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(body).lstrip("\n"))


w("shop/__init__.py", "")
w("shop/models.py", '''
    from dataclasses import dataclass, field


    @dataclass
    class Item:
        sku: str
        name: str
        price: float
        qty: int = 1


    @dataclass
    class Customer:
        id: int
        email: str
        region: str = "US"


    @dataclass
    class Order:
        id: int
        customer: Customer
        items: list = field(default_factory=list)
        status: str = "new"
        total: float = 0.0
''')
w("shop/pricing.py", '''
    """Pricing rules."""

    DISCOUNT_TIERS = [(500, 0.15), (100, 0.10)]


    def calculate_subtotal(items):
        return round(sum(i.price * i.qty for i in items), 2)


    def discount_rate(subtotal):
        """Discount rate for a subtotal.

        Orders of 100 or more get 10%; orders of 500 or more get 15%.
        """
        for threshold, rate in DISCOUNT_TIERS:
            if subtotal > threshold:
                return rate
        return 0.0


    def apply_discount(subtotal):
        return round(subtotal * (1 - discount_rate(subtotal)), 2)
''')
w("shop/tax.py", '''
    """Sales tax / VAT by region."""

    TAX_RATES = {"US": 0.08, "DE": 0.19, "JP": 0.10}


    def tax_for(region, amount):
        rate = TAX_RATES.get(region)
        if rate is None:
            raise ValueError(f"unknown region: {region}")
        return round(amount * rate, 2)
''')
w("shop/inventory.py", '''
    """In-memory stock."""


    class OutOfStock(Exception):
        pass


    STOCK = {"A1": 10, "B2": 5, "C3": 0}


    def reserve(items):
        for i in items:
            if STOCK.get(i.sku, 0) < i.qty:
                raise OutOfStock(i.sku)
        for i in items:
            STOCK[i.sku] -= i.qty


    def release(items):
        for i in items:
            STOCK[i.sku] = STOCK.get(i.sku, 0) + i.qty
''')
w("shop/payment.py", '''
    """Payment gateway wrapper with retry."""
    import time

    MAX_RETRIES = 3


    class PaymentError(Exception):
        pass


    def _gateway_charge(customer, amount):
        return f"txn-{customer.id}-{int(amount * 100)}"


    def charge(customer, amount):
        last = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return _gateway_charge(customer, amount)
            except PaymentError as e:
                last = e
                time.sleep(0.01 * attempt)
        raise PaymentError(f"declined after {MAX_RETRIES} attempts: {last}")
''')
w("shop/notify.py", '''
    """Notifications (stubbed)."""

    OUTBOX = []


    def send_confirmation(order):
        OUTBOX.append((order.customer.email, f"Order {order.id} confirmed"))
''')
w("shop/orders.py", '''
    """Order placement flow."""
    from . import inventory, notify, payment, pricing, tax
    from .models import Order


    def place_order(order_id, customer, items):
        # 1. validate
        if not items or any(i.qty <= 0 for i in items):
            raise ValueError("order needs at least one item with qty > 0")
        order = Order(id=order_id, customer=customer, items=list(items))

        # 2. reserve stock
        inventory.reserve(order.items)

        # 3. price: subtotal -> discount -> tax
        subtotal = pricing.calculate_subtotal(order.items)
        discounted = pricing.apply_discount(subtotal)
        order.total = round(discounted + tax.tax_for(customer.region, discounted), 2)

        # 4. charge; on failure roll back stock and mark failed (no email)
        try:
            payment.charge(customer, order.total)
        except payment.PaymentError:
            inventory.release(order.items)
            order.status = "failed"
            return order

        # 5. confirm
        order.status = "paid"
        notify.send_confirmation(order)
        return order
''')
# filler so blind full-file reads are wasteful
funcs = []
for n in range(1, 61):
    funcs.append(f'''
def helper_{n}(x):
    """Unrelated helper number {n}."""
    y = x + {n}
    if y % 2 == 0:
        return y // 2
    return y * 3 + 1
''')
w("shop/utils.py", '"""Misc helpers, unrelated to the order flow."""\n' + "".join(funcs))

w("tests/__init__.py", "")
w("tests/test_pricing.py", '''
    import unittest
    from shop import pricing


    class PricingTest(unittest.TestCase):
        def test_below_threshold_no_discount(self):
            self.assertEqual(pricing.apply_discount(99.99), 99.99)

        def test_exactly_100_gets_10_percent(self):
            self.assertEqual(pricing.apply_discount(100), 90.0)

        def test_exactly_500_gets_15_percent(self):
            self.assertEqual(pricing.apply_discount(500), 425.0)

        def test_above_500(self):
            self.assertEqual(pricing.apply_discount(1000), 850.0)


    if __name__ == "__main__":
        unittest.main()
''')
w("tests/test_orders.py", '''
    import unittest
    from unittest import mock
    from shop import inventory, notify, orders, payment
    from shop.models import Customer, Item


    class OrderTest(unittest.TestCase):
        def setUp(self):
            inventory.STOCK.update({"A1": 10, "B2": 5, "C3": 0})
            notify.OUTBOX.clear()

        def test_payment_failure_releases_stock(self):
            c = Customer(1, "a@x.com", "US")
            with mock.patch.object(payment, "_gateway_charge", side_effect=payment.PaymentError("no")):
                o = orders.place_order(1, c, [Item("A1", "pen", 5.0, 2)])
            self.assertEqual(o.status, "failed")
            self.assertEqual(inventory.STOCK["A1"], 10)
            self.assertEqual(notify.OUTBOX, [])


    if __name__ == "__main__":
        unittest.main()
''')

# hidden checks (never copied into run dirs; copied in only for grading)
w("hidden/test_th_sg.py", '''
    import unittest
    from shop import tax


    class HiddenTax(unittest.TestCase):
        def test_th(self):
            self.assertEqual(tax.tax_for("TH", 100), 7.0)

        def test_sg(self):
            self.assertEqual(tax.tax_for("SG", 100), 9.0)

        def test_unknown_still_raises(self):
            with self.assertRaises(ValueError):
                tax.tax_for("ZZ", 100)


    if __name__ == "__main__":
        unittest.main()
''', root=ROOT)

# ---- variant prompts ----
BASELINE = ""  # no extra rules

CURRENT = """# Token Optimization Rules
1. Search -> Slice -> Act: Use Bash grep/rg to find symbols first. Read only relevant line ranges with sed/head/tail. Never cat entire files.
2. Zero-Echo: Never re-quote file contents or command outputs. Cite as `path:L##` instead. No preambles ("Sure!", "Here's what I did"). No post-action recaps.
3. Surgical Edits: Use search/replace blocks with 3-5 line anchors. Never rewrite entire files. Trust edit tool success - don't re-read to verify.
4. Output Budgeting: Max 3 sentences unless asked for detail. Bullet points over paragraphs. Format: `FuncName (L##): description`.
5. Input Filtering: Pipe large outputs: `| head -n 25`, `| grep -E "ERROR|FAIL"`. Never dump raw logs or test output into context.
6. Context Hygiene: Use TodoWrite for broad searches. Keep max 2-3 files in active focus. Drop files once edits are verified.
7. Doom Loop Breaker: If same error appears twice after fix attempts - STOP and diagnose in 1 message. Never retry blindly.
"""

OPTIMIZED = """# Token Efficiency Rules (correctness first)
1. Locate before reading: use the Grep/Glob tools (or rg) with a tight pattern and head_limit; then Read with offset/limit around the hit. Never read a whole file over ~80 lines unless the task needs all of it. Skip files whose names/greps show they are unrelated.
2. Batch: issue independent tool calls together in one turn (e.g. several greps/reads at once). Do not narrate between calls.
3. Edit surgically: smallest unique-anchor edit; never rewrite a whole file. Trust edit success - do not re-read the file to confirm.
4. Verify by running, not re-reading: after a code change run the relevant test once with output filtered (e.g. `| tail -n 15`). If it passes, stop.
5. Answer format: lead with the answer. Concise by default - no preamble, no recap, no restating file contents; cite as `path:L##`. But COMPLETENESS OVERRIDES BREVITY: when the user asks for all steps/items/thresholds, list every one, tersely (one short line each).
6. If the same error occurs twice, stop and diagnose in one message instead of retrying.
7. Do not explore beyond what the task needs; do not open tests, docs or config unless the task references them.
"""

os.makedirs(os.path.join(ROOT, "variants"), exist_ok=True)
for name, body in (("A_baseline", BASELINE), ("B_current", CURRENT), ("C_optimized", OPTIMIZED)):
    with open(os.path.join(ROOT, "variants", name + ".txt"), "w", encoding="utf-8") as f:
        f.write(body)
print("ok")
