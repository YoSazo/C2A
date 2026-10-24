"""Live loop with a scripted fake LLM: translation rules, confirmation, baseline, logging."""

import builtins
import json

import pytest

from c2a import llm, store
from c2a.live import loop, truss


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("C2A_DATA_DIR", str(tmp_path))
    return tmp_path


def feed(monkeypatch, lines):
    it = iter(lines)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(llm.LLMError, match="OPENAI_API_KEY"):
        llm.require()


def test_reference_solution_is_never_shown_to_the_llm():
    prob = loop.load_problem("bridge_01")
    assert "reference_solution" not in json.dumps(loop.public(prob, prob["design"]))


def test_human_loop_solves_bridge_01_with_confirmed_translation(tmp_data, monkeypatch):
    prob = loop.load_problem("bridge_01")
    replies = iter([
        # first idea: the LLM sneaks in an extra resize -> rejected by the mention check, then fixed
        {"restatement": "Make bar m3 (A to D) size L.",
         "edit": {"ops": [{"op": "resize_member", "id": "m3", "section": "L"},
                          {"op": "resize_member", "id": "m4", "section": "L"}]}},
        {"restatement": "Make bars m3 (A to D) and m4 (D to C) size L.",
         "edit": {"ops": [{"op": "resize_member", "id": "m3", "section": "L"},
                          {"op": "resize_member", "id": "m4", "section": "L"}]}},
    ])
    monkeypatch.setattr(llm, "chat", lambda *a, **k: "plain words")
    monkeypatch.setattr(llm, "chat_json", lambda *a, **k: next(replies))
    monkeypatch.setattr(llm, "model", lambda: "fake")
    feed(monkeypatch, ["make both slanted bars thicker, size L", "y"])
    rec = loop.run_human(prob, max_loops=5)
    assert rec["solved"] and rec["loops"] == 1
    logs = list((tmp_data / "live_logs").glob("*_bridge_01_human.json"))
    assert len(logs) == 1 and json.loads(logs[0].read_text(encoding="utf-8"))["solved"]


def test_user_can_reject_a_translation(tmp_data, monkeypatch):
    prob = loop.load_problem("bridge_01")
    good = {"restatement": "Make bars m3 and m4 size L.",
            "edit": {"ops": [{"op": "resize_member", "id": "m3", "section": "L"},
                             {"op": "resize_member", "id": "m4", "section": "L"}]}}
    monkeypatch.setattr(llm, "chat", lambda *a, **k: "plain words")
    monkeypatch.setattr(llm, "chat_json", lambda *a, **k: good)
    monkeypatch.setattr(llm, "model", lambda: "fake")
    feed(monkeypatch, ["thicker slanted bars", "n", "thicker slanted bars, both of them", "y"])
    rec = loop.run_human(prob, max_loops=5)
    assert rec["solved"] and len(rec["rejections"]) == 1 and rec["rejections"][0]["by"] == "user"


def test_clarifying_question_is_relayed(tmp_data, monkeypatch):
    prob = loop.load_problem("bridge_02")
    replies = iter([{"clarify": "How thick should the new bar be?"},
                    {"restatement": "Add a thin bar m9 from B to F, size XS.",
                     "edit": {"ops": [{"op": "add_member", "id": "m9", "a": "B", "b": "F", "section": "XS"}]}}])
    monkeypatch.setattr(llm, "chat", lambda *a, **k: "plain words")
    monkeypatch.setattr(llm, "chat_json", lambda *a, **k: next(replies))
    monkeypatch.setattr(llm, "model", lambda: "fake")
    feed(monkeypatch, ["add a bar across the middle box from B to F", "the thinnest", "y"])
    rec = loop.run_human(prob, max_loops=5)
    assert rec["solved"] and rec["clarifications"][0]["answer"] == "the thinnest"


def test_baseline_counts_invalid_edits_as_loops(tmp_data, monkeypatch):
    prob = loop.load_problem("bridge_01")
    replies = iter([{"edit": {"ops": [{"op": "move_node", "id": "B", "x": 3, "y": 1}]}},   # B is a load point
                    {"edit": prob["reference_solution"]}])
    monkeypatch.setattr(llm, "chat_json", lambda *a, **k: next(replies))
    monkeypatch.setattr(llm, "model", lambda: "fake")
    rec = loop.run_baseline(prob, max_loops=5)
    assert rec["solved"] and rec["loops"] == 2 and rec["invalid"] == 1
    assert store.load("live_logs/" + next((tmp_data / "live_logs").glob("*baseline.json")).name)["kind"] == "baseline"


def test_manual_mode_needs_no_llm(tmp_data, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    prob = loop.load_problem("bridge_02")
    feed(monkeypatch, ["not json", json.dumps(prob["reference_solution"])])
    rec = loop.run_human(prob, max_loops=3, manual=True)
    assert rec["solved"] and rec["kind"] == "manual"
    assert truss.run(rec["final_design"], prob)["ok"]
