#!/usr/bin/env python3
"""C2A default app: serves web UI and backend training APIs."""

import argparse
import json
import os
import random
import threading
import time
import traceback
import webbrowser
from dataclasses import asdict
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from constraint_archetypes import get_archetype
from progression import calculate_level
from real_world_log import ConstraintEntry, RealWorldLog
from scaffolding_scheduler import scheduler as scaffolding_scheduler
from speed_track import CONSTRAINT_POOL, RepResult, SpeedTrack, SpeedTrackSession


ROOT = Path(__file__).parent
HTML_PATH = ROOT.parent / "ui" / "c2a_training.html"
MEMORY_DIR = ROOT.parent / "memory_data"
WEB_STATE_PATH = MEMORY_DIR / "web_state.json"


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
            "active_lesson": None,
            "domain": None,
            "selected_arch": "velocity",
            "llm_model": "qwen3.5:9b",
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

    def _compute_level(self, speed_stats: Dict[str, float]) -> int:
        sessions = self.data.get("sessions", [])
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
                "active_lesson": self.data.get("active_lesson"),
                "domain": self.data.get("domain"),
                "selected_arch": self.data.get("selected_arch", "velocity"),
                "llm_model": self.data.get("llm_model", "qwen3.5:9b"),
                "current_level": level,
                "speed_stats": speed_stats,
                "scaffold": asdict(scaffold),
                "phase": phase,
                "next_event": next_event,
                "speed_gate": asdict(gate),
                "realworld_today": realworld_status,
            }

    def record_session(self, payload: Dict[str, Any]) -> None:
        with self.lock:
            sessions = self.data.setdefault("sessions", [])
            sessions.append(
                {
                    "score": int(payload.get("score", 0)),
                    "arch": payload.get("arch", "velocity"),
                    "pattern": payload.get("pattern", ""),
                    "lessonMastered": bool(payload.get("lessonMastered", False)),
                    "ts": int(payload.get("ts", int(time.time() * 1000))),
                }
            )
            if "active_lesson" in payload:
                self.data["active_lesson"] = payload.get("active_lesson")
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
        archetype_name = (payload.get("archetype") or "velocity").lower()
        level = int(payload.get("level") or 1)
        session_count = int(payload.get("session_count") or 0)
        active_lesson = payload.get("active_lesson") or {}

        archetype = get_archetype(archetype_name)
        if archetype is None:
            raise ValueError(f"Unknown archetype: {archetype_name}")

        user_profile = {
            "total_sessions": session_count,
            "domain": payload.get("domain", "general life"),
            "strengths": [],
            "weaknesses": [],
            "recent_constraints": [],
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
WEB_STATE = WebStateStore(WEB_STATE_PATH)
SPEED_TRACK = SpeedTrack(data_dir=str(MEMORY_DIR))
REAL_WORLD = RealWorldLog(data_dir=str(MEMORY_DIR))
ACTIVE_SPEED_SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_service() -> Optional[C2AService]:
    global SERVICE, SERVICE_INIT_ERROR
    if SERVICE is not None:
        return SERVICE
    if SERVICE_INIT_ERROR is not None:
        return None
    try:
        SERVICE = C2AService()
        REAL_WORLD.llm = SERVICE.llm
        return SERVICE
    except Exception as exc:
        SERVICE_INIT_ERROR = f"{type(exc).__name__}: {exc}"
        print("[WARN] C2A service init failed; running fallback mode")
        traceback.print_exc()
        return None


def fallback_scenario(payload: Dict[str, Any]) -> Dict[str, Any]:
    archetype_name = (payload.get("archetype") or "velocity").lower()
    return {
        "title": "Compressed Launch Window",
        "situation": "A key decision must ship in under one hour with incomplete information and a fixed budget.",
        "hook": "Delay kills the opportunity.",
        "hint": "Use the constraint to force clarity.",
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


def available_local_models() -> list:
    service = get_service()
    if service is None:
        return ["qwen3.5:9b"]
    try:
        models = service.llm._get_local_models()
        return models or [getattr(service.llm, "model", "qwen3.5:9b")]
    except Exception:
        return [getattr(service.llm, "model", "qwen3.5:9b")]


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
            self._send_json(backend_state_payload())
            return

        if self.path == "/api/realworld/today":
            self._send_json(serializable_today_status())
            return

        if self.path == "/api/models":
            self._send_json({"models": available_local_models(), "selected": WEB_STATE.data.get("llm_model", "qwen3.5:9b")})
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
            self._send_json(backend_state_payload())
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

        if self.path == "/api/scenario":
            service = get_service()
            state = backend_state_payload()
            payload.setdefault("level", state.get("current_level", 1))
            payload.setdefault("session_count", len(state.get("sessions", [])))
            payload.setdefault("active_lesson", state.get("active_lesson"))
            payload.setdefault("llm_model", state.get("llm_model", "qwen3.5:9b"))
            payload.setdefault("domain", (state.get("domain") or {}).get("field", "general life"))
            payload.setdefault("llm_model", state.get("llm_model", "qwen3.5:9b"))
            if service is None:
                self._send_json(fallback_scenario(payload))
                return
            try:
                data = service.generate_scenario(payload)
            except Exception:
                data = fallback_scenario(payload)
            self._send_json(data)
            return

        if self.path == "/api/evaluate":
            service = get_service()
            state = backend_state_payload()
            payload.setdefault("level", state.get("current_level", 1))
            payload.setdefault("session_count", len(state.get("sessions", [])))
            payload.setdefault("active_lesson", state.get("active_lesson"))
            payload.setdefault("llm_model", state.get("llm_model", "qwen3.5:9b"))
            if service is None:
                self._send_json(fallback_evaluation())
                return
            try:
                data = service.evaluate_transmutation(payload)
            except Exception:
                data = fallback_evaluation()
            self._send_json(data)
            return

        if self.path == "/api/llm":
            service = get_service()
            if service is None:
                self._send_json({"text": ""})
                return
            state = backend_state_payload()
            payload.setdefault("llm_model", state.get("llm_model", "qwen3.5:9b"))
            try:
                text = service.chat_raw(payload)
            except Exception:
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


