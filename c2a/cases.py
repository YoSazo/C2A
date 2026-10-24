"""Mode 3: real cases. Predict, reveal the documented outcome, self-mark, extract the pattern."""

import random

from . import llm, store
from .term import ask, clear, wrap

MARKS = {"h": "hit", "p": "partial", "m": "miss"}

CHECK_PROMPT = """You compare a prediction against a documented outcome. Facts only.
List each concrete claim in the prediction and say whether the documented outcome
SUPPORTS it, CONTRADICTS it, or DOESN'T MENTION it, quoting the outcome text.
Do not grade, score, praise, or judge the reasoning. Do not add facts beyond the outcome text."""


def _match_pattern(text, patterns):
    t = text.strip().lower()
    for p in patterns.values():
        if t in (p["id"], p["name"].lower()):
            return p["id"]
    return None


def run(n=3, check=False, rng=random):
    items = store.load("cases.json", [])
    if not items:
        print("No cases in data/cases.json.")
        return
    if check:
        llm.require()
    patterns = store.by_id("patterns.json")
    prog = store.progress()
    done = {r["item"] for r in prog["cases"]}
    pool = [c for c in items if c["id"] not in done] or items
    # obscure cases first: famous ones are recall, not thinking
    order = {"high": 0, "medium": 1, "low": 2}
    pool = sorted(rng.sample(pool, len(pool)), key=lambda c: order[c["obscurity"]])
    for k, case in enumerate(pool[:n], 1):
        clear()
        print(f"[{k}/{min(n, len(pool))}]  {case['domain']}, {case['year']}"
              f"  (obscurity: {case['obscurity']})\n")
        print(wrap(case["situation"]))
        prediction = ask("\n  What happens next? Your prediction:\n  > ")
        constraint = ask("  What is the key constraint you see?\n  > ")
        print(f"\n  ── {case['title']} ──")
        print(wrap(f"Outcome: {case['outcome']}"))
        names = ", ".join(patterns[p]["name"] for p in case["pattern_ids"] if p in patterns)
        print(wrap(f"Patterns: {names}"))
        print(wrap(f"Source: {case['source']}"))
        if check:
            try:
                print("\n" + wrap(llm.chat([
                    {"role": "system", "content": CHECK_PROMPT},
                    {"role": "user", "content": f"PREDICTION:\n{prediction}\n\nDOCUMENTED OUTCOME:\n{case['outcome']}"},
                ], temperature=0)))
            except llm.LLMError as e:
                print(f"  (fact check unavailable: {e})")
        mark = MARKS[ask("\n  Self-mark: [h]it, [p]artial, [m]iss: ", set("hpm"))]
        named = ask("  Pattern you used (name or id, Enter to skip): ")
        pid = _match_pattern(named, patterns) if named else None
        if named and not pid:
            store.append("pattern_proposals.json", {
                "ts": store.now(), "case": case["id"], "proposed": named, "constraint": constraint})
            print("  Not in the library; logged to data/pattern_proposals.json for review.")
        prog["cases"].append({"ts": store.now(), "item": case["id"], "prediction": prediction,
                              "constraint": constraint, "mark": mark, "named_pattern": pid or named or None,
                              "obscurity": case["obscurity"], "repeat": case["id"] in done})
        store.save_progress(prog)
        if k < min(n, len(pool)) and ask("\n  Another? [y/n] ", set("yn")) == "n":
            break
