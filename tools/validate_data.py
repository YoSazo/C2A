"""Schema and reference checks for every data file. Exit code 1 on any error.

    python tools/validate_data.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"
PROBLEMS = ROOT / "c2a" / "live" / "problems"

FAMILIES = {"scarcity", "velocity", "asymmetry", "friction", "paradox"}
ORIGINS = {"real", "adapted", "synthetic"}
OBSCURITY = {"low", "medium", "high"}
TARGETS = {"patterns": 30, "drill_items": 300, "select_items": 30, "cases": 15, "problems": 5}

errors, warnings = [], []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def load(name):
    path = DATA / name
    if not path.exists():
        err(name, "missing")
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(name, f"invalid JSON: {e}")
        return []
    if not isinstance(data, list):
        err(name, "top level must be a list")
        return []
    return data


def is_url(s):
    return isinstance(s, str) and s.startswith(("http://", "https://"))


def check_fields(name, items, required):
    ids = Counter()
    for i, x in enumerate(items):
        where = f"{name}[{x.get('id', i)}]"
        for field, typ in required.items():
            if not isinstance(x.get(field), typ) or x.get(field) in ("", []):
                err(where, f"field '{field}' missing or not {typ.__name__ if isinstance(typ, type) else typ}")
        ids[x.get("id")] += 1
    for k, n in ids.items():
        if n > 1:
            err(name, f"duplicate id {k!r}")


def main():
    patterns = load("patterns.json")
    check_fields("patterns.json", patterns, {"id": str, "name": str, "constraint": str, "move": str,
                                             "anti_pattern": str, "family": str, "real_examples": list})
    pids = {p.get("id") for p in patterns}
    for p in patterns:
        where = f"patterns.json[{p.get('id')}]"
        if p.get("family") not in FAMILIES:
            err(where, f"family must be one of {sorted(FAMILIES)}")
        for ex in p.get("real_examples", []):
            if not ex.get("text") or not is_url(ex.get("source")):
                err(where, "each real example needs text and a source URL")
        if len(p.get("move", "")) > 90:
            warnings.append(f"{where}: move is long ({len(p['move'])} chars); it is shown as a drill option")

    drills = load("drill_items.json")
    check_fields("drill_items.json", drills, {"id": str, "pattern_id": str, "situation": str,
                                              "options": list, "answer": str, "origin": str})
    texts = Counter(d.get("situation", "").strip().lower() for d in drills)
    for d in drills:
        where = f"drill_items.json[{d.get('id')}]"
        opts = d.get("options", [])
        if d.get("pattern_id") not in pids:
            err(where, f"pattern_id {d.get('pattern_id')!r} not in patterns.json")
        if d.get("answer") != d.get("pattern_id"):
            err(where, "answer must equal pattern_id")
        if len(opts) != 4 or len(set(opts)) != 4:
            err(where, "needs exactly 4 distinct options")
        if d.get("answer") not in opts:
            err(where, "answer not among options")
        for o in opts:
            if o not in pids:
                err(where, f"option {o!r} not in patterns.json")
        if d.get("origin") not in ORIGINS:
            err(where, f"origin must be one of {sorted(ORIGINS)}")
        if d.get("origin") in ("real", "adapted") and not is_url(d.get("source")):
            err(where, "real/adapted items need a source URL")
        if texts[d.get("situation", "").strip().lower()] > 1:
            err(where, "duplicate situation text")
    per = Counter(d.get("pattern_id") for d in drills)
    for p in pids:
        if per[p] < 10:
            warnings.append(f"pattern {p}: {per[p]} drill items (target 10+)")
    sourced = sum(d.get("origin") in ("real", "adapted") for d in drills)
    if drills and sourced * 3 < len(drills):
        warnings.append(f"drill items: {sourced}/{len(drills)} real or adapted (target: at least a third)")

    sel = load("select_items.json")
    check_fields("select_items.json", sel, {"id": str, "situation": str, "goal": str, "options": list,
                                            "answer_index": int, "outcome": str, "source": str})
    for s in sel:
        where = f"select_items.json[{s.get('id')}]"
        if not 0 <= s.get("answer_index", -1) < len(s.get("options", [])):
            err(where, "answer_index out of range")
        if not is_url(s.get("source")):
            err(where, "source must be a URL")
        if s.get("origin", "real") == "synthetic":
            err(where, "synthetic items are not allowed in select")

    cases = load("cases.json")
    check_fields("cases.json", cases, {"id": str, "title": str, "year": int, "domain": str, "situation": str,
                                       "outcome": str, "pattern_ids": list, "obscurity": str, "source": str})
    for c in cases:
        where = f"cases.json[{c.get('id')}]"
        if c.get("obscurity") not in OBSCURITY:
            err(where, f"obscurity must be one of {sorted(OBSCURITY)}")
        if not is_url(c.get("source")):
            err(where, "source must be a URL")
        for p in c.get("pattern_ids", []):
            if p not in pids:
                err(where, f"pattern {p!r} not in patterns.json")
        if c.get("origin", "real") == "synthetic":
            err(where, "synthetic items are not allowed in cases")

    from c2a.live import truss
    problems = sorted(PROBLEMS.glob("*.json"))
    for f in problems:
        try:
            prob = json.loads(f.read_text(encoding="utf-8"))
            truss.validate_design(prob["design"], prob)
            for key in ("id", "title", "brief", "material", "budget", "design"):
                if key not in prob:
                    err(f.name, f"missing '{key}'")
            if prob.get("id") != f.stem:
                err(f.name, "id must match the file name")
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            err(f.name, str(e))

    counts = {"patterns": len(patterns), "drill_items": len(drills), "select_items": len(sel),
              "cases": len(cases), "problems": len(problems)}
    for k, n in counts.items():
        if n < TARGETS[k]:
            warnings.append(f"{k}: {n} (first-release target {TARGETS[k]})")
    medium_plus = sum(c.get("obscurity") in ("medium", "high") for c in cases)
    if medium_plus < 5:
        warnings.append(f"cases: {medium_plus} medium/high obscurity (target 5+)")

    print("Counts: " + ", ".join(f"{k} {v}" for k, v in counts.items())
          + f", drill real/adapted {sourced}")
    for w in warnings:
        print(f"  warn  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
