#!/usr/bin/env python3
"""C2A default app: serves web UI and backend training APIs."""

import argparse
import json
import os
import random
import re
import threading
import time
import traceback
import webbrowser
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from constraint_archetypes import get_archetype
from historical_arena import (
    arena_unlocked,
    beat_history_unlocked,
    blind_scenario_payload,
    composite_session_score,
    evaluate_beat_history,
    evaluate_pattern,
    evaluate_predict,
    pick_scenario,
)
from progression import (
    calculate_level,
    next_milestone,
    progression_band,
    progression_milestones,
    recommended_action,
    speed_transmutation_target,
)
from real_world_log import ConstraintEntry, RealWorldLog
from scaffolding_scheduler import scheduler as scaffolding_scheduler
from speed_track import CONSTRAINT_POOL, RepResult, SpeedTrack, SpeedTrackSession
from amava_engine import IDEAL_LEVEL, compile_transmutations, default_siblings_per_level, load_specs


ROOT = Path(__file__).parent
HTML_PATH = ROOT.parent / "ui" / "c2a_training.html"
MEMORY_DIR = ROOT.parent / "memory_data"
WEB_STATE_PATH = MEMORY_DIR / "web_state.json"

def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return max(1.0, float(raw))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


SCENARIO_TIMEOUT_SEC = _env_float("C2A_SCENARIO_TIMEOUT_SEC", 12.0)
EVALUATE_TIMEOUT_SEC = _env_float("C2A_EVALUATE_TIMEOUT_SEC", 20.0)
CHAT_TIMEOUT_SEC = _env_float("C2A_CHAT_TIMEOUT_SEC", 20.0)
TIMEBOX_POOL = ThreadPoolExecutor(max_workers=_env_int("C2A_TIMEBOX_WORKERS", 8))


