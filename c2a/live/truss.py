"""2D pin-jointed truss verifier (direct stiffness method). Units: m, N, Pa, m².

Interface shared by every verifier: run(design, problem) -> result with a
structured "failures" list. The failures are the constraints the user works on.

Design:
    {"nodes":    {"A": [0, 0], ...},
     "members":  [{"id": "m1", "a": "A", "b": "B", "section": "M"}, ...],
     "supports": {"A": "pin", "E": "roller"},          # roller resists vertical only
     "loads":    [{"node": "C", "fx": 0, "fy": -50000}]}
Problem adds: material {E, yield, cost_per_m3}, sections {name: area m²},
budget, optional max_deflection (m), region {xmin,xmax,ymin,ymax}, fixed_nodes.

Members are solid round bars, so I = A²/(4π); buckling is Euler, pinned-pinned (K=1).
"""

import copy
import math

import numpy as np

SUPPORT_DOF = {"pin": (True, True), "roller": (False, True), "roller_x": (True, False)}
TOL = 1e-9


class EditError(ValueError):
    pass


def section_area(problem, name):
    sections = (problem or {}).get("sections", {})
    if name not in sections:
        raise ValueError(f"unknown section {name!r}; choose from {sorted(sections)}")
    return sections[name]


def validate_design(design, problem=None):
    nodes = design.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise ValueError("design needs a non-empty 'nodes' mapping")
    for n, xy in nodes.items():
        if not (isinstance(xy, (list, tuple)) and len(xy) == 2 and all(isinstance(v, (int, float)) for v in xy)):
            raise ValueError(f"node {n}: coordinates must be [x, y]")
    ids = set()
    for m in design.get("members", []):
        if m.get("id") in ids:
            raise ValueError(f"duplicate member id {m.get('id')}")
        ids.add(m.get("id"))
        if m.get("a") not in nodes or m.get("b") not in nodes or m["a"] == m["b"]:
            raise ValueError(f"member {m.get('id')}: needs two different existing nodes")
        if problem is not None:
            section_area(problem, m.get("section"))
        if _length(nodes, m) < TOL:
            raise ValueError(f"member {m['id']}: zero length")
    for n, kind in design.get("supports", {}).items():
        if n not in nodes or kind not in SUPPORT_DOF:
            raise ValueError(f"support at {n}: node must exist and type be one of {sorted(SUPPORT_DOF)}")
    for ld in design.get("loads", []):
        if ld.get("node") not in nodes:
            raise ValueError(f"load at unknown node {ld.get('node')}")


def _length(nodes, m):
    (x1, y1), (x2, y2) = nodes[m["a"]], nodes[m["b"]]
    return math.hypot(x2 - x1, y2 - y1)


def cost(design, problem):
    unit = problem["material"]["cost_per_m3"]
    return sum(_length(design["nodes"], m) * section_area(problem, m["section"]) * unit
               for m in design["members"])


def solve(design, problem):
    """Return (member_forces, displacements) or raise np.linalg.LinAlgError for a mechanism.

    member_forces: {id: axial force N, tension positive}; displacements: {node: (dx, dy)}.
    """
    E = problem["material"]["E"]
    names = list(design["nodes"])
    idx = {n: i for i, n in enumerate(names)}
    K = np.zeros((2 * len(names), 2 * len(names)))
    geom = {}
    for m in design["members"]:
        (x1, y1), (x2, y2) = design["nodes"][m["a"]], design["nodes"][m["b"]]
        L = math.hypot(x2 - x1, y2 - y1)
        c, s = (x2 - x1) / L, (y2 - y1) / L
        k = E * section_area(problem, m["section"]) / L
        v = np.array([-c, -s, c, s])
        dofs = [2 * idx[m["a"]], 2 * idx[m["a"]] + 1, 2 * idx[m["b"]], 2 * idx[m["b"]] + 1]
        K[np.ix_(dofs, dofs)] += k * np.outer(v, v)
        geom[m["id"]] = (dofs, v, k)
    F = np.zeros(2 * len(names))
    for ld in design.get("loads", []):
        F[2 * idx[ld["node"]]] += ld.get("fx", 0.0)
        F[2 * idx[ld["node"]] + 1] += ld.get("fy", 0.0)
    fixed = set()
    for n, kind in design.get("supports", {}).items():
        fx, fy = SUPPORT_DOF[kind]
        if fx:
            fixed.add(2 * idx[n])
        if fy:
            fixed.add(2 * idx[n] + 1)
    free = [d for d in range(2 * len(names)) if d not in fixed]
    Kff = K[np.ix_(free, free)]
    loose = mechanism_nodes(Kff, free, names)
    if loose:
        raise np.linalg.LinAlgError(",".join(loose))
    u = np.zeros(2 * len(names))
    u[free] = np.linalg.solve(Kff, F[free])
    forces = {mid: float(k * v @ u[dofs]) for mid, (dofs, v, k) in geom.items()}
    disp = {n: (float(u[2 * i]), float(u[2 * i + 1])) for n, i in idx.items()}
    return forces, disp


