"""Command line and menu. Each mode module is imported only when used."""

import argparse
import sys

MENU = [
    ("1", "Drill: pattern recognition, timed (daily)", ["drill"]),
    ("2", "Drill under load (hold 7 digits)", ["drill", "--load"]),
    ("3", "Select: pick a trade, see what happened", ["select"]),
    ("4", "Cases: predict a real case", ["cases"]),
    ("5", "Live: fix a truss with an LLM translating", ["live"]),
    ("6", "Log a real decision / follow up on outcomes", ["log"]),
    ("7", "Stats", ["stats"]),
    ("q", "Quit", None),
]


def parser():
    ap = argparse.ArgumentParser(prog="python -m c2a", description="C2A: constraint to advantage.")
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("drill", help="pattern drills with spaced repetition")
    d.add_argument("--n", type=int, default=20, help="items per session (default 20)")
    d.add_argument("--load", action="store_true", help="load test: hold a 7-digit number during 5 items")
    s = sub.add_parser("select", help="choose between trades with real outcomes")
    s.add_argument("--n", type=int, default=5)
    c = sub.add_parser("cases", help="predict real cases, then see the outcome")
    c.add_argument("--n", type=int, default=3)
    c.add_argument("--check", action="store_true", help="LLM lists which prediction claims the outcome supports (no score)")
    lv = sub.add_parser("live", help="live loop against a real verifier (needs OPENAI_API_KEY)")
    lv.add_argument("--problem", help="problem id, e.g. bridge_01 (default: choose)")
    lv.add_argument("--baseline", action="store_true", help="run the LLM alone for comparison")
    lv.add_argument("--runs", type=int, default=5, help="baseline runs (default 5)")
    lv.add_argument("--max-loops", type=int, default=15)
    lv.add_argument("--manual", action="store_true", help="no LLM: type JSON edits yourself")
    sub.add_parser("log", help="log a real decision and prediction; follow up later")
    sub.add_parser("stats", help="mastery, reaction-time trend, real-world hit rate")
    return ap


def dispatch(args):
    if args.cmd == "drill":
        from . import drill
        drill.run(n=args.n, load=args.load)
    elif args.cmd == "select":
        from . import select
        select.run(n=args.n)
    elif args.cmd == "cases":
        from . import cases
        cases.run(n=args.n, check=args.check)
    elif args.cmd == "live":
        from .live import loop
        loop.main(args)
    elif args.cmd == "log":
        from . import log
        log.run()
    elif args.cmd == "stats":
        from . import stats
        stats.show()


def menu(ap):
    from . import log
    log.remind()
    while True:
        print("\nC2A\n")
        for key, label, _ in MENU:
            print(f"  {key}. {label}")
        choice = input("\n> ").strip().lower()
        argv = next((a for k, _, a in MENU if k == choice), "?")
        if argv is None:
            return
        if argv != "?":
            run(ap, argv)


def run(ap, argv):
    from .llm import LLMError
    try:
        dispatch(ap.parse_args(argv))
    except LLMError as e:
        print(f"\n{e}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Progress so far is saved.")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = parser()
    if not argv:
        try:
            menu(ap)
        except (KeyboardInterrupt, EOFError):
            print()
        return 0
    return run(ap, argv)