class WebStateStore:
    """Persistent web/desktop state owned by backend logic."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _default(self) -> Dict[str, Any]:
        return {
            "sessions": [],
            "historical_sessions": [],
            "active_lesson": None,
            "domain": None,
            "selected_arch": "velocity",
            "llm_model": "",
        }

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self._default()
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            default = self._default()
            default.update(data if isinstance(data, dict) else {})
            return default
        except Exception:
            return self._default()

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def _all_scored_sessions(self) -> list:
        training = self.data.get("sessions", []) or []
        historical = self.data.get("historical_sessions", []) or []
        return list(training) + list(historical)

    def _compute_level(self, speed_stats: Dict[str, float]) -> int:
        sessions = self._all_scored_sessions()
        total = len(sessions)
        avg = 0.0
        if total:
            avg = sum(float(s.get("score", 0)) for s in sessions) / total
        return calculate_level(
            total_sessions=total,
            avg_score=avg,
            scheduler=scaffolding_scheduler,
            speed_stats=speed_stats,
        )

    def get_payload(self, speed_stats: Dict[str, float], realworld_status: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            level = self._compute_level(speed_stats)
            scaffold = scaffolding_scheduler.get_feature_state(level)
            phase = scaffolding_scheduler.describe_current_phase(level)
            next_event = scaffolding_scheduler.get_next_retirement(level)
            gate = scaffolding_scheduler.check_speed_gate(level, speed_stats)

            return {
                "sessions": self.data.get("sessions", []),
                "historical_sessions": self.data.get("historical_sessions", []),
                "active_lesson": self.data.get("active_lesson"),
                "domain": self.data.get("domain"),
                "selected_arch": self.data.get("selected_arch", "velocity"),
                "llm_model": self.data.get("llm_model", ""),
                "current_level": level,
                "speed_stats": speed_stats,
                "scaffold": asdict(scaffold),
                "phase": phase,
                "next_event": next_event,
                "speed_gate": asdict(gate),
                "realworld_today": realworld_status,
                "progression_band": progression_band(level),
                "next_milestone": next_milestone(level),
                "progression_milestones": progression_milestones(),
                "speed_transmutation_target": speed_transmutation_target(level),
                "recommended_action": recommended_action(level, scaffold),
            }

    def record_session(self, payload: Dict[str, Any]) -> None:
        with self.lock:
            sessions = self.data.setdefault("sessions", [])
            transmutations = payload.get("transmutations") or []
            if not isinstance(transmutations, list):
                transmutations = []
            sessions.append(
                {
                    "score": int(payload.get("score", 0)),
                    "arch": payload.get("arch", "velocity"),
                    "pattern": payload.get("pattern", ""),
                    "lessonMastered": bool(payload.get("lessonMastered", False)),
                    "ts": int(payload.get("ts", int(time.time() * 1000))),
<<<<<<< HEAD
                    "scenario_title": payload.get("scenario_title", ""),
                    "scenario_situation": payload.get("scenario_situation", ""),
                    "scenario_hint": payload.get("scenario_hint", ""),
                    "session_duration": float(payload.get("session_duration", 0.0) or 0.0),
                    "timed_out": bool(payload.get("timed_out", False)),
                    "transmutations": payload.get("transmutations", []) or [],
                    "detection_required": bool(payload.get("detection_required", False)),
                    "detection_success": payload.get("detection_success"),
                    "detection_user_archetype": payload.get("detection_user_archetype", ""),
                    "detection_user_answer": payload.get("detection_user_answer", ""),
                    "detection_correct_archetype": payload.get("detection_correct_archetype", ""),
                    "detection_correct_answer": payload.get("detection_correct_answer", ""),
                    "detection_confusion_type": payload.get("detection_confusion_type", ""),
                    "meta_reflection": payload.get("meta_reflection", ""),
                    "breakthrough": bool(payload.get("breakthrough", False)),
=======
                    "detection_required": bool(payload.get("detection_required", False)),
                    "detection_success": bool(payload.get("detection_success", False)),
                    "detection_user_arch": str(payload.get("detection_user_arch", "")),
                    "detection_user_constraint": str(payload.get("detection_user_constraint", "")),
                    "target_transmutations": int(payload.get("target_transmutations", 1)),
                    "completed_transmutations": int(payload.get("completed_transmutations", 1)),
                    "time_taken_total": float(payload.get("time_taken_total", 0.0)),
                    "real_life_mode": bool(payload.get("real_life_mode", False)),
                    "transmutations": transmutations,
>>>>>>> refs/remotes/origin/main
                }
            )
            if "active_lesson" in payload:
                self.data["active_lesson"] = payload.get("active_lesson")
            self._save()

    def record_amava_session(self, payload: Dict[str, Any]) -> None:
        with self.lock:
            sessions = self.data.setdefault("amava_sessions", [])
            sessions.append(
                {
                    "problem_statement": payload.get("problem_statement", ""),
                    "baseline_constraint": payload.get("baseline_constraint", ""),
                    "level": int(payload.get("level", 1)),
                    "summary": payload.get("summary", {}),
                    "survivor_indices": payload.get("survivor_indices", []) or [],
                    "ts": int(payload.get("ts", int(time.time() * 1000))),
                }
            )
            self._save()

    def record_historical_session(self, payload: Dict[str, Any]) -> None:
        with self.lock:
            sessions = self.data.setdefault("historical_sessions", [])
            sessions.append(
                {
                    "session_type": "historical",
                    "score": int(payload.get("score", 0)),
                    "predict_score": int(payload.get("predict_score", 0)),
                    "pattern_score": int(payload.get("pattern_score", 0)),
                    "beat_score": int(payload.get("beat_score", 0) or 0),
                    "scenario_id": payload.get("scenario_id"),
                    "scenario_title": payload.get("scenario_title", ""),
                    "transmutations": payload.get("transmutations", []) or [],
                    "user_pattern": payload.get("user_pattern", ""),
                    "beat_transmutation": payload.get("beat_transmutation", ""),
                    "ts": int(payload.get("ts", int(time.time() * 1000))),
                }
            )
            self._save()

    def update_domain(self, domain: Dict[str, Any]) -> None:
        with self.lock:
            self.data["domain"] = domain
            self._save()

    def set_selected_arch(self, arch: str) -> None:
        with self.lock:
            self.data["selected_arch"] = arch
            self._save()

    def set_llm_model(self, model: str) -> None:
        with self.lock:
            self.data["llm_model"] = model
            self._save()


class C2AService:
    """Backend service wrapping scenario generation and evaluation."""

    def __init__(self):
        from llm_client import create_client_from_env
        from llm_scenario_engine import LLMScenarioEngine
        from llm_transmutation_judge import TransmutationJudge

        self.llm = create_client_from_env()
        model = getattr(self.llm, "model", "qwen3.5:9b")
        self.scenario_engine = LLMScenarioEngine(model=model, llm_client=self.llm)
        self.judge = TransmutationJudge(model=model, llm_client=self.llm)

    def apply_model_override(self, model_name: Optional[str]) -> None:
        if not model_name:
            return
        # Prevent invalid cross-provider overrides (e.g. qwen model while using Anthropic).
        provider_obj = getattr(getattr(self.llm, "config", None), "provider", "")
        provider = getattr(provider_obj, "value", str(provider_obj)).lower()
        if provider == "anthropic" and not str(model_name).startswith("claude"):
            return
        if provider == "local" and str(model_name).startswith("claude"):
            return
        try:
            self.llm.model = model_name
        except Exception:
            pass
        try:
            self.scenario_engine.model = model_name
        except Exception:
            pass
        try:
            self.judge.model = model_name
        except Exception:
            pass

    def generate_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.apply_model_override(payload.get("llm_model"))
        level = int(payload.get("level") or 1)
        session_count = int(payload.get("session_count") or 0)
        active_lesson = payload.get("active_lesson") or {}

        # Auto-rotate archetype early; honour explicit pick only when requested
        if payload.get("auto_archetype", True) and level <= 20:
            archetype_names = list(ARCHETYPES.keys())
            archetype_name = archetype_names[session_count % len(archetype_names)]
        else:
            archetype_name = (payload.get("archetype") or "velocity").lower()

        archetype = get_archetype(archetype_name)
        if archetype is None:
            raise ValueError(f"Unknown archetype: {archetype_name}")

        domain_field = (payload.get("domain") or "").strip()
        if not domain_field:
            domain_field = "general life"

        recent_titles = payload.get("recent_scenario_titles") or []
        if not recent_titles and payload.get("sessions"):
            recent_titles = [
                s.get("scenario_title", "")
                for s in payload.get("sessions", [])[-8:]
                if s.get("scenario_title")
            ]

        user_profile = {
            "total_sessions": session_count,
            "domain": domain_field,
            "strengths": [],
            "weaknesses": [],
            "recent_constraints": payload.get("recent_constraints") or [],
            "recent_scenario_titles": recent_titles,
        }

        if active_lesson:
            user_profile["recent_patterns"] = [active_lesson.get("title", "")]

        scenario = self.scenario_engine.generate_scenario(
            user_profile=user_profile,
            level=level,
            archetype=archetype,
            force_personal=False,
        )

        return {
            "title": scenario.title,
            "situation": scenario.situation,
            "hook": scenario.emotional_hook,
            "hint": scenario.hint,
            "arch": archetype_name,
        }

    def evaluate_transmutation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.apply_model_override(payload.get("llm_model"))
        transmutation = (payload.get("transmutation") or "").strip()
        if not transmutation:
            transmutation = "(no response)"

        archetype_name = (payload.get("archetype") or "velocity").lower()
        level = int(payload.get("level") or 1)
        active_lesson = payload.get("active_lesson") or {}

        scenario_input = payload.get("scenario") or {}
        scenario = {
            "title": scenario_input.get("title", "Untitled Scenario"),
            "situation": scenario_input.get("situation", "No scenario context."),
            "archetype": archetype_name,
        }

        user_profile = {
            "total_sessions": int(payload.get("session_count") or 0),
            "recent_patterns": payload.get("recent_patterns") or [],
            "strengths": payload.get("strengths") or [],
            "weaknesses": payload.get("weaknesses") or [],
            "recent_transmutations": payload.get("recent_transmutations") or [],
        }

        active_lesson_prompt = ""
        if active_lesson:
            title = active_lesson.get("title", "")
            question = active_lesson.get("question", "")
            active_lesson_prompt = f"{title}: {question}".strip(": ")

        score = self.judge.evaluate_transmutation(
            transmutation=transmutation,
            scenario=scenario,
            user_profile=user_profile,
            level=level,
            active_lesson=active_lesson_prompt,
        )

        return {
            "reframing": int(score.reframing_score),
            "novelty": int(score.novelty_score),
            "practicality": int(score.practicality_score),
            "sophistication": int(score.sophistication_score),
            "what_worked": score.what_worked,
            "what_missed": score.what_missed,
            "growth_edge": score.growth_edge,
            "pattern": score.pattern_identified,
            "breakthrough": bool(score.breakthrough_moment),
            "lesson_applied": bool(getattr(score, "lesson_applied", False)),
            "new_lesson_title": score.pattern_identified or "Sharpen The Constraint",
            "new_lesson_question": score.growth_edge or "What advantage disappears if the constraint is removed?",
        }

    def generate_gold_path(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an exemplar transmutation and teaching breakdown for post-session review."""
        self.apply_model_override(payload.get("llm_model"))
        scenario_input = payload.get("scenario") or {}
        archetype_name = (payload.get("archetype") or "velocity").lower()
        user_transmutation = (payload.get("transmutation") or "").strip() or "(no response)"
        what_missed = (payload.get("what_missed") or "").strip()
        growth_edge = (payload.get("growth_edge") or "").strip()
        level = int(payload.get("level") or 1)
        score = int(payload.get("score") or 0)

        title = scenario_input.get("title", "Untitled Scenario")
        situation = scenario_input.get("situation", "No scenario context.")

        system = (
            "You are a C2A coach. Teach constraint-to-advantage transmutation with concise, "
            "mechanistic examples. Respond ONLY with valid JSON."
        )
        prompt = f"""Create a Gold Path review for this C2A session.

ARCHETYPE: {archetype_name.upper()}
LEVEL: {level}
USER SCORE: {score}/100

SCENARIO: {title}
{situation}

USER TRANSMUTATION:
"{user_transmutation}"

JUDGE FEEDBACK:
- What missed: {what_missed or 'Not provided'}
- Growth edge: {growth_edge or 'Not provided'}

Requirements for exemplar:
- TRUE transmutation (constraint itself is the advantage; removing constraint removes advantage)
- Present-moment leverage (not "this helps later")
- Clear causal mechanism in 1-3 sentences
- Under 60 words

Return ONLY JSON:
{{
  "exemplar_transmutation": "High-quality exemplar transmutation",
  "pattern_name": "Short pattern label",
  "gap_from_user": "What kept the user answer from scoring higher",
  "why_high_score": "Why the exemplar earns a high score (mechanism + removal test)",
  "removal_test": "One sentence: if constraint vanished, why advantage vanishes"
}}"""

        raw = self.llm.chat(prompt, system=system, max_tokens=700)
        try:
            json_start = raw.find("{")
            json_end = raw.rfind("}") + 1
            data = json.loads(raw[json_start:json_end]) if json_start >= 0 and json_end > json_start else {}
        except Exception:
            data = {}

        return {
            "exemplar_transmutation": data.get("exemplar_transmutation", ""),
            "pattern_name": data.get("pattern_name", "Constraint As Lever"),
            "gap_from_user": data.get("gap_from_user", what_missed or growth_edge),
            "why_high_score": data.get("why_high_score", ""),
            "removal_test": data.get("removal_test", ""),
        }

    def chat_raw(self, payload: Dict[str, Any]) -> str:
        self.apply_model_override(payload.get("llm_model"))
        messages = payload.get("messages") or []
        system = payload.get("system")
        max_tokens = int(payload.get("max_tokens") or 1024)
        if not messages:
            return ""

        user_prompt = ""
        history = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                user_prompt = content
            elif role in ("assistant", "system"):
                history.append({"role": role, "content": content})
        if not user_prompt:
            user_prompt = messages[-1].get("content", "")

        return self.llm.chat(
            prompt=user_prompt,
            system=system,
            history=history,
            max_tokens=max_tokens,
        )


