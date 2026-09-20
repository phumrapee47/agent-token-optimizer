"""base_noisy = base + a noisy test suite and a noisy build script."""
import os, shutil, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, DST = os.path.join(ROOT, "base"), os.path.join(ROOT, "base_noisy")
if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)


def w(rel, body):
    p = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(body).lstrip("\n"))


w("tests/helpers_bulk.py", '''
    def _a(label, want, got):
        return _b(label, want, got)


    def _b(label, want, got):
        return _c(label, want, got)


    def _c(label, want, got):
        assert want == got, f"{label}: expected {want!r} but got {got!r}"


    def check(label, want, got):
        _a(label, want, got)


    def noisy(case):
        for k in range(1, 9):
            print(f"debug: case {case} step {k} ok")
''')

FAILS = [
    ("test_refund_partial", "refund", 15.0, 10.0),
    ("test_coupon_stacking", "coupon stacking", 2, 1),
    ("test_gift_wrap_fee", "gift wrap fee", 3.5, 0.0),
    ("test_loyalty_points", "loyalty points", 120, 100),
    ("test_shipping_zone_b", "shipping zone B", 9.9, 7.5),
    ("test_backorder_split", "backorder split", "2+1", "3+0"),
]
lines = ["import unittest", "from tests.helpers_bulk import check, noisy", "", "", "class BulkTest(unittest.TestCase):"]
for i in range(1, 35):
    lines += [f"    def test_ok_{i:02d}(self):", f"        noisy({i})", f"        check('ok {i}', {i}, {i})", ""]
for name, label, want, got in FAILS:
    lines += [f"    def {name}(self):", f"        noisy('{name}')", f"        check({label!r}, {want!r}, {got!r})", ""]
lines += ["", "if __name__ == '__main__':", "    unittest.main()", ""]
with open(os.path.join(DST, "tests", "test_bulk.py"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

w("tools/build.py", '''
    import sys

    for i in range(1, 241):
        print(f"warning: deprecated call legacy_fn_{i % 7} in module mod_{i} (line {i * 3})")
        if i % 40 == 0:
            print(f"note: compiling batch {i // 40} of 6 ...")
    sys.path.insert(0, ".")
    from shop import orders

    if not hasattr(orders, "ORDER_TIMEOUT"):
        print("ERROR: shop.orders is missing required constant ORDER_TIMEOUT (needed by build.py)")
        sys.exit(1)
    print("build ok")
''')
print("ok")