def mechanism_nodes(Kff, free, names):
    """Nodes that can move without stretching any member (zero-stiffness modes)."""
    if Kff.size == 0:
        return []
    w, vecs = np.linalg.eigh(Kff)
    scale = max(abs(w).max(), 1.0)
    zero = vecs[:, w < scale * 1e-10]
    if zero.shape[1] == 0:
        return []
    motion = np.sqrt((zero ** 2).sum(axis=1))
    loose = {names[free[i] // 2] for i in np.nonzero(motion > 1e-6)[0]}
    return sorted(loose)


def run(design, problem):
    """Check a design. Returns {"ok", "failures", "members", "displacements", "cost", "budget"}."""
    validate_design(design, problem)
    mat = problem["material"]
    failures, members, disp = [], {}, {}
    try:
        forces, disp = solve(design, problem)
    except np.linalg.LinAlgError as e:
        failures.append({"check": "mechanism", "nodes": str(e).split(",") if str(e) else [],
                         "detail": "structure can move without any member stretching (unstable)"})
        forces = {}
    for m in design["members"]:
        if m["id"] not in forces:
            continue
        A = section_area(problem, m["section"])
        L = _length(design["nodes"], m)
        N = forces[m["id"]]
        stress = N / A
        info = {"force": N, "stress": stress, "length": L, "section": m["section"],
                "yield_ratio": abs(stress) / mat["yield"]}
        if info["yield_ratio"] > 1 + TOL:
            failures.append({"check": "yield", "member": m["id"], "ratio": info["yield_ratio"],
                             "mode": "tension" if N > 0 else "compression", "force": N})
        if N < 0:
            I = A * A / (4 * math.pi)
            p_cr = math.pi ** 2 * mat["E"] * I / L ** 2
            info["buckling_ratio"] = -N / p_cr
            if info["buckling_ratio"] > 1 + TOL:
                failures.append({"check": "buckling", "member": m["id"], "ratio": info["buckling_ratio"],
                                 "force": N, "length": L})
        members[m["id"]] = info
    limit = problem.get("max_deflection")
    if limit and disp:
        node, (dx, dy) = max(disp.items(), key=lambda kv: math.hypot(*kv[1]))
        r = math.hypot(dx, dy) / limit
        if r > 1 + TOL:
            failures.append({"check": "deflection", "node": node, "ratio": r})
    total = cost(design, problem)
    budget = problem.get("budget")
    if budget and total > budget * (1 + TOL):
        failures.append({"check": "cost", "ratio": total / budget, "cost": total, "budget": budget})
    failures.sort(key=lambda f: (f["check"] != "mechanism", -f.get("ratio", 0)))
    return {"ok": not failures, "failures": failures, "members": members,
            "displacements": disp, "cost": total, "budget": budget}


# ── structured edits (what the LLM produces from the user's plain-words idea) ──

EDIT_OPS = {
    "add_node": ("id", "x", "y"), "move_node": ("id", "x", "y"), "remove_node": ("id",),
    "add_member": ("id", "a", "b", "section"), "remove_member": ("id",), "resize_member": ("id", "section"),
}


def apply_edit(design, edit, problem):
    """Apply {"ops": [...]} and return a new design. Supports and loads are fixed by the problem."""
    ops = edit.get("ops") if isinstance(edit, dict) else None
    if not isinstance(ops, list) or not ops:
        raise EditError("edit must be {\"ops\": [ ... ]} with at least one op")
    d = copy.deepcopy(design)
    fixed = set(problem.get("fixed_nodes", [])) | set(d.get("supports", {})) | {ld["node"] for ld in d.get("loads", [])}
    reg = problem.get("region")
    members = {m["id"]: m for m in d["members"]}
    for op in ops:
        kind = op.get("op")
        if kind not in EDIT_OPS:
            raise EditError(f"unknown op {kind!r}; allowed: {sorted(EDIT_OPS)}")
        missing = [k for k in EDIT_OPS[kind] if k not in op]
        if missing:
            raise EditError(f"{kind} needs {missing}")
        oid = str(op["id"])
        if kind in ("add_node", "move_node"):
            x, y = float(op["x"]), float(op["y"])
            if reg and not (reg["xmin"] - TOL <= x <= reg["xmax"] + TOL and reg["ymin"] - TOL <= y <= reg["ymax"] + TOL):
                raise EditError(f"node {oid} at ({x}, {y}) is outside the allowed region {reg}")
            if kind == "add_node" and oid in d["nodes"]:
                raise EditError(f"node {oid} already exists")
            if kind == "move_node" and oid not in d["nodes"]:
                raise EditError(f"node {oid} does not exist")
            if kind == "move_node" and oid in fixed:
                raise EditError(f"node {oid} is a support or load point and can't move")
            d["nodes"][oid] = [x, y]
        elif kind == "remove_node":
            if oid not in d["nodes"]:
                raise EditError(f"node {oid} does not exist")
            if oid in fixed:
                raise EditError(f"node {oid} is a support or load point and can't be removed")
            attached = [m["id"] for m in members.values() if oid in (m["a"], m["b"])]
            if attached:
                raise EditError(f"node {oid} still has members {attached}; remove them explicitly first")
            del d["nodes"][oid]
        elif kind == "add_member":
            if oid in members:
                raise EditError(f"member {oid} already exists")
            members[oid] = {"id": oid, "a": str(op["a"]), "b": str(op["b"]), "section": op["section"]}
        elif kind == "remove_member":
            if members.pop(oid, None) is None:
                raise EditError(f"member {oid} does not exist")
        elif kind == "resize_member":
            if oid not in members:
                raise EditError(f"member {oid} does not exist")
            members[oid] = {**members[oid], "section": op["section"]}
    d["members"] = list(members.values())
    try:
        validate_design(d, problem)
    except ValueError as e:
        raise EditError(str(e)) from e
    return d


def touched(edit):
    """Node and member ids an edit touches (used to check it against the plain-words restatement)."""
    out = set()
    for op in edit.get("ops", []):
        out.add(str(op.get("id")))
        if op.get("op") == "add_member":
            out.update({str(op.get("a")), str(op.get("b"))})
    return out


# ── terminal sketch ──────────────────────────────────────────────────────────

def sketch(design, failures=(), width=64, height=14):
    nodes = design["nodes"]
    xs, ys = [p[0] for p in nodes.values()], [p[1] for p in nodes.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sx = (width - 3) / ((x1 - x0) or 1)
    sy = (height - 3) / ((y1 - y0) or 1)
    s = min(sx, sy * 2.2)                      # terminal cells are ~2.2x taller than wide
    pos = {n: (1 + round((x - x0) * s), height - 3 - round((y - y0) * s / 2.2)) for n, (x, y) in nodes.items()}
    grid = [[" "] * (width + 2) for _ in range(height)]
    bad = {f.get("member") for f in failures}
    for m in design["members"]:
        (c1, r1), (c2, r2) = pos[m["a"]], pos[m["b"]]
        steps = max(abs(c2 - c1), abs(r2 - r1), 1)
        ch = "#" if m["id"] in bad else "."
        for t in range(steps + 1):
            c, r = round(c1 + (c2 - c1) * t / steps), round(r1 + (r2 - r1) * t / steps)
            grid[r][c] = ch
    for n, (c, r) in pos.items():
        grid[r][c] = n[0]
        kind = design.get("supports", {}).get(n)
        if kind and r + 1 < height:
            grid[r + 1][c] = "^" if kind == "pin" else "o"
    for ld in design.get("loads", []):
        c, r = pos[ld["node"]]
        if r - 1 >= 0 and ld.get("fy", 0) < 0:
            grid[r - 1][c] = "v"
    lines = ["".join(row).rstrip() for row in grid]
    return "\n".join(l for l in lines if l.strip()) + "\n  (# = failing member, ^ pin, o roller, v load)"
