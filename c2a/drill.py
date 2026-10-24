"""Mode 1: pattern drills with Leitner spaced repetition, reaction timing, load test.

Consistent mapping: every item has one fixed right answer (a pattern id), so the
same kind of situation always calls for the same move.
"""

import os
import random
import statistics
import time
from collections import Counter

from . import store
from .term import ask, clear, getkey, wrap

INTERVAL_DAYS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 16}   # Leitner box -> days until due
SPACING_HOURS = 20          # a correct answer counts as a new "spaced review" after this gap
MASTERY = {"reviews": 3, "stories": 3, "median_ms": int(os.environ.get("C2A_MASTERY_MS", 3000))}
NEW_PER_SESSION = 5


# ── scheduling (pure functions; see tests/test_scheduler.py) ────────────────

def update(state, item_id, correct, t):
    """Return the pattern's new Leitner state after one no-load answer at time t."""
    s = {"box": 0, "due": 0, "spaced_hits": [], "seen_items": {}, "last_item": None, **(state or {})}
    s = {**s, "spaced_hits": list(s["spaced_hits"]), "seen_items": dict(s["seen_items"])}
    if correct:
        if not s["spaced_hits"] or t - s["spaced_hits"][-1] >= SPACING_HOURS * 3600:
            s["spaced_hits"].append(t)
        s["box"] = min(5, max(s["box"], 1) + 1)
    else:
        s["box"] = 1
    s["due"] = t + INTERVAL_DAYS[s["box"]] * 86400
    s["last_item"] = item_id
    s["seen_items"][item_id] = s["seen_items"].get(item_id, 0) + 1
    return s


