"""`c2a log`: record a real decision and a prediction now; record the outcome later.

Real-world outcomes are the hardest evidence C2A can collect about itself.
"""

from . import store
from .term import ask

DAY = 86400
FILE = "predictions.json"


def due(preds, t):
    return [p for p in preds if p.get("outcome_correct") is None and t >= p["check_after"]]


def remind():
    n = len(due(store.load(FILE, []), store.now()))
    if n:
        print(f"\n{n} logged prediction(s) are ready for follow-up: python -m c2a log")


def run():
    preds = store.load(FILE, [])
    t = store.now()
    for p in due(preds, t):
        print(f"\nFollow-up (logged {(t - p['ts']) / DAY:.0f} days ago)")
        print(f"  Decision:   {p['decision']}")
        print(f"  Constraint: {p['constraint']}")
        print(f"  Predicted:  {p['prediction']}")
        a = ask("  Did it happen as predicted? [y]es / [n]o / [l]ater: ", set("ynl"))
        if a == "l":
            p["check_after"] = t + 7 * DAY
            continue
        p["outcome_correct"] = a == "y"
        p["outcome"] = ask("  What actually happened? ")
        p["resolved_ts"] = t
        store.save(FILE, preds)
    if ask("\nLog a new decision? [y/n] ", set("yn")) == "n":
        return
    decision = ask("  The real decision you're making: ")
    constraint = ask("  The constraint you're trading, and what you're trading it for: ")
    prediction = ask("  A specific, checkable prediction of the result: ")
    days = ""
    while not days.replace(".", "", 1).isdigit():
        days = ask("  Check back in how many days? [14] ") or "14"
    preds.append({"id": f"p-{len(preds) + 1:04d}", "ts": t, "decision": decision,
                  "constraint": constraint, "prediction": prediction,
                  "check_after": t + float(days) * DAY, "outcome_correct": None})
    store.save(FILE, preds)
    print(f"  Saved. You'll be reminded in {days} days.")
