"""
AMAVA — Adversarial Multi-Agent Validation Architecture
========================================================
Compiles C2A transmutations through a constraint DAG meat-grinder:
  Phase 0  Transmultiplication (human → sibling variants)
  Phase 1  Epistemic airgap (strip + graph map)
  Phase 2  Grounding engine (spec RAG + deterministic checks)
  Phase 3  Red vs Blue tribunal (max 3 patch cycles)
  Phase 4  Blind judge (validation matrix)
  Phase 5  Compiler handoff (survivor → execution plan)

Available at any level; highest throughput/novelty expected at Level 100+.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SPECS_PATH = Path(__file__).resolve().parent / "amava_specs.json"
MAX_BLUE_CYCLES = 3
MAX_HUMAN_INPUTS = 15
MAX_PIPELINE_ITEMS = 40
IDEAL_LEVEL = 100


def _parse_json_block(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


def load_specs() -> List[dict]:
    if not SPECS_PATH.exists():
        return []
    try:
        data = json.loads(SPECS_PATH.read_text(encoding="utf-8"))
        return list(data.get("specs") or [])
    except Exception:
        return []


def retrieve_specs(text: str, graph: dict) -> List[dict]:
    """Pull spec rows relevant to problem + graph labels."""
    blob = (text or "").lower()
    for node in graph.get("nodes") or []:
        if isinstance(node, dict):
            blob += " " + str(node.get("label", "")).lower()
            blob += " " + str(node.get("type", "")).lower()
            params = node.get("params") or {}
            if isinstance(params, dict):
                blob += " " + json.dumps(params).lower()
    hits: List[dict] = []
    for spec in load_specs():
        keywords = spec.get("keywords") or []
        if any(kw.lower() in blob for kw in keywords):
            hits.append(spec)
    if not hits:
        hits = load_specs()[:3]
    return hits


def _graph_nodes_edges(graph: dict) -> Tuple[List[dict], List[dict]]:
    nodes = list(graph.get("nodes") or [])
    edges = list(graph.get("edges") or [])
    return nodes, edges


def detect_dag_violations(graph: dict) -> List[dict]:
    """Deterministic cycle detection."""
    _, edges = _graph_nodes_edges(graph)
    adj: Dict[str, List[str]] = {}
    nodes_seen: Set[str] = set()
    for e in edges:
        if not isinstance(e, dict):
            continue
        src, dst = e.get("from"), e.get("to")
        if not src or not dst:
            continue
        nodes_seen.add(src)
        nodes_seen.add(dst)
        adj.setdefault(src, []).append(dst)

    tickets: List[dict] = []
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def dfs(n: str, stack: List[str]) -> None:
        if n in visiting:
            tickets.append(
                {
                    "agent": "Red-2",
                    "code": "DAG_CYCLE",
                    "node_ids": stack + [n],
                    "message": f"Cycle detected involving node '{n}' — graph is not a DAG.",
                    "severity": "fatal",
                    "spec_citation": None,
                }
            )
            return
        if n in visited:
            return
        visiting.add(n)
        for nxt in adj.get(n, []):
            dfs(nxt, stack + [n])
        visiting.remove(n)
        visited.add(n)

    for n in nodes_seen:
        if n not in visited:
            dfs(n, [])
    return tickets


def detect_dependency_violations(graph: dict) -> List[dict]:
    """Edges marked requires_prior must respect topological order."""
    nodes, edges = _graph_nodes_edges(graph)
    order = {n.get("id"): i for i, n in enumerate(nodes) if isinstance(n, dict) and n.get("id")}
    tickets: List[dict] = []
    for e in edges:
        if not isinstance(e, dict) or not e.get("requires_prior"):
            continue
        src, dst = e.get("from"), e.get("to")
        if src in order and dst in order and order[src] >= order[dst]:
            tickets.append(
                {
                    "agent": "Red-2",
                    "code": "DEPENDENCY_ORDER",
                    "node_ids": [src, dst],
                    "message": f"Edge {src}→{dst} violates declared execution order.",
                    "severity": "error",
                    "spec_citation": None,
                }
            )
    return tickets


def detect_bottleneck_violations(graph: dict, specs: List[dict]) -> List[dict]:
    """Compare claimed edge rates against retrieved spec limits."""
    tickets: List[dict] = []
    spec_by_type = {s.get("limit_type"): s for s in specs if s.get("limit_type")}

    for e in graph.get("edges") or []:
        if not isinstance(e, dict):
            continue
        claim = e.get("rate_claim")
        if claim is None:
            continue
        unit = (e.get("rate_unit") or "").lower()
        try:
            val = float(claim)
        except (TypeError, ValueError):
            continue

        if "m/s" in unit or unit == "velocity":
            orbital = spec_by_type.get("velocity_min")
            lab_max = spec_by_type.get("velocity_max")
            if orbital and val >= float(orbital.get("limit_value", 7800)) * 0.9:
                if lab_max and val > float(lab_max.get("limit_value", 3000)):
                    tickets.append(
                        {
                            "agent": "Red-1",
                            "code": "VELOCITY_BOTTLENECK",
                            "node_ids": [e.get("from"), e.get("to")],
                            "message": (
                                f"Claimed velocity {val} m/s approaches orbital class but exceeds "
                                f"compact EM launcher spec (~{lab_max.get('limit_value')} m/s) without staged proof."
                            ),
                            "severity": "error",
                            "spec_citation": lab_max.get("id"),
                        }
                    )
        if "mw" in unit or unit == "power":
            pmax = spec_by_type.get("power_max")
            if pmax and val > float(pmax.get("limit_value", 70)):
                tickets.append(
                    {
                        "agent": "Red-1",
                        "code": "POWER_BOTTLENECK",
                        "node_ids": [e.get("from"), e.get("to")],
                        "message": (
                            f"Claimed power {val} MW exceeds typical aircraft bleed budget "
                            f"(~{pmax.get('limit_value')} MW)."
                        ),
                        "severity": "error",
                        "spec_citation": pmax.get("id"),
                    }
                )
    return tickets


def run_deterministic_red(graph: dict, specs: List[dict]) -> List[dict]:
    tickets: List[dict] = []
    tickets.extend(detect_dag_violations(graph))
    tickets.extend(detect_dependency_violations(graph))
    tickets.extend(detect_bottleneck_violations(graph, specs))
    return tickets


def _llm_json(llm, system: str, user: str, temperature: float = 0.2) -> dict:
    try:
        raw = llm.chat(user, system=system, temperature=temperature, max_tokens=4096)
    except Exception as exc:
        return {"error": str(exc)}
    parsed = _parse_json_block(raw)
    if not parsed:
        return {"error": "non_json_response", "raw": (raw or "")[:500]}
    return parsed


STRIPPER_SYSTEM = """You are Agent 1: Lexical Stripper (AMAVA Phase 1).
Strip ALL metaphor, analogy, and persuasive language from the transmutation.
Output ONLY valid JSON:
{
  "directives": [
    {"id": "d1", "action": "add|remove|route|cache|trigger|measure", "subject": "...", "target": "...", "params": {}}
  ]
}
No commentary outside JSON."""


MAPPER_SYSTEM = """You are Agent 2: Graph Mapper (AMAVA Phase 1).
Build a Hypothesis Graph DAG from directives. You do NOT judge quality.
Output ONLY valid JSON:
{
  "nodes": [
    {"id": "n1", "type": "process|storage|transfer|sensor|actuator|constraint", "label": "...", "params": {}}
  ],
  "edges": [
    {"from": "n1", "to": "n2", "kind": "data|energy|control", "rate_claim": null, "rate_unit": "", "requires_prior": false}
  ]
}
Rules: acyclic graph, every edge references existing nodes."""


RED_SYSTEM = """You are the Red Team swarm (AMAVA Phase 3). Destroy the Hypothesis Graph.
You MUST cite spec_id from GROUNDING_SPECS for every technical violation.
Output ONLY valid JSON:
{
  "tickets": [
    {"agent": "Red-1|Red-2|Red-3", "code": "...", "node_ids": [], "message": "...", "severity": "fatal|error", "spec_citation": "spec_id or null"}
  ]
}
Red-1: bandwidth/energy/physics bottlenecks. Red-2: dependency/race/deadlock. Red-3: state corruption/overwrites.
If no violations, return {"tickets": []}. Be ruthless — do not please the user."""


BLUE_SYSTEM = """You are Blue-1 Engineer (AMAVA Phase 3).
You may ONLY patch locally — never delete the user's core transmutation advantage.
Output ONLY valid JSON:
{
  "patches": [
    {"ticket_code": "...", "action": "add_node|add_edge|modify_node|modify_edge", "detail": {}, "rationale": "..."}
  ],
  "core_preserved": true
}
If impossible without destroying core, return {"patches": [], "core_preserved": false}."""


JUDGE_SYSTEM = """You are the Epistemic Overseer (AMAVA Phase 4) — BLIND JUDGE.
You do NOT see the user's original analogy. You only see the survived graph, spec citations, and combat log.
Output ONLY valid JSON:
{
  "traceability": true,
  "red_rigor": true,
  "novel_vs_baseline": true,
  "pass": true,
  "kill_reason": ""
}
Set pass=false if any matrix item is false. Be strict on traceability."""


COMPILER_SYSTEM = """You are Agent Omega: Compiler (AMAVA Phase 5).
Translate the surviving Hypothesis Graph into execution reality.
Output ONLY valid JSON:
{
  "architecture_summary": "...",
  "mvp_phases": [{"name": "...", "proves": "...", "estimated_cost": "..."}],
  "kill_criteria": ["..."],
  "accounting_gaps": ["..."],
  "honest_claim": "what this actually proves vs what it does not"
}"""


TRANSMULTIPLY_SYSTEM = """You are the Transmultiplication Agent (AMAVA Phase 0).
Spawn sibling transmutations from a human C2A transmutation.

