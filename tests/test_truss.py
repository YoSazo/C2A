"""Truss verifier against hand-checked textbook solutions."""

import json
import math
from pathlib import Path

import pytest

from c2a.live import truss

STEEL = {"E": 200e9, "yield": 250e6, "cost_per_m3": 1000.0}
PROBLEM = {"material": STEEL, "sections": {"S": 5e-4, "M": 1e-3, "L": 4e-3}}
P = 10_000.0
PROBLEMS = Path(__file__).resolve().parent.parent / "c2a" / "live" / "problems"


def member(mid, a, b, section="M"):
    return {"id": mid, "a": a, "b": b, "section": section}


def test_triangle_member_forces():
    # Span 4 m, apex 2 m up, P down at the apex. Reactions P/2 each.
    # Joint A: F_AC sin45 = -P/2 -> F_AC = -P/sqrt2 (compression); F_AB = +P/2 (tension).
    d = {"nodes": {"A": [0, 0], "B": [4, 0], "C": [2, 2]},
         "members": [member("AB", "A", "B"), member("AC", "A", "C"), member("BC", "B", "C")],
         "supports": {"A": "pin", "B": "roller"}, "loads": [{"node": "C", "fy": -P}]}
    f, _ = truss.solve(d, PROBLEM)
    assert f["AC"] == pytest.approx(-P / math.sqrt(2), rel=1e-9)
    assert f["BC"] == pytest.approx(-P / math.sqrt(2), rel=1e-9)
    assert f["AB"] == pytest.approx(P / 2, rel=1e-9)


def warren():
    # Two equilateral panels (side 2 m), P at the middle bottom node B.
    h = math.sqrt(3)
    return {"nodes": {"A": [0, 0], "B": [2, 0], "C": [4, 0], "D": [1, h], "E": [3, h]},
            "members": [member("AB", "A", "B"), member("BC", "B", "C"), member("DE", "D", "E"),
                        member("AD", "A", "D"), member("BD", "B", "D"), member("BE", "B", "E"),
                        member("CE", "C", "E")],
            "supports": {"A": "pin", "C": "roller"}, "loads": [{"node": "B", "fy": -P}]}


def test_warren_member_forces():
    # Method of joints: AD = CE = DE = -P/sqrt3; BD = BE = +P/sqrt3; AB = BC = +P/(2 sqrt3).
    f, _ = truss.solve(warren(), PROBLEM)
    s3 = math.sqrt(3)
    expected = {"AD": -P / s3, "CE": -P / s3, "DE": -P / s3, "BD": P / s3, "BE": P / s3,
                "AB": P / (2 * s3), "BC": P / (2 * s3)}
    for mid, val in expected.items():
        assert f[mid] == pytest.approx(val, rel=1e-9), mid


def test_axial_bar_deflection_matches_PL_over_EA():
    d = {"nodes": {"A": [0, 0], "B": [3, 0]}, "members": [member("AB", "A", "B")],
         "supports": {"A": "pin", "B": "roller"}, "loads": [{"node": "B", "fx": P}]}
    _, u = truss.solve(d, PROBLEM)
    assert u["B"][0] == pytest.approx(P * 3 / (200e9 * 1e-3), rel=1e-9)


def test_square_without_diagonal_is_a_mechanism():
    d = {"nodes": {"A": [0, 0], "B": [2, 0], "C": [2, 2], "D": [0, 2]},
         "members": [member("AB", "A", "B"), member("BC", "B", "C"), member("CD", "C", "D"), member("DA", "D", "A")],
         "supports": {"A": "pin", "B": "roller"}, "loads": [{"node": "C", "fx": P}]}
    r = truss.run(d, PROBLEM)
    assert not r["ok"]
    mech = [f for f in r["failures"] if f["check"] == "mechanism"]
    assert mech and set(mech[0]["nodes"]) >= {"C", "D"}
    # adding the diagonal makes it stable
    d["members"].append(member("AC", "A", "C"))
    assert not any(f["check"] == "mechanism" for f in truss.run(d, PROBLEM)["failures"])


def test_unconnected_node_is_a_mechanism():
    d = warren()
    d["nodes"]["F"] = [5, 1]
    r = truss.run(d, PROBLEM)
    assert r["failures"][0]["check"] == "mechanism" and "F" in r["failures"][0]["nodes"]


def test_yield_buckling_and_cost_checks():
    prob = {**PROBLEM, "budget": 1.0}
    big = warren()
    big["loads"] = [{"node": "B", "fy": -600_000.0}]
    r = truss.run(big, prob)
    checks = {(f["check"], f.get("member")) for f in r["failures"]}
    # BD: +600k/sqrt3 = 346 kN over 1e-3 m² = 346 MPa > 250 MPa -> tension yield
    assert ("yield", "BD") in checks
    # AD: 346 kN compression; P_cr = pi² E (A²/4pi) / L² = pi*200e9*1e-6/(4*4) = 39.3 kN -> buckles
    ad = r["members"]["AD"]
    assert ad["buckling_ratio"] == pytest.approx((600_000 / math.sqrt(3)) / (math.pi * 200e9 * 1e-6 / 16), rel=1e-9)
    assert ("buckling", "AD") in checks
    # cost = total length 14 m * 1e-3 m² * 1000/m³ = 14 > budget 1
    assert r["cost"] == pytest.approx(14.0, rel=1e-9)
    assert ("cost", None) in checks


def test_light_load_passes():
    r = truss.run(warren(), {**PROBLEM, "budget": 100.0})
    assert r["ok"], r["failures"]


def test_apply_edit_rules():
    prob = {**PROBLEM, "region": {"xmin": 0, "xmax": 4, "ymin": 0, "ymax": 3}}
    d = warren()
    new = truss.apply_edit(d, {"ops": [{"op": "resize_member", "id": "AD", "section": "L"}]}, prob)
    assert {m["id"]: m["section"] for m in new["members"]}["AD"] == "L"
    assert {m["id"]: m["section"] for m in d["members"]}["AD"] == "M"   # original untouched
    bad = [
        {"ops": [{"op": "move_node", "id": "B", "x": 2, "y": 1}]},          # load point is fixed
        {"ops": [{"op": "add_node", "id": "F", "x": 9, "y": 1}]},           # outside region
        {"ops": [{"op": "remove_node", "id": "D"}]},                        # still has members
        {"ops": [{"op": "resize_member", "id": "AD", "section": "XXL"}]},   # unknown section
        {"ops": [{"op": "add_member", "id": "AB", "a": "A", "b": "C", "section": "S"}]},  # duplicate id
        {"ops": []},
    ]
    for e in bad:
        with pytest.raises(truss.EditError):
            truss.apply_edit(d, e, prob)
    assert truss.touched({"ops": [{"op": "add_member", "id": "m9", "a": "A", "b": "E", "section": "S"}]}) == {"m9", "A", "E"}


@pytest.mark.parametrize("path", sorted(PROBLEMS.glob("*.json")), ids=lambda p: p.stem)
def test_shipped_problems_start_broken_and_are_solvable(path):
    prob = json.loads(path.read_text(encoding="utf-8"))
    assert not truss.run(prob["design"], prob)["ok"], "a starting design should have failures to work on"
    ref = prob.get("reference_solution")
    assert ref, "each problem ships a reference edit proving it can be solved"
    solved = truss.apply_edit(prob["design"], ref, prob)
    r = truss.run(solved, prob)
    assert r["ok"], r["failures"]
