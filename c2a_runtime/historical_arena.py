"""
historical_arena.py
===================
Historical Arena: blind predict → reveal → pattern extract → (optional) beat history.

Uses real historical constraints with known outcomes for scored practice.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any, Dict, List, Optional

from historical_scenarios import SCENARIOS
from progression import progression_band, speed_transmutation_target


HISTORICAL_ARENA_UNLOCK = 70
BEAT_HISTORY_UNLOCK = 100


def arena_unlocked(level: int) -> bool:
    return level >= HISTORICAL_ARENA_UNLOCK


def beat_history_unlocked(level: int) -> bool:
    return level >= BEAT_HISTORY_UNLOCK


def _scenario_ids_for_level(level: int) -> List[int]:
    ids = sorted(SCENARIOS.keys())
    if level < 100:
        return [i for i in ids if i <= 10] or ids[:5]
    if level < 200:
        return [i for i in ids if i <= 15] or ids
    return ids


def pick_scenario(level: int, exclude_ids: Optional[List[int]] = None) -> dict:
    """Return full scenario dict including id."""
    exclude = set(exclude_ids or [])
    pool = [i for i in _scenario_ids_for_level(level) if i not in exclude]
    if not pool:
        pool = _scenario_ids_for_level(level)
    scenario_id = random.choice(pool)
    data = dict(SCENARIOS[scenario_id])
    data["id"] = scenario_id
    return data


def blind_scenario_payload(scenario: dict, level: int) -> dict:
    """Scenario shown before reveal — no outcome or pattern."""
    target = speed_transmutation_target(level)
    return {
        "id": scenario["id"],
        "title": scenario.get("title", "Historical Scenario"),
        "year": scenario.get("year"),
        "domain": scenario.get("domain", "General"),
        "difficulty": scenario.get("difficulty", ""),
        "situation": scenario.get("situation", ""),
        "explicit_constraint": scenario.get("explicit_constraint", ""),
        "hint": scenario.get("hint", ""),
        "success_criteria": scenario.get("success_criteria", ""),
        "target_transmutations": target,
        "time_limit_seconds": 90,
        "phase": "predict",
        "beat_history_enabled": beat_history_unlocked(level),
        "band": progression_band(level),
    }


def reveal_payload(scenario: dict) -> dict:
    return {
        "historical_outcome": scenario.get("historical_outcome", ""),
        "constraint_logic_pattern": scenario.get("constraint_logic_pattern", ""),
        "transmutation_keywords": scenario.get("transmutation_keywords", []),
    }


def _keyword_overlap_score(text: str, keywords: List[str]) -> int:
    if not text or not keywords:
        return 40
    lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in lower)
    return min(85, 35 + hits * 12)


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
            return {}
    return {}


def _fallback_predict_score(transmutations: List[str], scenario: dict) -> dict:
    joined = "\n".join(transmutations)
    keywords = scenario.get("transmutation_keywords") or []
    score = _keyword_overlap_score(joined, keywords)
    return {
        "predict_score": score,
        "logic_overlap": score,
        "what_matched": "Keyword overlap with historical move (offline fallback).",
        "what_missed": "Full logic comparison requires LLM.",
        "breakdown": {"logic": score, "plausibility": max(40, score - 10), "constraint_use": score},
    }


def evaluate_predict(
    llm,
    transmutations: List[str],
    scenario: dict,
    level: int,
) -> dict:
    """Score blind transmutations against historical constraint logic."""
    joined = "\n\n---\n\n".join(t.strip() for t in transmutations if t.strip()) or "(empty)"
    keywords = scenario.get("transmutation_keywords") or []
    pattern = scenario.get("constraint_logic_pattern", "")
    outcome = scenario.get("historical_outcome", "")

    if llm is None:
        result = _fallback_predict_score(transmutations, scenario)
        result["reveal"] = reveal_payload(scenario)
        return result

    system = (
        "You are a C2A historical arena judge. Score whether the user's blind transmutations "
        "match the CONSTRAINT LOGIC of what historically happened — not exact wording. "
        "Respond ONLY with valid JSON."
    )
    prompt = f"""LEVEL: {level}
SCENARIO: {scenario.get('title', '')}
CONSTRAINT: {scenario.get('explicit_constraint', '')}
SUCCESS CRITERIA: {scenario.get('success_criteria', '')}

USER TRANSMUTATIONS (blind — user has NOT seen the outcome):
{joined}

HISTORICAL OUTCOME (for judging only — user has not seen this yet in UI scoring step):
{outcome}

CONSTRAINT LOGIC PATTERN:
{pattern}

Score predict phase 0-100 on:
- logic_overlap: structural match to historical move class
- plausibility: would this have been viable
- constraint_use: constraint is fuel, not just tolerated

Also provide brief what_matched and what_missed strings.