PRESERVE the core constraint trade (the fundamental portfolio swap).
CHANGE mechanism, scale, sequencing, domain steal, material path, or topology.

Output ONLY valid JSON:
{
  "siblings": [
    {
      "label": "short variant name",
      "transmutation": "full standalone transmutation text",
      "mutation_axis": "what dimension changed vs the human original"
    }
  ]
}

Rules:
- Siblings must be genuinely different architectures, not paraphrases.
- Do NOT abandon the human's core trade for cope or reframe.
- Do NOT copy the original verbatim.
- Each sibling must still apply to the given problem and baseline constraint."""


def default_siblings_per_level(level: int) -> int:
    if level >= IDEAL_LEVEL:
        return 4
    if level >= 70:
        return 3
    if level >= 16:
        return 2
    return 1


def transmultiply_one(
    llm,
    problem: str,
    baseline: str,
    human_text: str,
    human_index: int,
    siblings_per: int,
) -> List[dict]:
    """Return sibling variant dicts for one human transmutation."""
    if siblings_per <= 0:
        return []
    prompt = (
        f"PROBLEM:\n{problem}\n\nBASELINE CONSTRAINT:\n{baseline}\n\n"
        f"HUMAN TRANSMUTATION #{human_index + 1}:\n{human_text}\n\n"
        f"Generate exactly {siblings_per} sibling variants."
    )
    data = _llm_json(llm, TRANSMULTIPLY_SYSTEM, prompt, temperature=0.55)
    siblings = data.get("siblings") if isinstance(data.get("siblings"), list) else []
    out: List[dict] = []
    for i, sib in enumerate(siblings[:siblings_per]):
        if not isinstance(sib, dict):
            continue
        text = (sib.get("transmutation") or "").strip()
        if not text or text.lower() == human_text.strip().lower():
            continue
        out.append(
            {
                "label": sib.get("label") or f"variant-{i + 1}",
                "transmutation": text,
                "mutation_axis": sib.get("mutation_axis") or "mechanism",
            }
        )
    return out


def expand_transmutation_queue(
    llm,
    problem: str,
    baseline: str,
    humans: List[str],
    *,
    transmultiply: bool,
    siblings_per: int,
    include_original: bool = True,
) -> Tuple[List[dict], dict]:
    """
    Expand human transmutations into pipeline queue items with lineage metadata.
    Each queue item: {text, human_index, is_original, sibling_label, mutation_axis}
    """
    queue: List[dict] = []
    expansion_stats = {
        "human_count": len(humans),
        "siblings_per_requested": siblings_per if transmultiply else 0,
        "expanded_count": 0,
        "sibling_count": 0,
    }

    for hi, human in enumerate(humans):
        if include_original:
            queue.append(
                {
                    "text": human,
                    "human_index": hi,
                    "is_original": True,
                    "sibling_label": "human",
                    "mutation_axis": None,
                }
            )
        if transmultiply and siblings_per > 0:
            siblings = transmultiply_one(llm, problem, baseline, human, hi, siblings_per)
            for sib in siblings:
                queue.append(
                    {
                        "text": sib["transmutation"],
                        "human_index": hi,
                        "is_original": False,
                        "sibling_label": sib.get("label") or "sibling",
                        "mutation_axis": sib.get("mutation_axis"),
                    }
                )
                expansion_stats["sibling_count"] += 1
        if len(queue) >= MAX_PIPELINE_ITEMS:
            break

    queue = queue[:MAX_PIPELINE_ITEMS]
    expansion_stats["expanded_count"] = len(queue)
    return queue, expansion_stats


def apply_patches(graph: dict, patches: List[dict]) -> dict:
    g = deepcopy(graph)
    nodes = list(g.get("nodes") or [])
    edges = list(g.get("edges") or [])
    node_ids = {n.get("id") for n in nodes if isinstance(n, dict)}

    for p in patches or []:
        if not isinstance(p, dict):
            continue
        action = p.get("action")
        detail = p.get("detail") or {}
        if action == "add_node" and detail.get("id"):
            if detail["id"] not in node_ids:
                nodes.append(detail)
                node_ids.add(detail["id"])
        elif action == "add_edge":
            edges.append(detail)
        elif action == "modify_node":
            nid = detail.get("id")
            for i, n in enumerate(nodes):
                if isinstance(n, dict) and n.get("id") == nid:
                    nodes[i] = {**n, **detail}
        elif action == "modify_edge":
            for i, e in enumerate(edges):
                if isinstance(e, dict) and e.get("from") == detail.get("from") and e.get("to") == detail.get("to"):
                    edges[i] = {**e, **detail}
    g["nodes"] = nodes
    g["edges"] = edges
    return g


def _strip_and_map(
    llm,
    problem: str,
    baseline: str,
    transmutation: str,
    index: int,
) -> dict:
    strip = _llm_json(
        llm,
        STRIPPER_SYSTEM,
        f"PROBLEM:\n{problem}\n\nBASELINE CONSTRAINT:\n{baseline}\n\nTRANSMUTATION #{index + 1}:\n{transmutation}",
    )
    directives = strip.get("directives") if isinstance(strip.get("directives"), list) else []

    graph_raw = _llm_json(
        llm,
        MAPPER_SYSTEM,
        f"PROBLEM:\n{problem}\n\nDIRECTIVES:\n{json.dumps(directives, indent=2)}",
    )
    graph = {
        "nodes": graph_raw.get("nodes") or [],
        "edges": graph_raw.get("edges") or [],
    }
    return {"directives": directives, "graph": graph, "strip_error": strip.get("error"), "map_error": graph_raw.get("error")}


def _red_pass(llm, graph: dict, specs: List[dict], deterministic: List[dict]) -> List[dict]:
    spec_blob = json.dumps(
        [{"id": s.get("id"), "claim": s.get("claim"), "limit": s.get("limit_value"), "unit": s.get("limit_unit")} for s in specs],
        indent=2,
    )
    red = _llm_json(
        llm,
        RED_SYSTEM,
        f"GROUNDING_SPECS:\n{spec_blob}\n\nDETERMINISTIC_TICKETS_ALREADY_FOUND:\n{json.dumps(deterministic, indent=2)}\n\nHYPOTHESIS_GRAPH:\n{json.dumps(graph, indent=2)}",
        temperature=0.15,
    )
    llm_tickets = red.get("tickets") if isinstance(red.get("tickets"), list) else []
    merged = list(deterministic)
    seen = {(t.get("code"), tuple(t.get("node_ids") or [])) for t in deterministic}
    for t in llm_tickets:
        if not isinstance(t, dict):
            continue
        key = (t.get("code"), tuple(t.get("node_ids") or []))
        if key not in seen:
            merged.append(t)
            seen.add(key)
    return merged


def _blue_patch(llm, graph: dict, tickets: List[dict], specs: List[dict]) -> dict:
    return _llm_json(
        llm,
        BLUE_SYSTEM,
        f"TICKETS:\n{json.dumps(tickets, indent=2)}\n\nSPECS:\n{json.dumps([s.get('id') for s in specs])}\n\nGRAPH:\n{json.dumps(graph, indent=2)}",
        temperature=0.25,
    )


def _judge_pass(llm, graph: dict, specs: List[dict], combat_log: List[dict], baseline: str) -> dict:
    cited = {t.get("spec_citation") for t in _flatten_tickets(combat_log) if t.get("spec_citation")}
    spec_ids = {s.get("id") for s in specs}
    return _llm_json(
        llm,
        JUDGE_SYSTEM,
        f"BASELINE_CONSTRAINT (for novelty only — not user voice):\n{baseline}\n\n"
        f"SPEC_IDS_AVAILABLE: {sorted(spec_ids)}\n"
        f"SPEC_IDS_CITED_IN_COMBAT: {sorted(cited)}\n\n"
        f"SURVIVED_GRAPH:\n{json.dumps(graph, indent=2)}\n\n"
        f"COMBAT_LOG:\n{json.dumps(combat_log, indent=2)}",
        temperature=0.1,
    )


def _flatten_tickets(combat_log: List[dict]) -> List[dict]:
    out: List[dict] = []
    for entry in combat_log:
        for t in entry.get("tickets") or []:
            out.append(t)
    return out


def _has_fatal_tickets(tickets: List[dict]) -> bool:
    return any((t.get("severity") == "fatal") for t in tickets if isinstance(t, dict))


def process_transmutation(
    llm,
    problem: str,
    baseline: str,
    transmutation: str,
    index: int,
    lineage: Optional[dict] = None,
) -> dict:
    phase_log: List[str] = []
    phase_log.append("Phase 1: Epistemic airgap — strip + map")

    sm = _strip_and_map(llm, problem, baseline, transmutation, index)
    graph = sm["graph"]
    specs = retrieve_specs(f"{problem} {baseline} {transmutation}", graph)
    phase_log.append(f"Phase 2: Grounding — {len(specs)} spec anchors loaded")

    combat_log: List[dict] = []
    tickets = run_deterministic_red(graph, specs)
    tickets = _red_pass(llm, graph, specs, tickets)
    combat_log.append({"cycle": 0, "phase": "initial_red", "tickets": tickets})

    cycles = 0
    fatal = False
    core_lost = False

    while tickets and cycles < MAX_BLUE_CYCLES:
        if _has_fatal_tickets(tickets):
            phase_log.append(f"Phase 3: Fatal tickets at cycle {cycles} — patch attempt")
        blue = _blue_patch(llm, graph, tickets, specs)
        patches = blue.get("patches") if isinstance(blue.get("patches"), list) else []
        if blue.get("core_preserved") is False or not patches:
            core_lost = True
            phase_log.append(f"Phase 3: Blue cannot patch without destroying core (cycle {cycles + 1})")
            break
        graph = apply_patches(graph, patches)
        cycles += 1
        tickets = run_deterministic_red(graph, specs)
        tickets = _red_pass(llm, graph, specs, tickets)
        combat_log.append({"cycle": cycles, "phase": "red_after_blue", "patches": patches, "tickets": tickets})

    if tickets:
        status = "FATAL"
        phase_log.append(f"Phase 3: Marked FATAL after {cycles} blue cycles")
        fatal = True
    else:
        status = "RED_CLEAR"
        phase_log.append("Phase 3: Red team found no remaining tickets")

    judge: dict = {}
    if not fatal:
        phase_log.append("Phase 4: Blind judge tribunal")
        judge = _judge_pass(llm, graph, specs, combat_log, baseline)
        if not judge.get("pass"):
            status = "KILLED_JUDGE"
            phase_log.append(f"Phase 4: Judge kill — {judge.get('kill_reason', 'matrix fail')}")
        elif not judge.get("novel_vs_baseline"):
            status = "KILLED_NOVELTY"
            phase_log.append("Phase 4: Non-novel — discarded")
        else:
            status = "SURVIVED"
            phase_log.append("Phase 4: Survived judge matrix")

    return {
        "index": index,
        "original": transmutation,
        "human_index": (lineage or {}).get("human_index"),
        "is_original": (lineage or {}).get("is_original", True),
        "sibling_label": (lineage or {}).get("sibling_label"),
        "mutation_axis": (lineage or {}).get("mutation_axis"),
        "human_source": (lineage or {}).get("human_source"),
        "directives": sm.get("directives") or [],
        "graph": graph,
        "grounding_specs": specs,
        "combat_log": combat_log,
        "blue_cycles": cycles,
        "core_lost": core_lost,
        "status": status,
        "judge_matrix": judge,
        "phase_log": phase_log,
    }


def compile_transmutations(
    llm,
    problem_statement: str,
    baseline_constraint: str,
    transmutations: List[str],
    level: int = 1,
    *,
    transmultiply: bool = True,
    siblings_per: Optional[int] = None,
    include_original: bool = True,
) -> dict:
    """Run full AMAVA pipeline on human transmutations (optionally expanded via Phase 0)."""
    problem = (problem_statement or "").strip()
    baseline = (baseline_constraint or "").strip()
    items = [t.strip() for t in transmutations if (t or "").strip()][:MAX_HUMAN_INPUTS]

    if not problem:
        return {"error": "problem_statement is required"}
    if not baseline:
        return {"error": "baseline_constraint is required"}
    if not items:
        return {"error": "At least one transmutation is required"}

    per = siblings_per if siblings_per is not None else default_siblings_per_level(level)
    per = max(0, min(6, int(per)))

    level_note = (
        "Level 100+ ideal — high transmutation rate and novelty expected."
        if level >= IDEAL_LEVEL
        else f"Level {level}: architecture works at any level; speed/novelty scale with practice. Target Level {IDEAL_LEVEL}+ for full symbiosis."
    )

    phase_log_global: List[str] = []
    expansion_stats: dict = {"human_count": len(items), "expanded_count": len(items)}

    if transmultiply and per > 0:
        phase_log_global.append(f"Phase 0: Transmultiply — up to {per} siblings per human transmutation")
        queue, expansion_stats = expand_transmutation_queue(
            llm,
            problem,
            baseline,
            items,
            transmultiply=True,
            siblings_per=per,
            include_original=include_original,
        )
        phase_log_global.append(
            f"Phase 0: {expansion_stats['human_count']} human → {expansion_stats['expanded_count']} pipeline items "
            f"({expansion_stats.get('sibling_count', 0)} siblings)"
        )
    else:
        queue = [
            {
                "text": t,
                "human_index": i,
                "is_original": True,
                "sibling_label": "human",
                "mutation_axis": None,
            }
            for i, t in enumerate(items)
        ]
        expansion_stats = {"human_count": len(items), "expanded_count": len(queue), "sibling_count": 0}

    results: List[dict] = []
    for i, item in enumerate(queue):
        hi = int(item.get("human_index", 0))
        human_source = items[hi] if hi < len(items) else item["text"]
        lineage = {
            "human_index": hi,
            "is_original": bool(item.get("is_original")),
            "sibling_label": item.get("sibling_label"),
            "mutation_axis": item.get("mutation_axis"),
            "human_source": human_source,
        }
        result = process_transmutation(llm, problem, baseline, item["text"], i, lineage=lineage)
        if i == 0 and phase_log_global:
            result["phase_log"] = phase_log_global + list(result.get("phase_log") or [])
        results.append(result)

    survivors = [r for r in results if r.get("status") == "SURVIVED"]
    compiler_output: dict = {}

    if survivors:
        best = survivors[0]
        compiler_output = _llm_json(
            llm,
            COMPILER_SYSTEM,
            f"PROBLEM:\n{problem}\n\nSURVIVING_GRAPH:\n{json.dumps(best.get('graph'), indent=2)}\n\n"
            f"JUDGE:\n{json.dumps(best.get('judge_matrix'), indent=2)}",
            temperature=0.3,
        )
        if survivors[0].get("phase_log") is not None:
            survivors[0]["phase_log"] = list(survivors[0]["phase_log"]) + ["Phase 5: Compiler handoff complete"]

    summary = {
        "human_count": expansion_stats.get("human_count", len(items)),
        "expanded_count": expansion_stats.get("expanded_count", len(results)),
        "sibling_count": expansion_stats.get("sibling_count", 0),
        "total": len(results),
        "survived": len(survivors),
        "fatal": sum(1 for r in results if r.get("status") == "FATAL"),
        "killed_judge": sum(1 for r in results if r.get("status") == "KILLED_JUDGE"),
        "killed_novelty": sum(1 for r in results if r.get("status") == "KILLED_NOVELTY"),
    }

    return {
        "problem_statement": problem,
        "baseline_constraint": baseline,
        "level": level,
        "ideal_level": IDEAL_LEVEL,
        "compatibility_note": level_note,
        "transmultiply": bool(transmultiply and per > 0),
        "siblings_per": per,
        "expansion": expansion_stats,
        "phase_log_global": phase_log_global,
        "transmutation_results": results,
        "summary": summary,
        "survivor_indices": [r["index"] for r in survivors],
        "compiler_output": compiler_output,
    }