SERVICE: Optional[C2AService] = None
SERVICE_INIT_ERROR: Optional[str] = None
RESEARCHER = None
WEB_STATE = WebStateStore(WEB_STATE_PATH)
SPEED_TRACK = SpeedTrack(data_dir=str(MEMORY_DIR))
REAL_WORLD = RealWorldLog(data_dir=str(MEMORY_DIR))
ACTIVE_SPEED_SESSIONS: Dict[str, Dict[str, Any]] = {}


def run_with_timeout(fn, timeout_sec: float):
    future = TIMEBOX_POOL.submit(fn)
    return future.result(timeout=timeout_sec)


def get_service() -> Optional[C2AService]:
    global SERVICE, SERVICE_INIT_ERROR, RESEARCHER
    if SERVICE is not None:
        return SERVICE
    if SERVICE_INIT_ERROR is not None:
        return None
    try:
        SERVICE = C2AService()
        REAL_WORLD.llm = SERVICE.llm
        try:
            from ai_researcher import AIResearcher

            RESEARCHER = AIResearcher(
                llm_client=SERVICE.llm,
                data_dir=str(ROOT / "research_notes"),
            )
        except Exception:
            RESEARCHER = None
        return SERVICE
    except Exception as exc:
        SERVICE_INIT_ERROR = f"{type(exc).__name__}: {exc}"
        print("[WARN] C2A service init failed; running fallback mode")
        traceback.print_exc()
        return None