JSON:
{{
  "predict_score": 0-100,
  "logic_overlap": 0-100,
  "plausibility": 0-100,
  "constraint_use": 0-100,
  "what_matched": "...",
  "what_missed": "..."
}}"""

    try:
        raw = llm.chat(prompt=prompt, system=system)
        data = _parse_json_block(raw)
        predict_score = int(data.get("predict_score", 0) or 0)
        if predict_score <= 0:
            predict_score = int(
                (
                    int(data.get("logic_overlap", 0) or 0)
                    + int(data.get("plausibility", 0) or 0)
                    + int(data.get("constraint_use", 0) or 0)
                )
                / 3
            )
        if predict_score <= 0:
            fb = _fallback_predict_score(transmutations, scenario)
            predict_score = fb["predict_score"]
        result = {
            "predict_score": max(0, min(100, predict_score)),
            "logic_overlap": int(data.get("logic_overlap", predict_score) or predict_score),
            "plausibility": int(data.get("plausibility", predict_score) or predict_score),
            "constraint_use": int(data.get("constraint_use", predict_score) or predict_score),
            "what_matched": data.get("what_matched", ""),
            "what_missed": data.get("what_missed", ""),
            "breakdown": {
                "logic": int(data.get("logic_overlap", predict_score) or predict_score),
                "plausibility": int(data.get("plausibility", predict_score) or predict_score),
                "constraint_use": int(data.get("constraint_use", predict_score) or predict_score),
            },
        }
    except Exception:
        result = _fallback_predict_score(transmutations, scenario)

    result["reveal"] = reveal_payload(scenario)
    return result


def _fallback_pattern_score(user_pattern: str, scenario: dict) -> dict:
    canonical = scenario.get("constraint_logic_pattern", "")
    score = 50
    if user_pattern.strip() and canonical:
        u = set(user_pattern.lower().split())
        c = set(canonical.lower().split())
        overlap = len(u & c)
        score = min(80, 40 + overlap)
    return {
        "pattern_score": score,
        "transfer_strength": score,
        "what_worked": "Offline keyword overlap with canonical pattern.",
        "what_missed": "Use LLM for full cross-domain transfer scoring.",
    }


def evaluate_pattern(
    llm,
    user_pattern: str,
    scenario: dict,
    level: int,
) -> dict:
    """Score user's extracted transferable pattern."""
    canonical = scenario.get("constraint_logic_pattern", "")
    if llm is None:
        return _fallback_pattern_score(user_pattern, scenario)

    system = (
        "You are a C2A pattern judge. Score whether the user extracted a transferable "
        "constraint logic pattern — portable across domains. Respond ONLY with valid JSON."
    )
    prompt = f"""LEVEL: {level}
SCENARIO: {scenario.get('title', '')}

CANONICAL PATTERN:
{canonical}

USER EXTRACTED PATTERN:
{user_pattern or '(empty)'}

Score 0-100:
- pattern_score: overall
- transfer_strength: works beyond this one story

JSON:
{{
  "pattern_score": 0-100,
  "transfer_strength": 0-100,
  "what_worked": "...",
  "what_missed": "..."
}}"""

    try:
        raw = llm.chat(prompt=prompt, system=system)
        data = _parse_json_block(raw)
        pattern_score = int(data.get("pattern_score", 0) or 0)
        if pattern_score <= 0:
            pattern_score = _fallback_pattern_score(user_pattern, scenario)["pattern_score"]
        return {
            "pattern_score": max(0, min(100, pattern_score)),
            "transfer_strength": int(data.get("transfer_strength", pattern_score) or pattern_score),
            "what_worked": data.get("what_worked", ""),
            "what_missed": data.get("what_missed", ""),
        }
    except Exception:
        return _fallback_pattern_score(user_pattern, scenario)


def evaluate_beat_history(
    llm,
    transmutation: str,
    scenario: dict,
    level: int,
) -> dict:
    """Score whether user surpassed historical solution (level 100+)."""
    if not beat_history_unlocked(level):
        return {"beat_score": 0, "skipped": True, "reason": "Unlocks at level 100."}

    outcome = scenario.get("historical_outcome", "")
    if llm is None:
        base = _keyword_overlap_score(transmutation, scenario.get("transmutation_keywords") or [])
        return {
            "beat_score": min(70, base),
            "superior": base >= 65,
            "what_worked": "Offline heuristic only.",
            "what_missed": "LLM required for strict beat-history judging.",
            "skipped": False,
        }

    system = (
        "You are a C2A beat-history judge. Decide if the user's transmutation is "
        "STRICTLY SUPERIOR to what historically happened — plausible, passes removal test, "
        "not fantasy. Respond ONLY with valid JSON."
    )
    prompt = f"""LEVEL: {level}
SCENARIO: {scenario.get('title', '')}
HISTORICAL OUTCOME: {outcome}
USER BEAT TRANSMUTATION: {transmutation or '(empty)'}

JSON:
{{
  "beat_score": 0-100,
  "superior": true/false,
  "what_worked": "...",
  "what_missed": "..."
}}"""

    try:
        raw = llm.chat(prompt=prompt, system=system)
        data = _parse_json_block(raw)
        beat_score = int(data.get("beat_score", 0) or 0)
        return {
            "beat_score": max(0, min(100, beat_score)),
            "superior": bool(data.get("superior", beat_score >= 75)),
            "what_worked": data.get("what_worked", ""),
            "what_missed": data.get("what_missed", ""),
            "skipped": False,
        }
    except Exception:
        base = _keyword_overlap_score(transmutation, scenario.get("transmutation_keywords") or [])
        return {
            "beat_score": min(70, base),
            "superior": False,
            "what_worked": "",
            "what_missed": "Evaluation failed; try again.",
            "skipped": False,
        }


def composite_session_score(
    predict_score: int,
    pattern_score: int,
    beat_score: int | None = None,
    beat_enabled: bool = False,
) -> int:
    """Weighted final score for a historical arena session."""
    if beat_enabled and beat_score is not None:
        return int(round(predict_score * 0.45 + pattern_score * 0.35 + beat_score * 0.20))
    return int(round(predict_score * 0.55 + pattern_score * 0.45))
