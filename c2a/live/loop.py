"""Mode 4: live loop. The verifier's failures are the constraints; the human transmutes;
the LLM only translates (problem -> plain words, failures -> plain words, idea -> edit).
"""

import json
import re
import time
from pathlib import Path

from .. import llm, store
from ..term import ask, wrap
from . import truss

PROBLEMS = Path(__file__).resolve().parent / "problems"
HIDDEN = ("reference_solution", "tutorial")     # never shown to the LLM

PLAIN = """You explain an engineering situation to a smart person with no engineering background.
Use everyday words. If you must use a technical idea (e.g. buckling), explain it in one plain sentence.
Describe what is happening and why, physically. NEVER suggest a fix, a change, or a direction to try,
not even as a question or hint. Refer to bars by their id and end points, e.g. "bar m3 (A to D)".
Keep it under 150 words."""

TRANSLATE = """You translate a person's plain-words idea into a structured edit of a 2D truss.
HARD RULES:
1. Translate the idea literally. Do NOT add improvements, extra bars, resizes, moves or fixes the
   person did not describe. If their idea won't work, translate it anyway; the calculator will say so.
2. If the idea is ambiguous (which bar, which point, where exactly, what size), ask ONE short
   clarifying question instead of guessing.
3. Reply with ONE JSON object only, either
   {"clarify": "<question>"}
   or
   {"restatement": "<plain words: what will change, naming every bar/point id the edit touches>",
    "edit": {"ops": [ ... ]}}
"""

OPS = """Allowed ops (ids are strings; coordinates in metres; section is one of the listed sizes):
  {"op":"add_node","id":"P","x":3,"y":1}       {"op":"move_node","id":"D","x":3,"y":2}
  {"op":"remove_node","id":"P"}                {"op":"add_member","id":"m9","a":"A","b":"P","section":"S"}
  {"op":"remove_member","id":"m4"}             {"op":"resize_member","id":"m3","section":"L"}
Supports and loads can't change. Points with a support or load can't move or be removed.
A point can only be removed after its bars are removed."""
TRANSLATE += OPS

BASELINE = """You are a structural engineer fixing a 2D pin-jointed truss so it passes every check
(strength, Euler buckling of solid round bars, stability, deflection if limited) within budget.
Each turn you get the calculator's report. Reply with ONE JSON object: {"edit": {"ops": [...]}}.
""" + OPS


def load_problem(pid):
    path = PROBLEMS / f"{pid}.json"
    if not path.exists():
        raise SystemExit(f"No problem {pid!r}. Available: {', '.join(p.stem for p in sorted(PROBLEMS.glob('*.json')))}")
    return json.loads(path.read_text(encoding="utf-8"))


def public(problem, design):
    """What the LLM may see: everything except the reference solution, with the current design."""
    return {**{k: v for k, v in problem.items() if k not in HIDDEN}, "design": design}


def member_table(design, result):
    ends = {m["id"]: f"{m['a']}-{m['b']}" for m in design["members"]}
    lines = []
    for mid, info in result["members"].items():
        kind = "pulled" if info["force"] > 0 else "pushed"
        line = (f"  {mid:4} {ends[mid]:5} size {info['section']:2} {info['length']:.2f} m  "
                f"{kind} {abs(info['force']) / 1000:6.1f} kN  strength used {info['yield_ratio']:4.0%}")
        if "buckling_ratio" in info:
            line += f"  bowing limit used {info['buckling_ratio']:4.0%}"
        lines.append(line)
    lines.append(f"  cost {result['cost']:.0f} of budget {result['budget']:.0f}")
    return "\n".join(lines)


def failure_lines(result):
    out = []
    for f in result["failures"]:
        if f["check"] == "mechanism":
            out.append(f"  UNSTABLE: points {', '.join(f['nodes'])} can move freely")
        elif f["check"] in ("yield", "buckling"):
            out.append(f"  {f['check'].upper():9} bar {f['member']}: {f['ratio']:.2f}x over the limit")
        else:
            out.append(f"  {f['check'].upper():9} {f['ratio']:.2f}x over the limit")
    return "\n".join(out) or "  none"