def get_researcher():
    global RESEARCHER
    if RESEARCHER is not None:
        return RESEARCHER
    service = get_service()
    if service is None:
        return None
    try:
        from ai_researcher import AIResearcher

        RESEARCHER = AIResearcher(
            llm_client=service.llm,
            data_dir=str(ROOT / "research_notes"),
        )
    except Exception:
        traceback.print_exc()
        RESEARCHER = None
    return RESEARCHER


def _web_sessions_for_research() -> list:
    sessions = WEB_STATE.data.get("sessions", [])
    rows = []
    for i, s in enumerate(sessions, start=1):
        rows.append(
            {
                "session_id": i,
                "level": calculate_level(
                    total_sessions=i,
                    avg_score=sum(float(x.get("score", 0)) for x in sessions[:i]) / max(i, 1),
                    scheduler=scaffolding_scheduler,
                    speed_stats=SPEED_TRACK.get_stats_dict(),
                ),
                "archetype": s.get("arch", "velocity"),
                "session_score": int(s.get("score", 0)),
                "pattern": s.get("pattern", ""),
                "scenario_title": s.get("scenario_title", ""),
                "scenario_situation": s.get("scenario_situation", ""),
                "scenario_hint": s.get("scenario_hint", ""),
                "session_duration": float(s.get("session_duration", 0.0) or 0.0),
                "timed_out": bool(s.get("timed_out", False)),
                "transmutations": s.get("transmutations", []) or [],
                "detection_required": bool(s.get("detection_required", False)),
                "detection_success": s.get("detection_success"),
                "detection_user_answer": s.get("detection_user_answer", ""),
                "detection_correct_answer": s.get("detection_correct_answer", ""),
                "detection_confusion_type": s.get("detection_confusion_type", ""),
                "meta_reflection": s.get("meta_reflection", ""),
                "breakthrough": bool(s.get("breakthrough", False)),
                "timestamp": datetime.fromtimestamp(int(s.get("ts", 0)) / 1000).isoformat()
                if s.get("ts")
                else datetime.now().isoformat(),
            }
        )
    return rows


def _research_user_profile() -> Dict[str, Any]:
    state = backend_state_payload()
    sessions = WEB_STATE.data.get("sessions", [])
    archetypes = ["scarcity", "velocity", "asymmetry", "friction", "paradox"]
    perf: Dict[str, float] = {}
    for arch in archetypes:
        arch_scores = [int(s.get("score", 0)) for s in sessions if s.get("arch") == arch]
        perf[arch] = round(sum(arch_scores) / len(arch_scores), 1) if arch_scores else 0.0
    return {
        "current_level": int(state.get("current_level", 1)),
        "total_sessions": len(sessions),
        "archetype_performance": perf,
        "average_score": sum(int(s.get("score", 0)) for s in sessions) / max(len(sessions), 1),
    }


def run_research_observation(payload: Dict[str, Any]) -> None:
    researcher = get_researcher()
    if researcher is None:
        return
    all_sessions = _web_sessions_for_research()
    if not all_sessions:
        return
    latest = all_sessions[-1]
    latest["detection_required"] = bool(payload.get("detection_required", False))
    latest["detection_success"] = payload.get("detection_success")
    latest["detection_user_answer"] = payload.get("detection_user_answer", "")
    latest["detection_correct_answer"] = payload.get("detection_correct_answer", "")
    latest["detection_confusion_type"] = payload.get("detection_confusion_type", "")
    latest["transmutations"] = payload.get("transmutations", [])
    latest["scenario_title"] = payload.get("scenario_title", "")
    latest["best_score"] = int(payload.get("score", latest["session_score"]))
    latest["divergence_score"] = int(payload.get("divergence", 0))
    latest["meta_reflection"] = payload.get("meta_reflection", "")
    latest["breakthrough"] = bool(payload.get("breakthrough", False))
    try:
        researcher.observe_session(latest, all_sessions, _research_user_profile())
    except Exception:
        traceback.print_exc()


def _observed_session_ids() -> set:
    ids = set()
    notes_dir = ROOT / "research_notes" / "session_notes"
    try:
        for f in notes_dir.glob("session_*.json"):
            name = f.stem  # session_0007
            sid = int(name.split("_")[-1])
            ids.add(sid)
    except Exception:
        pass
    return ids


def ensure_research_backfill(limit: int = 50) -> None:
    """Backfill missing researcher observations from existing saved sessions."""
    researcher = get_researcher()
    if researcher is None:
        return
    all_sessions = _web_sessions_for_research()
    if not all_sessions:
        return

    existing = _observed_session_ids()
    pending = [s for s in all_sessions if int(s.get("session_id", 0)) not in existing]
    if not pending:
        return

    user_profile = _research_user_profile()
    for sess in pending[: max(1, limit)]:
        try:
            # Historic web sessions don't include full raw details; researcher still works with summary fields.
            researcher.observe_session(sess, all_sessions, user_profile)
        except Exception:
            traceback.print_exc()
            break


def fallback_scenario(payload: Dict[str, Any]) -> Dict[str, Any]:
    from llm_scenario_engine import general_domain_for_session
    from constraint_archetypes import ARCHETYPES

    session_count = int(payload.get("session_count") or 0)
    names = list(ARCHETYPES.keys())
    archetype_name = names[session_count % len(names)]
    domain = general_domain_for_session(session_count)
    return {
        "title": f"{domain.split()[0].title()} Constraint",
        "situation": (
            f"In {domain}, a time-critical decision must be made with incomplete information. "
            f"The obvious path is blocked. Stakes are real and immediate."
        ),
        "hook": "The pressure is the teacher.",
        "hint": "Use the limit to force a sharper move.",
        "arch": archetype_name,
    }


