#!/usr/bin/env python3
"""Smoke tests for core C2A Elegant components."""

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUNTIME = ROOT / "c2a_runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def run_test(index, total, name, fn, required=True):
    print(f"\n[{index}/{total}] {name}...")
    try:
        fn()
        print(f"  {PASS} {name}")
        return True
    except Exception as exc:
        marker = FAIL if required else WARN
        print(f"  {marker} {name}: {exc}")
        traceback.print_exc()
        return False


def test_dependencies():
    import chromadb  # noqa: F401
    import requests  # noqa: F401
    from sentence_transformers import SentenceTransformer  # noqa: F401


def test_archetypes():
    from constraint_archetypes import ARCHETYPES, get_archetype

    expected = {"scarcity", "velocity", "asymmetry", "friction", "paradox"}
    assert set(ARCHETYPES.keys()) == expected, "Unexpected archetype set"
    scarcity = get_archetype("scarcity")
    assert scarcity is not None, "Could not load scarcity archetype"
    assert isinstance(scarcity.symbol, str) and scarcity.symbol, "Archetype symbol must be non-empty"


def test_scheduler_rules():
    from scaffolding_scheduler import scheduler

    level_15 = scheduler.get_feature_state(15)
    level_16 = scheduler.get_feature_state(16)
    level_41 = scheduler.get_feature_state(41)

    assert not level_15.speed_track_active, "Speed Track should be inactive before level 16"
    assert level_16.speed_track_active, "Speed Track should activate at level 16"
    assert level_16.real_world_log_available, "Real-world log should be available at level 16"
    assert not level_41.real_world_log_mandatory, "Real-world log should stay optional"
    level_70 = scheduler.get_feature_state(70)
    assert level_70.historical_arena_available, "Historical Arena should unlock at level 70"
    level_100 = scheduler.get_feature_state(100)
    assert level_100.historical_beat_history, "Beat-history should unlock at level 100"


def test_progression_logic():
    """Progression must be exercised against the real scheduler, not a stub."""
    from progression import calculate_level, session_value
    from scaffolding_scheduler import scheduler

    no_data = {"total_reps": 0, "pct_under_8s": 0.0, "pct_under_15s": 0.0, "pct_under_30s": 0.0}

    assert calculate_level(0, 0.0, scheduler, no_data) == 1, "Floor must be level 1"

    # Quality, not attendance: the same session count must land far apart.
    coping = calculate_level(30, 48.0, scheduler, no_data)
    strong = calculate_level(30, 85.0, scheduler, no_data)
    assert strong > coping * 3, (
        f"Score must dominate level: 30 sessions at avg 85 gave {strong}, at avg 48 gave {coping}"
    )
    assert session_value(40.0) < session_value(70.0) < session_value(95.0)


def test_speed_gate_is_escapable():
    """
    Regression: Speed Track must be reachable.

    The gate used to read a populated dict of zeros as "0%, failed" rather than
    "no data", capping every user at 15 — one level below where Speed Track
    unlocks. The drill was the only way to produce speed data, so the drill
    could never run.
    """
    from progression import calculate_level
    from scaffolding_scheduler import scheduler

    no_data = {"total_reps": 0, "pct_under_8s": 0.0, "pct_under_15s": 0.0, "pct_under_30s": 0.0}

    reached = [calculate_level(n, 80.0, scheduler, no_data) for n in range(1, 40)]
    assert max(reached) >= 16, f"Never reached Speed Track; peaked at {max(reached)}"

    # Every level a gate can hold you at must still offer the drill, or the
    # only remedy for the gate is unreachable from the gate.
    for stats in (
        no_data,
        {"total_reps": 40, "pct_under_8s": 0.0, "pct_under_15s": 0.0, "pct_under_30s": 0.1},
        {"total_reps": 40, "pct_under_8s": 0.0, "pct_under_15s": 0.1, "pct_under_30s": 0.9},
    ):
        for n in (10, 30, 80, 300):
            level = calculate_level(n, 85.0, scheduler, stats)
            gate = scheduler.check_speed_gate(level, stats)
            if not gate.passed:
                held = scheduler.get_feature_state(gate.blocked_at)
                assert held.speed_track_reps > 0, (
                    f"Held at level {gate.blocked_at} with no Speed Track reps available"
                )


def test_speed_gates_are_ordered():
    """A low gate must not be skipped by having a high raw level."""
    from scaffolding_scheduler import scheduler

    slow = {"total_reps": 100, "pct_under_8s": 0.0, "pct_under_15s": 0.0, "pct_under_30s": 0.0}
    # Failing the level-15 standard must not grant level-40 or level-70 privileges.
    for raw in (20, 45, 90, 400):
        assert scheduler.apply_speed_gate(raw, slow) <= 16, (
            f"raw level {raw} escaped the first speed gate"
        )


