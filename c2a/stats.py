"""Progress: patterns mastered, reaction-time trend, real-world hit rate. No levels."""

import statistics

from . import store
from .drill import is_mastered

DAY = 86400


def _med(xs):
    return statistics.median(xs) if xs else None


def _rate(xs):
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def live_runs():
    d = store.data_dir() / "live_logs"
    runs = []
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            runs.append(store.load(f"live_logs/{f.name}"))
        except ValueError:
            continue
    return runs


def compute():
    patterns = store.load("patterns.json", [])
    prog = store.progress()
    att = prog["attempts"]
    by_p = {}
    for a in att:
        by_p.setdefault(a["pattern"], []).append(a)
    mastered = [p["id"] for p in patterns if is_mastered(prog["patterns"].get(p["id"]), by_p.get(p["id"], []))]

    plain = [a for a in att if not a.get("load")]
    loaded = [a for a in att if a.get("load")]
    rt = {}
    if plain:
        t0, t1 = plain[0]["ts"], plain[-1]["ts"]
        rt["first7"] = _med([a["rt_ms"] for a in plain if a["ts"] < t0 + 7 * DAY])
        rt["last7"] = _med([a["rt_ms"] for a in plain if a["ts"] > t1 - 7 * DAY])
        rt["span_days"] = (t1 - t0) / DAY
    if loaded:
        lp = {a["pattern"] for a in loaded}       # compare on the same patterns
        base = [a for a in plain if a["pattern"] in lp]
        rt["load_rt"], rt["noload_rt"] = _med([a["rt_ms"] for a in loaded]), _med([a["rt_ms"] for a in base])
        rt["load_acc"], rt["noload_acc"] = _rate([a["correct"] for a in loaded])[0], _rate([a["correct"] for a in base])[0]
        rt["digits_ok"] = _rate([t["number_ok"] for t in prog["load_tests"]])[0]

    first = lambda recs: [r for r in recs if not r.get("repeat")]
    score = {"hit": 1.0, "partial": 0.5, "miss": 0.0}
    cases = first(prog["cases"])
    real = {
        "cases_eval": _rate([score[r["mark"]] for r in cases if r.get("obscurity") != "low"]),
        "cases_tutorial": _rate([score[r["mark"]] for r in cases if r.get("obscurity") == "low"]),
        "select": _rate([r["correct"] for r in first(prog["select"])]),
    }
    runs = live_runs()
    real["live_human"] = _rate([r["solved"] for r in runs if r.get("kind") == "human"])
    real["live_baseline"] = _rate([r["solved"] for r in runs if r.get("kind") == "baseline"])
    preds = [p for p in store.load("predictions.json", []) if p.get("outcome_correct") is not None]
    real["log"] = _rate([p["outcome_correct"] for p in preds])
    return {"mastered": len(mastered), "total": len(patterns), "attempts": len(plain),
            "rt": rt, "real": real}


def _pct(r):
    v, n = r
    return f"{v:.0%} (n={n})" if n else "no data yet"


def show():
    s = compute()
    rt = s["rt"]
    print("\n1. Patterns mastered")
    print(f"   {s['mastered']} of {s['total']}   ({s['attempts']} drill answers so far)")
    print("   Mastered = correct in >= 3 spaced reviews, >= 3 different stories, median RT under threshold.")
    print("\n2. Median reaction time (no load)")
    if rt.get("first7") is not None:
        print(f"   first 7 days: {rt['first7']:.0f} ms   last 7 days: {rt['last7']:.0f} ms"
              f"   (history spans {rt['span_days']:.1f} days)")
    else:
        print("   no data yet")
    if rt.get("load_rt") is not None:
        print(f"   under load: {rt['load_rt']:.0f} ms, {rt['load_acc']:.0%} correct   "
              f"same patterns, no load: {rt['noload_rt'] or 0:.0f} ms, {rt['noload_acc'] or 0:.0%} correct")
        print(f"   number recalled exactly: {rt['digits_ok']:.0%} of load tests")
    else:
        print("   load test: not run yet (python -m c2a drill --load)")
    r = s["real"]
    print("\n3. Real-world hit rate")
    print(f"   cases, medium/high obscurity: {_pct(r['cases_eval'])}   (hit=1, partial=0.5)")
    print(f"   cases, famous tutorials:      {_pct(r['cases_tutorial'])}   (recall; not evidence)")
    print(f"   select:                       {_pct(r['select'])}")
    print(f"   live solved, you + LLM:       {_pct(r['live_human'])}")
    print(f"   live solved, LLM alone:       {_pct(r['live_baseline'])}")
    print(f"   logged real predictions:      {_pct(r['log'])}")
    print()