def fallback_evaluation() -> Dict[str, Any]:
    return {
        "reframing": 15,
        "novelty": 12,
        "practicality": 12,
        "sophistication": 10,
        "what_worked": "You identified a plausible angle.",
        "what_missed": "The constraint itself did not clearly become the advantage.",
        "growth_edge": "Test whether removing the constraint removes the advantage.",
        "pattern": "Constraint As Lever",
        "breakthrough": False,
        "lesson_applied": False,
        "new_lesson_title": "The Removal Test",
        "new_lesson_question": "If I remove the constraint, does my advantage disappear?",
    }


def serializable_today_status() -> Dict[str, Any]:
    status = REAL_WORLD.get_today_status()
    entries = status.get("entries", [])
    status["entries"] = [e.to_dict() if hasattr(e, "to_dict") else e for e in entries]
    return status


def backend_state_payload() -> Dict[str, Any]:
    speed_stats = SPEED_TRACK.get_stats_dict()
    realworld_status = serializable_today_status()
    return WEB_STATE.get_payload(speed_stats=speed_stats, realworld_status=realworld_status)


def start_speed_session() -> Dict[str, Any]:
    state = backend_state_payload()
    level = int(state["current_level"])
    scaffold = state["scaffold"]
    reps = int(scaffold.get("speed_track_reps", 0))
    show_labels = bool(scaffold.get("archetype_labels_in_speed", True))

    if reps <= 0:
        return {"active": False, "message": "Speed Track unlocks at Level 16."}

    pool = list(CONSTRAINT_POOL)
    random.shuffle(pool)
    selected = pool[:reps]
    if len(selected) < reps:
        selected.extend(random.choices(pool, k=(reps - len(selected))))

    session_id = f"web_speed_{int(time.time() * 1000)}"
    ACTIVE_SPEED_SESSIONS[session_id] = {
        "level": level,
        "show_labels": show_labels,
        "constraints": [{"text": txt, "arch": arch} for txt, arch in selected],
        "created_at": datetime.now().isoformat(),
    }

    return {
        "active": True,
        "session_id": session_id,
        "level": level,
        "reps": reps,
        "show_labels": show_labels,
        "constraints": ACTIVE_SPEED_SESSIONS[session_id]["constraints"],
    }


def finish_speed_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    if not session_id or session_id not in ACTIVE_SPEED_SESSIONS:
        return {"error": "Speed session not found"}

    source = ACTIVE_SPEED_SESSIONS.pop(session_id)
    results_input = payload.get("results") or []

    session = SpeedTrackSession(
        session_id=session_id,
        level=int(source.get("level", 1)),
        reps=len(results_input),
        archetype_labels_shown=bool(source.get("show_labels", True)),
    )

    built_results = []
    for item in results_input:
        built_results.append(
            RepResult(
                constraint_text=str(item.get("constraint_text", "")),
                correct_archetype=str(item.get("correct_archetype", "")),
                user_archetype=str(item.get("user_archetype", "")),
                correct=bool(item.get("correct", False)),
                duration_seconds=float(item.get("duration_seconds", 0.0)),
            )
        )

    session.results = built_results
    SPEED_TRACK._compute_stats(session)
    SPEED_TRACK._save_session(session)

    stats = SPEED_TRACK.get_stats_dict()
    level = backend_state_payload()["current_level"]
    gate = asdict(scaffolding_scheduler.check_speed_gate(level, stats))

    return {
        "ok": True,
        "session": session.to_dict(),
        "speed_stats": stats,
        "speed_gate": gate,
    }


def add_realworld_entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    constraint = (payload.get("constraint") or "").strip()
    transmutation = (payload.get("transmutation") or "").strip()
    new_constraint = (payload.get("new_constraint") or "").strip()
    if not constraint:
        return {"error": "constraint is required"}

    now = datetime.now()
    entry = ConstraintEntry(
        entry_id=f"rwl_web_{int(now.timestamp() * 1000)}",
        logged_at=now.isoformat(),
        date_str=now.strftime("%Y-%m-%d"),
        constraint=constraint,
        transmutation=transmutation or "(not yet transmuted)",
        new_constraint=new_constraint or "(unknown - loop not yet visible)",
        archetype_guess=(payload.get("archetype") or None),
        domain=(payload.get("domain") or None),
    )
    REAL_WORLD.entries.append(entry)
    REAL_WORLD._save_entries()
    status = serializable_today_status()
    return {
        "ok": True,
        "entry": entry.to_dict(),
        "today": status,
    }


def _historical_scenario_by_id(scenario_id: int) -> Optional[dict]:
    from historical_scenarios import SCENARIOS

    if scenario_id not in SCENARIOS:
        return None
    data = dict(SCENARIOS[scenario_id])
    data["id"] = scenario_id
    return data


def start_historical_scenario(level: int) -> Dict[str, Any]:
    if not arena_unlocked(level):
        return {
            "active": False,
            "message": f"Historical Arena unlocks at Level {70}.",
        }

    historical = WEB_STATE.data.get("historical_sessions", []) or []
    recent_ids = [s.get("scenario_id") for s in historical[-5:] if s.get("scenario_id")]
    scenario = pick_scenario(level, exclude_ids=recent_ids)
    blind = blind_scenario_payload(scenario, level)
    return {"active": True, "scenario": blind}


def evaluate_historical_predict(payload: Dict[str, Any]) -> Dict[str, Any]:
    level = int(payload.get("level") or backend_state_payload()["current_level"])
    scenario_id = int(payload.get("scenario_id") or 0)
    scenario = _historical_scenario_by_id(scenario_id)
    if scenario is None:
        return {"error": "Unknown historical scenario."}

    transmutations = payload.get("transmutations") or []
    if isinstance(transmutations, str):
        transmutations = [transmutations]

    service = get_service()
    llm = service.llm if service else None
    result = evaluate_predict(llm, transmutations, scenario, level)
    result["scenario_id"] = scenario_id
    result["scenario_title"] = scenario.get("title", "")
    return result