def test_judge_rubric_is_coherent():
    """
    Regression: the judge prompt must teach the move at every level, and must
    not carry a band table that inverts.
    """
    from llm_transmutation_judge import TransmutationJudge

    judge = TransmutationJudge.__new__(TransmutationJudge)
    scenario = {"title": "T", "situation": "S", "archetype": "friction"}

    for level in (1, 5, 30, 60, 90, 150):
        prompt = TransmutationJudge._build_evaluation_prompt(
            judge, "narrowed the scope", scenario, {}, level, ""
        )
        assert "THE REMOVAL TEST" in prompt, f"Level {level} prompt lost the removal test"
        assert "COPING" in prompt, f"Level {level} prompt lost the coping distinction"
        assert "SCORING CALIBRATION FOR LEVEL" not in prompt, (
            f"Level {level} still carries the level-scaled band table"
        )


def test_drill_pool_and_selection():
    """The pool must outlast a session, and selection must favour weak spots."""
    from collections import Counter
    from speed_track import CONSTRAINT_POOL, select_drill_constraints

    assert len(CONSTRAINT_POOL) > 50, (
        f"Pool of {len(CONSTRAINT_POOL)} is not larger than a 50-rep session"
    )

    picked = select_drill_constraints(20, {})
    assert len(picked) == 20
    assert len({t for t, _ in picked}) == 20, "A single drill repeated an item"

    stats = {"archetype_accuracy": {"paradox": 0.2, "friction": 0.95,
                                    "scarcity": 0.95, "velocity": 0.95, "asymmetry": 0.95}}
    counts = Counter()
    for _ in range(150):
        for _, arch in select_drill_constraints(20, stats):
            counts[arch] += 1
    assert counts["paradox"] > counts["friction"], (
        f"Weak archetype not favoured: {counts}"
    )

    personal = [("A constraint I actually met", "velocity")]
    got = select_drill_constraints(9, stats, extra_pool=personal)
    assert any(t == personal[0][0] for t, _ in got), "Logged constraints never reach the drill"


def test_scenario_engine_init():
    """Structural only — must not need a live key to pass."""
    from llm_client import DEFAULT_MODEL, LLMClient
    from llm_scenario_engine import LLMScenarioEngine

    client = LLMClient(api_key="test-key-not-used")
    engine = LLMScenarioEngine(model=DEFAULT_MODEL, llm_client=client)
    assert hasattr(engine, "generate_scenario"), "Engine missing generate_scenario"
    assert engine.llm.model == DEFAULT_MODEL


def test_judge_score_shape():
    from llm_transmutation_judge import TransmutationScore

    score = TransmutationScore(
        overall_score=85,
        reframing_score=27,
        novelty_score=22,
        practicality_score=21,
        sophistication_score=15,
        what_worked="Good reframing",
        what_missed="Could be more novel",
        growth_edge="Practice meta-cognition",
        pattern_identified="Constraint as design parameter",
        vs_user_history="Better than average",
        breakthrough_moment=False,
        lesson_applied=False,
    )
    assert score.overall_score <= 100


def test_ui_init():
    from elegant_ui import ElegantUI

    ui = ElegantUI()
    assert ui.get_terminal_width() > 0
    assert ui.get_terminal_height() > 0


def test_rlm_imports():
    from rlm_engine import RLMEngine, SafeREPL, RLMConstraintAnalyzer  # noqa: F401


def test_memory_system():
    from c2a_elegant_main import MemorySystem

    memory = MemorySystem(collection_name="c2a_test")
    try:
        stats = memory.get_user_stats()
        for key in ("total_sessions", "current_level", "average_score"):
            assert key in stats, f"Missing key in stats: {key}"
    finally:
        try:
            memory.client.delete_collection("c2a_test")
        except Exception:
            pass


def test_openai_config_optional():
    """Optional: a usable OpenAI key is configured."""
    from llm_client import LLMClient

    client = LLMClient()
    models = client.list_models()
    assert models, "No models returned"


def main():
    tests = [
        ("Dependencies", test_dependencies, True),
        ("Constraint archetypes", test_archetypes, True),
        ("Scheduler rules", test_scheduler_rules, True),
        ("Progression logic", test_progression_logic, True),
        ("Speed gate is escapable", test_speed_gate_is_escapable, True),
        ("Speed gates are ordered", test_speed_gates_are_ordered, True),
        ("Judge rubric coherent", test_judge_rubric_is_coherent, True),
        ("Drill pool and selection", test_drill_pool_and_selection, True),
        ("Scenario engine init", test_scenario_engine_init, True),
        ("Judge score structure", test_judge_score_shape, True),
        ("UI init", test_ui_init, True),
        ("RLM imports", test_rlm_imports, True),
        ("Memory system", test_memory_system, True),
        ("OpenAI config (optional)", test_openai_config_optional, False),
    ]

    print("=" * 60)
    print("C2A ELEGANT - SMOKE TEST")
    print("=" * 60)

    required_failures = 0
    optional_failures = 0

    total = len(tests)
    for idx, (name, fn, required) in enumerate(tests, start=1):
        ok = run_test(idx, total, name, fn, required=required)
        if not ok:
            if required:
                required_failures += 1
            else:
                optional_failures += 1

    print("\n" + "=" * 60)
    print("SMOKE TEST COMPLETE")
    print("=" * 60)
    print(f"Required failures: {required_failures}")
    print(f"Optional failures: {optional_failures}")

    if required_failures:
        print("\nOne or more required checks failed.")
        sys.exit(1)

    print("\nSystem is ready.")
    print("Run: python C2A.py")


if __name__ == "__main__":
    main()