def report(design, problem, result):
    """Compact calculator report used as LLM input."""
    return json.dumps({"failures": result["failures"], "cost": result["cost"], "budget": result["budget"],
                       "members": {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()}
                                   for k, v in result["members"].items()},
                       "design": design}, default=float)


def unmentioned(edit, restatement):
    """Ids the edit touches that the plain-words restatement never names."""
    words = set(re.findall(r"[A-Za-z0-9_]+", restatement or ""))
    return sorted(i for i in truss.touched(edit) if i not in words)


def translate(idea, design, problem, history):
    """Ask the LLM for {clarify} or {restatement, edit}; enforce schema and the mention rule."""
    msgs = [{"role": "system", "content": TRANSLATE},
            {"role": "user", "content": "Current structure:\n" + json.dumps(public(problem, design))},
            *history, {"role": "user", "content": f"The person's idea: {idea}"}]
    for _ in range(2):
        resp = llm.chat_json(msgs, temperature=0)
        if resp.get("clarify"):
            return resp, None
        problems = []
        try:
            new = truss.apply_edit(design, resp.get("edit"), problem)
        except truss.EditError as e:
            problems.append(f"invalid edit: {e}")
            new = None
        missing = unmentioned(resp.get("edit") or {}, resp.get("restatement", "")) if new else []
        if missing:
            problems.append(f"the edit touches {missing}, which the restatement doesn't mention")
        if not problems:
            return resp, new
        msgs += [{"role": "assistant", "content": json.dumps(resp)},
                 {"role": "user", "content": "Rejected: " + "; ".join(problems) + ". Fix it, still literally."}]
    return {"error": "; ".join(problems)}, None


def _save(rec):
    d = store.data_dir() / "live_logs"
    d.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d-%H%M%S')}_{rec['problem']}_{rec['kind']}.json"
    store.save(f"live_logs/{name}", rec)
    return d / name


def choose_problem():
    probs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(PROBLEMS.glob("*.json"))]
    for k, p in enumerate(probs, 1):
        tag = "  (tutorial)" if p.get("tutorial") else ""
        print(f"  {k}. {p['id']}: {p['title']}  [difficulty {p.get('difficulty', '?')}]{tag}")
    k = ask("\n  Problem number: ", set("123456789"[:len(probs)]))
    return probs[int(k) - 1]


def run_human(problem, max_loops, manual=False):
    design = problem["design"]
    rec = {"kind": "manual" if manual else "human", "problem": problem["id"],
           "model": None if manual else llm.model(), "started": store.now(),
           "loops": 0, "history": [], "rejections": [], "clarifications": []}
    print(f"\n== {problem['title']} ==\n")
    if manual:
        print(wrap(problem["brief"]))
    else:
        print(wrap(llm.chat([{"role": "system", "content": PLAIN},
                             {"role": "user", "content": "Describe this problem:\n" + json.dumps(public(problem, design))}])))
    result = truss.run(design, problem)
    undo = []
    while not result["ok"] and rec["loops"] < max_loops:
        print("\n" + truss.sketch(design, result["failures"]))
        print("\nFailing checks:\n" + failure_lines(result))
        if not manual:
            print("\n" + wrap(llm.chat([{"role": "system", "content": PLAIN},
                                        {"role": "user", "content": "Explain what is failing and why:\n" + report(design, problem, result)}])))
        print(f"\n  Loop {rec['loops'] + 1}/{max_loops}.  Type your idea.  "
              "Commands: ? numbers, undo, q quit")
        idea = ask("  > ")
        if idea.lower() in ("q", "quit"):
            break
        if idea == "?":
            print(member_table(design, result))
            continue
        if idea.lower() == "undo":
            if undo:
                design = undo.pop()
                result = truss.run(design, problem)
            continue
        if manual:
            try:
                edit = json.loads(idea)
                new, restatement = truss.apply_edit(design, edit, problem), "(manual JSON edit)"
            except (json.JSONDecodeError, truss.EditError) as e:
                print(f"  Not applied: {e}")
                continue
        else:
            history = []
            while True:
                resp, new = translate(idea, design, problem, history)
                if resp.get("clarify"):
                    answer = ask(f"  Question: {resp['clarify']}\n  > ")
                    rec["clarifications"].append({"idea": idea, "question": resp["clarify"], "answer": answer})
                    history += [{"role": "assistant", "content": json.dumps(resp)},
                                {"role": "user", "content": f"Answer: {answer}"}]
                    continue
                break
            if new is None:
                print(f"  Couldn't turn that into a valid edit ({resp.get('error')}). Try rephrasing.")
                rec["rejections"].append({"idea": idea, "reason": resp.get("error"), "by": "validator"})
                continue
            edit, restatement = resp["edit"], resp["restatement"]
            print("\n" + wrap(f"Translation: {restatement}"))
            if ask("  Is this your idea? [y/n] ", set("yn")) == "n":
                rec["rejections"].append({"idea": idea, "restatement": restatement, "edit": edit, "by": "user"})
                print("  OK, rephrase it.")
                continue
        undo.append(design)
        design = new
        result = truss.run(design, problem)
        rec["loops"] += 1
        rec["history"].append({"idea": idea, "restatement": restatement, "edit": edit,
                               "failures": result["failures"], "cost": result["cost"]})
    return _finish(rec, design, problem, result)