def evaluate_historical_pattern(payload: Dict[str, Any]) -> Dict[str, Any]:
    level = int(payload.get("level") or backend_state_payload()["current_level"])
    scenario_id = int(payload.get("scenario_id") or 0)
    scenario = _historical_scenario_by_id(scenario_id)
    if scenario is None:
        return {"error": "Unknown historical scenario."}

    user_pattern = (payload.get("user_pattern") or "").strip()
    service = get_service()
    llm = service.llm if service else None
    result = evaluate_pattern(llm, user_pattern, scenario, level)
    result["scenario_id"] = scenario_id
    return result


def evaluate_historical_beat(payload: Dict[str, Any]) -> Dict[str, Any]:
    level = int(payload.get("level") or backend_state_payload()["current_level"])
    if not beat_history_unlocked(level):
        return {"error": "Beat-history unlocks at Level 100.", "skipped": True}

    scenario_id = int(payload.get("scenario_id") or 0)
    scenario = _historical_scenario_by_id(scenario_id)
    if scenario is None:
        return {"error": "Unknown historical scenario."}

    transmutation = (payload.get("beat_transmutation") or "").strip()
    service = get_service()
    llm = service.llm if service else None
    result = evaluate_beat_history(llm, transmutation, scenario, level)
    result["scenario_id"] = scenario_id
    return result


def complete_historical_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    level = int(payload.get("level") or backend_state_payload()["current_level"])
    predict_score = int(payload.get("predict_score") or 0)
    pattern_score = int(payload.get("pattern_score") or 0)
    beat_score = payload.get("beat_score")
    beat_score_int = int(beat_score) if beat_score is not None else None
    beat_enabled = beat_history_unlocked(level) and bool(payload.get("beat_attempted"))

    final_score = composite_session_score(
        predict_score=predict_score,
        pattern_score=pattern_score,
        beat_score=beat_score_int,
        beat_enabled=beat_enabled,
    )

    record = {
        "score": final_score,
        "predict_score": predict_score,
        "pattern_score": pattern_score,
        "beat_score": beat_score_int or 0,
        "scenario_id": payload.get("scenario_id"),
        "scenario_title": payload.get("scenario_title", ""),
        "transmutations": payload.get("transmutations", []) or [],
        "user_pattern": payload.get("user_pattern", ""),
        "beat_transmutation": payload.get("beat_transmutation", ""),
        "ts": int(payload.get("ts", int(time.time() * 1000))),
    }
    WEB_STATE.record_historical_session(record)
    state = backend_state_payload()
    state["historical_result"] = {"final_score": final_score, **record}
    return state


def run_amava_compile(payload: Dict[str, Any]) -> Dict[str, Any]:
    """AMAVA: compile transmutations through adversarial validation pipeline."""
    state = backend_state_payload()
    level = int(payload.get("level") or state.get("current_level", 1))
    problem = (payload.get("problem_statement") or "").strip()
    baseline = (payload.get("baseline_constraint") or "").strip()
    raw_tm = payload.get("transmutations") or payload.get("transmutation_text") or ""

    if isinstance(raw_tm, list):
        transmutations = [str(t).strip() for t in raw_tm if str(t).strip()]
    else:
        text = str(raw_tm).strip()
        transmutations = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(transmutations) <= 1 and text:
            transmutations = [ln.strip() for ln in text.splitlines() if ln.strip()]

    service = get_service()
    if service is None:
        return {"error": "LLM service unavailable — configure Ollama or API keys."}

    model = effective_selected_model()
    service.apply_model_override(model)

    transmultiply = payload.get("transmultiply", True)
    if isinstance(transmultiply, str):
        transmultiply = transmultiply.lower() not in ("0", "false", "no")
    siblings_per = payload.get("siblings_per")
    if siblings_per is not None:
        siblings_per = int(siblings_per)
    include_original = payload.get("include_original", True)

    try:
        result = compile_transmutations(
            service.llm,
            problem_statement=problem,
            baseline_constraint=baseline,
            transmutations=transmutations,
            level=level,
            transmultiply=bool(transmultiply),
            siblings_per=siblings_per,
            include_original=bool(include_original),
        )
    except Exception as exc:
        traceback.print_exc()
        return {"error": f"AMAVA compile failed: {exc}"}

    if result.get("error"):
        return result

    WEB_STATE.record_amava_session(
        {
            "problem_statement": problem,
            "baseline_constraint": baseline,
            "level": level,
            "summary": result.get("summary", {}),
            "survivor_indices": result.get("survivor_indices", []),
        }
    )
    result["spec_count"] = len(load_specs())
    result["ideal_level"] = IDEAL_LEVEL
    return result


def amava_info_payload() -> Dict[str, Any]:
    return {
        "name": "AMAVA",
        "full_name": "Adversarial Multi-Agent Validation Architecture",
        "available_at_any_level": True,
        "ideal_level": IDEAL_LEVEL,
        "ideal_level_note": (
            "Compatible at any level. Level 100+ users fire more transmutations per burst "
            "with higher novelty — this architecture scales with that throughput."
        ),
        "phases": [
            "Transmultiplication (human → sibling variants)",
            "Epistemic airgap (strip + graph map)",
            "Grounding engine (spec RAG + deterministic checks)",
            "Red vs Blue tribunal (max 3 patch cycles)",
            "Blind judge (validation matrix)",
            "Compiler handoff (survivor → MVP plan)",
        ],
        "transmultiply_default_siblings": {
            "1-15": default_siblings_per_level(1),
            "16-69": default_siblings_per_level(16),
            "70-99": default_siblings_per_level(70),
            "100+": default_siblings_per_level(100),
        },
        "max_pipeline_items": 40,
        "spec_count": len(load_specs()),
    }


