"""Run each (variant, task, rep) through headless Claude Code and grade it."""
import json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, os.environ.get("TK_BASE", "base"))
RUNS = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "tkexp")  # short path: ROOT is >260 chars on Windows
OUT = os.path.join(ROOT, sys.argv[3] if len(sys.argv) > 3 else "results.jsonl")
MODEL = "claude-sonnet-5"
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
VARIANTS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["A_baseline", "B_current", "C_optimized"]

TASKS = {
    "T1_locate": "Which function decides the discount rate in this repo, and what are the thresholds and rates? Answer with file, function name, thresholds and rates.",
    "T2_bugfix": "Running `python -m unittest tests.test_pricing` fails. Find the bug in the source code and fix it. Do not modify any test files.",
    "T3_explain": "Explain what place_order does, in order, and specifically what happens to stock, the order status and notifications when payment fails. List every step.",
    "T5_review": "Review shop/orders.py for correctness bugs and risks. List the issues you find, most serious first.",
    "T6_testlog": "Run the whole test suite with `python -m unittest discover -s tests -t .` and tell me exactly which tests fail and why, one line each.",
    "T7_build": "Running `python tools/build.py` fails. Find out why and fix the source. Do not modify tools/build.py.",
    "T4_feature": "Add tax support for Thailand (TH, 7% VAT) and Singapore (SG, 9% GST), and add tests for both in tests/test_tax.py.",
}

if os.environ.get("TK_TASKS"):
    TASKS = {k: v for k, v in TASKS.items() if k in os.environ["TK_TASKS"].split(",")}


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def unittest_ok(cwd, target):
    r = subprocess.run(["python", "-m", "unittest", target], cwd=cwd, capture_output=True, text=True)
    return r.returncode == 0


def grade(task, cwd, text):
    t = (text or "").lower()
    if task == "T1_locate":
        checks = ["pricing.py" in t, "discount_rate" in t, "100" in t and "500" in t,
                  bool(re.search(r"10\s*%|0\.10|0\.1\b", t)), bool(re.search(r"15\s*%|0\.15", t))]
        return sum(checks) / len(checks)
    if task == "T2_bugfix":
        tests_untouched = all(read(os.path.join(cwd, "tests", f)) == read(os.path.join(BASE, "tests", f))
                              for f in ("test_pricing.py", "test_orders.py"))
        return 1.0 if tests_untouched and unittest_ok(cwd, "tests.test_pricing") else 0.0
    if task == "T3_explain":
        checks = [bool(re.search(r"validat|qty|empty", t)), "reserv" in t, "discount" in t, "tax" in t,
                  "charge" in t, bool(re.search(r"retr|max_retries|3 attempts|three", t)),
                  "release" in t, "failed" in t,
                  bool(re.search(r"no (confirmation|email|notif)|not (sent|send)|without (send|notif|email)|skip|isn.t sent|no message", t))]
        return sum(checks) / len(checks)
    if task == "T4_feature":
        if not os.path.exists(os.path.join(cwd, "tests", "test_tax.py")):
            return 0.0
        shutil.copy(os.path.join(ROOT, "hidden", "test_th_sg.py"), os.path.join(cwd, "tests", "test_hidden_th_sg.py"))
        ok_hidden = unittest_ok(cwd, "tests.test_hidden_th_sg")
        ok_own = unittest_ok(cwd, "tests.test_tax")
        return 1.0 if ok_hidden and ok_own else (0.5 if ok_hidden else 0.0)
    if task == "T5_review":
        checks = [bool(re.search(r"leak|never released|not released|stays reserved|remain[s]? reserved|stuck|without releas|no rollback|not rolled back|orphan|permanently", t)),
                  bool(re.search(r"valueerror|unknown region|unsupported region|tax_for", t)),
                  bool(re.search(r"only paymenterror|other exception|non-payment|any other exception|unexpected exception|not caught|uncaught|outofstock", t)),
                  bool(re.search(r"transaction id|txn|discard|ignored|not stored|not recorded", t)),
                  bool(re.search(r"float|decimal|rounding|precision", t))]
        return sum(checks) / len(checks)
    if task == "T6_testlog":
        names = ["test_refund_partial", "test_coupon_stacking", "test_gift_wrap_fee", "test_loyalty_points",
                 "test_shipping_zone_b", "test_backorder_split", "exactly_100", "exactly_500"]
        return sum(n in t for n in names) / len(names)
    if task == "T7_build":
        untouched = read(os.path.join(cwd, "tools", "build.py")) == read(os.path.join(BASE, "tools", "build.py"))
        r = subprocess.run(["python", "tools/build.py"], cwd=cwd, capture_output=True, text=True)
        return 1.0 if untouched and r.returncode == 0 else 0.0
    return 0.0


def one(job):
    variant, task, rep = job
    cwd = os.path.join(RUNS, f"{variant}__{task}__r{rep}")
    if os.path.exists(cwd):
        shutil.rmtree(cwd)
    shutil.copytree(BASE, cwd)
    cmd = ["claude", "-p", TASKS[task], "--output-format", "json", "--model", MODEL,
           "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence",
           "--permission-mode", "acceptEdits", "--allowedTools", "Bash,Read,Edit,Write,Grep,Glob",
           "--max-budget-usd", "1.5"]
    vf = os.path.join(ROOT, "variants", variant + ".txt")
    if os.path.getsize(vf) > 0:
        cmd += ["--append-system-prompt-file", vf]
    env = dict(os.environ, CLAUDE_CODE_DISABLE_CLAUDE_MDS="1")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env, timeout=600)
    rec = {"variant": variant, "task": task, "rep": rep, "secs": round(time.time() - t0, 1)}
    try:
        d = json.loads(r.stdout)
        if "session limit" in (d.get("result") or "").lower() or not d.get("usage", {}).get("output_tokens"):
            raise RuntimeError("usage limit / empty run: " + (d.get("result") or "")[:80])
        u = d.get("usage", {})
        rec.update(
            ctx_in=u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0),
            fresh_in=u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
            cache_read=u.get("cache_read_input_tokens", 0),
            out=u.get("output_tokens", 0), cost=d.get("total_cost_usd", 0), turns=d.get("num_turns", 0),
            answer_chars=len(d.get("result", "") or ""), score=grade(task, cwd, d.get("result", "")),
            answer=(d.get("result", "") or "")[:1500])
    except Exception as e:  # keep failures visible instead of silently dropping
        rec.update(error=str(e)[:200], stderr=r.stderr[:300], stdout=r.stdout[:300])
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print("done", variant, task, rep, rec.get("score"), rec.get("cost"), flush=True)


if __name__ == "__main__":
    os.makedirs(RUNS, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    jobs = [(v, t, r) for r in range(1, REPS + 1) for t in TASKS for v in VARIANTS]
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(one, jobs))
    print("ALL DONE")