def _finish(rec, design, problem, result):
    rec.update(solved=result["ok"], final_cost=result["cost"], budget=problem["budget"],
               final_design=design, ended=store.now())
    path = _save(rec)
    status = "SOLVED" if result["ok"] else "not solved"
    print(f"\n{status} after {rec['loops']} loop(s); cost {result['cost']:.0f} of {problem['budget']}. Log: {path}")
    if result["ok"]:
        print(truss.sketch(design))
    return rec


def run_baseline(problem, max_loops):
    """The LLM alone, same loop cap, sees the raw calculator report each turn."""
    design = problem["design"]
    rec = {"kind": "baseline", "problem": problem["id"], "model": llm.model(), "started": store.now(),
           "loops": 0, "history": [], "invalid": 0}
    msgs = [{"role": "system", "content": BASELINE},
            {"role": "user", "content": "Problem:\n" + json.dumps(public(problem, design))}]
    result = truss.run(design, problem)
    while not result["ok"] and rec["loops"] < max_loops:
        msgs.append({"role": "user", "content": "Calculator report:\n" + report(design, problem, result)})
        rec["loops"] += 1
        try:
            resp = llm.chat_json(msgs, temperature=0.7)
            design = truss.apply_edit(design, resp.get("edit"), problem)
            msgs.append({"role": "assistant", "content": json.dumps(resp)})
        except (truss.EditError, llm.LLMError) as e:
            rec["invalid"] += 1
            msgs.append({"role": "user", "content": f"That edit was rejected: {e}"})
            continue
        result = truss.run(design, problem)
        rec["history"].append({"edit": resp.get("edit"), "failures": result["failures"], "cost": result["cost"]})
        print(f"  loop {rec['loops']}: {len(result['failures'])} failure(s), cost {result['cost']:.0f}")
    return _finish(rec, design, problem, result)


def main(args):
    if not args.manual:
        llm.require()
    problem = load_problem(args.problem) if args.problem else choose_problem()
    if args.baseline:
        if args.manual:
            raise SystemExit("--baseline needs the LLM; drop --manual.")
        runs = [run_baseline(problem, args.max_loops) for _ in range(args.runs)]
        solved = sum(r["solved"] for r in runs)
        print(f"\nBaseline, LLM alone: solved {solved}/{len(runs)}; "
              f"mean loops {sum(r['loops'] for r in runs) / len(runs):.1f}.")
        if solved == len(runs):
            print("The LLM alone always solves this one: treat it as a tutorial, not evidence.")
        return
    if args.manual:
        print("Manual mode: type edits as JSON, e.g. "
              '{"ops":[{"op":"resize_member","id":"m3","section":"L"}]}')
    run_human(problem, args.max_loops, manual=args.manual)
