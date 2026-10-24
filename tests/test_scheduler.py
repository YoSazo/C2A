"""Leitner scheduling, item rotation and the mastery rule."""

import random

from c2a import drill

H = 3600
DAY = 86400


def answers(pattern, n, correct=True, rt=1200, item="d-1"):
    return [{"pattern": pattern, "item": item, "correct": correct, "rt_ms": rt, "load": False}] * n


def test_correct_answers_climb_boxes_and_push_due_date_out():
    s = drill.update(None, "d-1", True, 0)
    assert s["box"] == 2 and s["due"] == 1 * DAY
    s = drill.update(s, "d-2", True, s["due"])
    assert s["box"] == 3 and s["due"] == 1 * DAY + 3 * DAY
    for _ in range(10):
        s = drill.update(s, "d-3", True, s["due"])
    assert s["box"] == 5


def test_miss_resets_to_box_one_and_is_due_now():
    s = drill.update(None, "d-1", True, 0)
    s = drill.update(s, "d-1", True, 2 * DAY)
    s = drill.update(s, "d-2", False, 3 * DAY)
    assert s["box"] == 1 and s["due"] == 3 * DAY


def test_spaced_hits_need_a_gap():
    s = drill.update(None, "d-1", True, 0)
    s = drill.update(s, "d-2", True, 1 * H)            # same sitting: not a new spaced review
    assert len(s["spaced_hits"]) == 1
    s = drill.update(s, "d-3", True, drill.SPACING_HOURS * H)
    assert len(s["spaced_hits"]) == 2


def test_plan_puts_due_patterns_first_and_never_repeats_back_to_back():
    states = {"a": {"box": 1, "due": 0}, "b": {"box": 4, "due": 10 * DAY}}
    pids = ["a", "b", "c", "d"]
    q = drill.plan(pids, states, 12, t=DAY, rng=random.Random(1))
    assert len(q) == 12 and "a" in q
    assert all(q[i] != q[i + 1] for i in range(len(q) - 1))
    # only due + new patterns fill a session before not-yet-due ones
    assert set(drill.plan(pids, states, 3, t=DAY, rng=random.Random(2))) == {"a", "c", "d"}


def test_pick_item_rotates_surface_stories():
    items = [{"id": f"d-{i}"} for i in range(3)]
    state = {"last_item": "d-0", "seen_items": {"d-0": 1, "d-1": 2}}
    assert drill.pick_item(items, state, rng=random.Random(0))["id"] == "d-2"   # least shown, not the last one
    state = {"last_item": "d-2", "seen_items": {"d-0": 3, "d-1": 3, "d-2": 1}}
    assert drill.pick_item(items, state, rng=random.Random(0))["id"] != "d-2"


def test_mastery_needs_reviews_stories_and_speed():
    s = None
    for k, t in enumerate([0, 1 * DAY, 4 * DAY]):
        s = drill.update(s, f"d-{k}", True, t)
    att = [a for k in range(3) for a in answers("p", 1, item=f"d-{k}")]
    assert drill.is_mastered(s, att)
    # same story every time -> not mastered
    assert not drill.is_mastered(s, answers("p", 3, item="d-0"))
    # too slow -> not mastered
    slow = [{**a, "rt_ms": 5000} for a in att]
    assert not drill.is_mastered(s, slow)
    # not enough spaced reviews -> not mastered
    assert not drill.is_mastered(drill.update(None, "d-0", True, 0), att)


def test_load_answers_do_not_count_toward_mastery():
    s = None
    for k, t in enumerate([0, 1 * DAY, 4 * DAY]):
        s = drill.update(s, f"d-{k}", True, t)
    att = [{"pattern": "p", "item": f"d-{k}", "correct": True, "rt_ms": 900, "load": True} for k in range(3)]
    assert not drill.is_mastered(s, att)
