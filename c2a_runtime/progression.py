"""Progression and leveling helpers for C2A."""

from typing import Any, Mapping


MIN_LEVEL = 1
MAX_LEVEL = 100


def calculate_level(total_sessions: int, avg_score: float, scheduler: Any, speed_stats: Mapping[str, float] | None = None) -> int:
    """Calculate effective mastery level and apply scheduler speed gates."""
    raw_level = int((total_sessions * 0.5) + (avg_score / 10))
    clamped_level = max(MIN_LEVEL, min(MAX_LEVEL, raw_level))
    return scheduler.apply_speed_gate(clamped_level, dict(speed_stats or {}))