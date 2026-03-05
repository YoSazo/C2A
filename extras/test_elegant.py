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
    from sentence_transformers import SentenceTransformer  # noqa: F401
    import ollama  # noqa: F401


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
    assert level_41.real_world_log_mandatory, "Real-world log should be mandatory at level 41"


def test_progression_logic():
    from progression import calculate_level

    class DummyScheduler:
        @staticmethod
        def apply_speed_gate(level, speed_stats):
            return level

    level = calculate_level(total_sessions=20, avg_score=80.0, scheduler=DummyScheduler(), speed_stats={})
    assert level == 18, f"Expected level 18, got {level}"

    clamped_low = calculate_level(total_sessions=0, avg_score=0.0, scheduler=DummyScheduler(), speed_stats={})
    assert clamped_low == 1, f"Expected minimum level 1, got {clamped_low}"

    clamped_high = calculate_level(total_sessions=1000, avg_score=100.0, scheduler=DummyScheduler(), speed_stats={})
    assert clamped_high == 100, f"Expected maximum level 100, got {clamped_high}"


def test_scenario_engine_init():
    from llm_scenario_engine import LLMScenarioEngine

    engine = LLMScenarioEngine(model="qwen2.5:14b")
    assert hasattr(engine, "generate_scenario"), "Engine missing generate_scenario"


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


def test_ollama_connection_optional():
    import ollama

    response = ollama.chat(
        model="qwen2.5:14b",
        messages=[{"role": "user", "content": "Say ready."}],
    )
    assert "message" in response, "Unexpected Ollama response shape"


def main():
    tests = [
        ("Dependencies", test_dependencies, True),
        ("Constraint archetypes", test_archetypes, True),
        ("Scheduler rules", test_scheduler_rules, True),
        ("Progression logic", test_progression_logic, True),
        ("Scenario engine init", test_scenario_engine_init, True),
        ("Judge score structure", test_judge_score_shape, True),
        ("UI init", test_ui_init, True),
        ("RLM imports", test_rlm_imports, True),
        ("Memory system", test_memory_system, True),
        ("Ollama connection (optional)", test_ollama_connection_optional, False),
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
    print("Run: python c2a_runtime/c2a_elegant_main.py")


if __name__ == "__main__":
    main()

