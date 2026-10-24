"""Mode 2: choose between trades; the right answer comes from a real, documented outcome."""

import random

from . import store
from .term import ask, clear, wrap


def run(n=5, rng=random):
    items = store.load("select_items.json", [])
    if not items:
        print("No items in data/select_items.json.")
        return
    prog = store.progress()
    done = {r["item"] for r in prog["select"]}
    fresh = [i for i in items if i["id"] not in done]
    pool = fresh or items
    for k, item in enumerate(rng.sample(pool, min(n, len(pool))), 1):
        clear()
        print(f"[{k}/{min(n, len(pool))}]{'' if fresh else '  (all items seen; repeating)'}\n")
        print(wrap(item["situation"]))
        print(f"\n  Goal: {item['goal']}\n")
        for j, opt in enumerate(item["options"], 1):
            print(wrap(f"{j}. {opt}", "  "))
        valid = "".join(str(j) for j in range(1, len(item["options"]) + 1)) + "q"
        ans = ask("\n  Your pick: ", set(valid))
        if ans == "q":
            break
        chosen = int(ans) - 1
        correct = chosen == item["answer_index"]
        print(f"\n  {'RIGHT' if correct else 'WRONG'}: the documented result favoured "
              f"option {item['answer_index'] + 1}.")
        print(wrap(f"What happened: {item['outcome']}"))
        print(wrap(f"Source: {item['source']}"))
        prog["select"].append({"ts": store.now(), "item": item["id"], "chosen": chosen,
                               "correct": correct, "repeat": item["id"] in done})
        store.save_progress(prog)
        input("\n  [Enter] next")
    recs = [r for r in prog["select"] if not r.get("repeat")]
    if recs:
        print(f"\nSelect accuracy, first attempts: {sum(r['correct'] for r in recs)}/{len(recs)}")
