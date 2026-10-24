"""Progression and leveling helpers for C2A."""

from typing import Any, Mapping


MIN_LEVEL = 1
# No hard cap — levels climb with sustained practice.
MAX_LEVEL = None

# ─── Mastery weighting ────────────────────────────────────────────────────────
# Level used to be 0.5 per session plus avg/10, which made it ~90% attendance:
# 100 took ~190 sessions regardless of whether you were actually transmuting.
# It now runs on quality. Each session is worth ATTENDANCE_FLOOR plus a mastery
# bonus that only starts accruing above COPING_CEILING — the score below which
# the judge considers a response coping rather than transmutation.
#
# Sessions to Level 100 at a sustained average:
#     avg 50  ->  ~250     (coping; the curve refuses to move)
#     avg 65  ->  ~73
#     avg 75  ->  ~52
#     avg 85  ->  ~40
#     avg 95  ->  ~33
ATTENDANCE_FLOOR = 0.25   # every completed session is worth a little
COPING_CEILING = 45.0     # below this, only the floor accrues
MASTERY_DIVISOR = 18.0    # points gained per point of score above the ceiling
MASTERY_CAP = 2.75        # ceiling on the per-session mastery bonus


def session_value(avg_score: float) -> float:
    """Level-points a single session is worth at this average score."""
    bonus = (float(avg_score) - COPING_CEILING) / MASTERY_DIVISOR
    return ATTENDANCE_FLOOR + max(0.0, min(MASTERY_CAP, bonus))


def raw_level_from_stats(total_sessions: int, avg_score: float) -> int:
    """Session-derived level before speed gates. Quality-weighted."""
    points = int(total_sessions) * session_value(avg_score)
    return max(MIN_LEVEL, int(MIN_LEVEL + points))


def calculate_level(
    total_sessions: int,
    avg_score: float,
    scheduler: Any,
    speed_stats: Mapping[str, float] | None = None,
) -> int:
    """Calculate effective mastery level and apply scheduler speed gates."""
    raw_level = raw_level_from_stats(total_sessions, avg_score)
    return scheduler.apply_speed_gate(raw_level, dict(speed_stats or {}))


def speed_transmutation_target(level: int) -> int:
    """
    Distinct transmutations expected within a 90-second burst.
    Ramps from 1 early to ~10 at 90+, then slowly toward 15.
    """
    if level < 90:
        return max(1, min(5, 1 + level // 25))
    return min(15, 10 + max(0, level - 90) // 20)


def progression_band(level: int) -> dict:
    """Human-readable band for limitless progression."""
    if level < 16:
        return {
            "band": "install",
            "name": "Install",
            "focus": "Learn transmutation vocabulary and archetypes.",
        }
    if level < 41:
        return {
            "band": "groove",
            "name": "Groove",
            "focus": "Speed Track automaticity and first-attempt quality.",
        }
    if level < 70:
        return {
            "band": "pressure",
            "name": "Pressure",
            "focus": "Tight speed gates and cold recognition.",
        }
    if level < 100:
        return {
            "band": "historical_predict",
            "name": "Historical Arena",
            "focus": "Blind transmutation on real constraints — predict outcomes.",
        }
    if level < 200:
        return {
            "band": "historical_beat",
            "name": "Historical Mastery",
            "focus": "Predict, reveal, then surpass what history did.",
        }
    if level < 350:
        return {
            "band": "pattern_depth",
            "name": "Pattern Depth",
            "focus": "Extract and transfer constraint logic across domains.",
        }
    return {
        "band": "reverse_c2a",
        "name": "Reverse C2A",
        "focus": "Design constraint landscapes; multiply historical seeds.",
    }


def progression_milestones() -> list:
    """Unlock milestones for UI (level, label)."""
    return [
        (5, "Research Dashboard unlocks"),
        (10, "Deep Analysis unlocks"),
        (16, "Speed Track unlocks · correction loop retired"),
        (20, "Meta-reflection retired"),
        (25, "Active lesson display retired"),
        (41, "LLM scenarios retired"),
        (70, "Historical Arena unlocks"),
        (71, "Archetype labels removed from Speed Track"),
        (100, "Beat-history phase unlocks · Compiler Arena (AMAVA)"),
        (200, "Pattern depth band"),
        (350, "Reverse C2A band"),
    ]


def next_milestone(level: int) -> dict | None:
    for unlock_level, label in progression_milestones():
        if unlock_level > level:
            return {"level": unlock_level, "label": label}
    return None


def recommended_action(level: int, scaffold: Any) -> dict:
    """Scheduler-driven default rep for the home screen."""
    if isinstance(scaffold, dict):
        historical = bool(scaffold.get("historical_arena_available"))
        speed_active = bool(scaffold.get("speed_track_active"))
        reps = int(scaffold.get("speed_track_reps") or 20)
    else:
        historical = bool(getattr(scaffold, "historical_arena_available", False))
        speed_active = bool(getattr(scaffold, "speed_track_active", False))
        reps = int(getattr(scaffold, "speed_track_reps", 0) or 20)

    if historical:
        return {
            "action": "historical",
            "title": "Historical Arena",
            "description": "Blind transmutation on real constraints — predict, reveal, extract pattern.",
        }
    if speed_active:
        return {
            "action": "speedtrack",
            "title": "Speed Track",
            "description": f"{reps or 20} constraints at speed — install automaticity.",
        }
    return {
        "action": "train",
        "title": "Training Session",
        "description": "Install the move — transmute the constraint into advantage.",
    }