def plan(pattern_ids, states, n, t, rng=random, new_limit=NEW_PER_SESSION):
    """Pick n pattern slots: due patterns first (lowest box first), then new ones, then the rest."""
    seen = [p for p in pattern_ids if p in states]
    due = sorted((p for p in seen if states[p]["due"] <= t), key=lambda p: (states[p]["box"], states[p]["due"]))
    new = [p for p in pattern_ids if p not in states]
    rng.shuffle(new)
    later = sorted((p for p in seen if states[p]["due"] > t), key=lambda p: states[p]["due"])
    pool = due + new[:new_limit] + later + new[new_limit:]
    if not pool:
        return []
    counts = Counter((pool * (n // len(pool) + 1))[:n])
    out = []
    while counts:   # random order, never the same pattern twice in a row when avoidable
        choices = [p for p in counts if not out or p != out[-1]] or list(counts)
        top = max(counts[p] for p in choices)
        p = rng.choice(sorted(p for p in choices if counts[p] == top))
        out.append(p)
        counts[p] -= 1
        if not counts[p]:
            del counts[p]
    return out


def pick_item(items, state, avoid=None, rng=random):
    """Least-shown surface story for this pattern, never the one shown last."""
    seen = (state or {}).get("seen_items", {})
    skip = {(state or {}).get("last_item"), avoid}
    pool = [i for i in items if i["id"] not in skip] or items
    low = min(seen.get(i["id"], 0) for i in pool)
    return rng.choice([i for i in pool if seen.get(i["id"], 0) == low])


def is_mastered(state, attempts, rules=MASTERY):
    """>= 3 spaced correct reviews, across >= 3 stories, median RT of recent correct answers under threshold."""
    if not state:
        return False
    correct = [a for a in attempts if a["correct"] and not a.get("load")]
    if len(state.get("spaced_hits", [])) < rules["reviews"]:
        return False
    if len({a["item"] for a in correct}) < rules["stories"]:
        return False
    recent = [a["rt_ms"] for a in correct[-10:]]
    return statistics.median(recent) < rules["median_ms"]


# ── interactive ─────────────────────────────────────────────────────────────

def _present(item, patterns, rng, n, i, brief=False):
    opts = list(item["options"])
    rng.shuffle(opts)
    clear()
    print(f"[{i}/{n}]\n")
    print(wrap(item["situation"]))
    print()
    for k, pid in enumerate(opts, 1):
        print(f"  {k}. {patterns[pid]['move']}")
    print("\n  (1-4, q to stop)")
    t0 = time.perf_counter()
    key = getkey("1234q")
    rt = round((time.perf_counter() - t0) * 1000)
    if key == "q":
        return None
    chosen = opts[int(key) - 1]
    correct = chosen == item["answer"]
    p = patterns[item["answer"]]
    print(f"\n  {'RIGHT' if correct else 'WRONG'}   {rt} ms")
    if not correct:
        print(f"  You picked: {patterns[chosen]['name']}")
    print(f"  Pattern: {p['name']}")
    if not brief:
        print(wrap(f"Move: {p['move']}", "  "))
        if p.get("real_examples"):
            ex = p["real_examples"][0]
            print(wrap(f"Real: {ex['text']} ({ex['source']})", "  "))
    return {"item": item["id"], "pattern": item["answer"], "chosen": chosen,
            "correct": correct, "rt_ms": rt}


def _wait():
    print("\n  [Enter] next")
    input()


def run(n=20, load=False, rng=random):
    patterns = store.by_id("patterns.json")
    items = store.load("drill_items.json", [])
    by_pattern = {}
    for it in items:
        by_pattern.setdefault(it["pattern_id"], []).append(it)
    prog = store.progress()
    states = prog["patterns"]
    pids = [p for p in patterns if p in by_pattern]
    if not pids:
        print("No drill items found in data/drill_items.json.")
        return
    if load:
        return _run_load(prog, patterns, by_pattern, rng)

    queue = plan(pids, states, n, store.now(), rng)
    requeued, last_item, done = set(), None, 0
    i = 0
    while i < len(queue):
        pid = queue[i]
        item = pick_item(by_pattern[pid], states.get(pid), avoid=last_item, rng=rng)
        rec = _present(item, patterns, rng, len(queue), i + 1)
        if rec is None:
            break
        t = store.now()
        rec.update(ts=t, mode="drill", load=False)
        prog["attempts"].append(rec)
        states[pid] = update(states.get(pid), item["id"], rec["correct"], t)
        if not rec["correct"] and pid not in requeued:   # missed: comes back in a few items
            queue.insert(min(i + 4, len(queue)), pid)
            requeued.add(pid)
        store.save_progress(prog)
        last_item, done, i = item["id"], done + 1, i + 1
        _wait()
    _summary(prog["attempts"][-done:] if done else [])


def _summary(recs):
    if not recs:
        return
    acc = sum(r["correct"] for r in recs) / len(recs)
    med = statistics.median(r["rt_ms"] for r in recs)
    print(f"\nSession: {len(recs)} items, {acc:.0%} correct, median {med:.0f} ms. "
          "Run `python -m c2a stats` for trends.")


def _run_load(prog, patterns, by_pattern, rng, n_items=5):
    """Hold a 7-digit number for the whole block; automatic skills should survive the load."""
    states = prog["patterns"]
    known = [p for p in by_pattern if states.get(p, {}).get("box", 0) >= 2]
    pool = known if len(known) >= n_items else list(by_pattern)
    pids = rng.sample(pool, min(n_items, len(pool)))
    number = str(rng.randint(1_000_000, 9_999_999))
    clear()
    print(f"\n\n    Remember this number:   {number}\n")
    time.sleep(3)
    recs = []
    for i, pid in enumerate(pids, 1):
        item = pick_item(by_pattern[pid], states.get(pid), rng=rng)
        rec = _present(item, patterns, rng, len(pids), i, brief=True)
        if rec is None:
            return
        rec.update(ts=store.now(), mode="drill", load=True)
        recs.append(rec)
        time.sleep(1.2)
    clear()
    typed = ask("Type the number: ")
    digits = sum(a == b for a, b in zip(typed, number))
    prog["attempts"].extend(recs)
    prog["load_tests"].append({"ts": store.now(), "number_ok": typed == number,
                               "digits_correct": digits, "items": [r["item"] for r in recs]})
    store.save_progress(prog)
    print(f"Number: {number}  ({digits}/7 digits right)")
    _summary(recs)