def available_local_models() -> list:
    service = get_service()
    if service is None:
        return ["qwen3.5:9b"]
    try:
        provider_obj = getattr(getattr(service.llm, "config", None), "provider", "")
        provider = getattr(provider_obj, "value", str(provider_obj)).lower()
        if provider == "anthropic":
            return [getattr(service.llm, "model", "claude-sonnet-4-20250514")]
        models = service.llm._get_local_models()
        return models or [getattr(service.llm, "model", "qwen3.5:9b")]
    except Exception:
        return [getattr(service.llm, "model", "qwen3.5:9b")]


def effective_selected_model() -> str:
    """Return provider-compatible selected model for UI/backend requests."""
    service = get_service()
    state_model = (WEB_STATE.data.get("llm_model") or "").strip()
    if service is None:
        return state_model or "qwen3.5:9b"

    current_model = str(getattr(service.llm, "model", "") or "")
    provider_obj = getattr(getattr(service.llm, "config", None), "provider", "")
    provider = getattr(provider_obj, "value", str(provider_obj)).lower()

    if provider == "anthropic":
        if state_model.startswith("claude"):
            return state_model
        return current_model or "claude-sonnet-4-20250514"

    if provider == "local":
        if state_model and not state_model.startswith("claude"):
            return state_model
        return current_model or "qwen3.5:9b"

    return state_model or current_model or "qwen3.5:9b"


class C2ARequestHandler(BaseHTTPRequestHandler):
    server_version = "C2A/1.0"

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_html()
            return

        if self.path == "/api/health":
            service_ready = get_service() is not None
            payload = {"ok": True, "service_ready": service_ready}
            if SERVICE_INIT_ERROR:
                payload["service_error"] = SERVICE_INIT_ERROR
            self._send_json(payload)
            return

        if self.path == "/api/state":
            payload = backend_state_payload()
            payload["llm_model"] = effective_selected_model()
            self._send_json(payload)
            return

        if self.path == "/api/realworld/today":
            self._send_json(serializable_today_status())
            return

        if self.path == "/api/models":
            self._send_json({"models": available_local_models(), "selected": effective_selected_model()})
            return

        if self.path == "/api/amava/info":
            self._send_json(amava_info_payload())
            return

        if self.path == "/api/research/summary":
            researcher = get_researcher()
            if researcher is None:
                self._send_json({"error": "researcher unavailable"}, status=503)
                return
            summary = researcher.get_research_summary()
            summary["total_sessions_in_app"] = len(WEB_STATE.data.get("sessions", []))
            summary["unobserved_sessions"] = max(
                0, summary.get("total_sessions_in_app", 0) - summary.get("total_sessions_observed", 0)
            )
            self._send_json(summary)
            return

        if self.path.startswith("/api/research/latest"):
            researcher = get_researcher()
            if researcher is None:
                self._send_json({"error": "researcher unavailable"}, status=503)
                return
            try:
                n = int(self._get_query_param("n", "3"))
            except Exception:
                n = 3
            self._send_json({"observations": researcher.get_latest_observations(max(1, min(n, 10)))})
            return

        if self.path == "/api/research/proposals":
            researcher = get_researcher()
            if researcher is None:
                self._send_json({"error": "researcher unavailable"}, status=503)
                return
            self._send_json({"proposals": researcher.get_all_refinement_proposals()})
            return

        if self.path.startswith("/api/historical/scenario"):
            state = backend_state_payload()
            level = int(self._get_query_param("level", str(state.get("current_level", 1))))
            self._send_json(start_historical_scenario(level))
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        payload = self._read_json()

        if self.path == "/api/state/select-archetype":
            arch = (payload.get("archetype") or "velocity").lower()
            if get_archetype(arch) is None:
                self._send_json({"error": "unknown archetype"}, status=400)
                return
            WEB_STATE.set_selected_arch(arch)
            self._send_json({"ok": True, "selected_arch": arch})
            return

        if self.path == "/api/state/domain":
            WEB_STATE.update_domain(payload or {})
            self._send_json({"ok": True})
            return

        if self.path == "/api/state/model":
            model = (payload.get("model") or "").strip()
            if not model:
                self._send_json({"error": "model is required"}, status=400)
                return
            WEB_STATE.set_llm_model(model)
            self._send_json({"ok": True, "llm_model": model})
            return

        if self.path == "/api/session":
            WEB_STATE.record_session(payload)
            run_research_observation(payload)
            self._send_json(backend_state_payload())
            return

        if self.path == "/api/research/report":
            researcher = get_researcher()
            if researcher is None:
                self._send_json({"error": "researcher unavailable"}, status=503)
                return
            ensure_research_backfill()
            all_sessions = _web_sessions_for_research()
            if len(all_sessions) < 1:
                self._send_json({"error": "No sessions yet. Complete one session first."}, status=400)
                return
            try:
                report = researcher.generate_research_report(all_sessions, _research_user_profile())
                reports_dir = ROOT / "research_notes" / "reports"
                latest_path = ""
                try:
                    files = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if files:
                        latest_path = str(files[0])
                except Exception:
                    latest_path = ""
                self._send_json(
                    {
                        "ok": True,
                        "report_preview": report[:2500],
                        "report_path": latest_path,
                        "note": "Low-session report: insights are preliminary."
                        if len(all_sessions) < 5
                        else "",
                    }
                )
            except Exception:
                traceback.print_exc()
                self._send_json({"error": "Failed to generate report"}, status=500)
            return

        if self.path == "/api/research/backfill":
            researcher = get_researcher()
            if researcher is None:
                self._send_json({"error": "researcher unavailable"}, status=503)
                return
            ensure_research_backfill(limit=1)
            summary = researcher.get_research_summary()
            summary["total_sessions_in_app"] = len(WEB_STATE.data.get("sessions", []))
            summary["unobserved_sessions"] = max(
                0, summary.get("total_sessions_in_app", 0) - summary.get("total_sessions_observed", 0)
            )
            self._send_json({"ok": True, "summary": summary})
            return

        if self.path == "/api/speedtrack/start":
            self._send_json(start_speed_session())
            return

        if self.path == "/api/speedtrack/finish":
            result = finish_speed_session(payload)
            status = 400 if "error" in result else 200
            self._send_json(result, status=status)
            return

        if self.path == "/api/realworld/add":
            result = add_realworld_entry(payload)
            status = 400 if "error" in result else 200
            self._send_json(result, status=status)
            return

        if self.path == "/api/historical/evaluate-predict":
            result = evaluate_historical_predict(payload)
            status = 400 if "error" in result else 200
            self._send_json(result, status=status)
            return

        if self.path == "/api/historical/evaluate-pattern":
            result = evaluate_historical_pattern(payload)
            status = 400 if "error" in result else 200
            self._send_json(result, status=status)
            return

        if self.path == "/api/historical/evaluate-beat":
            result = evaluate_historical_beat(payload)
            status = 400 if "error" in result else 200
            self._send_json(result, status=status)
            return

        if self.path == "/api/historical/complete":
            self._send_json(complete_historical_session(payload))
            return

        if self.path == "/api/amava/compile":
            result = run_amava_compile(payload)
            status = 400 if result.get("error") else 200
            self._send_json(result, status=status)
            return

        if self.path == "/api/scenario":
            service = get_service()
            state = backend_state_payload()
            payload.setdefault("level", state.get("current_level", 1))
            payload.setdefault("session_count", len(state.get("sessions", [])))
            payload.setdefault("sessions", state.get("sessions", []))
            payload.setdefault("active_lesson", state.get("active_lesson"))
            payload.setdefault("llm_model", effective_selected_model())
            payload.setdefault("auto_archetype", True)
            domain_field = (state.get("domain") or {}).get("field") or payload.get("domain") or ""
            payload.setdefault("domain", domain_field.strip() or "general life")
            if service is None:
                self._send_json(fallback_scenario(payload))
                return
            try:
