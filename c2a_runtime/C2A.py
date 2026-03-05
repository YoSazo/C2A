#!/usr/bin/env python3
"""C2A default app: serves web UI and backend training APIs."""

import argparse
import json
import os
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

from constraint_archetypes import get_archetype


ROOT = Path(__file__).parent
HTML_PATH = ROOT.parent / "ui" / "c2a_training.html"


class C2AService:
    """Backend service wrapping scenario generation and evaluation."""

    def __init__(self):
        # Lazy import to avoid killing server startup when optional deps are missing.
        from llm_client import create_client_from_env
        from llm_scenario_engine import LLMScenarioEngine
        from llm_transmutation_judge import TransmutationJudge

        self.llm = create_client_from_env()
        model = getattr(self.llm, "model", "qwen2.5:14b")
        self.scenario_engine = LLMScenarioEngine(model=model, llm_client=self.llm)
        self.judge = TransmutationJudge(model=model, llm_client=self.llm)

    def generate_scenario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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

        new_title = score.pattern_identified or "Sharpen The Constraint"
        new_question = score.growth_edge or "What advantage disappears if the constraint is removed?"

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
            "new_lesson_title": new_title,
            "new_lesson_question": new_question,
        }

    def chat_raw(self, payload: Dict[str, Any]) -> str:
        """Direct chat passthrough for advanced frontend prompts."""
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


def get_service() -> Optional[C2AService]:
    global SERVICE, SERVICE_INIT_ERROR
    if SERVICE is not None:
        return SERVICE
    if SERVICE_INIT_ERROR is not None:
        return None
    try:
        SERVICE = C2AService()
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


class C2ARequestHandler(BaseHTTPRequestHandler):
    """HTTP routes for C2A web app."""

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

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        if self.path == "/api/scenario":
            payload = self._read_json()
            service = get_service()
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
            payload = self._read_json()
            service = get_service()
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
            payload = self._read_json()
            service = get_service()
            if service is None:
                self._send_json({"text": ""})
                return
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