<<<<<<< HEAD
                data = service.generate_scenario(payload)
            except Exception:
                traceback.print_exc()
=======
                data = run_with_timeout(lambda: service.generate_scenario(payload), SCENARIO_TIMEOUT_SEC)
            except FutureTimeoutError:
                print(f"[WARN] /api/scenario timeout after {SCENARIO_TIMEOUT_SEC:.1f}s; using fallback")
                data = fallback_scenario(payload)
            except Exception as exc:
                print(f"[WARN] /api/scenario failed ({type(exc).__name__}); using fallback")
>>>>>>> refs/remotes/origin/main
                data = fallback_scenario(payload)
            self._send_json(data)
            return

        if self.path == "/api/evaluate":
            service = get_service()
            state = backend_state_payload()
            payload.setdefault("level", state.get("current_level", 1))
            payload.setdefault("session_count", len(state.get("sessions", [])))
            payload.setdefault("active_lesson", state.get("active_lesson"))
            payload.setdefault("llm_model", effective_selected_model())
            if service is None:
                self._send_json(fallback_evaluation())
                return
            try:
<<<<<<< HEAD
                data = service.evaluate_transmutation(payload)
            except Exception:
                traceback.print_exc()
=======
                data = run_with_timeout(lambda: service.evaluate_transmutation(payload), EVALUATE_TIMEOUT_SEC)
            except FutureTimeoutError:
                print(f"[WARN] /api/evaluate timeout after {EVALUATE_TIMEOUT_SEC:.1f}s; using fallback")
                data = fallback_evaluation()
            except Exception as exc:
                print(f"[WARN] /api/evaluate failed ({type(exc).__name__}); using fallback")
>>>>>>> refs/remotes/origin/main
                data = fallback_evaluation()
            self._send_json(data)
            return

        if self.path == "/api/gold-path":
            service = get_service()
            if service is None:
                self._send_json({"error": "service unavailable"}, status=503)
                return
            payload.setdefault("llm_model", effective_selected_model())
            try:
                data = service.generate_gold_path(payload)
            except Exception:
                traceback.print_exc()
                self._send_json({"error": "Failed to generate gold path"}, status=500)
                return
            self._send_json(data)
            return

        if self.path == "/api/llm":
            service = get_service()
            if service is None:
                self._send_json({"text": ""})
                return
            payload.setdefault("llm_model", effective_selected_model())
            try:
<<<<<<< HEAD
                text = service.chat_raw(payload)
            except Exception:
                traceback.print_exc()
=======
                text = run_with_timeout(lambda: service.chat_raw(payload), CHAT_TIMEOUT_SEC)
            except FutureTimeoutError:
                print(f"[WARN] /api/llm timeout after {CHAT_TIMEOUT_SEC:.1f}s")
                text = ""
            except Exception as exc:
                print(f"[WARN] /api/llm failed ({type(exc).__name__})")
>>>>>>> refs/remotes/origin/main
                text = ""
            self._send_json({"text": text})
            return

        self._send_json({"error": "Not found"}, status=404)

    def _serve_html(self):
        if not HTML_PATH.exists():
            self._send_json({"error": "c2a_training.html not found"}, status=500)
            return
        content = HTML_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _get_query_param(self, key: str, default: str = "") -> str:
        if "?" not in self.path:
            return default
        query = self.path.split("?", 1)[1]
        for pair in query.split("&"):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            if k == key:
                return v
        return default

    def _send_json(self, payload: Dict[str, Any], status: int = 200):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, fmt: str, *args):
        pass


def run_server(port: int, open_browser: bool):
    server = ThreadingHTTPServer(("127.0.0.1", port), C2ARequestHandler)
    url = f"http://127.0.0.1:{port}/"
    print("C2A web app starting...")
    print(f"Serving: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nC2A stopped.")
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run C2A web app")
    parser.add_argument("--port", type=int, default=int(os.environ.get("C2A_PORT", "8765")))
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser")
    args = parser.parse_args()
    run_server(port=args.port, open_browser=(not args.no_browser))


if __name__ == "__main__":
    main()



